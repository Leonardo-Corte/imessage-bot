import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from lib.filter import build_pattern, matches


def test_match_positive():
    p = build_pattern(["NY", "NYC", "New York", "New York City", "Newyork"])
    assert matches(p, "Chiara", "New York City")
    assert matches(p, "John", "NYC")
    assert matches(p, "Maria", "NY")
    assert matches(p, "Bob", "newyork")
    assert matches(p, "", "", "Acme NY office")


def test_match_negative():
    p = build_pattern(["NY", "NYC", "New York", "New York City", "Newyork"])
    assert not matches(p, "Tony", "Smith")
    assert not matches(p, "Anya", "Doe")
    assert not matches(p, "Sydney", "Jones")
    assert not matches(p, "Bunny", "")
    assert not matches(p, "", "Bonelli")


def test_case_insensitive():
    p = build_pattern(["NY"])
    assert matches(p, "John", "ny")
    assert matches(p, "John", "Ny")
    assert matches(p, "John", "nY")


if __name__ == "__main__":
    test_match_positive()
    test_match_negative()
    test_case_insensitive()
    print("filter OK")
