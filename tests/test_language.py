import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from lib.language import detect_language


def test_italian():
    msgs = ["Ciao come stai", "Grazie mille", "Domani ci vediamo bene"]
    assert detect_language(msgs) == "it"


def test_english():
    msgs = ["Hey how are you", "Thanks a lot", "See you tomorrow"]
    assert detect_language(msgs) == "en"


def test_default_when_empty():
    assert detect_language([]) == "it"
    assert detect_language(["xyz qqq"]) == "it"
    assert detect_language([], default="en") == "en"


if __name__ == "__main__":
    test_italian()
    test_english()
    test_default_when_empty()
    print("language OK")
