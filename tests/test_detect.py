import pytest

from denoise.detect import _is_page_number


@pytest.mark.parametrize("text", [
    "12",
    "- 12 -",
    "第 12 页",
    "Page 12",
    "p. 12",
    "1 / 20",
])
def test_detects_page_numbers(text):
    assert _is_page_number(text) is True


@pytest.mark.parametrize("text", [
    "Introduction",
    "Chapter 3 Overview",
    "see section 12 for details",
    "",
])
def test_rejects_non_page_numbers(text):
    assert _is_page_number(text) is False
