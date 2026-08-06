import pygame
from typing import List, Tuple, Any, Optional, Dict

class RenderBlock:
    """Represents a pre-rendered 2D graphical composition of a math equation part.
    
    Includes the Pygame Surface containing the rendered graphics, pixel dimensions,
    and the y-offset of the math axis (for alignment).
    """
    def __init__(self, surface: pygame.Surface, axis: int, inserts: Optional[List[Dict[str, Any]]] = None):
        self.surface = surface
        self.width = surface.get_width()
        self.height = surface.get_height()
        self.axis = axis
        self.inserts = inserts if inserts is not None else []

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
    def offset_inserts(cls, block: "RenderBlock", dx: int, dy: int) -> List[Dict[str, Any]]:
        """Offsets all insert box relative coordinates in a block."""
        return [{
            'id': ins['id'],
            'x': ins['x'] + dx,
            'y': ins['y'] + dy,
            'width': ins['width'],
            'height': ins['height'],
            'char_width': ins['char_width'],
            'font_size': ins['font_size']
        } for ins in block.inserts]

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
        
        # Offset and merge inserts
        new_inserts = cls.offset_inserts(A, 0, offset_A) + cls.offset_inserts(B, A.width, offset_B)
        
        return cls(surf, res_axis, new_inserts)


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
        
        # Offset and merge inserts
        inserts = RenderBlock.offset_inserts(T, tx, T_y) + RenderBlock.offset_inserts(B, bx, B_y)
        
        return RenderBlock(surf, axis, inserts)


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
        
        return RenderBlock(E.surface, axis, E.inserts)


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
        
        inserts = RenderBlock.offset_inserts(A, root_sign_width + padding_right, spacing_top + line_thickness)
        
        return RenderBlock(surf, axis, inserts)


