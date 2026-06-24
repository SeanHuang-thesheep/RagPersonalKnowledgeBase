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


from denoise.extract import Line
from denoise.detect import flag_noise, _normalize


def _edge_top(page, text):
    return Line(page, text, 20.0, 33.0, 800.0, 50.0, 200.0)


def _edge_bottom(page, text):
    return Line(page, text, 760.0, 773.0, 800.0, 50.0, 200.0)


def _body(page, text):
    return Line(page, text, 400.0, 413.0, 800.0, 50.0, 200.0)


def test_normalize_groups_digits():
    assert _normalize("Page 1") == _normalize("Page 2")
    assert _normalize("  Foo   Bar ") == "Foo Bar"


def test_repeated_header_flagged():
    lines = []
    for p in range(4):
        lines.append(_edge_top(p, "ACME Confidential"))
        lines.append(_body(p, f"unique body {p}"))
    noise = flag_noise(lines, num_pages=4)
    flagged = {lines[i].text for i in noise}
    assert "ACME Confidential" in flagged
    assert all(f"unique body {p}" not in flagged for p in range(4))


def test_page_number_in_footer_flagged():
    lines = [_edge_bottom(p, str(p + 1)) for p in range(3)]
    lines += [_body(p, f"body {p}") for p in range(3)]
    noise = flag_noise(lines, num_pages=3)
    assert {lines[i].text for i in noise} == {"1", "2", "3"}


def test_unique_edge_text_not_flagged():
    # 各页边缘文字不同且非页码 -> 不应被删
    titles = ["Introduction to widgets", "Analysis of results", "Concluding remarks"]
    lines = [_edge_top(p, titles[p]) for p in range(3)]
    noise = flag_noise(lines, num_pages=3)
    assert noise == set()


def test_repetition_skipped_for_single_page():
    lines = [_edge_top(0, "Confidential"), _edge_bottom(0, "5"), _body(0, "body")]
    noise = flag_noise(lines, num_pages=1)
    # 单页：重复检测跳过，仅页码被删
    assert {lines[i].text for i in noise} == {"5"}
