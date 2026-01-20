import pandas as pd
from main import add_canonical_name_column, find_media_day_players_in_players_df, to_ascii, to_canonical


class TestToAscii:
    def test_simple_text(self):
        assert to_ascii("hello") == "hello"

    def test_accented_characters(self):
        assert to_ascii("José") == "Jose"
        assert to_ascii("García") == "Garcia"
        assert to_ascii("López") == "Lopez"
        assert to_ascii("María") == "Maria"
        assert to_ascii("Ñoño") == "Nono"

    def test_special_characters(self):
        assert to_ascii("café") == "cafe"
        assert to_ascii("naïve") == "naive"
        assert to_ascii("über") == "uber"

    def test_empty_string(self):
        assert to_ascii("") == ""

    def test_non_string_input(self):
        assert to_ascii(None) == ""
        assert to_ascii(123) == "123"


class TestToCanonical:
    def test_simple_name(self):
        assert to_canonical("Juan Garcia") == "juan_garcia"

    def test_name_with_accents(self):
        assert to_canonical("José García López") == "jose_garcia_lopez"

    def test_empty_string(self):
        assert to_canonical("") == ""

    def test_na_handling(self):
        assert to_canonical("N/A") == ""
        assert to_canonical("Juan N/A Garcia") == "juan_garcia"

    def test_multiple_spaces(self):
        assert to_canonical("Juan  Garcia   Lopez") == "juan_garcia_lopez"

    def test_leading_trailing_spaces(self):
        assert to_canonical("  Juan Garcia  ") == "juan_garcia"


class TestAddCanonicalNameColumn:
    def test_basic_name_combination(self):
        df = pd.DataFrame({"Nombre": ["Juan"], "Apellidos": ["Garcia Lopez"]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "juan_garcia_lopez"

    def test_accented_names(self):
        df = pd.DataFrame({"Nombre": ["José María"], "Apellidos": ["García López"]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "jose_maria_garcia_lopez"

    def test_empty_nombre(self):
        df = pd.DataFrame({"Nombre": [""], "Apellidos": ["Garcia"]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "garcia"

    def test_empty_apellidos(self):
        df = pd.DataFrame({"Nombre": ["Juan"], "Apellidos": [""]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "juan"

    def test_nan_values(self):
        df = pd.DataFrame({"Nombre": [None], "Apellidos": ["Garcia"]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "garcia"

    def test_multiple_rows(self):
        df = pd.DataFrame({"Nombre": ["Juan", "María"], "Apellidos": ["García", "López"]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "juan_garcia"
        assert result["CanonicalName"].iloc[1] == "maria_lopez"

    def test_extra_whitespace(self):
        df = pd.DataFrame({"Nombre": ["  Juan  "], "Apellidos": ["  Garcia   Lopez  "]})
        result = add_canonical_name_column(df)
        assert result["CanonicalName"].iloc[0] == "juan_garcia_lopez"


class TestFindMediaDayPlayersInPlayersDF:
    def test_finds_exact_match(self):
        media_day_df = pd.DataFrame({"Role": ["1", "2"], "CanonicalName": ["juan_garcia", "maria_lopez"]})
        players_df = pd.DataFrame({"CanonicalName": ["juan_garcia", "pedro_sanchez"]})

        found, not_found = find_media_day_players_in_players_df(media_day_df, players_df)

        assert len(found) == 1
        assert len(not_found) == 1
        assert found["CanonicalName"].iloc[0] == "juan_garcia"
        assert not_found["CanonicalName"].iloc[0] == "maria_lopez"

    def test_finds_prefix_match(self):
        media_day_df = pd.DataFrame({"Role": ["1"], "CanonicalName": ["juan_garcia"]})
        players_df = pd.DataFrame({"CanonicalName": ["juan_garcia_lopez"]})

        found, not_found = find_media_day_players_in_players_df(media_day_df, players_df)

        assert len(found) == 1
        assert len(not_found) == 0
        assert found["CanonicalName"].iloc[0] == "juan_garcia"

    def test_filters_only_numeric_roles(self):
        media_day_df = pd.DataFrame(
            {
                "Role": ["1", "Tutor", "2", None, ""],
                "CanonicalName": ["player1", "tutor1", "player2", "unknown", "empty"],
            }
        )
        players_df = pd.DataFrame({"CanonicalName": ["player1", "player2", "tutor1"]})

        found, not_found = find_media_day_players_in_players_df(media_day_df, players_df)

        # Only 2 rows with numeric roles should be processed
        assert len(found) + len(not_found) == 2
        assert len(found) == 2

    def test_empty_media_day_players(self):
        media_day_df = pd.DataFrame({"Role": ["Tutor"], "CanonicalName": ["tutor1"]})
        players_df = pd.DataFrame({"CanonicalName": ["player1"]})

        found, not_found = find_media_day_players_in_players_df(media_day_df, players_df)

        assert len(found) == 0
        assert len(not_found) == 0

    def test_empty_canonical_name(self):
        media_day_df = pd.DataFrame({"Role": ["1", "2"], "CanonicalName": ["", "juan_garcia"]})
        players_df = pd.DataFrame({"CanonicalName": ["juan_garcia"]})

        found, not_found = find_media_day_players_in_players_df(media_day_df, players_df)

        assert len(found) == 1
        assert len(not_found) == 1  # Empty canonical name is not found
