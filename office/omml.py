from lxml import etree

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
_VAL = f"{{{MATH_NS}}}val"

MATH_NOTATION_RULES = (
    "数学公式按以下约定线性化，整体用 $...$ 包裹：\n"
    "- 上标: x^2；多字符 x^(n+1)\n"
    "- 下标: x_n；多字符 x_(i,j)\n"
    "- 上+下标: x_n^2\n"
    "- 分数: (分子)/(分母)，如 (dy)/(dt)\n"
    "- 平方根: sqrt(x)；n 次根: root(n)(x)\n"
    "- 矩阵: [(a,b,c),(d,e,f)] —— 每行一对括号，逗号分隔元素，行间逗号\n"
    "- 积分/求和/连乘: 符号_(下限)^(上限) 操作数，符号用原字符 ∫/∑/∏\n"
    "- 定界符: 用其括号原样包裹，内部多项用逗号分隔\n"
    "- 函数: 名(参数)，如 sin(x)\n"
    "- 上划线/帽: bar(x)、hat(x)\n"
    "- 其它文字/符号: 原样\n"
)


def _ln(el) -> str:
    return etree.QName(el).localname


def _children(el, name):
    return [c for c in el if isinstance(c.tag, str) and _ln(c) == name]


def _child(el, name):
    for c in el:
        if isinstance(c.tag, str) and _ln(c) == name:
            return c
    return None


def _wrap(s: str) -> str:
    return s if len(s) == 1 else f"({s})"


def _part(el, name) -> str:
    c = _child(el, name)
    return _render(c).strip() if c is not None else ""


def _join_children(el) -> str:
    return "".join(_render(c) for c in el if isinstance(c.tag, str))


def _delims(el):
    pr = _child(el, "dPr")
    beg, end = "(", ")"
    if pr is not None:
        b = _child(pr, "begChr")
        e = _child(pr, "endChr")
        if b is not None and b.get(_VAL) is not None:
            beg = b.get(_VAL)
        if e is not None and e.get(_VAL) is not None:
            end = e.get(_VAL)
    return beg, end


def _pr_chr(el, pr_name, default):
    pr = _child(el, pr_name)
    if pr is not None:
        c = _child(pr, "chr")
        if c is not None and c.get(_VAL):
            return c.get(_VAL)
    return default


def _render(el) -> str:
    name = _ln(el)
    if name == "t":
        return el.text or ""
    if name == "r":
        t = _child(el, "t")
        return (t.text or "") if t is not None else ""
    if name == "sSup":
        return f"{_wrap(_part(el, 'e'))}^{_wrap(_part(el, 'sup'))}"
    if name == "sSub":
        return f"{_wrap(_part(el, 'e'))}_{_wrap(_part(el, 'sub'))}"
    if name == "sSubSup":
        return f"{_wrap(_part(el, 'e'))}_{_wrap(_part(el, 'sub'))}^{_wrap(_part(el, 'sup'))}"
    if name == "f":
        return f"({_part(el, 'num')})/({_part(el, 'den')})"
    if name == "rad":
        deg = _part(el, "deg")
        e = _part(el, "e")
        return f"root({deg})({e})" if deg else f"sqrt({e})"
    if name == "d":
        beg, end = _delims(el)
        es = [_render(c).strip() for c in _children(el, "e")]
        return f"{beg}{','.join(es)}{end}"
    if name == "m":
        rows = []
        for mr in _children(el, "mr"):
            cells = [_render(c).strip() for c in _children(mr, "e")]
            rows.append("(" + ",".join(cells) + ")")
        return "[" + ",".join(rows) + "]"
    if name == "nary":
        out = _pr_chr(el, "naryPr", "∫")
        sub = _part(el, "sub")
        sup = _part(el, "sup")
        e = _part(el, "e")
        if sub:
            out += f"_({sub})"
        if sup:
            out += f"^({sup})"
        if e:
            out += f" {e}"
        return out
    if name == "func":
        return f"{_part(el, 'fName')}({_part(el, 'e')})"
    if name == "acc":
        chr_ = _pr_chr(el, "accPr", "̂")
        e = _part(el, "e")
        if chr_ == "̄":
            return f"bar({e})"
        if chr_ == "̂":
            return f"hat({e})"
        return f"acc({e})"
    if name == "bar":
        return f"bar({_part(el, 'e')})"
    return _join_children(el)


def omath_to_text(el) -> str:
    """把一个 <m:oMath> 元素线性化为字符串（不含 $ 包裹）。"""
    return " ".join(_render(el).split())


def linearize_math_in(container) -> list:
    """找出 container 下所有 <m:oMath>，逐个线性化，返回字符串列表。"""
    return [omath_to_text(el) for el in container.iter(f"{{{MATH_NS}}}oMath")]