class InsertFunction(MathFunction):
    """Formats a text input field placeholder with character width specified in arg."""
    def __init__(self):
        super().__init__("insert", 1)

    def format(
        self,
        args: List[List[ASTNode]],
        renderer: "MathEquationRenderer",
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        arg_text = ""
        if args and args[0]:
            for node in args[0]:
                if isinstance(node, TextNode):
                    arg_text += node.text
        try:
            width_chars = int(arg_text.strip())
        except ValueError:
            width_chars = 3
            
        font = renderer.get_font(font_size)
        char_w, _ = font.size(" ")
        line_h = font.get_linesize()
        
        w = char_w * width_chars + 12
        h = line_h
        
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        axis = int(font.get_ascent() * 0.65)
        
        renderer.insert_counter += 1
        ins_id = f"insert_{renderer.insert_counter}"
        
        inserts = [{
            'id': ins_id,
            'x': 0,
            'y': 0,
            'width': w,
            'height': h,
            'char_width': width_chars,
            'font_size': font_size
        }]
        
        return RenderBlock(surf, axis, inserts)


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
        self.register_function(InsertFunction())
        self.insert_counter = 0

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

    def render(
        self,
        nodes: List[ASTNode],
        font_size: int,
        color: Tuple[int, int, int]
    ) -> RenderBlock:
        """Top-level render entry point. Resets the insert counter and compiles AST."""
        self.insert_counter = 0
        return self.render_nodes(nodes, font_size, color)


class MathEquationWidget:
    """A Pygame UI widget that pre-renders and displays math equations with interactive fields.
    
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
        
        # Interactive state
        self.insert_values: Dict[str, str] = {}
        self.focused_insert_id: Optional[str] = None
        self.cursor_visible = True
        self.cursor_timer = 0.0
        
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
            self.render_block = self.renderer.render(nodes, self.font_size, color)
        except Exception as e:
            # Fallback to rendering the error message visually
            font = self.renderer.get_font(self.font_size)
            surf = font.render(f"[Error: {str(e)}]", True, (255, 65, 54))
            self.render_block = RenderBlock(surf, int(font.get_ascent() * 0.65))
            
        self.rect = pygame.Rect(self.pos, (self.render_block.width, self.render_block.height))
        self.baseline_y = self.pos[1] + self.render_block.axis
        
        # Sync values with current layout blocks
        current_ids = {ins['id'] for ins in self.render_block.inserts}
        for ins_id in current_ids:
            if ins_id not in self.insert_values:
                self.insert_values[ins_id] = ""
        # Clean up old unused ids
        for old_id in list(self.insert_values.keys()):
            if old_id not in current_ids:
                del self.insert_values[old_id]
        if self.focused_insert_id not in current_ids:
            self.focused_insert_id = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes mouse clicks for focus transitions and keypresses for text editing."""
        if not self.render_block:
            return
            
        # 1. Mouse Click Collision Detection (Focus)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = getattr(event, "pos", None)
            if mouse_pos is None:
                if pygame.display.get_init():
                    mouse_pos = pygame.mouse.get_pos()
                else:
                    mouse_pos = (0, 0)
                
            clicked_any = False
            for ins in self.render_block.inserts:
                rect = pygame.Rect(
                    self.pos[0] + ins['x'],
                    self.pos[1] + ins['y'],
                    ins['width'],
                    ins['height']
                )
                if rect.collidepoint(mouse_pos):
                    self.focused_insert_id = ins['id']
                    self.cursor_visible = True
                    self.cursor_timer = 0.0
                    clicked_any = True
                    break
            if not clicked_any:
                self.focused_insert_id = None
                
        # 2. Text Input when Focused
        elif event.type == pygame.KEYDOWN and self.focused_insert_id is not None:
            active_ins = None
            for ins in self.render_block.inserts:
                if ins['id'] == self.focused_insert_id:
                    active_ins = ins
                    break
                    
            if active_ins:
                text = self.insert_values.get(self.focused_insert_id, "")
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                    self.cursor_visible = True
                    self.cursor_timer = 0.0
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                    self.focused_insert_id = None
                else:
                    if event.unicode and event.unicode.isprintable() and event.unicode != "":
                        if len(text) < active_ins['char_width']:
                            text += event.unicode
                            self.cursor_visible = True
                            self.cursor_timer = 0.0
                            
                self.insert_values[self.focused_insert_id] = text

    def update(self, dt: float) -> None:
        """Blinks the active input cursor."""
        if self.focused_insert_id is not None:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer -= 0.5
                self.cursor_visible = not self.cursor_visible
        else:
            self.cursor_visible = False

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Blits the pre-rendered equation surface and draws active input boxes."""
        target_color = self.color
        if target_color is None:
            if hasattr(app, "get_color"):
                target_color = app.get_color("secondary", (230, 230, 230, 255))[:3]
            else:
                target_color = (230, 230, 230)
                
        # Re-render if the theme color has changed
        if target_color != self._cached_color:
            self._render(target_color)
            
        if self.render_block:
            # Draw math graphics first
            screen.blit(self.render_block.surface, self.pos)
            
            # Fetch application colors for text inputs
            bg_color = (25, 25, 30, 255)
            accent_color = (255, 65, 54, 255)
            primary_color = (0, 150, 255, 255)
            
            if hasattr(app, "get_color"):
                bg_color = app.get_color("wheel_bg", bg_color)
                accent_color = app.get_color("accent", accent_color)
                primary_color = app.get_color("primary", primary_color)
                
            # Draw each interactive insert box
            for ins in self.render_block.inserts:
                ins_id = ins['id']
                text = self.insert_values.get(ins_id, "")
                
                # Absolute coordinates
                rect = pygame.Rect(
                    self.pos[0] + ins['x'],
                    self.pos[1] + ins['y'],
                    ins['width'],
                    ins['height']
                )
                
                # Draw field background
                pygame.draw.rect(screen, bg_color, rect)
                
                # Draw border depending on focus
                if self.focused_insert_id == ins_id:
                    pygame.draw.rect(screen, primary_color, rect, 2)
                else:
                    border_color = (target_color[0] // 2, target_color[1] // 2, target_color[2] // 2, 255)
                    pygame.draw.rect(screen, border_color, rect, 1)
                    
                # Render text inside field
                font = self.renderer.get_font(ins['font_size'])
                text_surf = font.render(text, True, target_color)
                
                # Align text inside rect (margin-left: 6px, vertically centered)
                tx = rect.x + 6
                ty = rect.y + (rect.height - text_surf.get_height()) // 2
                screen.blit(text_surf, (tx, ty))
                
                # Draw blinking cursor if focused
                if self.focused_insert_id == ins_id and self.cursor_visible:
                    text_w = font.size(text)[0]
                    cx = tx + text_w + 1
                    pygame.draw.line(screen, accent_color, (cx, ty), (cx, ty + text_surf.get_height()), 2)
