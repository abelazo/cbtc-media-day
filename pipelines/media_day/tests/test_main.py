import pandas as pd
from main import add_canonical_name_column, to_ascii, to_canonical


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
