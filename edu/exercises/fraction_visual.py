"""Exercise type: Show this another way (interactive pie slicing or typing equivalent fraction)."""
import math
from typing import List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_pie_chart,
    ACCENT_BLUE,
    CARD_BG,
    CARD_BORDER,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class FractionVisualExercise(BaseExercise):
    """Show this another way: either click pie slices to represent a fraction, or type the fraction."""
    
    def __init__(
        self,
        mode: str,  # "interactive_slices" or "type_equivalent"
        prompt_fraction: str,  # e.g. "2/6" or "3/4"
        target_slices: int,    # e.g. 3 slices in pie
        target_shaded: int,    # e.g. 1 slice shaded (1/3 = 2/6)
        initial_shaded: int = 0,
        accepted_fractions: Optional[List[str]] = None,
        title: str = "Show this another way",
        help_tip: str = "Find an equivalent way to represent the fraction shown."
    ):
        super().__init__(
            title=title,
            help_title="Equivalent Fractions",
            help_tip=help_tip,
            help_faqs=[
                ("What is an equivalent fraction?", "Fractions that represent the same value even though they use different numbers, like 2/6 = 1/3 or 6/8 = 3/4."),
                ("How to interact?", "In slice mode, click any slice to shade or unshade it. In text mode, type using number keys and '/' symbol.")
            ]
        )
        self.mode = mode
        self.prompt_fraction = prompt_fraction
        self.target_slices = target_slices
        self.target_shaded = target_shaded
        self.accepted_fractions = accepted_fractions or [prompt_fraction]
        
        # Interactive slices state
        self.selected_slices = [i < initial_shaded for i in range(target_slices)]
        self.hovered_slice: int = -1
        self.circle_center: Tuple[int, int] = (0, 0)
        self.circle_radius: int = 90
        
        # Type mode state
        self.input_text: str = ""
        self.input_rect = pygame.Rect(0, 0, 240, 52)
        self.cursor_blink: float = 0.0

    def is_ready_to_check(self) -> bool:
        if self.mode == "interactive_slices":
            return any(self.selected_slices)
        else:
            return len(self.input_text.strip()) > 0

    def check(self) -> bool:
        if self.mode == "interactive_slices":
            self.is_solved = (sum(self.selected_slices) == self.target_shaded)
        else:
            txt = self.input_text.strip().replace(" ", "")
            # Check accepted string fractions or float equality
            if txt in self.accepted_fractions:
                self.is_solved = True
            else:
                try:
                    if "/" in txt:
                        num, den = txt.split("/")
                        user_val = float(num) / float(den)
                        target_val = float(self.target_shaded) / float(self.target_slices)
                        self.is_solved = abs(user_val - target_val) < 1e-6
                    else:
                        self.is_solved = False
                except Exception:
                    self.is_solved = False
                    
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Amazing!", "")
        if self.mode == "interactive_slices":
            return ("Not quite.", f"{self.target_shaded} out of {self.target_slices} slices")
        return ("Not quite.", self.accepted_fractions[0])

    def reset(self) -> None:
        super().reset()
        self.selected_slices = [False] * self.target_slices
        self.input_text = ""

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.mode == "interactive_slices":
            if event.type == pygame.MOUSEMOTION:
                self.hovered_slice = self._get_slice_at(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                idx = self._get_slice_at(event.pos)
                if idx != -1:
                    self.selected_slices[idx] = not self.selected_slices[idx]
                    sound_manager.play_snap()
        else:
            # Typing mode
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    sound_manager.play_click()
                elif event.unicode in "0123456789/":
                    if len(self.input_text) < 10:
                        self.input_text += event.unicode
                        sound_manager.play_click()

    def _get_slice_at(self, pos: Tuple[int, int]) -> int:
        cx, cy = self.circle_center
        dx = pos[0] - cx
        dy = pos[1] - cy
        dist = math.hypot(dx, dy)
        if dist > self.circle_radius or dist < 2:
            return -1
        theta = math.atan2(dy, dx)
        angle = (theta - (-math.pi / 2.0)) % (2.0 * math.pi)
        slice_angle = (2.0 * math.pi) / self.target_slices
        return int(angle // slice_angle)

    def update(self, dt: float) -> None:
        self.cursor_blink = (self.cursor_blink + dt * 2.5) % 1.0

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # Title
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 40)))

        if self.mode == "interactive_slices":
            # Display target fraction at top
            frac_font = get_font(26, bold=True)
            f_parts = self.prompt_fraction.split("/")
            fy = area_rect.y + 115
            if len(f_parts) == 2:
                num_surf = frac_font.render(f_parts[0], True, TEXT_WHITE)
                den_surf = frac_font.render(f_parts[1], True, TEXT_WHITE)
                fw = max(num_surf.get_width(), den_surf.get_width()) + 8
                screen.blit(num_surf, num_surf.get_rect(center=(area_rect.centerx, fy - 14)))
                pygame.draw.line(screen, TEXT_WHITE, (area_rect.centerx - fw // 2, fy), (area_rect.centerx + fw // 2, fy), 2)
                screen.blit(den_surf, den_surf.get_rect(center=(area_rect.centerx, fy + 14)))

            # Interactive Circle
            self.circle_center = (area_rect.centerx, area_rect.y + 260)
            self.circle_radius = min(110, (area_rect.height - 240) // 2)
            draw_pie_chart(
                screen, self.circle_center, self.circle_radius,
                self.target_slices, self.selected_slices,
                base_color=(24, 39, 46),
                fill_color=ACCENT_BLUE,
                border_color=(43, 61, 71),
                hovered_slice=self.hovered_slice
            )

        else:
            # Display static Circle Model
            self.circle_center = (area_rect.centerx, area_rect.y + 160)
            self.circle_radius = 85
            draw_pie_chart(
                screen, self.circle_center, self.circle_radius,
                self.target_slices, self.selected_slices,
                base_color=(24, 39, 46),
                fill_color=ACCENT_BLUE,
                border_color=(43, 61, 71)
            )

            # Input box below
            in_y = area_rect.y + 290
            in_w = 260
            in_h = 52
            self.input_rect = pygame.Rect(area_rect.centerx - in_w // 2, in_y, in_w, in_h)
            
            draw_rounded_rect(screen, self.input_rect, CARD_BG, radius=12, border_color=(43, 61, 71), border_width=2)
            
            # Text inside input
            txt_font = get_font(26, bold=True)
            txt_surf = txt_font.render(self.input_text, True, TEXT_WHITE)
            tx = self.input_rect.x + 20
            ty = self.input_rect.centery - txt_surf.get_height() // 2
            screen.blit(txt_surf, (tx, ty))

            # Flashing cursor
            if self.cursor_blink < 0.5:
                cx = tx + txt_surf.get_width() + 2
                pygame.draw.line(screen, ACCENT_BLUE, (cx, ty + 2), (cx, ty + txt_surf.get_height() - 2), 2)
