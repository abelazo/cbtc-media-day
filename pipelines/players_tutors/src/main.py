import os
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


def add_canonical_name_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a CanonicalName column by combining Nombre and Apellidos, normalized to ASCII lowercase with underscores."""
    df["CanonicalName"] = (
        (df["Nombre"].fillna("").astype(str).str.strip() + " " + df["Apellidos"].fillna("").astype(str).str.strip())
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Normalize to ASCII, then lowercase and replace spaces with underscores
    df["CanonicalName"] = df["CanonicalName"].apply(to_ascii).str.lower().str.replace(" ", "_")

    return df


def generate_players_df(all_df: pd.DataFrame) -> pd.DataFrame:
    # Filter for players only
    players_df = all_df[all_df["Roles"].str.contains("Deportista", na=False)].copy()
    players_df = add_canonical_name_column(players_df)
    return players_df


def generate_tutors_df(all_df: pd.DataFrame) -> pd.DataFrame:
    # Filter for tutors only
    tutors_df = all_df[all_df["Roles"].str.contains("Tutor", na=False)].copy()
    tutors_df = add_canonical_name_column(tutors_df)
    return tutors_df


def main():
    # Example: Load the cbtc_all.xlsx file
    file_path = os.environ.get("CBTC_ALL_PLAYERS_PATH", "data/cbtc_all.xlsx")

    all_df = load_excel(file_path)
    print(f"Loaded {len(all_df)} rows")

    players_df = generate_players_df(all_df)
    print(f"Processed {len(players_df)} players")

    tutors_df = generate_tutors_df(all_df)
    print(f"Processed {len(tutors_df)} tutors")


if __name__ == "__main__":
    main()
