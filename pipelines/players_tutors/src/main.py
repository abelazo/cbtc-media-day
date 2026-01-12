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
    """Parse Tutores column into Tutor1 and Tutor2 columns in canonical format, handling both / and // separators."""

    # Split by '/' and filter out empty parts (handles both / and //)
    def parse_tutores(tutores_value):
        if pd.isna(tutores_value) or str(tutores_value).strip() == "":
            return pd.Series(["", ""])

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


def print_statistics(players_df: pd.DataFrame, tutors_df: pd.DataFrame):
    # Calculate statistics
    total_players = len(players_df)
    total_tutors = len(tutors_df)

    # Players with two tutors
    players_with_both = players_df[(players_df["Tutor1"] != "") & (players_df["Tutor2"] != "")]
    count_both = len(players_with_both)
    pct_both = (count_both / total_players * 100) if total_players > 0 else 0

    # Players with only Tutor1
    players_with_tutor1_only = players_df[(players_df["Tutor1"] != "") & (players_df["Tutor2"] == "")]
    count_tutor1_only = len(players_with_tutor1_only)
    pct_tutor1_only = (count_tutor1_only / total_players * 100) if total_players > 0 else 0

    # Players with only Tutor2 (edge case, should be rare)
    players_with_tutor2_only = players_df[(players_df["Tutor1"] == "") & (players_df["Tutor2"] != "")]
    count_tutor2_only = len(players_with_tutor2_only)
    pct_tutor2_only = (count_tutor2_only / total_players * 100) if total_players > 0 else 0

    # Players without any tutors
    players_without_tutors = players_df[(players_df["Tutor1"] == "") & (players_df["Tutor2"] == "")]
    count_without = len(players_without_tutors)
    pct_without = (count_without / total_players * 100) if total_players > 0 else 0

    # Print statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"\nTotal Players: {total_players}")
    print(f"Total Tutors: {total_tutors}")
    print(f"\nPlayers with two tutors: {count_both} ({pct_both:.2f}%)")
    print(f"Players with Tutor1 only: {count_tutor1_only} ({pct_tutor1_only:.2f}%)")
    print(f"Players with Tutor2 only: {count_tutor2_only} ({pct_tutor2_only:.2f}%)")
    print(f"Players without tutors: {count_without} ({pct_without:.2f}%)")
    print("=" * 60)

    # Print details of players without tutors
    if count_without > 0:
        print("\n" + "=" * 60)
        print(f"PLAYERS WITHOUT TUTORS ({count_without})")
        print("=" * 60)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", 30)
        print(players_without_tutors[["CanonicalName", "DNI", "NIE", "Pasaporte", "Fecha nac."]].to_string(index=False))
        print("=" * 60)

    # Show examples with double slash format
    players_with_double_slash = players_df[players_df["Tutores"].str.contains("//", na=False)]
    print(f"\nFound {len(players_with_double_slash)} players with double slash format (//) in Tutores")


def main():
    # Example: Load the cbtc_all.xlsx file
    file_path = os.environ.get("CBTC_ALL_PLAYERS_PATH", "data/cbtc_all.xlsx")

    all_df = load_excel(file_path)
    print(f"Loaded {len(all_df)} rows")

    players_df = generate_players_df(all_df)
    tutors_df = generate_tutors_df(all_df)

    print_statistics(players_df, tutors_df)


if __name__ == "__main__":
    main()
