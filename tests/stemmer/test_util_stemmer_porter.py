from pathlib import Path

import pytest

from sphinx.util.stemmer.porter import PorterStemmer

STEMMER_DIR = Path(__file__).parent.resolve()
INPUT_WORDS = STEMMER_DIR / "input.txt"
EXPECTED_WORDS = STEMMER_DIR / "expected.txt"


@pytest.mark.parametrize("input_word,expected_word",
    [*zip(INPUT_WORDS.read_text(encoding="utf-8").splitlines(),
          EXPECTED_WORDS.read_text(encoding="utf-8").splitlines())][::21]
)
def test_porter_stemmer(input_word: str, expected_word: str):
    assert PorterStemmer().stem(input_word) == expected_word
