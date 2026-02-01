from unittest.mock import MagicMock

import pandas as pd
from src.main import (
    DNI_COLUMNS,
    generate_players_data,
    row_to_player_data,
    upload_players_data,
)


class TestRowToPlayerData:
    def test_all_dnis_present(self):
        row = pd.Series(
            {
                "CanonicalName": "juan_garcia",
                "Equipo": "Infantil A",
                "Player_DNI": "12345678Z",
                "Player_NIE": "X1234567A",
                "Player_Pasaporte": "AAA123456",
                "Player_Tutor1DNI": "11111111H",
                "Player_Tutor1NIE": "Y1111111B",
                "Player_Tutor1Passport": "BBB111111",
                "Player_Tutor2DNI": "22222222J",
                "Player_Tutor2NIE": "Z2222222C",
                "Player_Tutor2Passport": "CCC222222",
            }
        )
        result = row_to_player_data(row)

        assert result["username"] == "juan_garcia"
        assert len(result["dnis"]) == 9
        assert "12345678Z" in result["dnis"]
        assert "X1234567A" in result["dnis"]
        assert "AAA123456" in result["dnis"]
        assert result["photos"] == ["juan_garcia/001.png", "juan_garcia/002.png", "Teams/Infantil A.png"]

    def test_some_dnis_null(self):
        row = pd.Series(
            {
                "CanonicalName": "maria_lopez",
                "Equipo": "Alevin B",
                "Player_DNI": "12345678Z",
                "Player_NIE": None,
                "Player_Pasaporte": "",
                "Player_Tutor1DNI": "11111111H",
                "Player_Tutor1NIE": None,
                "Player_Tutor1Passport": None,
                "Player_Tutor2DNI": None,
                "Player_Tutor2NIE": None,
                "Player_Tutor2Passport": None,
            }
        )
        result = row_to_player_data(row)

        assert result["username"] == "maria_lopez"
        assert len(result["dnis"]) == 2
        assert "12345678Z" in result["dnis"]
        assert "11111111H" in result["dnis"]
        assert result["photos"] == ["maria_lopez/001.png", "maria_lopez/002.png", "Teams/Alevin B.png"]

    def test_no_dnis(self):
        row = pd.Series(
            {
                "CanonicalName": "pedro_sanchez",
                "Equipo": "Cadete",
                "Player_DNI": None,
                "Player_NIE": None,
                "Player_Pasaporte": None,
                "Player_Tutor1DNI": None,
                "Player_Tutor1NIE": None,
                "Player_Tutor1Passport": None,
                "Player_Tutor2DNI": None,
                "Player_Tutor2NIE": None,
                "Player_Tutor2Passport": None,
            }
        )
        result = row_to_player_data(row)

        assert result["username"] == "pedro_sanchez"
        assert result["dnis"] == []
        assert result["photos"] == ["pedro_sanchez/001.png", "pedro_sanchez/002.png", "Teams/Cadete.png"]

    def test_whitespace_only_dnis_excluded(self):
        row = pd.Series(
            {
                "CanonicalName": "ana_martinez",
                "Equipo": "Junior",
                "Player_DNI": "12345678Z",
                "Player_NIE": "   ",
                "Player_Pasaporte": None,
                "Player_Tutor1DNI": None,
                "Player_Tutor1NIE": None,
                "Player_Tutor1Passport": None,
                "Player_Tutor2DNI": None,
                "Player_Tutor2NIE": None,
                "Player_Tutor2Passport": None,
            }
        )
        result = row_to_player_data(row)

        assert len(result["dnis"]) == 1
        assert "12345678Z" in result["dnis"]

    def test_dnis_are_stripped(self):
        row = pd.Series(
            {
                "CanonicalName": "carlos_ruiz",
                "Equipo": "Senior",
                "Player_DNI": "  12345678Z  ",
                "Player_NIE": None,
                "Player_Pasaporte": None,
                "Player_Tutor1DNI": None,
                "Player_Tutor1NIE": None,
                "Player_Tutor1Passport": None,
                "Player_Tutor2DNI": None,
                "Player_Tutor2NIE": None,
                "Player_Tutor2Passport": None,
            }
        )
        result = row_to_player_data(row)

        assert result["dnis"] == ["12345678Z"]

    def test_photos_format(self):
        row = pd.Series(
            {
                "CanonicalName": "luis_fernandez",
                "Equipo": "Prebenjamin",
                "Player_DNI": "12345678Z",
                "Player_NIE": None,
                "Player_Pasaporte": None,
                "Player_Tutor1DNI": None,
                "Player_Tutor1NIE": None,
                "Player_Tutor1Passport": None,
                "Player_Tutor2DNI": None,
                "Player_Tutor2NIE": None,
                "Player_Tutor2Passport": None,
            }
        )
        result = row_to_player_data(row)

        assert result["photos"] == ["luis_fernandez/001.png", "luis_fernandez/002.png", "Teams/Prebenjamin.png"]


class TestGeneratePlayersData:
    def test_multiple_rows(self):
        df = pd.DataFrame(
            {
                "CanonicalName": ["player1", "player2"],
                "Equipo": ["Team A", "Team B"],
                "Player_DNI": ["11111111H", "22222222J"],
                "Player_NIE": [None, "X1234567A"],
                "Player_Pasaporte": [None, None],
                "Player_Tutor1DNI": [None, None],
                "Player_Tutor1NIE": [None, None],
                "Player_Tutor1Passport": [None, None],
                "Player_Tutor2DNI": [None, None],
                "Player_Tutor2NIE": [None, None],
                "Player_Tutor2Passport": [None, None],
            }
        )
        result = generate_players_data(df)

        assert len(result) == 2
        assert result[0]["username"] == "player1"
        assert result[0]["dnis"] == ["11111111H"]
        assert result[0]["photos"] == ["player1/001.png", "player1/002.png", "Teams/Team A.png"]
        assert result[1]["username"] == "player2"
        assert len(result[1]["dnis"]) == 2
        assert result[1]["photos"] == ["player2/001.png", "player2/002.png", "Teams/Team B.png"]

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["CanonicalName", "Equipo"] + DNI_COLUMNS)
        result = generate_players_data(df)

        assert result == []


class TestUploadPlayersData:
    def test_uploads_all_players(self):
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch_writer)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)

        players_data = [
            {
                "username": "player1",
                "dnis": ["11111111H"],
                "photos": ["player1/001.png", "player1/002.png", "Teams/Team A.png"],
            },
            {
                "username": "player2",
                "dnis": ["22222222J", "X1234567A"],
                "photos": ["player2/001.png", "player2/002.png", "Teams/Team B.png"],
            },
        ]

        upload_players_data(players_data, "users", dynamodb_resource=mock_dynamodb)

        mock_dynamodb.Table.assert_called_once_with("users")
        assert mock_batch_writer.put_item.call_count == 2
        mock_batch_writer.put_item.assert_any_call(Item=players_data[0])
        mock_batch_writer.put_item.assert_any_call(Item=players_data[1])

    def test_uploads_empty_list(self):
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch_writer)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)

        upload_players_data([], "users", dynamodb_resource=mock_dynamodb)

        mock_batch_writer.put_item.assert_not_called()

    def test_uses_correct_table_name(self):
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_batch_writer = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch_writer)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)

        upload_players_data([], "my_custom_table", dynamodb_resource=mock_dynamodb)

        mock_dynamodb.Table.assert_called_once_with("my_custom_table")


class TestDniColumns:
    def test_dni_columns_order(self):
        expected = [
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
        assert DNI_COLUMNS == expected
