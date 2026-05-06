import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from lib.name import extract_first_name


def test_strip_tags():
    assert extract_first_name("NYC John", "Smith") == "John"
    assert extract_first_name("Chiara", "New York City") == "Chiara"
    assert extract_first_name("John Coi", "NY") == "John"
    assert extract_first_name("New York", "Bob") == "Bob"


def test_fallback():
    assert extract_first_name("", "") == "amico"
    assert extract_first_name("Marco", "") == "Marco"
    assert extract_first_name("", "Rossi") == "Rossi"


def test_only_tags():
    # all tokens are tags → fall back to given
    assert extract_first_name("NY NYC", "New York") == "NY"


if __name__ == "__main__":
    test_strip_tags()
    test_fallback()
    test_only_tags()
    print("name OK")
