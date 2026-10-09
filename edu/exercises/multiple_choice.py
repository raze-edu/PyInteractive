"""Exercise type: Multiple choice / Fill in the blank (algebraic expansion, geometry area, visual choices)."""
from typing import List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_pie_chart,
    draw_cylinder_3d,
    draw_coordinate_grid,
    ACCENT_BLUE,
    ACCENT_BLUE_LIGHT,
    CARD_BG,
    CARD_BORDER,
    CARD_HOVER,
    CARD_SELECTED_BG,
    CARD_SELECTED_BORDER,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class MultipleChoiceExercise(BaseExercise):
    """Multiple choice / Fill in the blank exercise."""
    
    def __init__(
        self,
        question_text: str,                 # e.g. "6(x - 1) = [ ] - 6" or "Select the area..."
        choices: List[str],                 # list of choice strings
        correct_choice_index: int,
        diagram_type: Optional[str] = None, # None, "grid_rectangle", "visual_fractions"
        diagram_data: Optional[dict] = None,# e.g. {"w": 6, "h": 4} or fraction data
        character_speech: Optional[str] = None, # If present, draws speech bubble
        title: str = "Fill in the blank",
        help_tip: str = "Select the option that correctly completes the statement or equation."
    ):
        super().__init__(
            title=title,
            help_title="Tip",
            help_tip=help_tip,
            help_faqs=[
                ("How to solve distributive property?", "Multiply the outside number by everything inside: a(b + c) = ab + ac."),
                ("How does triangle area relate to a rectangle?", "A diagonal divides any rectangle into two identical right triangles, so each triangle's area is exactly half.")
            ]
        )
        self.question_text = question_text
        self.choices = choices
        self.correct_choice_index = correct_choice_index
        self.diagram_type = diagram_type
        self.diagram_data = diagram_data or {}
        self.character_speech = character_speech
        
        self.selected_index: Optional[int] = None
        self.choice_rects: List[pygame.Rect] = []
        self.hovered_index: Optional[int] = None

    def is_ready_to_check(self) -> bool:
        return self.selected_index is not None

    def check(self) -> bool:
        self.is_solved = (self.selected_index == self.correct_choice_index)
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Good job!", "")
        return ("Not quite.", self.choices[self.correct_choice_index])

    def reset(self) -> None:
        super().reset()
        self.selected_index = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.hovered_index = None
            for idx, r in enumerate(self.choice_rects):
                if r.collidepoint(event.pos):
                    self.hovered_index = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, r in enumerate(self.choice_rects):
                if r.collidepoint(event.pos):
                    sound_manager.play_click()
                    self.selected_index = idx
                    return

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # Title
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 35)))

        cur_y = area_rect.y + 80

        # Optional: Character with speech bubble
        if self.character_speech:
            cur_y = self._draw_speech_prompt(screen, area_rect, cur_y)
        else:
            # Render equation / question prompt
            cur_y = self._draw_equation_prompt(screen, area_rect, cur_y)

        # Optional Diagrams
        if self.diagram_type == "grid_rectangle":
            cur_y = self._draw_grid_rectangle(screen, area_rect, cur_y)
        elif self.diagram_type == "cylinder_3d":
            cur_y = self._draw_cylinder_diagram(screen, area_rect, cur_y)
        elif self.diagram_type == "pattern_table":
            cur_y = self._draw_pattern_table(screen, area_rect, cur_y)

        # Choice Cards
        self._draw_choices(screen, area_rect, cur_y)

    def _draw_speech_prompt(self, screen: pygame.Surface, area_rect: pygame.Rect, start_y: int) -> int:
        char_x = area_rect.centerx - 280
        char_y = start_y
        
        # Draw character
        cx, cy = char_x + 30, char_y + 30
        pygame.draw.rect(screen, (235, 120, 150), pygame.Rect(cx - 20, cy + 12, 40, 26), border_radius=10)
        pygame.draw.circle(screen, (255, 205, 175), (cx, cy), 18)
        pygame.draw.arc(screen, (230, 80, 120), (cx - 20, cy - 20, 40, 36), 0, 3.1415, 6)
        pygame.draw.circle(screen, (40, 40, 50), (cx - 6, cy - 1), 3)
        pygame.draw.circle(screen, (40, 40, 50), (cx + 6, cy - 1), 3)

        # Speech bubble
        bubble_x = char_x + 75
        bubble_y = char_y + 8
        bubble_w = 480
        bubble_h = 56
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
        draw_rounded_rect(screen, bubble_rect, (32, 47, 54), radius=14, border_color=(43, 61, 71), border_width=2)
        
        # Pointer
        pts = [(bubble_x, bubble_y + 18), (bubble_x - 10, bubble_y + 26), (bubble_x, bubble_y + 34)]
        pygame.draw.polygon(screen, (32, 47, 54), pts)
        
        # Text
        font = get_font(18)
        txt = self.character_speech
        if self.selected_index is not None:
            txt = txt.replace("_____", f" {self.choices[self.selected_index]} ")
        txt_surf = font.render(txt, True, TEXT_WHITE)
        screen.blit(txt_surf, txt_surf.get_rect(center=bubble_rect.center))
        
        # Underline rule
        pygame.draw.line(screen, (32, 47, 54), (char_x, bubble_rect.bottom + 18), (char_x + 580, bubble_rect.bottom + 18), 2)
        return bubble_rect.bottom + 30

    def _draw_equation_prompt(self, screen: pygame.Surface, area_rect: pygame.Rect, start_y: int) -> int:
        eq_font = get_font(38, bold=True)
        if "[ ]" in self.question_text:
            parts = self.question_text.split("[ ]")
            left_text = parts[0].strip()
            right_text = parts[1].strip()
            
            chosen_val = self.choices[self.selected_index] if self.selected_index is not None else ""
            box_w = max(64, len(chosen_val) * 20 + 24)
            box_h = 52
            
            left_surf = eq_font.render(left_text, True, TEXT_WHITE) if left_text else None
            right_surf = eq_font.render(right_text, True, TEXT_WHITE) if right_text else None
            
            total_w = box_w + 24
            if left_surf:
                total_w += left_surf.get_width() + 16
            if right_surf:
                total_w += right_surf.get_width() + 16
                
            cur_x = area_rect.centerx - total_w // 2
            if left_surf:
                screen.blit(left_surf, (cur_x, start_y + 10))
                cur_x += left_surf.get_width() + 16
                
            box_rect = pygame.Rect(cur_x, start_y + 6, box_w, box_h)
            draw_rounded_rect(screen, box_rect, (24, 39, 46), radius=10, border_color=ACCENT_BLUE, border_width=2)
            if chosen_val:
                val_surf = eq_font.render(chosen_val, True, ACCENT_BLUE)
                screen.blit(val_surf, val_surf.get_rect(center=box_rect.center))
            cur_x += box_w + 16
            if right_surf:
                screen.blit(right_surf, (cur_x, start_y + 10))
            return start_y + 80
        else:
            q_surf = eq_font.render(self.question_text, True, TEXT_WHITE)
            screen.blit(q_surf, q_surf.get_rect(center=(area_rect.centerx, start_y + 20)))
            return start_y + 60

    def _draw_grid_rectangle(self, screen: pygame.Surface, area_rect: pygame.Rect, start_y: int) -> int:
        cols = 10
        rows = 6
        cell = 26
        gw = cols * cell
        gh = rows * cell
        gx = area_rect.centerx - gw // 2
        gy = start_y + 10
        
        # Grid lines
        for c in range(cols + 1):
            pygame.draw.line(screen, (28, 42, 50), (gx + c * cell, gy), (gx + c * cell, gy + gh), 1)
        for r in range(rows + 1):
            pygame.draw.line(screen, (28, 42, 50), (gx, gy + r * cell), (gx + gw, gy + r * cell), 1)

        # Highlighted rectangle
        rw_cells = self.diagram_data.get("w", 6)
        rh_cells = self.diagram_data.get("h", 4)
        rx = gx + (cols - rw_cells) // 2 * cell
        ry = gy + (rows - rh_cells) // 2 * cell
        rw = rw_cells * cell
        rh = rh_cells * cell
        rect_geom = pygame.Rect(rx, ry, rw, rh)
        
        # Translucent fill
        f_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
        f_surf.fill((28, 176, 246, 20))
        screen.blit(f_surf, (rx, ry))
        pygame.draw.rect(screen, (73, 192, 248), rect_geom, width=3)
        
        # Diagonal line
        pygame.draw.line(screen, (73, 192, 248), (rx, ry + rh), (rx + rw, ry), 3)

        # Dimension labels
        dim_font = get_font(18, bold=True)
        w_surf = dim_font.render(str(rw_cells), True, (73, 192, 248))
        screen.blit(w_surf, w_surf.get_rect(center=(rx + rw // 2, ry + rh + 14)))
        h_surf = dim_font.render(str(rh_cells), True, (73, 192, 248))
        screen.blit(h_surf, h_surf.get_rect(center=(rx + rw + 14, ry + rh // 2)))

        return gy + gh + 35

    def _draw_cylinder_diagram(self, screen: pygame.Surface, area_rect: pygame.Rect, start_y: int) -> int:
        r = self.diagram_data.get("r", 3)
        h = self.diagram_data.get("h", 5)
        show_r = self.diagram_data.get("show_r", True)
        show_h = self.diagram_data.get("show_h", True)
        r_lbl = f"r = {r}" if show_r else None
        h_lbl = f"h = {h}" if show_h else None
        ba_lbl = self.diagram_data.get("base_area_label")

        # Proportional cylinder scaling so it stays well-proportioned and avoids vertical clipping
        rad_px = min(75, max(46, 42 + int(r * 4.2)))
        h_px = min(80, max(46, 38 + int(h * 5.0)))
        y_squash = 0.32
        ry = max(10, int(rad_px * y_squash))

        # Position cylinder: comfortable gap below question text
        top_cy = start_y + ry + 15
        cyl_center_y = top_cy + h_px // 2
        cyl_bot_y = top_cy + h_px + ry

        draw_cylinder_3d(
            screen,
            (area_rect.centerx, cyl_center_y),
            radius_px=rad_px,
            height_px=h_px,
            y_squash=y_squash,
            radius_label=r_lbl,
            height_label=h_lbl,
            base_area_label=ba_lbl,
            highlight_base=self.diagram_data.get("highlight_base", True)
        )
        return cyl_bot_y + 20

    def _draw_pattern_table(self, screen: pygame.Surface, area_rect: pygame.Rect, start_y: int) -> int:
        cols = self.diagram_data.get("headers", ["Expression", "Value"])
        rows = self.diagram_data.get("rows", [])
        tw = 420
        hdr_h = 36
        row_h = 34
        th = hdr_h + len(rows) * row_h
        trect = pygame.Rect(area_rect.centerx - tw // 2, start_y + 5, tw, th)
        draw_rounded_rect(screen, trect, CARD_BG, radius=10, border_color=CARD_BORDER, border_width=1)

        # Center divider
        pygame.draw.line(screen, CARD_BORDER, (trect.centerx, trect.top), (trect.centerx, trect.bottom), 1)
        pygame.draw.line(screen, CARD_BORDER, (trect.left, trect.top + hdr_h), (trect.right, trect.top + hdr_h), 1)

        hfont = get_font(16, bold=True)
        rfont = get_font(16, bold=False)

        # Headers
        c1 = hfont.render(cols[0], True, ACCENT_BLUE)
        screen.blit(c1, (trect.left + tw // 4 - c1.get_width() // 2, trect.top + 8))
        c2 = hfont.render(cols[1], True, ACCENT_BLUE)
        screen.blit(c2, (trect.left + 3 * tw // 4 - c2.get_width() // 2, trect.top + 8))

        for i, (v1, v2) in enumerate(rows):
            ry = trect.top + hdr_h + i * row_h
            pygame.draw.line(screen, CARD_BORDER, (trect.left, ry + row_h), (trect.right, ry + row_h), 1)
            s1 = rfont.render(str(v1), True, TEXT_WHITE)
            screen.blit(s1, (trect.left + tw // 4 - s1.get_width() // 2, ry + 7))

            # If v2 is '?', render it inside a highlighted blue box
            if str(v2) == "?":
                qbox = pygame.Rect(trect.left + 3 * tw // 4 - 20, ry + 4, 40, 26)
                draw_rounded_rect(screen, qbox, CARD_SELECTED_BG, radius=6, border_color=CARD_SELECTED_BORDER, border_width=1)
                qs = hfont.render("?", True, ACCENT_BLUE_LIGHT)
                screen.blit(qs, qs.get_rect(center=qbox.center))
            else:
                s2 = rfont.render(str(v2), True, TEXT_WHITE)
                screen.blit(s2, (trect.left + 3 * tw // 4 - s2.get_width() // 2, ry + 7))

        return trect.bottom + 20

    def _draw_choices(self, screen: pygame.Surface, area_rect: pygame.Rect, start_y: int) -> None:
        self.choice_rects = []
        n = len(self.choices)

        # If visual fractions diagram
        if self.diagram_type == "visual_fractions":
            cw = min(220, (area_rect.width - 80) // 2)
            ch = 140
            total_w = n * cw + (n - 1) * 24
            sx = area_rect.centerx - total_w // 2

            for i, opt in enumerate(self.choices):
                crect = pygame.Rect(sx + i * (cw + 24), start_y + 40, cw, ch)
                self.choice_rects.append(crect)
                is_sel = (self.selected_index == i)
                is_hov = (self.hovered_index == i)
                bg = CARD_SELECTED_BG if is_sel else (CARD_HOVER if is_hov else CARD_BG)
                border = CARD_SELECTED_BORDER if is_sel else ((53, 75, 87) if is_hov else CARD_BORDER)
                draw_rounded_rect(screen, crect, bg, radius=16, border_color=border, border_width=2)

                # Render pie option
                num, den = map(int, opt.split("/"))
                slices = [True] * num + [False] * (den - num)
                draw_pie_chart(screen, crect.center, 46, den, slices, base_color=(24, 39, 46), fill_color=ACCENT_BLUE)
            return

        # If visual coordinate grids diagram
        if self.diagram_type == "visual_grids":
            cw = 140
            ch = 140
            total_w = n * cw + (n - 1) * 16
            sx = area_rect.centerx - total_w // 2

            for i, opt in enumerate(self.choices):
                crect = pygame.Rect(sx + i * (cw + 16), start_y + 20, cw, ch)
                self.choice_rects.append(crect)
                is_sel = (self.selected_index == i)
                is_hov = (self.hovered_index == i)
                bg = CARD_SELECTED_BG if is_sel else (CARD_HOVER if is_hov else CARD_BG)
                border = CARD_SELECTED_BORDER if is_sel else ((53, 75, 87) if is_hov else CARD_BORDER)
                draw_rounded_rect(screen, crect, bg, radius=14, border_color=border, border_width=2)

                # Parse "(x, y)" or use diagram_data choice points
                pts_data = self.diagram_data.get("choice_points", {}).get(i)
                if pts_data is None:
                    try:
                        clean = opt.strip("() ").split(",")
                        pts_data = (int(clean[0]), int(clean[1]))
                    except Exception:
                        pts_data = (0, 0)

                inner_grid = crect.inflate(-16, -16)
                draw_coordinate_grid(
                    screen,
                    inner_grid,
                    x_range=self.diagram_data.get("x_range", (-4, 4)),
                    y_range=self.diagram_data.get("y_range", (-4, 4)),
                    highlight_point=pts_data,
                    show_projections=True,
                    show_labels=False
                )
            return

        # Standard vertical stacked buttons
        btn_w = min(480, area_rect.width - 80)
        btn_h = 48 if self.diagram_type else 52
        btn_gap = 10 if self.diagram_type else 12
        sx = area_rect.centerx - btn_w // 2
        opt_font = get_font(22, bold=True)

        for i, opt in enumerate(self.choices):
            crect = pygame.Rect(sx, start_y + i * (btn_h + btn_gap), btn_w, btn_h)
            self.choice_rects.append(crect)
            is_sel = (self.selected_index == i)
            is_hov = (self.hovered_index == i)

            bg = CARD_SELECTED_BG if is_sel else (CARD_HOVER if is_hov else CARD_BG)
            border = CARD_SELECTED_BORDER if is_sel else ((53, 75, 87) if is_hov else CARD_BORDER)
            draw_rounded_rect(screen, crect, bg, radius=14, border_color=border, border_width=2)

            txt_surf = opt_font.render(opt, True, TEXT_WHITE)
            screen.blit(txt_surf, txt_surf.get_rect(center=crect.center))
