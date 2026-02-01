import logging
import os

import boto3
import pandas as pd

from .logger import get_logger

log_levels = {
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

logger = get_logger(__name__, level=log_levels[os.environ.get("PLAYERS_DATA_UPLOADER_LOG_LEVEL", "INFO").upper()])

DNI_COLUMNS = [
    "Player_DNI",
    "Player_NIE",
    "Player_Pasaporte",
    "Player_Tutor1DNI",
    "Player_Tutor1NIE",
    "Player_Tutor1Passport",
    "Player_Tutor2DNI",
    "Player_Tutor2NIE",
    "Player_Tutor2Passport",
]


def row_to_player_data(row: pd.Series) -> dict:
    """Convert a DataFrame row to player data dictionary.

    Returns a dictionary with 'username', 'dnis', and 'photos' keys.
    Only non-null DNI values are included in the dnis list.
    """
    dnis = []
    for col in DNI_COLUMNS:
        value = row.get(col)
        if pd.notna(value) and str(value).strip() != "":
            dnis.append(str(value).strip())

    canonical_name = row["CanonicalName"]
    equipo = row["Equipo"]

    photos = [
        f"{canonical_name}/001.png",
        f"{canonical_name}/002.png",
        f"Teams/{equipo}.png",
    ]

    return {
        "username": canonical_name,
        "dnis": dnis,
        "photos": photos,
    }


def generate_players_data(df: pd.DataFrame) -> list[dict]:
    """Generate list of player data dictionaries from DataFrame."""
    players_data = []
    for _, row in df.iterrows():
        player_data = row_to_player_data(row)
        players_data.append(player_data)
    return players_data


def upload_players_data(players_data: list[dict], table_name: str, dynamodb_resource=None) -> None:
    """Upload player data items to DynamoDB users table."""
    if dynamodb_resource is None:
        dynamodb_resource = boto3.resource("dynamodb")

    table = dynamodb_resource.Table(table_name)

    with table.batch_writer() as batch:
        for player in players_data:
            batch.put_item(Item=player)

    logger.info(f"Uploaded {len(players_data)} items to {table_name}")


def main():
    logger.info("Starting players data uploader pipeline")

    input_path = os.environ.get("CBTC_MEDIA_DAY_OUTPUT_PATH", "output/cbtc_media_day_players.csv")
    table_name = os.environ.get("CBTC_PLAYERS_TABLE_NAME", "players")

    logger.info(f"Reading CSV from {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8")
    logger.info(f"Loaded {len(df)} rows from CSV")

    logger.info("Generating player data")
    players_data = generate_players_data(df)

    logger.info(f"Uploading {len(players_data)} players to DynamoDB table '{table_name}'")
    upload_players_data(players_data, table_name)


if __name__ == "__main__":
    main()
