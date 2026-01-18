import os
import re
import unicodedata

import pandas as pd


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
    # Filter for players only
    players_df = all_df[all_df["Roles"].str.contains("Deportista", na=False)].copy()
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
                print(f"Tutor1 '{tutor1_name}' not found for player '{row['CanonicalName']}'")
                players_df.at[idx, "Tutor1"] = "not_found"

        tutor2_name = row["Tutor2"]
        if tutor2_name and tutor2_name != "":
            if tutor2_name in tutor_lookup:
                tutor_info = tutor_lookup[tutor2_name]
                players_df.at[idx, "Tutor2DNI"] = tutor_info.get("DNI", "") or ""
                players_df.at[idx, "Tutor2NIE"] = tutor_info.get("NIE", "") or ""
                players_df.at[idx, "Tutor2Passport"] = tutor_info.get("Pasaporte", "") or ""
            else:
                print(f"Tutor2 '{tutor2_name}' not found for player '{row['CanonicalName']}'")
                players_df.at[idx, "Tutor2"] = "not_found"

    return players_df


def print_statistics(
    players_df: pd.DataFrame,
    tutors_df: pd.DataFrame,
    players_with_both: pd.DataFrame,
    players_with_tutor1_only: pd.DataFrame,
    players_with_tutor2_only: pd.DataFrame,
    players_without_tutors: pd.DataFrame,
    tutor1_not_found: pd.DataFrame,
    tutor2_not_found: pd.DataFrame,
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
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"\nTotal Players: {total_players}")
    print(f"Total Tutors: {total_tutors}")
    print("-" * 60)
    print(f"\nPlayers with two tutors: {count_both} ({pct_both:.2f}%)")
    print(players_with_both.head().to_string(index=False))
    print("-" * 60)
    print(players_with_tutor1_only.head().to_string(index=False))
    print("-" * 60)
    print(f"Players with Tutor1 only: {count_tutor1_only} ({pct_tutor1_only:.2f}%)")
    print(players_with_tutor1_only.head().to_string(index=False))
    print("-" * 60)
    print(f"Players with Tutor2 only: {count_tutor2_only} ({pct_tutor2_only:.2f}%)")
    print(players_with_tutor2_only[["CanonicalName", "Tutor1", "Tutor2"]].head().to_string(index=False))
    print("-" * 60)
    print(f"Players without tutors: {count_without} ({pct_without:.2f}%)")
    if count_without > 0:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", 30)
        players_without_tutors = players_without_tutors.sort_values(by="BirthDate")
        print(players_without_tutors[["CanonicalName", "DNI", "NIE", "Pasaporte", "BirthDate"]].to_string(index=False))

    print("-" * 60)
    # Statistics for not_found tutors
    count_tutor1_not_found = len(tutor1_not_found)
    count_tutor2_not_found = len(tutor2_not_found)

    print("\n" + "=" * 60)
    print("NOT FOUND TUTORS STATISTICS")
    print("=" * 60)
    print(f"Players with Tutor1 not found: {count_tutor1_not_found}")
    print(f"Players with Tutor2 not found: {count_tutor2_not_found}")

    if count_tutor1_not_found > 0:
        print(f"\nPlayers with Tutor1 not found ({count_tutor1_not_found}):")
        print(tutor1_not_found[["CanonicalName", "Tutor1"]].to_string(index=False))

    if count_tutor2_not_found > 0:
        print(f"\nPlayers with Tutor2 not found ({count_tutor2_not_found}):")
        print(tutor2_not_found[["CanonicalName", "Tutor2"]].to_string(index=False))

    print("=" * 60)


def main():
    # Example: Load the cbtc_all.xlsx file
    file_path = os.environ.get("CBTC_ALL_PLAYERS_PATH", "data/cbtc_all.xlsx")

    all_df = load_excel(file_path)
    print(f"Loaded {len(all_df)} rows")
    all_df["BirthDate"] = pd.to_datetime(all_df["Fecha nac."], errors="coerce", dayfirst=True)

    players_df = generate_players_df(all_df)
    tutors_df = generate_tutors_df(all_df)
    players_df = merge_tutor_info(players_df, tutors_df)

    players_with_both = players_df[(players_df["Tutor1"] != "") & (players_df["Tutor2"] != "")]
    players_with_tutor1_only = players_df[(players_df["Tutor1"] != "") & (players_df["Tutor2"] == "")]
    players_with_tutor2_only = players_df[(players_df["Tutor1"] == "") & (players_df["Tutor2"] != "")]
    players_without_tutors = players_df[(players_df["Tutor1"] == "") & (players_df["Tutor2"] == "")]
    tutor1_not_found = players_df[players_df["Tutor1"] == "not_found"]
    tutor2_not_found = players_df[players_df["Tutor2"] == "not_found"]

    print_statistics(
        players_df,
        tutors_df,
        players_with_both,
        players_with_tutor1_only,
        players_with_tutor2_only,
        players_without_tutors,
        tutor1_not_found,
        tutor2_not_found,
    )


if __name__ == "__main__":
    main()
