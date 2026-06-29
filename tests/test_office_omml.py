from lxml import etree

from office.omml import omath_to_text, linearize_math_in, MATH_NOTATION_RULES

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _omath(inner: str):
    xml = f'<m:oMath xmlns:m="{M}">{inner}</m:oMath>'
    return etree.fromstring(xml.encode("utf-8"))


def _run(text):
    return f"<m:r><m:t>{text}</m:t></m:r>"


def test_run_text():
    assert omath_to_text(_omath(_run("a + b"))) == "a + b"


def test_superscript():
    inner = f"<m:sSup><m:e>{_run('x')}</m:e><m:sup>{_run('2')}</m:sup></m:sSup>"
    assert omath_to_text(_omath(inner)) == "x^2"


def test_superscript_multichar_parens():
    inner = f"<m:sSup><m:e>{_run('x')}</m:e><m:sup>{_run('n+1')}</m:sup></m:sSup>"
    assert omath_to_text(_omath(inner)) == "x^(n+1)"


def test_subscript():
    inner = f"<m:sSub><m:e>{_run('x')}</m:e><m:sub>{_run('n')}</m:sub></m:sSub>"
    assert omath_to_text(_omath(inner)) == "x_n"


def test_subsup():
    inner = f"<m:sSubSup><m:e>{_run('x')}</m:e><m:sub>{_run('i')}</m:sub><m:sup>{_run('2')}</m:sup></m:sSubSup>"
    assert omath_to_text(_omath(inner)) == "x_i^2"


def test_fraction():
    inner = f"<m:f><m:num>{_run('dy')}</m:num><m:den>{_run('dt')}</m:den></m:f>"
    assert omath_to_text(_omath(inner)) == "(dy)/(dt)"


def test_sqrt():
    inner = f"<m:rad><m:e>{_run('x')}</m:e></m:rad>"
    assert omath_to_text(_omath(inner)) == "sqrt(x)"


def test_nth_root():
    inner = f"<m:rad><m:deg>{_run('3')}</m:deg><m:e>{_run('x')}</m:e></m:rad>"
    assert omath_to_text(_omath(inner)) == "root(3)(x)"


def test_matrix_2x2():
    row1 = f"<m:mr><m:e>{_run('a')}</m:e><m:e>{_run('b')}</m:e></m:mr>"
    row2 = f"<m:mr><m:e>{_run('c')}</m:e><m:e>{_run('d')}</m:e></m:mr>"
    inner = f"<m:m>{row1}{row2}</m:m>"
    assert omath_to_text(_omath(inner)) == "[(a,b),(c,d)]"


def test_function():
    inner = f"<m:func><m:fName>{_run('sin')}</m:fName><m:e>{_run('x')}</m:e></m:func>"
    assert omath_to_text(_omath(inner)) == "sin(x)"


def test_nary_sum():
    pr = '<m:naryPr><m:chr m:val="&#x2211;"/></m:naryPr>'
    inner = f"<m:nary>{pr}<m:sub>{_run('i=1')}</m:sub><m:sup>{_run('n')}</m:sup><m:e>{_run('i')}</m:e></m:nary>"
    assert omath_to_text(_omath(inner)) == "∑_(i=1)^(n) i"


def test_nested_fraction_with_superscript():
    sup = f"<m:sSup><m:e>{_run('x')}</m:e><m:sup>{_run('2')}</m:sup></m:sSup>"
    inner = f"<m:f><m:num>{sup}</m:num><m:den>{_run('y')}</m:den></m:f>"
    assert omath_to_text(_omath(inner)) == "(x^2)/(y)"


def test_fallback_unknown_tag_keeps_text():
    inner = f"<m:weirdThing>{_run('z')}</m:weirdThing>"
    assert omath_to_text(_omath(inner)) == "z"


def test_linearize_math_in_finds_all():
    s1 = f"<m:sSup><m:e>{_run('x')}</m:e><m:sup>{_run('2')}</m:sup></m:sSup>"
    xml = (
        f'<m:oMathPara xmlns:m="{M}">'
        f'<m:oMath>{s1}</m:oMath><m:oMath>{_run("a")}</m:oMath>'
        f'</m:oMathPara>'
    )
    container = etree.fromstring(xml.encode("utf-8"))
    assert linearize_math_in(container) == ["x^2", "a"]


def test_rules_nonempty():
    assert "[(" in MATH_NOTATION_RULES
    assert "sqrt" in MATH_NOTATION_RULES


def test_delimiter_default_paren_multi():
    inner = f"<m:d><m:e>{_run('a')}</m:e><m:e>{_run('b')}</m:e></m:d>"
    assert omath_to_text(_omath(inner)) == "(a,b)"


def test_delimiter_custom_brackets():
    pr = '<m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr>'
    inner = f"<m:d>{pr}<m:e>{_run('x')}</m:e></m:d>"
    assert omath_to_text(_omath(inner)) == "[x]"


def test_accent_bar():
    inner = f'<m:acc><m:accPr><m:chr m:val="̄"/></m:accPr><m:e>{_run("x")}</m:e></m:acc>'
    assert omath_to_text(_omath(inner)) == "bar(x)"


def test_accent_hat():
    inner = f'<m:acc><m:accPr><m:chr m:val="̂"/></m:accPr><m:e>{_run("y")}</m:e></m:acc>'
    assert omath_to_text(_omath(inner)) == "hat(y)"


def test_bar_element():
    inner = f"<m:bar><m:e>{_run('z')}</m:e></m:bar>"
    assert omath_to_text(_omath(inner)) == "bar(z)"


def test_empty_superscript_no_empty_parens():
    # degenerate: sup element is empty -> should not produce (), base superscript degrades to empty
    inner = f"<m:sSup><m:e>{_run('x')}</m:e><m:sup></m:sup></m:sSup>"
    out = omath_to_text(_omath(inner))
    assert "()" not in out
    assert out.startswith("x^")
