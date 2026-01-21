import logging
import os
import re
import unicodedata

import pandas as pd

from .logger import get_logger

logger = get_logger(__name__, level=logging.DEBUG)


def load_excel(file_path: str, sheet_name: str | int = 0) -> pd.DataFrame:
    """Load data from an Excel file."""
    return pd.read_excel(file_path, sheet_name=sheet_name)


def to_ascii(text: str) -> str:
    """Convert accented/special characters to plain ASCII."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def to_canonical(text: str) -> str:
    """Convert text to canonical format: ASCII lowercase with single underscores replacing spaces."""
    if not text:
        return ""
    # Replace N/A substring by empty string
    text = re.sub(r"\bN/A\b", "", text, flags=re.IGNORECASE).strip()
    # Convert to ASCII, lowercase, replace spaces with underscores, then normalize multiple underscores
    canonical = to_ascii(text).lower().replace(" ", "_")
    # Replace multiple underscores with single underscore
    canonical = re.sub(r"_+", "_", canonical)
    return canonical


def add_canonical_name_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a CanonicalName column by combining Nombre and Apellidos, normalized to canonical format."""
    # Combine Nombre and Apellidos, normalizing whitespace
    df["CanonicalName"] = (
        (df["Nombre"].fillna("").astype(str).str.strip() + " " + df["Apellidos"].fillna("").astype(str).str.strip())
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Convert to canonical format
    df["CanonicalName"] = df["CanonicalName"].apply(to_canonical)

    return df


def add_tutor_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Parse Tutores column into Tutor1 and Tutor2 columns in canonical format, handling both / and // separators.

    Deduplicates tutors so that if Tutor1 and Tutor2 are the same, only Tutor1 is kept.
    """

    # Split by '/' and filter out empty parts (handles both / and //)
    def parse_tutores(tutores_value):
        if pd.isna(tutores_value) or str(tutores_value).strip() == "":
            return pd.Series(["", ""])

        tutores_value = re.sub(r"\bN/A\b", "", tutores_value, flags=re.IGNORECASE).strip()

        # Split by '/' and filter out empty strings
        parts = [part.strip() for part in str(tutores_value).split("/") if part.strip()]

        tutor1 = parts[0] if len(parts) >= 1 else ""
        tutor2 = parts[1] if len(parts) >= 2 else ""

        return pd.Series([tutor1, tutor2])

    # Apply parsing to all rows
    df[["Tutor1", "Tutor2"]] = df["Tutores"].apply(parse_tutores)

    # Convert to canonical format
    df["Tutor1"] = df["Tutor1"].apply(to_canonical)
    df["Tutor2"] = df["Tutor2"].apply(to_canonical)

    # Deduplicate: if Tutor1 and Tutor2 are the same, clear Tutor2
    mask = (df["Tutor1"] != "") & (df["Tutor1"] == df["Tutor2"])
    df.loc[mask, "Tutor2"] = ""

    return df


def generate_players_df(all_df: pd.DataFrame) -> pd.DataFrame:
    # Filter for players (Deportista) or Fans
    is_player = all_df["Roles"].str.contains("Deportista", na=False)
    is_strict_fan = all_df["Roles"].fillna("").str.strip() == "Fan"
    players_df = all_df[is_player | is_strict_fan].copy()
    players_df = add_canonical_name_column(players_df)
    players_df = add_tutor_columns(players_df)
    return players_df


def generate_tutors_df(all_df: pd.DataFrame) -> pd.DataFrame:
    # Filter for tutors only
    tutors_df = all_df[all_df["Roles"].str.contains("Tutor", na=False)].copy()
    tutors_df = add_canonical_name_column(tutors_df)
    return tutors_df


def merge_tutor_info(players_df: pd.DataFrame, tutors_df: pd.DataFrame) -> pd.DataFrame:
    """Merge tutor ID information (DNI, NIE, Pasaporte) into players dataframe.

    For each tutor column (Tutor1, Tutor2), looks up the tutor by CanonicalName
    in tutors_df and adds corresponding ID columns. If a tutor is not found,
    the tutor name is replaced with 'not_found'.
    """
    # Create a lookup dictionary from tutors_df indexed by CanonicalName
    # Drop duplicates keeping first occurrence to handle tutors with same name
    tutors_unique = tutors_df.drop_duplicates(subset="CanonicalName", keep="first")
    tutor_lookup = tutors_unique.set_index("CanonicalName")[["DNI", "NIE", "Pasaporte"]].to_dict("index")

    # Initialize new columns
    players_df["Tutor1DNI"] = ""
    players_df["Tutor1NIE"] = ""
    players_df["Tutor1Passport"] = ""
    players_df["Tutor2DNI"] = ""
    players_df["Tutor2NIE"] = ""
    players_df["Tutor2Passport"] = ""

    # Process Tutor1
    for idx, row in players_df.iterrows():
        tutor1_name = row["Tutor1"]
        if tutor1_name and tutor1_name != "":
            if tutor1_name in tutor_lookup:
                tutor_info = tutor_lookup[tutor1_name]
                players_df.at[idx, "Tutor1DNI"] = tutor_info.get("DNI", "") or ""
                players_df.at[idx, "Tutor1NIE"] = tutor_info.get("NIE", "") or ""
                players_df.at[idx, "Tutor1Passport"] = tutor_info.get("Pasaporte", "") or ""
            else:
                logger.warning(f"Tutor1 '{tutor1_name}' not found for player '{row['CanonicalName']}'")
                players_df.at[idx, "Tutor1"] = "not_found"

        tutor2_name = row["Tutor2"]
        if tutor2_name and tutor2_name != "":
            if tutor2_name in tutor_lookup:
                tutor_info = tutor_lookup[tutor2_name]
                players_df.at[idx, "Tutor2DNI"] = tutor_info.get("DNI", "") or ""
                players_df.at[idx, "Tutor2NIE"] = tutor_info.get("NIE", "") or ""
                players_df.at[idx, "Tutor2Passport"] = tutor_info.get("Pasaporte", "") or ""
            else:
                logger.warning(f"Tutor2 '{tutor2_name}' not found for player '{row['CanonicalName']}'")
                players_df.at[idx, "Tutor2"] = "not_found"

    return players_df


def find_media_day_players_in_players_df(
    media_day_all_df: pd.DataFrame, players_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:

    # Filter media_day_all_df for players only (Role column contains a number)
    media_day_players = media_day_all_df[
        media_day_all_df["Role"].apply(lambda x: str(x).strip().isdigit() if pd.notna(x) else False)
    ].copy()

    # Get list of canonical names from players_df
    players_canonical_names = players_df["CanonicalName"].tolist()

    def is_found_in_players(media_day_canonical_name: str) -> bool:
        """Check if any players_df CanonicalName starts with the media day CanonicalName."""
        if not media_day_canonical_name:
            return False
        return any(player_name.startswith(media_day_canonical_name) for player_name in players_canonical_names)

    # Determine which media day players are found
    media_day_players["FoundInPlayersDF"] = media_day_players["CanonicalName"].apply(is_found_in_players)

    found_df = media_day_players[media_day_players["FoundInPlayersDF"]].copy()
    not_found_df = media_day_players[~media_day_players["FoundInPlayersDF"]].copy()

    return found_df, not_found_df


def print_media_day_statistics(found_df: pd.DataFrame, not_found_df: pd.DataFrame):
    """Print statistics about media day players found/not found in players_df."""
    total = len(found_df) + len(not_found_df)
    found_count = len(found_df)
    not_found_count = len(not_found_df)

    found_pct = (found_count / total * 100) if total > 0 else 0
    not_found_pct = (not_found_count / total * 100) if total > 0 else 0

    logger.debug("=" * 60)
    logger.debug("MEDIA DAY PLAYERS STATISTICS")
    logger.debug("=" * 60)
    logger.debug(f"Total Media Day Players: {total}")
    logger.debug(f"Found in players_df: {found_count} ({found_pct:.2f}%)")
    logger.debug(f"NOT found in players_df: {not_found_count} ({not_found_pct:.2f}%)")
    # if not_found_count > 0:
    #     pd.set_option("display.max_columns", None)
    #     pd.set_option("display.width", None)
    #     pd.set_option("display.max_colwidth", 30)
    #     logger.debug(not_found_df[["CanonicalName"]].to_string(index=False))
    logger.debug("-" * 60)


def print_statistics(
    players_df: pd.DataFrame,
    tutors_df: pd.DataFrame,
    players_with_both: pd.DataFrame,
    players_with_tutor1_only: pd.DataFrame,
    players_with_tutor2_only: pd.DataFrame,
    players_without_tutors: pd.DataFrame,
    tutor1_not_found: pd.DataFrame,
    tutor2_not_found: pd.DataFrame,
    players_without_any_id: pd.DataFrame,
):
    # Calculate statistics
    total_players = len(players_df)
    total_tutors = len(tutors_df)

    # Players with two tutors
    count_both = len(players_with_both)
    pct_both = (count_both / total_players * 100) if total_players > 0 else 0

    # Players with only Tutor1
    count_tutor1_only = len(players_with_tutor1_only)
    pct_tutor1_only = (count_tutor1_only / total_players * 100) if total_players > 0 else 0

    # Players with only Tutor2 (edge case, should be rare)
    count_tutor2_only = len(players_with_tutor2_only)
    pct_tutor2_only = (count_tutor2_only / total_players * 100) if total_players > 0 else 0

    # Players without any tutors
    count_without = len(players_without_tutors)
    pct_without = (count_without / total_players * 100) if total_players > 0 else 0

    # Print statistics
    logger.debug("=" * 60)
    logger.debug("STATISTICS")
    logger.debug("=" * 60)
    logger.debug(f"Total Players: {total_players}")
    logger.debug(f"Total Tutors: {total_tutors}")
    logger.debug(f"Players with two tutors: {count_both} ({pct_both:.2f}%)")
    # logger.info(players_with_both.head().to_string(index=False))
    logger.debug(f"Players with Tutor1 only: {count_tutor1_only} ({pct_tutor1_only:.2f}%)")
    # logger.info(players_with_tutor1_only.head().to_string(index=False))
    logger.debug(f"Players with Tutor2 only: {count_tutor2_only} ({pct_tutor2_only:.2f}%)")
    # logger.info(players_with_tutor2_only[["CanonicalName", "Tutor1", "Tutor2"]].head().to_string(index=False))
    logger.debug(f"Players without tutors: {count_without} ({pct_without:.2f}%)")
    # if count_without > 0:
    #     pd.set_option("display.max_columns", None)
    #     pd.set_option("display.width", None)
    #     pd.set_option("display.max_colwidth", 30)
    #     players_without_tutors = players_without_tutors.sort_values(by="BirthDate")
    #     logger.info(players_without_tutors[["CanonicalName", "DNI", "NIE", "Pasaporte", "BirthDate"]]
    #           .to_string(index=False))
    # logger.info("-" * 60)

    # Statistics for not_found tutors
    count_tutor1_not_found = len(tutor1_not_found)
    count_tutor2_not_found = len(tutor2_not_found)
    logger.debug("=" * 60)
    logger.debug("NOT FOUND TUTORS STATISTICS")
    logger.debug("=" * 60)
    logger.debug(f"Players with Tutor1 not found: {count_tutor1_not_found}")
    logger.debug(f"Players with Tutor2 not found: {count_tutor2_not_found}")
    # if count_tutor1_not_found > 0:
    #     logger.debug(f"\nPlayers with Tutor1 not found ({count_tutor1_not_found}):")
    #     logger.debug(tutor1_not_found[["CanonicalName", "Tutor1"]].to_string(index=False))
    # if count_tutor2_not_found > 0:
    #     logger.debug(f"\nPlayers with Tutor2 not found ({count_tutor2_not_found}):")
    #     logger.debug(tutor2_not_found[["CanonicalName", "Tutor2"]].to_string(index=False))
    logger.debug("-" * 60)

    # Statistics for players without any ID (player and tutors)
    count_without_any_id = len(players_without_any_id)
    logger.debug("=" * 60)
    logger.debug("PLAYERS WITHOUT ANY ID (PLAYER AND TUTORS)")
    logger.debug("=" * 60)
    logger.debug(f"Players without DNI/NIE/Passport where tutors also lack IDs: {count_without_any_id}")
    # if count_without_any_id > 0:
    #     players_without_any_id_sorted = players_without_any_id.sort_values(by="BirthDate")
    #     logger.info(players_without_any_id_sorted[["CanonicalName", "BirthDate", "Tutor1", "Tutor2"]]
    #           .to_string(index=False))
    logger.debug("-" * 60)


def main():
    logger.info("Loading Media Day players...")
    media_day_path = os.environ.get("CBTC_MEDIA_DAY_PATH", "data/cbtc_media_day.csv")
    media_day_all_df = pd.read_csv(media_day_path, encoding="utf-8")
    media_day_all_df = add_canonical_name_column(media_day_all_df)
    logger.info(f"Loaded {len(media_day_all_df)} rows")

    logger.info("Loading CBTC members...")
    players_tutors_path = os.environ.get("CBTC_ALL_PLAYERS_PATH", "data/cbtc_all.xlsx")
    all_df = load_excel(players_tutors_path)
    logger.info(f"Loaded {len(all_df)} rows")

    logger.info("Processing CBTC members")
    logger.info("Starting transformations")
    all_df["BirthDate"] = pd.to_datetime(all_df["Fecha nac."], errors="coerce", dayfirst=True)

    players_df = generate_players_df(all_df)
    logger.info(f"Extracted {len(players_df)} members with role Player or Fan")

    tutors_df = generate_tutors_df(all_df)
    logger.info(f"Extracted {len(tutors_df)} members with role Tutor")

    logger.info("Aggregating Tutor information to Player/Fan...")
    players_df = merge_tutor_info(players_df, tutors_df)

    # Find media day players in players_df and print statistics
    logger.info("Aggregating CBTC membership information to Media Day players...")
    media_day_found, media_day_not_found = find_media_day_players_in_players_df(media_day_all_df, players_df)

    # Show all media day players found
    logger.info(f"Media Day players found in CBTC members: {len(media_day_found)}")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", 30)
    # Print all columns
    logger.info(media_day_found.to_string(index=False))

    # Statistics
    print_media_day_statistics(media_day_found, media_day_not_found)
    players_with_both = players_df[(players_df["Tutor1"] != "") & (players_df["Tutor2"] != "")]
    players_with_tutor1_only = players_df[(players_df["Tutor1"] != "") & (players_df["Tutor2"] == "")]
    players_with_tutor2_only = players_df[(players_df["Tutor1"] == "") & (players_df["Tutor2"] != "")]
    players_without_tutors = players_df[(players_df["Tutor1"] == "") & (players_df["Tutor2"] == "")]
    tutor1_not_found = players_df[players_df["Tutor1"] == "not_found"]
    tutor2_not_found = players_df[players_df["Tutor2"] == "not_found"]

    # Players without any ID: player has no DNI/NIE/Passport AND tutors also lack IDs
    def has_no_id(row):
        # Check player has no ID
        player_no_id = pd.isna(row["DNI"]) and pd.isna(row["NIE"]) and pd.isna(row["Pasaporte"])
        if not player_no_id:
            return False

        # Check Tutor1 has no ID (empty tutor or tutor without IDs)
        tutor1_no_id = (
            row["Tutor1"] == ""
            or row["Tutor1"] == "not_found"
            or (
                (pd.isna(row["Tutor1DNI"]) or row["Tutor1DNI"] == "")
                and (pd.isna(row["Tutor1NIE"]) or row["Tutor1NIE"] == "")
                and (pd.isna(row["Tutor1Passport"]) or row["Tutor1Passport"] == "")
            )
        )

        # Check Tutor2 has no ID (empty tutor or tutor without IDs)
        tutor2_no_id = (
            row["Tutor2"] == ""
            or row["Tutor2"] == "not_found"
            or (
                (pd.isna(row["Tutor2DNI"]) or row["Tutor2DNI"] == "")
                and (pd.isna(row["Tutor2NIE"]) or row["Tutor2NIE"] == "")
                and (pd.isna(row["Tutor2Passport"]) or row["Tutor2Passport"] == "")
            )
        )

        return tutor1_no_id and tutor2_no_id

    players_without_any_id = players_df[players_df.apply(has_no_id, axis=1)]

    print_statistics(
        players_df,
        tutors_df,
        players_with_both,
        players_with_tutor1_only,
        players_with_tutor2_only,
        players_without_tutors,
        tutor1_not_found,
        tutor2_not_found,
        players_without_any_id,
    )


if __name__ == "__main__":
    main()
