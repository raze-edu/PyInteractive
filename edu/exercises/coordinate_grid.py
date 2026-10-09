"""Coordinate grid interactive exercises:
1. Place a point at (x, y) with snap-to-grid and dashed projection lines.
2. Create a graph matching a table of points with line connection.
"""
from typing import Dict, List, Optional, Tuple, Set
import pygame
from edu.exercises.base import BaseExercise
from edu.theme import (
    CARD_BG, CARD_BORDER, CARD_HOVER, CARD_SELECTED_BG, CARD_SELECTED_BORDER,
    ACCENT_BLUE, ACCENT_BLUE_LIGHT, GREEN_CORRECT, RED_INCORRECT, GOLD_STREAK,
    TEXT_WHITE, TEXT_MUTED, get_font, draw_rounded_rect,
    draw_coordinate_grid, coord_to_pixel, pixel_to_coord
)


class CoordinateGridExercise(BaseExercise):
    """Exercise for Cartesian coordinate plotting and graph construction."""

    def __init__(
        self,
        prompt: str,
        target_points: List[Tuple[int, int]],
        mode: str = "place_point",  # "place_point" or "create_graph"
        x_range: Tuple[int, int] = (-6, 6),
        y_range: Tuple[int, int] = (-6, 6),
        instruction: Optional[str] = None,
        table_data: Optional[List[Tuple[int, int]]] = None
    ) -> None:
        self.instruction = instruction or (
            "Click on the grid to position the point."
            if mode == "place_point"
            else "Plot the points from the table and connect the line."
        )
        super().__init__(
            title=prompt,
            help_title="Coordinate Grid Help",
            help_tip=self.instruction,
            help_faqs=[
                ("Coordinates format", "In (x, y), x is horizontal and y is vertical."),
                ("Adjusting points", "Click and drag any point on the grid to adjust its position.")
            ]
        )
        self.prompt = prompt
        self.target_points = target_points
        self.mode = mode
        self.x_range = x_range
        self.y_range = y_range
        self.table_data = table_data or target_points
        self.feedback_message: str = ""

        # Current user placed points: list of (x, y) integers
        if self.mode == "place_point":
            self.user_points: List[Tuple[int, int]] = []
        else:
            # Start with 2 initial points on x-axis or origin for user to drag/adjust
            self.user_points = [(0, 0), (2, 2)]

        self.dragging_idx: Optional[int] = None
        self.grid_rect = pygame.Rect(180, 160, 440, 360)

        # UI Buttons for create_graph mode
        self.btn_add_point = pygame.Rect(0, 0, 110, 40)
        self.btn_del_point = pygame.Rect(0, 0, 110, 40)
        self.btn_reset = pygame.Rect(0, 0, 90, 40)

    def is_ready_to_check(self) -> bool:
        return len(self.user_points) > 0

    def check(self) -> bool:
        self.is_solved = self.check_answer()
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Good job!", self.feedback_message)
        return ("Not quite.", self.feedback_message)

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        self.render(screen, area_rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.is_solved:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Check buttons in create_graph mode
            if self.mode == "create_graph":
                if self.btn_add_point.collidepoint(mx, my):
                    # Add a new point near center that isn't already there
                    new_pt = (len(self.user_points) - 2, len(self.user_points) - 2)
                    self.user_points.append(new_pt)
                    return
                if self.btn_del_point.collidepoint(mx, my) and len(self.user_points) > 1:
                    self.user_points.pop()
                    return
                if self.btn_reset.collidepoint(mx, my):
                    self.user_points = [(0, 0), (2, 2)]
                    return

            # Check if clicked on grid
            if self.grid_rect.collidepoint(mx, my):
                gx, gy = pixel_to_coord(mx, my, self.grid_rect, self.x_range, self.y_range)
                rx, ry = int(round(gx)), int(round(gy))
                # Clamp within ranges
                rx = max(self.x_range[0], min(self.x_range[1], rx))
                ry = max(self.y_range[0], min(self.y_range[1], ry))

                if self.mode == "place_point":
                    self.user_points = [(rx, ry)]
                    self.dragging_idx = 0
                else:
                    # Check if clicked near an existing point to drag it
                    found = False
                    for idx, pt in enumerate(self.user_points):
                        px, py = coord_to_pixel(pt[0], pt[1], self.grid_rect, self.x_range, self.y_range)
                        if (mx - px) ** 2 + (my - py) ** 2 <= 256:  # 16px radius
                            self.dragging_idx = idx
                            found = True
                            break
                    if not found:
                        # Add or move point
                        self.user_points.append((rx, ry))
                        self.dragging_idx = len(self.user_points) - 1

        elif event.type == pygame.MOUSEMOTION and self.dragging_idx is not None:
            mx, my = event.pos
            gx, gy = pixel_to_coord(mx, my, self.grid_rect, self.x_range, self.y_range)
            rx = max(self.x_range[0], min(self.x_range[1], int(round(gx))))
            ry = max(self.y_range[0], min(self.y_range[1], int(round(gy))))
            if 0 <= self.dragging_idx < len(self.user_points):
                self.user_points[self.dragging_idx] = (rx, ry)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_idx = None

    def check_answer(self) -> bool:
        if self.mode == "place_point":
            if not self.user_points:
                self.feedback_message = "Click on the grid to place the point."
                return False
            pt = self.user_points[0]
            tgt = self.target_points[0]
            if pt == tgt:
                self.feedback_message = f"Spot on! Point located at ({tgt[0]}, {tgt[1]})."
                return True
            else:
                self.feedback_message = f"Placed at ({pt[0]}, {pt[1]}). Expected ({tgt[0]}, {tgt[1]})."
                return False
        else:
            # create_graph mode: check if target set of points matches user points
            user_set = set(self.user_points)
            target_set = set(self.target_points)
            if user_set == target_set:
                self.feedback_message = "Excellent! All points correctly plotted and connected."
                return True
            else:
                missing = target_set - user_set
                self.feedback_message = f"Not quite. {len(missing)} points still need adjustment."
                return False

    def render(self, surface: pygame.Surface, area_rect: Optional[pygame.Rect] = None) -> None:
        font_prompt = get_font(24, bold=True)
        font_sub = get_font(15, bold=False)
        font_btn = get_font(14, bold=True)

        # Dynamic layout based on mode
        w, h = surface.get_size()
        center_x = w // 2

        # Header Prompt
        prompt_surf = font_prompt.render(self.prompt, True, TEXT_WHITE)
        surface.blit(prompt_surf, (center_x - prompt_surf.get_width() // 2, 70))

        sub_surf = font_sub.render(self.instruction, True, TEXT_MUTED)
        surface.blit(sub_surf, (center_x - sub_surf.get_width() // 2, 105))

        if self.mode == "create_graph":
            # Grid on left/center-right, Table on left
            table_x = max(30, center_x - 360)
            table_w = 160
            self.grid_rect = pygame.Rect(table_x + table_w + 30, 140, 440, 370)

            # Draw Data Table
            self._render_table(surface, pygame.Rect(table_x, 140, table_w, 240))

            # Buttons under table
            btn_y = 395
            self.btn_add_point = pygame.Rect(table_x, btn_y, 75, 36)
            self.btn_del_point = pygame.Rect(table_x + 85, btn_y, 75, 36)
            self.btn_reset = pygame.Rect(table_x, btn_y + 45, 160, 34)

            draw_rounded_rect(surface, self.btn_add_point, CARD_BG, radius=6, border_color=ACCENT_BLUE, border_width=1)
            t_add = font_btn.render("+ POINT", True, ACCENT_BLUE)
            surface.blit(t_add, (self.btn_add_point.centerx - t_add.get_width() // 2, self.btn_add_point.centery - t_add.get_height() // 2))

            draw_rounded_rect(surface, self.btn_del_point, CARD_BG, radius=6, border_color=CARD_BORDER, border_width=1)
            t_del = font_btn.render("- POINT", True, TEXT_MUTED)
            surface.blit(t_del, (self.btn_del_point.centerx - t_del.get_width() // 2, self.btn_del_point.centery - t_del.get_height() // 2))

            draw_rounded_rect(surface, self.btn_reset, CARD_BG, radius=6, border_color=CARD_BORDER, border_width=1)
            t_res = font_btn.render("RESET GRAPH", True, TEXT_MUTED)
            surface.blit(t_res, (self.btn_reset.centerx - t_res.get_width() // 2, self.btn_reset.centery - t_res.get_height() // 2))

            # Sort points by x for connecting line
            sorted_pts = sorted(self.user_points, key=lambda p: p[0])
            lines = [sorted_pts] if len(sorted_pts) >= 2 else None

            draw_coordinate_grid(
                surface,
                self.grid_rect,
                x_range=self.x_range,
                y_range=self.y_range,
                points=self.user_points,
                lines=lines,
                show_projections=True,
                show_labels=True
            )
        else:
            # Place point mode: grid centered
            self.grid_rect = pygame.Rect(center_x - 210, 140, 420, 370)
            highlight = self.user_points[0] if self.user_points else None

            draw_coordinate_grid(
                surface,
                self.grid_rect,
                x_range=self.x_range,
                y_range=self.y_range,
                points=self.user_points,
                highlight_point=highlight,
                show_projections=True,
                show_labels=True
            )

            # Display currently selected coordinate pill below grid
            if self.user_points:
                cur_x, cur_y = self.user_points[0]
                pill_rect = pygame.Rect(center_x - 70, 520, 140, 36)
                draw_rounded_rect(surface, pill_rect, CARD_SELECTED_BG, radius=18, border_color=CARD_SELECTED_BORDER, border_width=2)
                cur_lbl = get_font(18, bold=True).render(f"({cur_x}, {cur_y})", True, ACCENT_BLUE_LIGHT)
                surface.blit(cur_lbl, (pill_rect.centerx - cur_lbl.get_width() // 2, pill_rect.centery - cur_lbl.get_height() // 2))

    def _render_table(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Renders the (x, y) target data table."""
        draw_rounded_rect(surface, rect, CARD_BG, radius=8, border_color=CARD_BORDER, border_width=1)
        font_header = get_font(16, bold=True)
        font_row = get_font(15, bold=False)

        # Header: x | y
        hdr_h = 36
        pygame.draw.line(surface, CARD_BORDER, (rect.centerx, rect.top), (rect.centerx, rect.bottom), 1)
        pygame.draw.line(surface, CARD_BORDER, (rect.left, rect.top + hdr_h), (rect.right, rect.top + hdr_h), 1)

        tx = font_header.render("x", True, ACCENT_BLUE)
        surface.blit(tx, (rect.left + rect.width // 4 - tx.get_width() // 2, rect.top + 8))
        ty = font_header.render("y", True, ACCENT_BLUE)
        surface.blit(ty, (rect.left + 3 * rect.width // 4 - ty.get_width() // 2, rect.top + 8))

        row_h = 32
        for idx, (px, py) in enumerate(self.table_data[:6]):
            ry = rect.top + hdr_h + idx * row_h
            if ry + row_h > rect.bottom:
                break
            pygame.draw.line(surface, CARD_BORDER, (rect.left, ry + row_h), (rect.right, ry + row_h), 1)

            # Check if this point is currently plotted by user
            matched = (px, py) in self.user_points
            color = GREEN_CORRECT if matched else TEXT_WHITE

            sx = font_row.render(str(px), True, color)
            sy = font_row.render(str(py), True, color)
            surface.blit(sx, (rect.left + rect.width // 4 - sx.get_width() // 2, ry + 6))
            surface.blit(sy, (rect.left + 3 * rect.width // 4 - sy.get_width() // 2, ry + 6))
