import os

import pandas as pd


def main():
    file_path = os.environ.get("CBTC_MEDIA_DAY_PATH", "data/cbtc_all.xlsx")

    df = pd.read_csv(file_path, encoding="utf-8")
    print(df.head())


if __name__ == "__main__":
    main()
