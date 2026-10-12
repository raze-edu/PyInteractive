"""Mathematical typography and equation rendering engine for Pygame.
Provides seamless inline rendering of mathematical equations including:
- Superscripts / Exponents (e.g. x^2, 2^{10}, (r)^2)
- Subscripts / Log notation (e.g. \\log_2(8), log_2(8), a_1)
- Fractions with horizontal vinculum bar (e.g. \\frac{a}{b}, [a/b], frac(a, b))
- Roots with dynamic radical vinculum and optional index (e.g. \\sqrt{64}, \\sqrt[3]{27}, sqrt(x))
- Mathematical symbols (\\pi, \\theta, \\cdot, \\times, \\pm, \\approx, \\le, \\ge, \\ne, \\infty)
- Seamless inline integration with normal text and multi-line wrapping.
"""
from typing import Dict, List, Optional, Tuple, Union
import pygame
from .theme import get_font, TEXT_WHITE

MATH_SYMBOLS = {
    r"\pi": "π",
    r"\theta": "θ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\sigma": "σ",
    r"\omega": "ω",
    r"\cdot": "·",
    r"\times": "×",
    r"\div": "÷",
    r"\pm": "±",
    r"\approx": "≈",
    r"\le": "≤",
    r"\leq": "≤",
    r"\ge": "≥",
    r"\geq": "≥",
    r"\ne": "≠",
    r"\neq": "≠",
    r"\infty": "∞",
    r"\degree": "°",
}

UNICODE_SUPERSCRIPTS = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")",
    "ⁿ": "n", "ⁱ": "i",
}

UNICODE_SUBSCRIPTS = {
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "₊": "+", "₋": "-", "₌": "=", "₍": "(", "₎": ")",
    "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₓ": "x", "ᵢ": "i", "ⱼ": "j",
}

UNICODE_FRACTIONS = {
    "½": ("1", "2"),
    "⅓": ("1", "3"),
    "⅔": ("2", "3"),
    "¼": ("1", "4"),
    "¾": ("3", "4"),
    "⅕": ("1", "5"),
    "⅖": ("2", "5"),
    "⅗": ("3", "5"),
    "⅘": ("4", "5"),
    "⅙": ("1", "6"),
    "⅚": ("5", "6"),
    "⅛": ("1", "8"),
    "⅜": ("3", "8"),
    "⅝": ("5", "8"),
    "⅞": ("7", "8"),
}


def _parse_balanced(s: str, idx: int, open_c: str, close_c: str) -> Tuple[str, int]:
    """Extracts content inside matching balanced brackets or braces."""
    if idx >= len(s) or s[idx] != open_c:
        return "", idx
    depth = 0
    i = idx
    content: List[str] = []
    while i < len(s):
        c = s[i]
        if c == open_c:
            depth += 1
            if depth > 1:
                content.append(c)
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return "".join(content), i + 1
            else:
                content.append(c)
        else:
            content.append(c)
        i += 1
    return "".join(content), i


class RenderResult:
    """Encapsulates a rendered math surface with its exact typographical baseline."""

    def __init__(self, surface: pygame.Surface, baseline: int):
        self.surface = surface
        self.baseline = baseline
        self.width = surface.get_width()
        self.height = surface.get_height()


class ASTNode:
    """Base class for math AST nodes."""

    def render(self, font_size: int, color: Tuple[int, int, int], bold: bool = True) -> RenderResult:
        raise NotImplementedError


class TextNode(ASTNode):
    """Renders plain text tokens or mathematical symbols."""

    def __init__(self, text: str):
        self.text = text

    def render(self, font_size: int, color: Tuple[int, int, int], bold: bool = True) -> RenderResult:
        if not self.text:
            s = pygame.Surface((1, 1), pygame.SRCALPHA)
            return RenderResult(s, 0)
        font = get_font(font_size, bold=bold)
        surf = font.render(self.text, True, color)
        return RenderResult(surf, font.get_ascent())


