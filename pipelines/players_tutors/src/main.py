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


def main():
    # Example: Load the cbtc_all.xlsx file
    file_path = os.environ.get("CBTC_ALL_PLAYERS_PATH", "data/cbtc_all.xlsx")

    all_df = load_excel(file_path)
    print(f"Loaded {len(all_df)} rows")

    # Filter for players only
    players_df = all_df[all_df["Roles"].str.contains("Deportista", na=False)]
    players_df["CanonicalName"] = (
        (
            players_df["Nombre"].fillna("").astype(str).str.strip()
            + " "
            + players_df["Apellidos"].fillna("").astype(str).str.strip()
        )
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Normalize to ASCII, then lowercase and replace spaces with underscores
    players_df["CanonicalName"] = players_df["CanonicalName"].apply(to_ascii).str.lower().str.replace(" ", "_")

    test_df = players_df[players_df["Nombre"].str.contains("Cel", na=False)]
    print(test_df)


if __name__ == "__main__":
    main()
