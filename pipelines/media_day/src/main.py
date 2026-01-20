import os
import re
import unicodedata

import pandas as pd


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


def main():
    file_path = os.environ.get("CBTC_MEDIA_DAY_PATH", "data/cbtc_media_day.csv")

    all_df = pd.read_csv(file_path, encoding="utf-8")
    all_df = add_canonical_name_column(all_df)
    print(all_df.to_string())


if __name__ == "__main__":
    main()
