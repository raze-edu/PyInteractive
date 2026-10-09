"""Exercise type: Type the answer (typing numeric answer with calculator integration)."""
from typing import Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_coordinate_grid,
    ACCENT_BLUE,
    CARD_BG,
    CARD_BORDER,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class TypeAnswerExercise(BaseExercise):
    """Type the answer exercise with physical keyboard and on-screen keypad support."""
    
    def __init__(
        self,
        equation_format: str,  # e.g. "400 - 20 - 1 = [ ]" or "x = [ ]"
        correct_answer: str,   # e.g. "379"
        title: str = "Type the answer",
        help_tip: str = "Perform the arithmetic operations and type the numerical answer.",
        prompt_coord: Optional[Tuple[int, int]] = None,
        highlight_coord: str = "x",
        prompt_grid_point: Optional[Tuple[int, int]] = None,
        x_range: Tuple[int, int] = (-5, 5),
        y_range: Tuple[int, int] = (-5, 5),
        show_keypad: bool = True
    ):
        super().__init__(
            title=title,
            help_title="Calculation Tip",
            help_tip=help_tip,
            help_faqs=[
                ("Step by step", "Subtract the tens first from the hundreds, then subtract the remaining ones."),
                ("Using the toolkit", "Tap the calculator icon on the bottom left to open the scratchpad and calculator!")
            ]
        )
        self.equation_format = equation_format
        self.correct_answer = str(correct_answer).strip()
        self.prompt_coord = prompt_coord
        self.highlight_coord = highlight_coord
        self.prompt_grid_point = prompt_grid_point
        self.x_range = x_range
        self.y_range = y_range
        self.show_keypad = show_keypad

        self.user_text: str = ""
        self.input_rect = pygame.Rect(0, 0, 160, 56)
        self.cursor_blink: float = 0.0
        self.keypad_rects: list = []  # list of (Rect, char)

    def is_ready_to_check(self) -> bool:
        return len(self.user_text.strip()) > 0

    def check(self) -> bool:
        try:
            # Compare numeric or string value
            clean_user = self.user_text.strip()
            self.is_solved = (clean_user == self.correct_answer or float(clean_user) == float(self.correct_answer))
        except Exception:
            self.is_solved = (self.user_text.strip() == self.correct_answer)
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Awesome!", "")
        return ("Not quite.", self.correct_answer)

    def reset(self) -> None:
        super().reset()
        self.user_text = ""

    def append_char(self, char: str) -> None:
        """Called when calculator or keypad inserts a character."""
        if len(self.user_text) < 12 and char in "0123456789.-":
            self.user_text += char
            sound_manager.play_click()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for rect, ch in self.keypad_rects:
                if rect.collidepoint(mx, my):
                    if ch == "back":
                        self.user_text = self.user_text[:-1]
                        sound_manager.play_click()
                    else:
                        self.append_char(ch)
                    return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.user_text = self.user_text[:-1]
                sound_manager.play_click()
            elif event.unicode in "0123456789.-":
                self.append_char(event.unicode)

    def update(self, dt: float) -> None:
        self.cursor_blink = (self.cursor_blink + dt * 2.5) % 1.0

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        self.keypad_rects = []
        # Title
        title_font = get_font(30, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 35)))

        eq_y = area_rect.y + 120

        # Optional Coordinate Grid
        if self.prompt_grid_point is not None:
            gw, gh = 200, 160
            grect = pygame.Rect(area_rect.centerx - gw // 2, area_rect.y + 60, gw, gh)
            draw_coordinate_grid(
                screen,
                grect,
                x_range=self.x_range,
                y_range=self.y_range,
                highlight_point=self.prompt_grid_point,
                show_projections=True,
                show_labels=True
            )
            eq_y = area_rect.y + 245
        elif self.prompt_coord is not None:
            # Render coordinate prompt
            cfont = get_font(36, bold=True)
            px, py = self.prompt_coord
            lbl = cfont.render(f"({px}, {py})", True, TEXT_WHITE)
            pill = pygame.Rect(area_rect.centerx - 75, area_rect.y + 65, 150, 46)
            draw_rounded_rect(screen, pill, CARD_BG, radius=10, border_color=CARD_BORDER, border_width=1)
            screen.blit(lbl, lbl.get_rect(center=pill.center))
            eq_y = area_rect.y + 140

        # Equation / Input box line
        eq_font = get_font(36, bold=True)
        parts = self.equation_format.split("[ ]")
        box_w = max(80, len(self.user_text) * 22 + 28)
        box_h = 50
        
        if len(parts) == 2:
            left_text = parts[0].strip()
            right_text = parts[1].strip()
            left_surf = eq_font.render(left_text, True, TEXT_WHITE) if left_text else None
            right_surf = eq_font.render(right_text, True, TEXT_WHITE) if right_text else None
            
            total_w = box_w + 20
            if left_surf:
                total_w += left_surf.get_width() + 12
            if right_surf:
                total_w += right_surf.get_width() + 12
                
            cur_x = area_rect.centerx - total_w // 2
            if left_surf:
                screen.blit(left_surf, (cur_x, eq_y - left_surf.get_height() // 2))
                cur_x += left_surf.get_width() + 12
                
            self.input_rect = pygame.Rect(cur_x, eq_y - box_h // 2, box_w, box_h)
            draw_rounded_rect(screen, self.input_rect, CARD_BG, radius=10, border_color=ACCENT_BLUE, border_width=3)
            
            # Text inside box
            if self.user_text:
                txt_surf = eq_font.render(self.user_text, True, ACCENT_BLUE)
                screen.blit(txt_surf, txt_surf.get_rect(center=self.input_rect.center))
                
            # Flashing cursor
            if self.cursor_blink < 0.5:
                if self.user_text:
                    cx = self.input_rect.centerx + len(self.user_text) * 11 + 4
                else:
                    cx = self.input_rect.centerx
                pygame.draw.line(screen, ACCENT_BLUE, (cx, self.input_rect.centery - 14), (cx, self.input_rect.centery + 14), 2)
                
            cur_x += box_w + 12
            if right_surf:
                screen.blit(right_surf, (cur_x, eq_y - right_surf.get_height() // 2))

        # On-screen Numeric Keypad (4 rows x 3 cols)
        if self.show_keypad:
            key_layout = [
                ["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"],
                ["-", "0", "back"]
            ]
            kw, kh = 62, 42
            spacing = 8
            total_kw = 3 * kw + 2 * spacing
            start_kx = area_rect.centerx - total_kw // 2
            start_ky = eq_y + 40
            
            kfont = get_font(20, bold=True)
            mouse_pos = pygame.mouse.get_pos()

            for r_idx, row in enumerate(key_layout):
                for c_idx, val in enumerate(row):
                    bx = start_kx + c_idx * (kw + spacing)
                    by = start_ky + r_idx * (kh + spacing)
                    btn_rect = pygame.Rect(bx, by, kw, kh)
                    self.keypad_rects.append((btn_rect, val))

                    is_hov = btn_rect.collidepoint(mouse_pos)
                    bcol = (35, 54, 64) if is_hov else CARD_BG
                    border = ACCENT_BLUE if is_hov else CARD_BORDER
                    draw_rounded_rect(screen, btn_rect, bcol, radius=8, border_color=border, border_width=1)

                    disp_text = "⌫" if val == "back" else val
                    t_col = ACCENT_BLUE if is_hov else TEXT_WHITE
                    ts = kfont.render(disp_text, True, t_col)
                    screen.blit(ts, ts.get_rect(center=btn_rect.center))
        else:
            pad_rect = pygame.Rect(area_rect.centerx - 220, area_rect.y + 260, 440, 52)
            draw_rounded_rect(screen, pad_rect, (24, 39, 46), radius=14, border_color=(35, 52, 61), border_width=1)
            hint_font = get_font(18)
            hint_surf = hint_font.render("Type digits on your keyboard or open Toolkit (left)", True, TEXT_MUTED)
            screen.blit(hint_surf, hint_surf.get_rect(center=pad_rect.center))
