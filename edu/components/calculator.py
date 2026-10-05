"""Interactive side calculator keypad and scratchpad matching the Duolingo Toolkit."""
from typing import List, Optional, Tuple
import pygame
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class CalculatorWidget:
    """Side calculator panel and scratchpad widget."""
    
    def __init__(self):
        self.is_open: bool = False
        self.expression: str = ""
        self.result: str = ""
        self.history: List[str] = []
        
        # Dimensions and slide animation
        self.width = 300
        self.x_offset: float = -320.0
        self.target_x_offset: float = -320.0
        
        self.buttons: List[Tuple[pygame.Rect, str, str]] = []  # (rect, label, action)
        self.hovered_btn: Optional[str] = None
        self.pressed_btn: Optional[str] = None

    def toggle(self) -> None:
        self.is_open = not self.is_open
        self.target_x_offset = 0.0 if self.is_open else -320.0

    def open(self) -> None:
        self.is_open = True
        self.target_x_offset = 0.0

    def close(self) -> None:
        self.is_open = False
        self.target_x_offset = -320.0

    def update(self, dt: float) -> None:
        self.x_offset += (self.target_x_offset - self.x_offset) * min(1.0, dt * 16.0)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handles calculator clicks and typing. Returns inserted character/result if any."""
        if not self.is_open and self.x_offset < -300:
            return None

        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self.hovered_btn = None
            for rect, label, action in self.buttons:
                if rect.collidepoint(pos):
                    self.hovered_btn = action
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for rect, label, action in self.buttons:
                if rect.collidepoint(pos):
                    self.pressed_btn = action
                    sound_manager.play_click()
                    return self._execute_action(action)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed_btn = None

        return None

    def _execute_action(self, action: str) -> Optional[str]:
        if action == "close":
            self.close()
        elif action == "clear":
            self.expression = ""
            self.result = ""
        elif action == "backspace":
            self.expression = self.expression[:-1]
        elif action == "=":
            self._evaluate()
        elif action == "**2":
            if self.expression:
                self.expression += "²"
            elif self.result:
                self.expression = f"{self.result}²"
        elif action == "sqrt":
            self.expression += "√("
        elif action in ("pi", "3.1415"):
            self.expression += "π"
        elif action == "%":
            self.expression += "%"
        elif action in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "(", ")", "+", "-", "*", "/"):
            self.expression += action
            return action
        elif action == "×":
            self.expression += "*"
        elif action == "÷":
            self.expression += "/"
        return None

    def _evaluate(self) -> None:
        if not self.expression:
            return
        try:
            import math
            clean_expr = self.expression
            clean_expr = clean_expr.replace("×", "*").replace("÷", "/")
            clean_expr = clean_expr.replace("²", "**2")
            clean_expr = clean_expr.replace("√", "math.sqrt")
            clean_expr = clean_expr.replace("π", "math.pi")
            clean_expr = clean_expr.replace("%", "/100")

            # Balance any unclosed parentheses
            open_count = clean_expr.count("(") - clean_expr.count(")")
            if open_count > 0:
                clean_expr += ")" * open_count

            # Safe eval with math functions allowed
            safe_scope = {
                "__builtins__": None,
                "math": math,
                "sqrt": math.sqrt,
                "pi": math.pi,
                "abs": abs
            }
            val = eval(clean_expr, safe_scope, {})
            if isinstance(val, (int, float)):
                if isinstance(val, float) and val.is_integer():
                    val = int(val)
                elif isinstance(val, float):
                    val = round(val, 6)
                self.result = str(val)
                self.history.append(f"{self.expression} = {self.result}")
            else:
                self.result = "Error"
        except Exception:
            self.result = "Error"

    def draw(self, screen: pygame.Surface, screen_rect: pygame.Rect) -> None:
        if self.x_offset < -310:
            return

        x = int(screen_rect.x + 20 + self.x_offset)
        y = screen_rect.y + 70
        h = min(680, screen_rect.height - 180)
        panel_rect = pygame.Rect(x, y, self.width, h)

        # Panel background
        draw_rounded_rect(screen, panel_rect, (24, 39, 46), radius=16, border_color=(43, 61, 71), border_width=2)

        # Scratchpad display area
        disp_h = 160
        disp_rect = pygame.Rect(x + 14, y + 14, self.width - 28, disp_h)
        draw_rounded_rect(screen, disp_rect, (19, 31, 36), radius=10, border_color=(35, 52, 61), border_width=1)

        # Expression & Result
        font_expr = get_font(22, bold=True)
        font_res = get_font(26, bold=True)
        expr_surf = font_expr.render(self.expression or "0", True, (200, 220, 230))
        disp_rect_inner = disp_rect.inflate(-20, -20)
        screen.blit(expr_surf, (disp_rect_inner.left, disp_rect_inner.top + 10))

        if self.result:
            res_surf = font_res.render(f"= {self.result}", True, (28, 176, 246))
            screen.blit(res_surf, (disp_rect_inner.right - res_surf.get_width(), disp_rect_inner.bottom - res_surf.get_height()))

        # Keypad Grid layout
        key_grid = [
            [("π", "3.1415"), ("x²", "**2"), ("√", "sqrt"), ("(", "("), (")", ")")],
            [("7", "7"), ("8", "8"), ("9", "9"), ("÷", "/"), ("⌫", "backspace")],
            [("4", "4"), ("5", "5"), ("6", "6"), ("×", "*"), ("C", "clear")],
            [("1", "1"), ("2", "2"), ("3", "3"), ("-", "-"), ("=", "=")],
            [("0", "0"), (".", "."), ("+", "+"), ("▼", "close")]
        ]

        self.buttons = []
        btn_y = disp_rect.bottom + 16
        pad = 6
        cols = 5
        bw = (self.width - 28 - pad * (cols - 1)) // cols
        bh = 44

        font_btn = get_font(18, bold=True)

        for row_idx, row in enumerate(key_grid):
            for col_idx, (label, action) in enumerate(row):
                # Check for wide buttons on bottom row
                cur_bw = bw
                if row_idx == 4 and col_idx == 0:
                    cur_bw = bw * 2 + pad
                elif row_idx == 4 and col_idx > 0:
                    bx = x + 14 + (col_idx + 1) * (bw + pad)
                else:
                    bx = x + 14 + col_idx * (bw + pad)

                if row_idx == 4 and col_idx == 0:
                    bx = x + 14

                by = btn_y + row_idx * (bh + pad)
                brect = pygame.Rect(bx, by, cur_bw, bh)

                # Colors based on key category
                is_op = action in ("+", "-", "*", "/", "=", "backspace", "clear", "close")
                is_num = action.isdigit() or action == "."

                bg = (32, 47, 54)
                if is_op:
                    if action == "=":
                        bg = (245, 158, 11)  # Orange accent for equals
                    elif action in ("+", "-", "*", "/"):
                        bg = (28, 176, 246)  # Blue for math ops
                    else:
                        bg = (40, 56, 65)

                if self.hovered_btn == action:
                    bg = tuple(min(255, int(c * 1.25) + 20) for c in bg)

                txt_color = (19, 31, 36) if action in ("+", "-", "*", "/", "=") else TEXT_WHITE
                draw_rounded_rect(screen, brect, bg, radius=8)
                lbl_surf = font_btn.render(label, True, txt_color)
                screen.blit(lbl_surf, lbl_surf.get_rect(center=brect.center))

                self.buttons.append((brect, label, action))
