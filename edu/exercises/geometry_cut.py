"""Exercise type: Create the shapes (interactive grid with draggable cutting line)."""
from typing import List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class GeometryCutExercise(BaseExercise):
    """Cut a rectangle on a grid into two right triangles using a draggable cutting line."""
    
    def __init__(
        self,
        grid_size: Tuple[int, int] = (8, 8),      # (cols, rows)
        rect_bounds: Tuple[int, int, int, int] = (2, 2, 4, 4), # (col, row, width, height)
        target_shape_name: str = "two right triangles",
        title: str = "Create the shapes",
        help_tip: str = "Place that line to split the rectangle into two triangles, so each keeps a square corner."
    ):
        super().__init__(
            title=title,
            help_title="Cutting Shapes",
            help_tip=help_tip,
            help_faqs=[
                ("What is a right triangle?", "A triangle that has one 90-degree square corner."),
                ("What if I cut straight down?", "A vertical or horizontal cut creates smaller rectangles, not triangles! Try cutting corner-to-corner diagonally.")
            ]
        )
        self.grid_cols, self.grid_rows = grid_size
        self.rect_col, self.rect_row, self.rect_w, self.rect_h = rect_bounds
        self.target_shape_name = target_shape_name
        
        # Initial cut line handles (e.g. vertical cut through the middle)
        mid_col = self.rect_col + self.rect_w // 2
        self.handle1_grid = [mid_col, self.rect_row]
        self.handle2_grid = [mid_col, self.rect_row + self.rect_h]
        
        self.active_handle: Optional[int] = None
        self.grid_origin: Tuple[int, int] = (0, 0)
        self.cell_size: int = 40
        self.handle_radius: int = 14

    def is_ready_to_check(self) -> bool:
        # Ready if the two handles are distinct
        return self.handle1_grid != self.handle2_grid

    def check(self) -> bool:
        # Target: diagonal split of the rectangle!
        # Diagonal 1: (top-left, bottom-right)
        diag1_a = (self.rect_col, self.rect_row)
        diag1_b = (self.rect_col + self.rect_w, self.rect_row + self.rect_h)
        # Diagonal 2: (bottom-left, top-right)
        diag2_a = (self.rect_col, self.rect_row + self.rect_h)
        diag2_b = (self.rect_col + self.rect_w, self.rect_row)
        
        h1 = (self.handle1_grid[0], self.handle1_grid[1])
        h2 = (self.handle2_grid[0], self.handle2_grid[1])
        
        match_diag1 = (h1 == diag1_a and h2 == diag1_b) or (h1 == diag1_b and h2 == diag1_a)
        match_diag2 = (h1 == diag2_a and h2 == diag2_b) or (h1 == diag2_b and h2 == diag2_a)
        
        self.is_solved = (match_diag1 or match_diag2)
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Nicely done!", "")
        return ("Not quite.", "Cut diagonally from corner to corner.")

    def reset(self) -> None:
        super().reset()
        mid_col = self.rect_col + self.rect_w // 2
        self.handle1_grid = [mid_col, self.rect_row]
        self.handle2_grid = [mid_col, self.rect_row + self.rect_h]
        self.active_handle = None

    def _grid_to_pixel(self, col: int, row: int) -> Tuple[int, int]:
        gx, gy = self.grid_origin
        return (gx + col * self.cell_size, gy + row * self.cell_size)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            p1 = self._grid_to_pixel(self.handle1_grid[0], self.handle1_grid[1])
            p2 = self._grid_to_pixel(self.handle2_grid[0], self.handle2_grid[1])
            
            d1 = (pos[0] - p1[0]) ** 2 + (pos[1] - p1[1]) ** 2
            d2 = (pos[0] - p2[0]) ** 2 + (pos[1] - p2[1]) ** 2
            hit_r2 = (self.handle_radius + 12) ** 2
            
            if d1 <= hit_r2:
                self.active_handle = 1
                sound_manager.play_click()
            elif d2 <= hit_r2:
                self.active_handle = 2
                sound_manager.play_click()

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_handle is not None:
                self.active_handle = None
                sound_manager.play_snap()

        elif event.type == pygame.MOUSEMOTION:
            if self.active_handle is not None:
                pos = event.pos
                gx, gy = self.grid_origin
                col = round((pos[0] - gx) / self.cell_size)
                row = round((pos[1] - gy) / self.cell_size)
                # Clamp within grid
                col = max(0, min(self.grid_cols, col))
                row = max(0, min(self.grid_rows, row))
                
                if self.active_handle == 1:
                    if [col, row] != self.handle1_grid:
                        self.handle1_grid = [col, row]
                        sound_manager.play_click()
                elif self.active_handle == 2:
                    if [col, row] != self.handle2_grid:
                        self.handle2_grid = [col, row]
                        sound_manager.play_click()

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # Title
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 35)))

        # Subtitle
        sub_font = get_font(26, bold=True)
        sub_surf = sub_font.render(self.target_shape_name, True, TEXT_WHITE)
        screen.blit(sub_surf, sub_surf.get_rect(center=(area_rect.centerx, area_rect.y + 75)))

        # Compute grid geometry
        self.cell_size = min(44, (area_rect.height - 180) // self.grid_rows)
        grid_total_w = self.grid_cols * self.cell_size
        grid_total_h = self.grid_rows * self.cell_size
        self.grid_origin = (
            area_rect.centerx - grid_total_w // 2,
            area_rect.y + 115 + (area_rect.height - 135 - grid_total_h) // 2
        )
        gx, gy = self.grid_origin

        # 1. Draw subtle grid lines
        grid_col = (28, 42, 50)
        for c in range(self.grid_cols + 1):
            x = gx + c * self.cell_size
            pygame.draw.line(screen, grid_col, (x, gy), (x, gy + grid_total_h), 1)
        for r in range(self.grid_rows + 1):
            y = gy + r * self.cell_size
            pygame.draw.line(screen, grid_col, (gx, y), (gx + grid_total_w, y), 1)

        # 2. Draw Target Rectangle
        rx, ry = self._grid_to_pixel(self.rect_col, self.rect_row)
        rw = self.rect_w * self.cell_size
        rh = self.rect_h * self.cell_size
        shape_rect = pygame.Rect(rx, ry, rw, rh)
        
        # Translucent shape fill
        fill_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
        fill_surf.fill((28, 176, 246, 25))
        screen.blit(fill_surf, (rx, ry))
        # Blue border
        pygame.draw.rect(screen, (73, 192, 248), shape_rect, width=3)

        # 3. Draw Interactive Cutting Line
        p1 = self._grid_to_pixel(self.handle1_grid[0], self.handle1_grid[1])
        p2 = self._grid_to_pixel(self.handle2_grid[0], self.handle2_grid[1])
        pygame.draw.line(screen, (73, 192, 248), p1, p2, 4)

        # 4. Draw Circular Handles
        for idx, (hx, hy) in enumerate([p1, p2]):
            is_active = (self.active_handle == (idx + 1))
            col = (120, 220, 255) if is_active else (73, 192, 248)
            pygame.draw.circle(screen, col, (hx, hy), self.handle_radius)
            pygame.draw.circle(screen, (24, 39, 46), (hx, hy), self.handle_radius - 4)
            pygame.draw.circle(screen, col, (hx, hy), self.handle_radius - 7)
