import pygame
from typing import List, Tuple, Any, Optional, Dict

class RenderBlock:
    """Represents a pre-rendered 2D graphical composition of a math equation part.
    
    Includes the Pygame Surface containing the rendered graphics, pixel dimensions,
    and the y-offset of the math axis (for alignment).
    """
    def __init__(self, surface: pygame.Surface, axis: int):
        self.surface = surface
        self.width = surface.get_width()
        self.height = surface.get_height()
        self.axis = axis

    @classmethod
    def concat(cls, blocks: List["RenderBlock"]) -> "RenderBlock":
        """Concatenates a list of RenderBlocks side-by-side, aligning their math axes."""
        if not blocks:
            surf = pygame.Surface((0, 0), pygame.SRCALPHA)
            return cls(surf, 0)
        
        result = blocks[0]
        for block in blocks[1:]:
            result = cls._concat_two(result, block)
        return result

    @classmethod
    def _concat_two(cls, A: "RenderBlock", B: "RenderBlock") -> "RenderBlock":
        """Helper to concatenate two RenderBlocks side-by-side, aligning their math axes."""
        res_axis = max(A.axis, B.axis)
        offset_A = res_axis - A.axis
        offset_B = res_axis - B.axis
        
        below_A = A.height - A.axis
        below_B = B.height - B.axis
        res_height = res_axis + max(below_A, below_B)
        res_width = A.width + B.width
        
        # Create a transparent composite surface
        surf = pygame.Surface((res_width, res_height), pygame.SRCALPHA)
        surf.blit(A.surface, (0, offset_A))
        surf.blit(B.surface, (A.width, offset_B))
        
        return cls(surf, res_axis)


