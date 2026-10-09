"""Interactive Generator Menu for choosing operations and difficulty levels."""
from typing import List, Optional, Tuple
import pygame
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    CARD_BG,
    CARD_BORDER,
    CARD_HOVER,
    CARD_SELECTED_BG,
    CARD_SELECTED_BORDER,
    GREEN_CORRECT,
    GREEN_DARK,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class GeneratorMenu:
    """Full-screen or overlay menu to customize operation, difficulty, and generate new lessons."""

    OPERATIONS = [
        ("addition", "Addition", "+", (46, 204, 113)),
        ("subtraction", "Subtraction", "−", (52, 152, 219)),
        ("multiplication", "Multiplication", "×", (155, 89, 182)),
        ("division", "Division", "÷", (243, 156, 18)),
        ("coordinates", "Coordinates", "xy", (52, 152, 219)),
        ("logarithms", "Logarithms", "log", (155, 89, 182)),
        ("cylinder", "Cylinder 3D", "3D", (46, 204, 113)),
        ("mixed", "Mixed Ops", "🔀", (231, 76, 60)),
        ("curriculum", "All Lessons", "★", (149, 165, 166)),
    ]

    DIFFICULTIES = [
        ("easy", "Easy", (46, 204, 113)),
        ("medium", "Medium", (241, 196, 15)),
        ("hard", "Hard", (231, 76, 60)),
    ]

    COUNTS = [5, 8, 10, 15]

    def __init__(self):
        self.is_open: bool = False
        self.selected_op: str = "addition"
        self.selected_diff: str = "easy"
        self.selected_count: int = 8

        # UI rects
        self.op_rects: List[Tuple[pygame.Rect, str]] = []
        self.diff_rects: List[Tuple[pygame.Rect, str]] = []
        self.count_rects: List[Tuple[pygame.Rect, int]] = []
        self.start_rect = pygame.Rect(0, 0, 240, 56)
        self.close_rect = pygame.Rect(0, 0, 36, 36)

        self.hovered_item: Optional[str] = None
        self.start_pressed: bool = False

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> Optional[Tuple[str, str, int]]:
        """Handles menu clicks. Returns (operation, difficulty, count) if 'START' is clicked."""
        if not self.is_open:
            return None

        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self.hovered_item = None
            if self.close_rect.collidepoint(pos):
                self.hovered_item = "close"
            elif self.start_rect.collidepoint(pos):
                self.hovered_item = "start"
            else:
                for rect, op in self.op_rects:
                    if rect.collidepoint(pos):
                        self.hovered_item = f"op_{op}"
                        break
                for rect, diff in self.diff_rects:
                    if rect.collidepoint(pos):
                        self.hovered_item = f"diff_{diff}"
                        break
                for rect, cnt in self.count_rects:
                    if rect.collidepoint(pos):
                        self.hovered_item = f"cnt_{cnt}"
                        break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.close_rect.collidepoint(pos):
                sound_manager.play_click()
                self.close()
                return None

            if self.start_rect.collidepoint(pos):
                self.start_pressed = True
                sound_manager.play_correct()
                self.close()
                return (self.selected_op, self.selected_diff, self.selected_count)

            # Operation cards
            for rect, op in self.op_rects:
                if rect.collidepoint(pos):
                    sound_manager.play_click()
                    self.selected_op = op
                    return None

            # Difficulty pills
            for rect, diff in self.diff_rects:
                if rect.collidepoint(pos):
                    sound_manager.play_click()
                    self.selected_diff = diff
                    return None

            # Count buttons
            for rect, cnt in self.count_rects:
                if rect.collidepoint(pos):
                    sound_manager.play_click()
                    self.selected_count = cnt
                    return None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.start_pressed = False

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_m):
                self.close()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.close()
                return (self.selected_op, self.selected_diff, self.selected_count)

        return None

    def draw(self, screen: pygame.Surface, screen_rect: pygame.Rect) -> None:
        if not self.is_open:
            return

        # Dim overlay
        dim = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        screen.blit(dim, (0, 0))

        # Modal window container
        mw = min(880, screen_rect.width - 40)
        mh = min(710, screen_rect.height - 20)
        mx = (screen_rect.width - mw) // 2
        my = (screen_rect.height - mh) // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)

        draw_rounded_rect(screen, modal_rect, CARD_BG, radius=20, border_color=CARD_BORDER, border_width=2)

        # Title
        t_font = get_font(30, bold=True)
        t_surf = t_font.render("Math Exercise Generator", True, TEXT_WHITE)
        screen.blit(t_surf, t_surf.get_rect(center=(mx + mw // 2, my + 38)))

        # Close X
        self.close_rect = pygame.Rect(mx + mw - 48, my + 20, 32, 32)
        c_col = (200, 220, 230) if self.hovered_item == "close" else TEXT_MUTED
        cx = self.close_rect.centerx
        cy = self.close_rect.centery
        d = 7
        pygame.draw.line(screen, c_col, (cx - d, cy - d), (cx + d, cy + d), 3)
        pygame.draw.line(screen, c_col, (cx - d, cy + d), (cx + d, cy - d), 3)

        cur_y = my + 70

        # Section 1: Choose Operation
        sec_font = get_font(18, bold=True)
        sec1_surf = sec_font.render("1. SELECT OPERATION", True, (119, 142, 155))
        screen.blit(sec1_surf, (mx + 40, cur_y))
        cur_y += 26

        # 9 Operation Cards (3 rows x 3 columns)
        self.op_rects = []
        cols = 3
        rows = 3
        cw = (mw - 80 - (cols - 1) * 14) // cols
        ch = 56
        icon_font = get_font(20, bold=True)
        op_label_font = get_font(17, bold=True)

        for i, (op_key, op_name, op_symbol, op_color) in enumerate(self.OPERATIONS):
            r = i // cols
            c = i % cols
            card_rect = pygame.Rect(mx + 40 + c * (cw + 14), cur_y + r * (ch + 8), cw, ch)
            self.op_rects.append((card_rect, op_key))

            is_sel = (self.selected_op == op_key)
            is_hov = (self.hovered_item == f"op_{op_key}")

            bg = CARD_SELECTED_BG if is_sel else (CARD_HOVER if is_hov else (32, 47, 54))
            border = op_color if is_sel else ((53, 75, 87) if is_hov else CARD_BORDER)
            border_w = 3 if is_sel else 2

            draw_rounded_rect(screen, card_rect, bg, radius=12, border_color=border, border_width=border_w)

            # Icon badge
            badge_r = 16
            bx = card_rect.x + 24
            by = card_rect.centery
            pygame.draw.circle(screen, op_color, (bx, by), badge_r)
            sym_surf = icon_font.render(op_symbol, True, (19, 31, 36))
            screen.blit(sym_surf, sym_surf.get_rect(center=(bx, by)))

            # Name label
            lbl_surf = op_label_font.render(op_name, True, TEXT_WHITE)
            screen.blit(lbl_surf, (bx + 24, by - lbl_surf.get_height() // 2))

        cur_y += rows * (ch + 8) + 16

        # Section 2: Choose Difficulty
        sec2_surf = sec_font.render("2. SELECT DIFFICULTY", True, (119, 142, 155))
        screen.blit(sec2_surf, (mx + 40, cur_y))
        cur_y += 30

        self.diff_rects = []
        dw = (mw - 80 - 2 * 14) // 3
        dh = 48
        diff_font = get_font(18, bold=True)

        for i, (d_key, d_name, d_color) in enumerate(self.DIFFICULTIES):
            drect = pygame.Rect(mx + 40 + i * (dw + 14), cur_y, dw, dh)
            self.diff_rects.append((drect, d_key))

            is_sel = (self.selected_diff == d_key)
            is_hov = (self.hovered_item == f"diff_{d_key}")

            bg = CARD_SELECTED_BG if is_sel else (CARD_HOVER if is_hov else (32, 47, 54))
            border = d_color if is_sel else ((53, 75, 87) if is_hov else CARD_BORDER)
            draw_rounded_rect(screen, drect, bg, radius=12, border_color=border, border_width=3 if is_sel else 2)

            # Dot indicator
            pygame.draw.circle(screen, d_color, (drect.x + 24, drect.centery), 6)
            txt_surf = diff_font.render(d_name, True, TEXT_WHITE)
            screen.blit(txt_surf, txt_surf.get_rect(center=(drect.centerx + 8, drect.centery)))

        cur_y += dh + 24

        # Section 3: Question Count
        sec3_surf = sec_font.render("3. NUMBER OF EXERCISES", True, (119, 142, 155))
        screen.blit(sec3_surf, (mx + 40, cur_y))
        cur_y += 30

        self.count_rects = []
        cw_cnt = (mw - 80 - 3 * 14) // 4
        ch_cnt = 42
        for i, cnt in enumerate(self.COUNTS):
            crect = pygame.Rect(mx + 40 + i * (cw_cnt + 14), cur_y, cw_cnt, ch_cnt)
            self.count_rects.append((crect, cnt))

            is_sel = (self.selected_count == cnt)
            is_hov = (self.hovered_item == f"cnt_{cnt}")

            bg = CARD_SELECTED_BG if is_sel else (CARD_HOVER if is_hov else (32, 47, 54))
            border = ACCENT_BLUE if is_sel else ((53, 75, 87) if is_hov else CARD_BORDER)
            draw_rounded_rect(screen, crect, bg, radius=10, border_color=border, border_width=2)

            csurf = diff_font.render(f"{cnt} Questions", True, ACCENT_BLUE if is_sel else TEXT_WHITE)
            screen.blit(csurf, csurf.get_rect(center=crect.center))

        cur_y += ch_cnt + 34

        # Big "START LESSON" button
        self.start_rect = pygame.Rect(mx + mw // 2 - 140, cur_y, 280, 56)
        btn_font = get_font(22, bold=True)
        draw_bevel_button(
            screen, self.start_rect, "START LESSON",
            bg_color=GREEN_CORRECT,
            bevel_color=GREEN_DARK,
            text_color=TEXT_WHITE,
            font=btn_font,
            is_hovered=(self.hovered_item == "start"),
            is_pressed=self.start_pressed,
            border_radius=16
        )