class SequenceNode(ASTNode):
    """Horizontal sequence of baseline-aligned nodes."""

    def __init__(self, nodes: List[ASTNode]):
        self.nodes = [n for n in nodes if n is not None]

    def render(self, font_size: int, color: Tuple[int, int, int], bold: bool = True) -> RenderResult:
        if not self.nodes:
            s = pygame.Surface((1, 1), pygame.SRCALPHA)
            return RenderResult(s, 0)
        if len(self.nodes) == 1:
            return self.nodes[0].render(font_size, color, bold)

        results = [n.render(font_size, color, bold) for n in self.nodes]
        max_ascent = max(r.baseline for r in results)
        max_descent = max(r.height - r.baseline for r in results)
        total_w = sum(r.width for r in results)
        total_h = max(1, max_ascent + max_descent)

        surf = pygame.Surface((max(1, total_w), total_h), pygame.SRCALPHA)
        curr_x = 0
        for r in results:
            y = max_ascent - r.baseline
            surf.blit(r.surface, (curr_x, y))
            curr_x += r.width
        return RenderResult(surf, max_ascent)


class FractionNode(ASTNode):
    """Renders a stacked fraction with a horizontal fraction bar aligned to the math axis."""

    def __init__(self, num: ASTNode, den: ASTNode):
        self.num = num
        self.den = den

    def render(self, font_size: int, color: Tuple[int, int, int], bold: bool = True) -> RenderResult:
        f_size = max(11, int(font_size * 0.82))
        num_res = self.num.render(f_size, color, bold)
        den_res = self.den.render(f_size, color, bold)

        bar_thick = max(2, int(font_size / 14))
        gap = max(3, int(font_size / 9))
        pad = max(6, int(font_size / 4))
        w = max(num_res.width, den_res.width) + pad

        bar_y = num_res.height + gap
        den_y = bar_y + bar_thick + gap
        total_h = den_y + den_res.height

        main_font = get_font(font_size, bold=bold)
        math_axis = int(main_font.get_ascent() * 0.40)
        baseline = bar_y + bar_thick // 2 + math_axis

        surf = pygame.Surface((w, total_h), pygame.SRCALPHA)
        surf.blit(num_res.surface, ((w - num_res.width) // 2, 0))
        pygame.draw.line(surf, color, (1, bar_y + bar_thick // 2), (w - 1, bar_y + bar_thick // 2), bar_thick)
        surf.blit(den_res.surface, ((w - den_res.width) // 2, den_y))
        return RenderResult(surf, baseline)


class RootNode(ASTNode):
    """Renders a square or n-th root with dynamic radical sign and horizontal overbar."""

    def __init__(self, rad: ASTNode, index: Optional[ASTNode] = None):
        self.rad = rad
        self.index = index

    def render(self, font_size: int, color: Tuple[int, int, int], bold: bool = True) -> RenderResult:
        rad_res = self.rad.render(font_size, color, bold)
        idx_res = self.index.render(max(10, int(font_size * 0.52)), color, bold) if self.index else None

        thick = max(2, int(font_size / 14))
        crook_w = max(14, int(font_size * 0.52))
        if idx_res:
            crook_w = max(crook_w, idx_res.width + 5)

        top_c = max(3, int(font_size * 0.12))
        bot_c = max(2, int(font_size * 0.08))

        w = crook_w + rad_res.width + 5
        h = top_c + thick + rad_res.height + bot_c
        rx = crook_w + 1
        ry = top_c + thick
        baseline = ry + rad_res.baseline

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.blit(rad_res.surface, (rx, ry))

        crook_bot_x = rx - int(crook_w * 0.38)
        crook_bot_y = h - bot_c
        pts = [
            (rx - crook_w + 2, h - int((h - ry) * 0.42)),
            (crook_bot_x, crook_bot_y),
            (rx, ry - 1),
            (w - 1, ry - 1),
            (w - 1, ry + 2),  # subtle right serif tick
        ]
        pygame.draw.lines(surf, color, False, pts, thick)
        if idx_res:
            surf.blit(idx_res.surface, (2, max(0, ry - idx_res.height + 3)))
        return RenderResult(surf, baseline)


class ScriptNode(ASTNode):
    """Renders a base with superscript and/or subscript characters."""

    def __init__(self, base: ASTNode, sup: Optional[ASTNode] = None, sub: Optional[ASTNode] = None):
        self.base = base
        self.sup = sup
        self.sub = sub

    def render(self, font_size: int, color: Tuple[int, int, int], bold: bool = True) -> RenderResult:
        base_res = self.base.render(font_size, color, bold)
        s_size = max(10, int(font_size * 0.68))
        sup_res = self.sup.render(s_size, color, bold) if self.sup else None
        sub_res = self.sub.render(s_size, color, bold) if self.sub else None

        script_w = max(sup_res.width if sup_res else 0, sub_res.width if sub_res else 0)
        total_w = base_res.width + (script_w + 1 if (sup_res or sub_res) else 0)

        b_base = base_res.baseline
        sup_shift = -int(font_size * 0.42)
        sub_shift = int(font_size * 0.32)

        # Avoid collision between sup and sub if both exist
        if sup_res and sub_res:
            sup_bot = b_base + sup_shift + (sup_res.height - sup_res.baseline)
            sub_top = b_base + sub_shift - sub_res.baseline
            if sup_bot > sub_top - 2:
                overlap = sup_bot - (sub_top - 2)
                sup_shift -= (overlap + 1) // 2
                sub_shift += (overlap + 1) // 2

        sup_top = (b_base + sup_shift - sup_res.baseline) if sup_res else 0
        sup_bot = (b_base + sup_shift + (sup_res.height - sup_res.baseline)) if sup_res else 0
        sub_top = (b_base + sub_shift - sub_res.baseline) if sub_res else base_res.height
        sub_bot = (b_base + sub_shift + (sub_res.height - sub_res.baseline)) if sub_res else base_res.height

        min_y = min(0, sup_top if sup_res else 0, sub_top if sub_res else 0)
        max_y = max(base_res.height, sup_bot if sup_res else 0, sub_bot if sub_res else 0)
        total_h = max_y - min_y
        baseline = b_base - min_y

        surf = pygame.Surface((max(1, total_w), max(1, total_h)), pygame.SRCALPHA)
        surf.blit(base_res.surface, (0, -min_y))
        if sup_res:
            surf.blit(sup_res.surface, (base_res.width + 1, sup_top - min_y))
        if sub_res:
            surf.blit(sub_res.surface, (base_res.width + 1, sub_top - min_y))
        return RenderResult(surf, baseline)


class MathRenderer:
    """Parses mathematical syntax and renders formatted equations with baseline alignment."""

    def __init__(self):
        self._ast_cache: Dict[str, ASTNode] = {}
        self._render_cache: Dict[Tuple[str, int, Tuple[int, int, int], bool, Optional[int]], pygame.Surface] = {}

    def parse(self, text: str) -> ASTNode:
        """Parses a math string into an executable AST tree."""
        if not text:
            return TextNode("")
        if text in self._ast_cache:
            return self._ast_cache[text]

        node = self._parse_expr(text)
        if len(self._ast_cache) > 400:
            self._ast_cache.clear()
        self._ast_cache[text] = node
        return node

    def _parse_expr(self, s: str) -> ASTNode:
        nodes: List[ASTNode] = []
        i = 0
        n = len(s)

        while i < n:
            # 1. Whitespace
            if s[i].isspace():
                sp_start = i
                while i < n and s[i].isspace():
                    i += 1
                nodes.append(TextNode(s[sp_start:i]))
                continue

            # 2. Unicode Fractions (e.g. ½, ¼)
            if s[i] in UNICODE_FRACTIONS:
                num, den = UNICODE_FRACTIONS[s[i]]
                nodes.append(FractionNode(TextNode(num), TextNode(den)))
                i += 1
                continue

            # 3. Unicode Square Root (e.g. √64)
            if s[i] == "√":
                i += 1
                while i < n and s[i].isspace():
                    i += 1
                if i < n and s[i] in "({[":
                    open_c = s[i]
                    close_c = "}" if open_c == "{" else ("]" if open_c == "[" else ")")
                    rad_str, i = _parse_balanced(s, i, open_c, close_c)
                    nodes.append(RootNode(self._parse_expr(rad_str)))
                else:
                    # Collect contiguous token
                    start_r = i
                    while i < n and not s[i].isspace() and s[i] not in "\\^_{}[]()=+-*·":
                        i += 1
                    rad_str = s[start_r:i]
                    nodes.append(RootNode(self._parse_expr(rad_str)))
                continue

            # 4. Unicode Superscripts (e.g. ², ³, ⁿ)
            if s[i] in UNICODE_SUPERSCRIPTS:
                char_val = UNICODE_SUPERSCRIPTS[s[i]]
                i += 1
                target_node = TextNode(char_val)
                self._attach_script(nodes, target_node, is_sup=True)
                continue

            # 5. Unicode Subscripts (e.g. ₂, ₃)
            if s[i] in UNICODE_SUBSCRIPTS:
                char_val = UNICODE_SUBSCRIPTS[s[i]]
                i += 1
                target_node = TextNode(char_val)
                self._attach_script(nodes, target_node, is_sup=False)
                continue

            # 6. LaTeX commands or escaped symbols
            if s[i] == "\\":
                j = i + 1
                while j < n and s[j].isalpha():
                    j += 1
                cmd = s[i:j]

                if cmd == r"\frac":
                    i = j
                    while i < n and s[i].isspace(): i += 1
                    num_str, i = _parse_balanced(s, i, "{", "}")
                    while i < n and s[i].isspace(): i += 1
                    den_str, i = _parse_balanced(s, i, "{", "}")
                    nodes.append(FractionNode(self._parse_expr(num_str), self._parse_expr(den_str)))
                    continue
                elif cmd == r"\sqrt":
                    i = j
                    while i < n and s[i].isspace(): i += 1
                    idx_str = None
                    if i < n and s[i] == "[":
                        idx_str, i = _parse_balanced(s, i, "[", "]")
                        while i < n and s[i].isspace(): i += 1
                    rad_str, i = _parse_balanced(s, i, "{", "}")
                    idx_node = self._parse_expr(idx_str) if idx_str else None
                    nodes.append(RootNode(self._parse_expr(rad_str), idx_node))
                    continue
                elif cmd in (r"\log", r"\ln", r"\sin", r"\cos", r"\tan"):
                    nodes.append(TextNode(cmd[1:]))
                    i = j
                    continue
                elif cmd in MATH_SYMBOLS:
                    nodes.append(TextNode(MATH_SYMBOLS[cmd]))
                    i = j
                    continue
                else:
                    nodes.append(TextNode(cmd))
                    i = j
                    continue

            # 7. Shorthand function frac(a, b) or frac{a}{b}
            if s[i:i+4] == "frac" and i + 4 < n and s[i+4] in "({":
                i += 4
                if s[i] == "{":
                    num_str, i = _parse_balanced(s, i, "{", "}")
                    while i < n and s[i].isspace(): i += 1
                    den_str, i = _parse_balanced(s, i, "{", "}")
                    nodes.append(FractionNode(self._parse_expr(num_str), self._parse_expr(den_str)))
                elif s[i] == "(":
                    args_str, i = _parse_balanced(s, i, "(", ")")
                    parts = args_str.split(",", 1)
                    if len(parts) == 2:
                        nodes.append(FractionNode(self._parse_expr(parts[0].strip()), self._parse_expr(parts[1].strip())))
                    else:
                        nodes.append(TextNode(f"frac({args_str})"))
                continue

            # 8. Shorthand function sqrt(...)
            if s[i:i+4] == "sqrt" and (i + 4 == n or s[i+4] in "([{ "):
                i += 4
                while i < n and s[i].isspace(): i += 1
                idx_str = None
                if i < n and s[i] == "[":
                    idx_str, i = _parse_balanced(s, i, "[", "]")
                    while i < n and s[i].isspace(): i += 1
                if i < n and s[i] in "({":
                    open_c = s[i]
                    close_c = "}" if open_c == "{" else ")"
                    rad_str, i = _parse_balanced(s, i, open_c, close_c)
                    idx_node = self._parse_expr(idx_str) if idx_str else None
                    nodes.append(RootNode(self._parse_expr(rad_str), idx_node))
                    continue
                else:
                    nodes.append(TextNode("sqrt"))
                    continue

            # 9. Bracketed fraction e.g. [3/4] or input slot [ ]
            if s[i] == "[":
                content, next_i = _parse_balanced(s, i, "[", "]")
                if "/" in content and not ("[" in content or "]" in content):
                    fparts = content.split("/", 1)
                    nodes.append(FractionNode(self._parse_expr(fparts[0].strip()), self._parse_expr(fparts[1].strip())))
                    i = next_i
                    continue
                elif content.strip() == "":
                    # Empty answer slot: "[ ]"
                    nodes.append(TextNode("[ ]"))
                    i = next_i
                    continue
                else:
                    nodes.append(TextNode("[" + content + "]"))
                    i = next_i
                    continue

            # 10. Superscript '^' and Subscript '_'
            if s[i] in ("^", "_"):
                is_sup = (s[i] == "^")
                i += 1
                while i < n and s[i].isspace(): i += 1
                target_str = ""
                if i < n:
                    if s[i] == "{":
                        target_str, i = _parse_balanced(s, i, "{", "}")
                    elif s[i] == "(" and is_sup:
                        target_str, i = _parse_balanced(s, i, "(", ")")
                    elif s[i] in "+-" and i + 1 < n and s[i + 1].isdigit():
                        start_target = i
                        i += 1
                        while i < n and s[i].isdigit():
                            i += 1
                        target_str = s[start_target:i]
                    elif s[i].isdigit():
                        start_target = i
                        while i < n and s[i].isdigit():
                            i += 1
                        target_str = s[start_target:i]
                    else:
                        target_str = s[i]
                        i += 1
                target_node = self._parse_expr(target_str)
                self._attach_script(nodes, target_node, is_sup=is_sup)
                continue

            # 11. Regular text / numbers / operators
            start_t = i
            while (
                i < n
                and not s[i].isspace()
                and s[i] not in ("\\", "^", "_", "{", "}", "√")
                and s[i] not in UNICODE_SUPERSCRIPTS
                and s[i] not in UNICODE_SUBSCRIPTS
                and s[i] not in UNICODE_FRACTIONS
                and not (s[i:i+4] in ("frac", "sqrt"))
                and s[i] != "["
            ):
                i += 1
            chunk = s[start_t:i]
            if chunk:
                nodes.append(TextNode(chunk))

        if len(nodes) == 1:
            return nodes[0]
        return SequenceNode(nodes)

    def _attach_script(self, nodes: List[ASTNode], target_node: ASTNode, is_sup: bool) -> None:
        if not nodes:
            nodes.append(ScriptNode(TextNode(""), sup=target_node if is_sup else None, sub=target_node if not is_sup else None))
            return

        prev = nodes.pop()
        if isinstance(prev, ScriptNode):
            if is_sup and prev.sup is None:
                prev.sup = target_node
                nodes.append(prev)
            elif not is_sup and prev.sub is None:
                prev.sub = target_node
                nodes.append(prev)
            else:
                nodes.append(ScriptNode(prev, sup=target_node if is_sup else None, sub=target_node if not is_sup else None))
        elif isinstance(prev, TextNode):
            txt = prev.text
            if txt in ("log", "ln", "sin", "cos", "tan", "lim", "det"):
                nodes.append(ScriptNode(TextNode(txt), sup=target_node if is_sup else None, sub=target_node if not is_sup else None))
            elif len(txt) > 1 and not txt.endswith(" "):
                base_char = txt[-1]
                remain_txt = txt[:-1]
                if remain_txt:
                    nodes.append(TextNode(remain_txt))
                nodes.append(ScriptNode(TextNode(base_char), sup=target_node if is_sup else None, sub=target_node if not is_sup else None))
            else:
                nodes.append(ScriptNode(prev, sup=target_node if is_sup else None, sub=target_node if not is_sup else None))
        else:
            nodes.append(ScriptNode(prev, sup=target_node if is_sup else None, sub=target_node if not is_sup else None))

    def render(
        self,
        text: str,
        font_size: int = 24,
        color: Tuple[int, int, int] = TEXT_WHITE,
        bold: bool = True,
        max_width: Optional[int] = None
    ) -> pygame.Surface:
        """Renders the math text into a transparent Surface. Wraps lines if max_width is exceeded."""
        cache_key = (text, font_size, color, bold, max_width)
        if cache_key in self._render_cache:
            return self._render_cache[cache_key]

        if max_width is None:
            ast = self.parse(text)
            res = ast.render(font_size, color, bold)
            surface = res.surface
        else:
            surface = self._render_multiline(text, font_size, color, bold, max_width)

        if len(self._render_cache) > 500:
            self._render_cache.clear()
        self._render_cache[cache_key] = surface
        return surface

    def _render_multiline(
        self,
        text: str,
        font_size: int,
        color: Tuple[int, int, int],
        bold: bool,
        max_width: int
    ) -> pygame.Surface:
        """Renders words and math nodes wrapped across multiple lines with baseline alignment."""
        tokens = text.split(" ")
        lines: List[List[str]] = []
        cur_line: List[str] = []
        cur_w = 0
        space_w = get_font(font_size, bold=bold).size(" ")[0]

        for tok in tokens:
            if not tok:
                continue
            ast = self.parse(tok)
            w = ast.render(font_size, color, bold).width
            needed = w if not cur_line else (cur_w + space_w + w)
            if needed <= max_width or not cur_line:
                cur_line.append(tok)
                cur_w = needed
            else:
                lines.append(cur_line)
                cur_line = [tok]
                cur_w = w

        if cur_line:
            lines.append(cur_line)

        if not lines:
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        line_surfs: List[pygame.Surface] = []
        total_h = 0
        max_line_w = 0
        gap = max(4, int(font_size / 4))

        for line_tokens in lines:
            line_str = " ".join(line_tokens)
            l_ast = self.parse(line_str)
            l_res = l_ast.render(font_size, color, bold)
            line_surfs.append(l_res.surface)
            max_line_w = max(max_line_w, l_res.width)
            total_h += l_res.height + gap

        total_h = max(1, total_h - gap)
        out_surf = pygame.Surface((max(1, max_line_w), total_h), pygame.SRCALPHA)
        y = 0
        for l_surf in line_surfs:
            out_surf.blit(l_surf, ((max_line_w - l_surf.get_width()) // 2, y))
            y += l_surf.get_height() + gap

        return out_surf

    def get_size(
        self,
        text: str,
        font_size: int = 24,
        bold: bool = True,
        max_width: Optional[int] = None
    ) -> Tuple[int, int]:
        """Returns the (width, height) of the rendered math equation."""
        surf = self.render(text, font_size=font_size, color=TEXT_WHITE, bold=bold, max_width=max_width)
        return surf.get_size()

    def draw(
        self,
        surface: pygame.Surface,
        text: str,
        pos_or_rect: Union[Tuple[int, int], pygame.Rect],
        font_size: int = 24,
        color: Tuple[int, int, int] = TEXT_WHITE,
        bold: bool = True,
        align: str = "left",
        max_width: Optional[int] = None
    ) -> pygame.Rect:
        """Renders math text and blits it onto surface. Returns the destination rect."""
        eq_surf = self.render(text, font_size=font_size, color=color, bold=bold, max_width=max_width)
        ew, eh = eq_surf.get_size()

        if isinstance(pos_or_rect, pygame.Rect):
            r = pos_or_rect
            if align == "center":
                dest_rect = eq_surf.get_rect(center=r.center)
            elif align == "right":
                dest_rect = pygame.Rect(r.right - ew, r.centery - eh // 2, ew, eh)
            else:  # left
                dest_rect = pygame.Rect(r.x, r.centery - eh // 2, ew, eh)
        else:
            x, y = pos_or_rect
            if align == "center":
                dest_rect = pygame.Rect(x - ew // 2, y - eh // 2, ew, eh)
            elif align == "right":
                dest_rect = pygame.Rect(x - ew, y, ew, eh)
            else:  # left
                dest_rect = pygame.Rect(x, y, ew, eh)

        surface.blit(eq_surf, dest_rect)
        return dest_rect


# Global singleton instance
math_renderer = MathRenderer()


def render_math(
    text: str,
    font_size: int = 24,
    color: Tuple[int, int, int] = TEXT_WHITE,
    bold: bool = True,
    max_width: Optional[int] = None
) -> pygame.Surface:
    """Convenience function to render a math formula or equation into a transparent Surface."""
    return math_renderer.render(text, font_size=font_size, color=color, bold=bold, max_width=max_width)


def get_math_size(
    text: str,
    font_size: int = 24,
    bold: bool = True,
    max_width: Optional[int] = None
) -> Tuple[int, int]:
    """Convenience function to calculate rendered math dimensions (width, height)."""
    return math_renderer.get_size(text, font_size=font_size, bold=bold, max_width=max_width)


def draw_math(
    surface: pygame.Surface,
    text: str,
    pos_or_rect: Union[Tuple[int, int], pygame.Rect],
    font_size: int = 24,
    color: Tuple[int, int, int] = TEXT_WHITE,
    bold: bool = True,
    align: str = "left",
    max_width: Optional[int] = None
) -> pygame.Rect:
    """Convenience function to draw math text directly onto a target Pygame surface."""
    return math_renderer.draw(
        surface, text, pos_or_rect,
        font_size=font_size, color=color, bold=bold, align=align, max_width=max_width
    )