class MathFunction:
    """Base class for custom math rendering functions."""
    def __init__(self, name: str, num_args: int):
        self.name = name
        self.num_args = num_args

    def format(
        self,
        args: List[List["ASTNode"]],
        renderer: "MathEquationRenderer",
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        """Formats the function args (AST lists) into a single RenderBlock."""
        raise NotImplementedError("MathFunction subclasses must implement format.")


class FracFunction(MathFunction):
    """Formats two arguments as a fraction (numerator over denominator) with scaled down text."""
    def __init__(self):
        super().__init__("frac", 2)

    def format(
        self,
        args: List[List["ASTNode"]],
        renderer: "MathEquationRenderer",
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        # Scale down child fonts (e.g. ~60% of the parent height, minimum 8px)
        child_font_size = max(8, int(font_size * 0.6))
        
        T = renderer.render_nodes(args[0], child_font_size, color)
        B = renderer.render_nodes(args[1], child_font_size, color)
        
        # Add horizontal padding on sides of fraction line
        padding_h = max(2, int(font_size * 0.1))
        frac_w = max(T.width, B.width) + 2 * padding_h
        
        # Center positions
        tx = (frac_w - T.width) // 2
        bx = (frac_w - B.width) // 2
        
        # Vertical spacing/line parameters
        spacing_v = max(1, int(font_size * 0.05))
        line_thickness = max(1, int(font_size * 0.05))
        
        # Stack vertically
        T_y = 0
        line_y = T.height + spacing_v
        B_y = line_y + line_thickness + spacing_v
        
        total_h = B_y + B.height
        
        # Create transparency-enabled surface
        surf = pygame.Surface((frac_w, total_h), pygame.SRCALPHA)
        surf.blit(T.surface, (tx, T_y))
        surf.blit(B.surface, (bx, B_y))
        
        # Draw fraction separator line
        line_center_y = line_y + line_thickness // 2
        pygame.draw.line(
            surf,
            color,
            (0, line_center_y),
            (frac_w, line_center_y),
            line_thickness
        )
        
        # The math axis aligns perfectly with the center of the fraction line
        axis = line_center_y
        
        return RenderBlock(surf, axis)


class ExpoFunction(MathFunction):
    """Formats one argument as an exponent (superscript)."""
    def __init__(self):
        super().__init__("expo", 1)

    def format(
        self,
        args: List[List[ASTNode]],
        renderer: "MathEquationRenderer",
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        # Exponents are scaled down (e.g. 60% of font size)
        child_font_size = max(8, int(font_size * 0.6))
        E = renderer.render_nodes(args[0], child_font_size, color)
        
        # We shift the exponent up relative to the math axis
        parent_font = renderer.get_font(font_size)
        parent_ascent = parent_font.get_ascent()
        
        # Shift the bottom of the exponent up
        shift = int(parent_ascent * 0.45)
        axis = E.height + shift
        
        return RenderBlock(E.surface, axis)


class SqrtFunction(MathFunction):
    """Formats one argument inside a square root symbol."""
    def __init__(self):
        super().__init__("sqrt", 1)

    def format(
        self,
        args: List[List[ASTNode]],
        renderer: "MathEquationRenderer",
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        # Sqrt argument is rendered at full size
        A = renderer.render_nodes(args[0], font_size, color)
        
        # Dimensions and spacing
        line_thickness = max(1, int(font_size * 0.05))
        spacing_top = max(2, int(font_size * 0.08))
        spacing_bottom = max(1, int(font_size * 0.04))
        
        root_sign_width = max(10, int(font_size * 0.5))
        padding_right = max(2, int(font_size * 0.06))
        
        W = root_sign_width + padding_right + A.width
        H = A.height + spacing_top + line_thickness + spacing_bottom
        
        # Math axis of the root block
        axis = spacing_top + line_thickness + A.axis
        
        # Create transparent surface
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        
        # Blit the argument
        surf.blit(A.surface, (root_sign_width + padding_right, spacing_top + line_thickness))
        
        # Draw root sign path
        sw = root_sign_width
        x0 = 0
        y0 = axis
        
        x1 = int(sw * 0.35)
        y1 = axis + max(1, int(font_size * 0.06))
        
        x2 = int(sw * 0.65)
        y2 = H - spacing_bottom
        
        x3 = sw
        y3 = line_thickness // 2
        
        x4 = W
        y4 = line_thickness // 2
        
        # Draw root sign with lines
        pygame.draw.lines(
            surf,
            color,
            False,
            [(x0, y0), (x1, y1), (x2, y2), (x3, y3), (x4, y4)],
            line_thickness
        )
        
        return RenderBlock(surf, axis)


class ASTNode:
    """Base class for AST representation."""
    pass


class TextNode(ASTNode):
    """Represents raw text in the math equation."""
    def __init__(self, text: str):
        self.text = text


class FunctionNode(ASTNode):
    """Represents a function (e.g. !frac) in the math equation."""
    def __init__(self, name: str, args: List[List[ASTNode]]):
        self.name = name
        self.args = args


class MathEquationRenderer:
    """Parses math equations and builds graphical RenderBlocks."""
    def __init__(self, font_name: Optional[str] = "arial"):
        self.functions: Dict[str, MathFunction] = {}
        self.font_name = font_name
        self.font_cache: Dict[Tuple[Optional[str], int], pygame.font.Font] = {}
        self.register_function(FracFunction())
        self.register_function(ExpoFunction())
        self.register_function(SqrtFunction())

    def register_function(self, func: MathFunction) -> None:
        """Registers a function formatter."""
        self.functions[func.name] = func

    def get_function(self, name: str) -> Optional[MathFunction]:
        """Retrieves a function formatter by name."""
        return self.functions.get(name)

    def get_font(self, font_size: int) -> pygame.font.Font:
        """Helper to cached-retrieve pygame Font objects."""
        key = (self.font_name, font_size)
        if key not in self.font_cache:
            try:
                if self.font_name:
                    font = pygame.font.SysFont(self.font_name, font_size)
                else:
                    font = pygame.font.SysFont("arial", font_size)
            except Exception:
                font = pygame.font.Font(None, font_size)
            self.font_cache[key] = font
        return self.font_cache[key]

    def parse(self, text: str) -> List[ASTNode]:
        """Parses the equation string into a sequence of AST nodes."""
        idx = 0
        n = len(text)
        
        def parse_sequence() -> List[ASTNode]:
            nonlocal idx
            nodes = []
            current_text = []
            
            def flush_text():
                if current_text:
                    nodes.append(TextNode("".join(current_text)))
                    current_text.clear()
                    
            while idx < n:
                char = text[idx]
                if char == '\\':
                    if idx + 1 < n:
                        next_char = text[idx + 1]
                        if next_char in ('!', '{', '}', '\\'):
                            current_text.append(next_char)
                            idx += 2
                            continue
                    current_text.append('\\')
                    idx += 1
                elif char == '!':
                    flush_text()
                    idx += 1  # skip '!'
                    
                    ident_start = idx
                    while idx < n and (text[idx].isalnum() or text[idx] == '_'):
                        idx += 1
                    func_name = text[ident_start:idx]
                    
                    if not func_name:
                        raise ValueError(f"Expected function name after '!' at position {ident_start}")
                    
                    func_obj = self.get_function(func_name)
                    if not func_obj:
                        raise ValueError(f"Unknown math function: {func_name}")
                        
                    args = []
                    for arg_idx in range(func_obj.num_args):
                        # skip spacing
                        while idx < n and text[idx].isspace():
                            idx += 1
                            
                        if idx >= n or text[idx] != '{':
                            raise ValueError(f"Expected '{{' for argument {arg_idx + 1} of function '{func_name}' at position {idx}")
                        
                        idx += 1  # skip '{'
                        
                        arg_start = idx
                        brace_count = 1
                        while idx < n and brace_count > 0:
                            c = text[idx]
                            if c == '\\':
                                idx += 2
                                continue
                            elif c == '{':
                                brace_count += 1
                            elif c == '}':
                                brace_count -= 1
                            if brace_count > 0:
                                idx += 1
                                
                        if brace_count > 0:
                            raise ValueError(f"Unmatched '{{' for argument {arg_idx + 1} of function '{func_name}' starting at position {arg_start - 1}")
                            
                        arg_text = text[arg_start:idx]
                        idx += 1  # skip '}'
                        
                        args.append(self.parse(arg_text))
                        
                    nodes.append(FunctionNode(func_name, args))
                elif char in ('{', '}'):
                    raise ValueError(f"Unexpected unescaped character '{char}' at position {idx}")
                else:
                    current_text.append(char)
                    idx += 1
                    
            flush_text()
            return nodes
            
        return parse_sequence()

    def render_nodes(
        self,
        nodes: List[ASTNode],
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        """Renders and aligns list of AST nodes into a single RenderBlock."""
        blocks = []
        for node in nodes:
            if isinstance(node, TextNode):
                font = self.get_font(font_size)
                surf = font.render(node.text, True, color)
                ascent = font.get_ascent()
                # Math axis is typically a bit above baseline (approx 65% of ascent)
                axis = int(ascent * 0.65)
                blocks.append(RenderBlock(surf, axis))
            elif isinstance(node, FunctionNode):
                func_obj = self.get_function(node.name)
                block = func_obj.format(node.args, self, font_size, color)
                blocks.append(block)
        return RenderBlock.concat(blocks)


class MathEquationWidget:
    """A Pygame UI widget that pre-renders and displays math equations.
    
    Conforms to the PyInteractive GameObject protocol.
    """
    def __init__(
        self,
        pos: Tuple[int, int],
        expression: str,
        font_size: int = 32,
        color: Optional[Tuple[int, int, int]] = None,
        font_name: Optional[str] = "arial"
    ):
        self.pos = pos
        self._expression = expression
        self.font_size = font_size
        self.color = color
        self.font_name = font_name
        
        self.renderer = MathEquationRenderer(font_name=font_name)
        self.render_block: Optional[RenderBlock] = None
        self.rect = pygame.Rect(pos, (0, 0))
        self.baseline_y = pos[1]
        
        self._cached_color = None
        self._render()

    @property
    def expression(self) -> str:
        return self._expression

    @expression.setter
    def expression(self, val: str) -> None:
        if self._expression != val:
            self._expression = val
            self._render(self._cached_color)

    def _render(self, color_to_use: Optional[Tuple[int, int, int]] = None) -> None:
        """Pre-renders the equation to a single surface."""
        color = color_to_use or self.color or (230, 230, 230)
        self._cached_color = color
        
        try:
            nodes = self.renderer.parse(self._expression)
            self.render_block = self.renderer.render_nodes(nodes, self.font_size, color)
        except Exception as e:
            # Fallback to rendering the error message visually
            font = self.renderer.get_font(self.font_size)
            surf = font.render(f"[Error: {str(e)}]", True, (255, 65, 54))
            self.render_block = RenderBlock(surf, int(font.get_ascent() * 0.65))
            
        self.rect = pygame.Rect(self.pos, (self.render_block.width, self.render_block.height))
        self.baseline_y = self.pos[1] + self.render_block.axis

    def update(self, dt: float) -> None:
        """Satisfies the PyInteractive update signature."""
        pass

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Blits the pre-rendered equation surface onto the screen."""
        target_color = self.color
        if target_color is None:
            # Pull secondary color from application theme
            if hasattr(app, "get_color"):
                target_color = app.get_color("secondary", (230, 230, 230, 255))[:3]
            else:
                target_color = (230, 230, 230)
                
        # Re-render if the theme color has changed
        if target_color != self._cached_color:
            self._render(target_color)
            
        if self.render_block:
            screen.blit(self.render_block.surface, self.pos)
