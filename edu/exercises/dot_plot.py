"""Exercise type: Dot plot (plot data to match target mode, or select the mode)."""
from typing import Dict, List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    ACCENT_BLUE_LIGHT,
    ACCENT_BLUE_DARK,
    CARD_BG,
    CARD_BORDER,
    CARD_HOVER,
    CARD_SELECTED_BG,
    CARD_SELECTED_BORDER,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class DotPlotExercise(BaseExercise):
    """Dot plot exercise for learning statistical mode."""
    
    def __init__(
        self,
        mode_type: str,     # "plot" or "select"
        ticks: List[int],
        target_mode: int,
        initial_counts: Optional[Dict[int, int]] = None,
        choices: Optional[List[int]] = None,
        title: Optional[str] = None,
        help_tip: str = "The mode is the value that appears most frequently (the tallest stack of dots)."
    ):
        ex_title = title or ("Plot the data with" if mode_type == "plot" else "Select the mode")
        super().__init__(
            title=ex_title,
            help_title="Mode Tips",
            help_tip=help_tip,
            help_faqs=[
                ("What is the mode?", "The mode is the number that shows up the most times in the data."),
                ("How to add or remove dots?", "Click above a number to add a dot to its stack. Click the top dot to remove it.")
            ]
        )
        self.mode_type = mode_type
        self.ticks = ticks
        self.target_mode = target_mode
        self.choices = choices or []
        
        # Counts per tick value
        self.initial_counts = initial_counts or {t: 1 for t in ticks}
        self.counts: Dict[int, int] = dict(self.initial_counts)
        
        # State for select mode
        self.selected_choice: Optional[int] = None
        self.choice_rects: List[Tuple[pygame.Rect, int]] = []
        self.hovered_choice: Optional[int] = None
        
        # Geometry
        self.dot_radius: int = 13
        self.dot_spacing: int = 30
        self.line_start_x: int = 0
        self.line_end_x: int = 0
        self.line_y: int = 0

    def is_ready_to_check(self) -> bool:
        if self.mode_type == "plot":
            return any(c > 0 for c in self.counts.values())
        else:
            return self.selected_choice is not None

    def _get_current_mode(self) -> Optional[int]:
        max_count = max(self.counts.values()) if self.counts else 0
        if max_count <= 0:
            return None
        modes = [val for val, count in self.counts.items() if count == max_count]
        # Must be unique mode
        return modes[0] if len(modes) == 1 else None

    def check(self) -> bool:
        if self.mode_type == "plot":
            self.is_solved = (self._get_current_mode() == self.target_mode)
        else:
            self.is_solved = (self.selected_choice == self.target_mode)
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Nicely done!", "")
        return ("Not quite.", f"The mode is {self.target_mode}")

    def reset(self) -> None:
        super().reset()
        self.counts = dict(self.initial_counts)
        self.selected_choice = None

    def _get_tick_x(self, val: int) -> float:
        if val not in self.ticks:
            return float(self.line_start_x)
        idx = self.ticks.index(val)
        n = len(self.ticks)
        if n <= 1:
            return float(self.line_start_x)
        return self.line_start_x + (idx / (n - 1)) * (self.line_end_x - self.line_start_x)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.mode_type == "select":
            if event.type == pygame.MOUSEMOTION:
                self.hovered_choice = None
                for rect, val in self.choice_rects:
                    if rect.collidepoint(event.pos):
                        self.hovered_choice = val
                        break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, val in self.choice_rects:
                    if rect.collidepoint(event.pos):
                        sound_manager.play_click()
                        self.selected_choice = val
                        return

        else:
            # Plot mode: clicking to add/remove dots
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for val in self.ticks:
                    tx = self._get_tick_x(val)
                    # Check column zone
                    if abs(pos[0] - tx) <= self.dot_radius + 12:
                        cnt = self.counts.get(val, 0)
                        # Check if clicking on top dot (remove)
                        if cnt > 0:
                            top_dot_y = self.line_y - 18 - (cnt - 1) * self.dot_spacing
                            if abs(pos[1] - top_dot_y) <= self.dot_radius + 4:
                                self.counts[val] = max(0, cnt - 1)
                                sound_manager.play_snap()
                                return

                        # Check if clicking above line to add
                        if self.line_y - 220 <= pos[1] <= self.line_y + 10:
                            if cnt < 5:
                                self.counts[val] = cnt + 1
                                sound_manager.play_snap()
                                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # Title
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 40)))

        # Subtitle / prompt value
        if self.mode_type == "plot":
            sub_font = get_font(36, bold=True)
            txt = f"mode  =  {self.target_mode}"
            # Render "mode" in white, "=" in blue, value in white
            sub_surf = sub_font.render(txt, True, TEXT_WHITE)
            screen.blit(sub_surf, sub_surf.get_rect(center=(area_rect.centerx, area_rect.y + 90)))

        # Setup number line coordinates
        self.line_start_x = area_rect.centerx - 220
        self.line_end_x = area_rect.centerx + 220
        
        if self.mode_type == "plot":
            self.line_y = area_rect.y + 310
        else:
            self.line_y = area_rect.y + 230

        # Draw axis
        axis_color = (60, 80, 92)
        pygame.draw.line(screen, axis_color, (self.line_start_x - 15, self.line_y), (self.line_end_x + 15, self.line_y), 3)

        # Draw ticks and numbers
        lbl_font = get_font(20, bold=True)
        for val in self.ticks:
            tx = self._get_tick_x(val)
            pygame.draw.line(screen, axis_color, (tx, self.line_y - 6), (tx, self.line_y + 6), 2)
            lbl = lbl_font.render(str(val), True, TEXT_MUTED)
            screen.blit(lbl, lbl.get_rect(center=(tx, self.line_y + 22)))

            # Draw stacked dots
            cnt = self.counts.get(val, 0)
            for i in range(cnt):
                dy = self.line_y - 20 - i * self.dot_spacing
                pygame.draw.circle(screen, ACCENT_BLUE_LIGHT, (int(tx), dy), self.dot_radius)
                # Soft lighter inner dot highlight
                pygame.draw.circle(screen, (150, 230, 255), (int(tx - 3), dy - 3), 4)

        # Draw Multiple Choice Buttons for "Select" mode
        if self.mode_type == "select":
            self.choice_rects = []
            btn_w = 420
            btn_h = 56
            btn_gap = 14
            start_btn_y = self.line_y + 70
            opt_font = get_font(24, bold=True)

            for i, opt in enumerate(self.choices):
                brect = pygame.Rect(area_rect.centerx - btn_w // 2, start_btn_y + i * (btn_h + btn_gap), btn_w, btn_h)
                self.choice_rects.append((brect, opt))

                is_sel = (self.selected_choice == opt)
                is_hov = (self.hovered_choice == opt)

                if is_sel:
                    bg = CARD_SELECTED_BG
                    border = CARD_SELECTED_BORDER
                elif is_hov:
                    bg = CARD_HOVER
                    border = (53, 75, 87)
                else:
                    bg = CARD_BG
                    border = CARD_BORDER

                draw_rounded_rect(screen, brect, bg, radius=14, border_color=border, border_width=2)
                txt_surf = opt_font.render(str(opt), True, TEXT_WHITE)
                screen.blit(txt_surf, txt_surf.get_rect(center=brect.center))
