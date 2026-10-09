"""Cylinder 3D interactive geometry exercises:
1. Create a base area by adjusting radius slider with real-time isometric cylinder scaling.
2. Create a volume by adjusting height/radius slider with real-time 3D geometry updates.
"""
from typing import Optional, Tuple
import math
import pygame
from edu.exercises.base import BaseExercise
from edu.theme import (
    CARD_BG, CARD_BORDER, CARD_SELECTED_BG, CARD_SELECTED_BORDER,
    ACCENT_BLUE, ACCENT_BLUE_LIGHT, GREEN_CORRECT, RED_INCORRECT, GOLD_STREAK,
    TEXT_WHITE, TEXT_MUTED, get_font, draw_rounded_rect,
    draw_cylinder_3d
)


class Cylinder3DExercise(BaseExercise):
    """Exercise for 3D cylinder geometry, base area, and volume with interactive sliders."""

    def __init__(
        self,
        prompt: str,
        target_val: int,
        mode: str = "base_area",  # "base_area" or "volume"
        fixed_radius: Optional[int] = None,
        fixed_height: Optional[int] = None,
        min_slider: int = 1,
        max_slider: int = 10,
        initial_slider: int = 2,
        instruction: Optional[str] = None
    ) -> None:
        self.instruction = instruction or (
            "Adjust the slider until the cylinder has the requested base area."
            if mode == "base_area"
            else "Adjust the slider to achieve the target volume."
        )
        super().__init__(
            title=prompt,
            help_title="3D Cylinder Geometry",
            help_tip=self.instruction,
            help_faqs=[
                ("Formula for base area", "A = π · r²"),
                ("Formula for volume", "V = base area · height = π · r² · h")
            ]
        )
        self.prompt = prompt
        self.target_val = target_val
        self.mode = mode
        self.min_slider = min_slider
        self.max_slider = max_slider
        self.slider_val = initial_slider
        self.feedback_message: str = ""

        # If base_area mode, slider controls radius; height is fixed visual constant
        # If volume mode:
        #   If fixed_radius is set, slider controls height: V = π * r^2 * h
        #   If fixed_height is set, slider controls radius: V = π * r^2 * h
        self.fixed_radius = fixed_radius
        self.fixed_height = fixed_height

        self.dragging_slider = False
        self.slider_track_rect = pygame.Rect(200, 480, 400, 14)
        self.slider_thumb_rect = pygame.Rect(200, 473, 28, 28)

    @property
    def current_radius(self) -> int:
        if self.mode == "base_area":
            return self.slider_val
        if self.fixed_radius is not None:
            return self.fixed_radius
        return self.slider_val

    @property
    def current_height(self) -> int:
        if self.mode == "base_area":
            return 5  # visually constant
        if self.fixed_height is not None:
            return self.fixed_height
        return self.slider_val

    @property
    def computed_base_area(self) -> int:
        return self.current_radius ** 2

    @property
    def computed_volume(self) -> int:
        return (self.current_radius ** 2) * self.current_height

    def is_ready_to_check(self) -> bool:
        return True

    def check(self) -> bool:
        self.is_solved = self.check_answer()
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Good job!", self.feedback_message)
        return ("Not quite.", self.feedback_message)

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        self.render(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.is_solved:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Expand hit area for thumb and track
            hit_track = self.slider_track_rect.inflate(30, 30)
            if hit_track.collidepoint(mx, my):
                self.dragging_slider = True
                self._update_slider_from_pos(mx)

        elif event.type == pygame.MOUSEMOTION and self.dragging_slider:
            mx, _ = event.pos
            self._update_slider_from_pos(mx)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_slider = False

    def _update_slider_from_pos(self, mx: int) -> None:
        frac = (mx - self.slider_track_rect.left) / max(1, self.slider_track_rect.width)
        frac = max(0.0, min(1.0, frac))
        raw_val = self.min_slider + frac * (self.max_slider - self.min_slider)
        self.slider_val = int(round(raw_val))

    def check_answer(self) -> bool:
        if self.mode == "base_area":
            # Target is the base area coefficient of pi (e.g. 9 for 9π, or radius squared)
            curr = self.computed_base_area
            if curr == self.target_val or self.slider_val ** 2 == self.target_val:
                self.feedback_message = f"Spot on! Base area = π({self.current_radius})² = {curr}π."
                return True
            else:
                self.feedback_message = f"Current base area is {curr}π. Target is {self.target_val}π."
                return False
        else:
            curr_v = self.computed_volume
            if curr_v == self.target_val:
                self.feedback_message = f"Correct! Volume = π({self.current_radius})² · {self.current_height} = {curr_v}π."
                return True
            else:
                self.feedback_message = f"Current volume is {curr_v}π. Target is {self.target_val}π."
                return False

    def render(self, surface: pygame.Surface, area_rect: Optional[pygame.Rect] = None) -> None:
        w, h = surface.get_size()
        center_x = w // 2

        font_prompt = get_font(24, bold=True)
        font_sub = get_font(15, bold=False)
        font_eq = get_font(20, bold=True)
        font_val = get_font(18, bold=True)

        # Header Prompt
        prompt_surf = font_prompt.render(self.prompt, True, TEXT_WHITE)
        surface.blit(prompt_surf, (center_x - prompt_surf.get_width() // 2, 70))

        sub_surf = font_sub.render(self.instruction, True, TEXT_MUTED)
        surface.blit(sub_surf, (center_x - sub_surf.get_width() // 2, 105))

        # 3D Cylinder rendering
        # Dynamic visual scaling based on current_radius and current_height
        rad_px = 35 + int(self.current_radius * 11)
        h_px = 60 + int(self.current_height * 14)
        cyl_center = (center_x, 260)

        r_lbl = f"r = {self.current_radius}"
        h_lbl = f"h = {self.current_height}" if self.mode == "volume" else None
        ba_lbl = None

        draw_cylinder_3d(
            surface,
            cyl_center,
            radius_px=rad_px,
            height_px=h_px,
            y_squash=0.32,
            radius_label=r_lbl,
            height_label=h_lbl,
            base_area_label=ba_lbl,
            highlight_base=True
        )

        # Dynamic Equation banner
        eq_y = 390
        if self.mode == "base_area":
            eq_text = f"base area = π · ({self.slider_val})² = {self.computed_base_area}π"
        else:
            eq_text = f"volume = π({self.current_radius})² · ({self.current_height}) = {self.computed_volume}π"

        eq_surf = font_eq.render(eq_text, True, ACCENT_BLUE_LIGHT)
        eq_bg = pygame.Rect(center_x - eq_surf.get_width() // 2 - 16, eq_y - 8, eq_surf.get_width() + 32, 44)
        draw_rounded_rect(surface, eq_bg, CARD_BG, radius=8, border_color=CARD_BORDER, border_width=1)
        surface.blit(eq_surf, (center_x - eq_surf.get_width() // 2, eq_y))

        # Slider Track & Controls
        track_w = 420
        self.slider_track_rect = pygame.Rect(center_x - track_w // 2, 470, track_w, 12)
        draw_rounded_rect(surface, self.slider_track_rect, (35, 50, 60), radius=6)

        # Slider progress fill
        frac = (self.slider_val - self.min_slider) / max(1, self.max_slider - self.min_slider)
        fill_w = int(frac * track_w)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.slider_track_rect.left, self.slider_track_rect.top, fill_w, 12)
            draw_rounded_rect(surface, fill_rect, ACCENT_BLUE, radius=6)

        # Slider Thumb
        thumb_x = self.slider_track_rect.left + fill_w
        self.slider_thumb_rect = pygame.Rect(thumb_x - 14, self.slider_track_rect.centery - 14, 28, 28)
        pygame.draw.circle(surface, (10, 20, 28), (thumb_x, self.slider_track_rect.centery), 16)
        pygame.draw.circle(surface, ACCENT_BLUE, (thumb_x, self.slider_track_rect.centery), 14)
        pygame.draw.circle(surface, (255, 255, 255), (thumb_x, self.slider_track_rect.centery), 5)

        # Slider label: e.g. "radius: 3" or "height: 4"
        param_name = "radius" if (self.mode == "base_area" or self.fixed_radius is None) else "height"
        lbl_thumb = font_val.render(f"{param_name} = {self.slider_val}", True, GOLD_STREAK)
        surface.blit(lbl_thumb, (center_x - lbl_thumb.get_width() // 2, 502))
