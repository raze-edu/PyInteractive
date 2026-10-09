"""Exercise type: Match the pairs (matching fraction expressions with visual circle models)."""
from typing import List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_pie_chart,
    draw_coordinate_grid,
    CARD_BG,
    CARD_BORDER,
    CARD_HOVER,
    CARD_SELECTED_BG,
    CARD_SELECTED_BORDER,
    GREEN_CORRECT,
    RED_INCORRECT,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class MatchPairItem:
    def __init__(self, item_id: int, expr_str: str, total_slices: int = 0, shaded_slices: int = 0, right_text: str = "", coord_point: Optional[Tuple[int, int]] = None):
        self.item_id = item_id
        self.expr_str = expr_str
        self.total_slices = total_slices
        self.shaded_slices = shaded_slices
        self.right_text = right_text
        self.coord_point = coord_point

class MatchPairsExercise(BaseExercise):
    """Match pairs of mathematical expressions with visual representations or text answers."""
    
    def __init__(
        self,
        pairs: Optional[List[Tuple[str, int, int]]] = None,  # [(expr_str, total_slices, shaded_count), ...]
        text_pairs: Optional[List[Tuple[str, str]]] = None,  # [(left_expr, right_val), ...]
        grid_pairs: Optional[List[Tuple[str, Tuple[int, int]]]] = None,  # [(coord_str, (x, y)), ...]
        title: str = "Match the pairs",
        help_tip: str = "Match each expression on the left with its corresponding value on the right."
    ):
        super().__init__(
            title=title,
            help_title="Matching Pairs",
            help_tip=help_tip,
            help_faqs=[
                ("How does matching work?", "Select an item on the left and then tap its matching counterpart on the right."),
                ("How to solve?", "Evaluate each problem mentally or with scratch work to find the matching result.")
            ]
        )
        self.items: List[MatchPairItem] = []
        if pairs:
            for i, (expr, tot, shd) in enumerate(pairs):
                self.items.append(MatchPairItem(i, expr, tot, shd))
        elif text_pairs:
            for i, (l_expr, r_val) in enumerate(text_pairs):
                self.items.append(MatchPairItem(i, l_expr, right_text=r_val))
        elif grid_pairs:
            for i, (l_expr, r_pt) in enumerate(grid_pairs):
                self.items.append(MatchPairItem(i, l_expr, coord_point=r_pt))

        import random
        # Left cards (expression items) and Right cards
        self.left_ids = [item.item_id for item in self.items]
        # Shuffle right cards so they aren't directly in the same row
        self.right_ids = list(self.left_ids)
        if len(self.right_ids) > 1:
            # Shift by 1 or shuffle so index doesn't match row index
            self.right_ids = self.right_ids[1:] + self.right_ids[:1]
        
        self.selected_left: Optional[int] = None
        self.selected_right: Optional[int] = None
        self.matched_ids: set[int] = set()
        
        # Interaction rects
        self.left_rects: List[pygame.Rect] = []
        self.right_rects: List[pygame.Rect] = []
        self.hovered_left: Optional[int] = None
        self.hovered_right: Optional[int] = None
        self.error_timer: float = 0.0

    def is_ready_to_check(self) -> bool:
        return len(self.matched_ids) == len(self.items)

    def check(self) -> bool:
        self.is_solved = (len(self.matched_ids) == len(self.items))
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Good job!", "")
        return ("Not quite.", "Match each expression to its visual fraction.")

    def reset(self) -> None:
        super().reset()
        self.selected_left = None
        self.selected_right = None
        self.matched_ids.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self.hovered_left = None
            for idx, r in enumerate(self.left_rects):
                if r.collidepoint(pos) and self.left_ids[idx] not in self.matched_ids:
                    self.hovered_left = idx
                    break
            self.hovered_right = None
            for idx, r in enumerate(self.right_rects):
                if r.collidepoint(pos) and self.right_ids[idx] not in self.matched_ids:
                    self.hovered_right = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Left card click
            for idx, r in enumerate(self.left_rects):
                item_id = self.left_ids[idx]
                if r.collidepoint(pos) and item_id not in self.matched_ids:
                    sound_manager.play_click()
                    self.selected_left = item_id
                    self._check_match()
                    return

            # Right card click
            for idx, r in enumerate(self.right_rects):
                item_id = self.right_ids[idx]
                if r.collidepoint(pos) and item_id not in self.matched_ids:
                    sound_manager.play_click()
                    self.selected_right = item_id
                    self._check_match()
                    return

    def _check_match(self) -> None:
        if self.selected_left is not None and self.selected_right is not None:
            if self.selected_left == self.selected_right:
                # Correct match!
                self.matched_ids.add(self.selected_left)
                sound_manager.play_correct()
                self.selected_left = None
                self.selected_right = None
            else:
                # Wrong match
                sound_manager.play_error()
                self.error_timer = 0.4
                self.selected_left = None
                self.selected_right = None

    def update(self, dt: float) -> None:
        if self.error_timer > 0:
            self.error_timer -= dt

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # Title
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 40)))

        # Card columns setup
        n = len(self.items)
        card_w = min(220, (area_rect.width - 120) // 2)
        card_h = min(115, (area_rect.height - 180) // n)
        card_gap = 16
        
        total_grid_h = n * card_h + (n - 1) * card_gap
        start_y = area_rect.y + 110 + (area_rect.height - 130 - total_grid_h) // 2
        
        col_gap = 40
        left_x = area_rect.centerx - card_w - col_gap // 2
        right_x = area_rect.centerx + col_gap // 2

        self.left_rects = []
        self.right_rects = []

        # 1. Draw Left Cards (Expressions)
        expr_font = get_font(28, bold=True)
        for i, item_id in enumerate(self.left_ids):
            card_rect = pygame.Rect(left_x, start_y + i * (card_h + card_gap), card_w, card_h)
            self.left_rects.append(card_rect)
            
            is_matched = item_id in self.matched_ids
            is_selected = (self.selected_left == item_id)
            is_hovered = (self.hovered_left == i)
            
            if is_matched:
                bg = (20, 48, 32)
                border = GREEN_CORRECT
                text_col = GREEN_CORRECT
            elif is_selected:
                bg = CARD_SELECTED_BG
                border = CARD_SELECTED_BORDER
                text_col = ACCENT_BLUE
            elif is_hovered:
                bg = CARD_HOVER
                border = (53, 75, 87)
                text_col = TEXT_WHITE
            else:
                bg = CARD_BG
                border = CARD_BORDER
                text_col = TEXT_WHITE

            draw_rounded_rect(screen, card_rect, bg, radius=16, border_color=border, border_width=2)
            
            # Format fraction nicely e.g. 2/3 · 2/2
            item = next(it for it in self.items if it.item_id == item_id)
            self._draw_fraction_mult(screen, card_rect.center, item.expr_str, text_col)

        # 2. Draw Right Cards (Visual Fraction Slices)
        for i, item_id in enumerate(self.right_ids):
            card_rect = pygame.Rect(right_x, start_y + i * (card_h + card_gap), card_w, card_h)
            self.right_rects.append(card_rect)
            
            is_matched = item_id in self.matched_ids
            is_selected = (self.selected_right == item_id)
            is_hovered = (self.hovered_right == i)
            
            if is_matched:
                bg = (20, 48, 32)
                border = GREEN_CORRECT
                slice_col = GREEN_CORRECT
            elif is_selected:
                bg = CARD_SELECTED_BG
                border = CARD_SELECTED_BORDER
                slice_col = ACCENT_BLUE
            elif is_hovered:
                bg = CARD_HOVER
                border = (53, 75, 87)
                slice_col = ACCENT_BLUE
            else:
                bg = CARD_BG
                border = CARD_BORDER
                slice_col = ACCENT_BLUE

            draw_rounded_rect(screen, card_rect, bg, radius=16, border_color=border, border_width=2)
            
            item = next(it for it in self.items if it.item_id == item_id)
            if item.coord_point is not None:
                inner_grid = card_rect.inflate(-16, -16)
                draw_coordinate_grid(
                    screen,
                    inner_grid,
                    x_range=(-5, 5),
                    y_range=(-5, 5),
                    highlight_point=item.coord_point,
                    show_projections=True,
                    show_labels=False
                )
            elif item.right_text:
                r_font = get_font(24, bold=True)
                txt_col = GREEN_CORRECT if is_matched else (ACCENT_BLUE if is_selected else TEXT_WHITE)
                r_surf = r_font.render(item.right_text, True, txt_col)
                screen.blit(r_surf, r_surf.get_rect(center=card_rect.center))
            else:
                sel_slices = [True] * item.shaded_slices + [False] * (item.total_slices - item.shaded_slices)
                radius = min(card_h // 2 - 12, 42)
                draw_pie_chart(
                    screen, card_rect.center, radius,
                    item.total_slices, sel_slices,
                    base_color=(24, 39, 46),
                    fill_color=slice_col,
                    border_color=(43, 61, 71)
                )

    def _draw_fraction_mult(self, screen: pygame.Surface, center: Tuple[int, int], expr: str, text_color: Tuple[int, int, int]) -> None:
        """Renders stacked fractions with multiplication dot: e.g. 2/3 · 2/2."""
        parts = [p.strip() for p in expr.split("·") if p.strip()]
        if len(parts) == 1 and "*" in expr:
            parts = [p.strip() for p in expr.split("*") if p.strip()]

        f_font = get_font(20, bold=True)
        dot_font = get_font(28, bold=True)
        
        # Calculate width
        cx, cy = center
        if len(parts) == 2:
            frac1 = parts[0].split("/")
            frac2 = parts[1].split("/")
            if len(frac1) == 2 and len(frac2) == 2:
                # Draw frac 1
                f1_x = cx - 36
                self._draw_single_fraction(screen, f1_x, cy, frac1[0], frac1[1], text_color, f_font)
                
                # Dot
                dot_surf = dot_font.render("·", True, text_color)
                screen.blit(dot_surf, dot_surf.get_rect(center=(cx, cy - 2)))
                
                # Draw frac 2
                f2_x = cx + 36
                self._draw_single_fraction(screen, f2_x, cy, frac2[0], frac2[1], text_color, f_font)
                return

        # Fallback single line
        fallback_surf = f_font.render(expr, True, text_color)
        screen.blit(fallback_surf, fallback_surf.get_rect(center=center))

    def _draw_single_fraction(
        self, surface: pygame.Surface, x: int, y: int, num: str, den: str,
        color: Tuple[int, int, int], font: pygame.font.Font
    ) -> None:
        num_surf = font.render(num, True, color)
        den_surf = font.render(den, True, color)
        w = max(num_surf.get_width(), den_surf.get_width()) + 8
        
        surface.blit(num_surf, num_surf.get_rect(center=(x, y - 14)))
        pygame.draw.line(surface, color, (x - w // 2, y), (x + w // 2, y), 2)
        surface.blit(den_surf, den_surf.get_rect(center=(x, y + 14)))
