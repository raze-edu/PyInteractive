"""Exercise type: Answer on the line (interactive number line with slider peg)."""
from typing import List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_coordinate_grid,
    ACCENT_BLUE,
    ACCENT_BLUE_LIGHT,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class NumberLineExercise(BaseExercise):
    """Answer on the line exercise with interactive draggable house-shaped peg."""
    
    def __init__(
        self,
        equation_format: str,  # e.g. "210 - 60 - 15 = [ ]" or "[ ] = 400 - 10 - 5" or "Show x on the line"
        correct_value: int,
        ticks: List[int],
        initial_tick_index: int = 0,
        title: str = "Answer on the line",
        help_tip: str = "Calculate the result of the equation and drag the slider to mark the correct value on the number line.",
        help_faqs: Optional[List[Tuple[str, str]]] = None,
        prompt_coord: Optional[Tuple[int, int]] = None,
        highlight_coord: str = "x",
        prompt_grid_point: Optional[Tuple[int, int]] = None,
        x_range: Tuple[int, int] = (-5, 5),
        y_range: Tuple[int, int] = (-5, 5)
    ):
        super().__init__(
            title=title,
            help_title="Number Line Tip",
            help_tip=help_tip,
            help_faqs=help_faqs or [
                ("How to calculate?", "Subtract step-by-step: first subtract the tens, then subtract the remaining ones."),
                ("How to use the slider?", "Click any tick on the line or drag the blue marker.")
            ]
        )
        self.equation_format = equation_format
        self.correct_value = correct_value
        self.ticks = ticks
        self.selected_index = initial_tick_index
        self.prompt_coord = prompt_coord
        self.highlight_coord = highlight_coord
        self.prompt_grid_point = prompt_grid_point
        self.x_range = x_range
        self.y_range = y_range
        
        # Interactive / visual peg state
        self.current_peg_x: float = 0.0
        self.target_peg_x: float = 0.0
        self.is_dragging: bool = False
        self.peg_rect = pygame.Rect(0, 0, 36, 44)
        self.line_start_x = 0
        self.line_end_x = 0
        self.line_y = 0

    @property
    def current_value(self) -> int:
        if 0 <= self.selected_index < len(self.ticks):
            return self.ticks[self.selected_index]
        return 0

    def is_ready_to_check(self) -> bool:
        return True

    def check(self) -> bool:
        self.is_solved = (self.current_value == self.correct_value)
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Good job!", "")
        return ("Not quite.", str(self.correct_value))

    def _get_tick_x(self, index: int) -> float:
        if len(self.ticks) <= 1:
            return float(self.line_start_x)
        fraction = index / (len(self.ticks) - 1)
        return self.line_start_x + fraction * (self.line_end_x - self.line_start_x)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Check if clicked peg or along the number line
            hit_line = (self.line_start_x - 30 <= pos[0] <= self.line_end_x + 30 and
                        self.line_y - 45 <= pos[1] <= self.line_y + 55)
            if self.peg_rect.collidepoint(pos) or hit_line:
                self.is_dragging = True
                self._update_selection_from_mouse(pos[0])

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                sound_manager.play_snap()

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self._update_selection_from_mouse(event.pos[0])

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and self.selected_index > 0:
                self.selected_index -= 1
                sound_manager.play_snap()
            elif event.key == pygame.K_RIGHT and self.selected_index < len(self.ticks) - 1:
                self.selected_index += 1
                sound_manager.play_snap()

    def _update_selection_from_mouse(self, mouse_x: int) -> None:
        if len(self.ticks) <= 1:
            return
        line_w = max(1, self.line_end_x - self.line_start_x)
        ratio = max(0.0, min(1.0, (mouse_x - self.line_start_x) / line_w))
        closest_idx = int(round(ratio * (len(self.ticks) - 1)))
        if closest_idx != self.selected_index:
            self.selected_index = closest_idx
            sound_manager.play_click()

    def update(self, dt: float) -> None:
        # Smooth peg sliding
        self.target_peg_x = self._get_tick_x(self.selected_index)
        if self.current_peg_x == 0.0:
            self.current_peg_x = self.target_peg_x
        else:
            self.current_peg_x += (self.target_peg_x - self.current_peg_x) * min(1.0, dt * 20.0)

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # 1. Title at top
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 40)))

        # 2. Coordinate Grid / Coordinate Prompt / Equation Box
        if self.prompt_grid_point is not None:
            # Mini 2D coordinate grid prompt
            grid_w, grid_h = 240, 200
            grid_rect = pygame.Rect(area_rect.centerx - grid_w // 2, area_rect.y + 85, grid_w, grid_h)
            draw_coordinate_grid(
                screen,
                grid_rect,
                x_range=self.x_range,
                y_range=self.y_range,
                highlight_point=self.prompt_grid_point,
                show_projections=True,
                show_labels=True
            )
            self.line_y = area_rect.y + 365
        elif self.prompt_coord is not None:
            # Display (x, y) with highlighted target coordinate
            eq_font = get_font(44, bold=True)
            lbl_font = get_font(20, bold=False)
            eq_y = area_rect.y + 140
            px, py = self.prompt_coord
            
            coord_str = f"({px}, {py})"
            # Render instruction note above
            note = f"Find the {'x-coordinate' if self.highlight_coord == 'x' else 'y-coordinate'}:"
            note_surf = lbl_font.render(note, True, TEXT_MUTED)
            screen.blit(note_surf, note_surf.get_rect(center=(area_rect.centerx, eq_y - 40)))

            pill_rect = pygame.Rect(area_rect.centerx - 90, eq_y - 28, 180, 56)
            draw_rounded_rect(screen, pill_rect, (24, 39, 46), radius=12, border_color=ACCENT_BLUE, border_width=2)
            c_surf = eq_font.render(coord_str, True, TEXT_WHITE)
            screen.blit(c_surf, c_surf.get_rect(center=pill_rect.center))
            self.line_y = area_rect.y + 330
        else:
            eq_font = get_font(40, bold=True)
            eq_y = area_rect.y + 130
            
            # Format equation replacing [ ] with the selected value or input box
            val_str = str(self.current_value) if self.selected_index >= 0 else ""
            
            # Render left and right parts around [ ]
            parts = self.equation_format.split("[ ]")
            box_w = max(60, len(val_str) * 24 + 24)
            box_h = 56
            
            if len(parts) == 2:
                left_text = parts[0].strip()
                right_text = parts[1].strip()
                
                left_surf = eq_font.render(left_text, True, TEXT_WHITE) if left_text else None
                right_surf = eq_font.render(right_text, True, TEXT_WHITE) if right_text else None
                
                total_w = box_w + 24
                if left_surf:
                    total_w += left_surf.get_width() + 16
                if right_surf:
                    total_w += right_surf.get_width() + 16
                    
                cur_x = area_rect.centerx - total_w // 2
                
                if left_surf:
                    screen.blit(left_surf, (cur_x, eq_y - left_surf.get_height() // 2))
                    cur_x += left_surf.get_width() + 16
                    
                box_rect = pygame.Rect(cur_x, eq_y - box_h // 2, box_w, box_h)
                draw_rounded_rect(screen, box_rect, (24, 39, 46), radius=10, border_color=ACCENT_BLUE, border_width=3)
                
                if val_str:
                    val_surf = eq_font.render(val_str, True, ACCENT_BLUE)
                    screen.blit(val_surf, val_surf.get_rect(center=box_rect.center))
                    
                cur_x += box_w + 16
                if right_surf:
                    screen.blit(right_surf, (cur_x, eq_y - right_surf.get_height() // 2))
            self.line_y = area_rect.y + 360

        # 3. Number Line Axis
        self.line_start_x = area_rect.centerx - 340
        self.line_end_x = area_rect.centerx + 340
        axis_color = (60, 80, 92)
        
        # Horizontal line
        pygame.draw.line(screen, axis_color, (self.line_start_x, self.line_y), (self.line_end_x, self.line_y), 4)

        # Draw ticks and labels
        label_font = get_font(20, bold=True)
        tick_h = 16
        
        for i, val in enumerate(self.ticks):
            tx = self._get_tick_x(i)
            is_active = (i == self.selected_index)
            t_col = ACCENT_BLUE if is_active else axis_color
            
            # Tick mark
            pygame.draw.line(screen, t_col, (tx, self.line_y - tick_h // 2), (tx, self.line_y + tick_h // 2), 3)

            # Value label above tick
            lbl_col = ACCENT_BLUE if is_active else TEXT_MUTED
            lbl_surf = label_font.render(str(val), True, lbl_col)
            screen.blit(lbl_surf, lbl_surf.get_rect(center=(tx, self.line_y - 24)))

        # 4. Draggable house-shaped peg marker below the number line
        peg_cx = int(self.current_peg_x)
        peg_top_y = self.line_y + 12
        peg_w = 34
        peg_h = 42
        
        self.peg_rect = pygame.Rect(peg_cx - peg_w // 2, peg_top_y, peg_w, peg_h)
        
        # Pentagonal house polygon pointing upward
        # Points: tip, top-right, bottom-right, bottom-left, top-left
        roof_h = 12
        pts = [
            (peg_cx, peg_top_y),
            (peg_cx + peg_w // 2, peg_top_y + roof_h),
            (peg_cx + peg_w // 2, peg_top_y + peg_h),
            (peg_cx - peg_w // 2, peg_top_y + peg_h),
            (peg_cx - peg_w // 2, peg_top_y + roof_h)
        ]
        
        peg_color = (73, 192, 248) if self.is_dragging else ACCENT_BLUE
        pygame.draw.polygon(screen, peg_color, pts)
        
        # Inner subtle shading
        inner_pts = [
            (peg_cx, peg_top_y + 4),
            (peg_cx + peg_w // 2 - 3, peg_top_y + roof_h + 1),
            (peg_cx + peg_w // 2 - 3, peg_top_y + peg_h - 3),
            (peg_cx - peg_w // 2 + 3, peg_top_y + peg_h - 3),
            (peg_cx - peg_w // 2 + 3, peg_top_y + roof_h + 1)
        ]
        pygame.draw.polygon(screen, tuple(min(255, c + 25) for c in peg_color), inner_pts, width=1)
