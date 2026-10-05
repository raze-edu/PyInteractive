"""Top navigation and status header component."""
from typing import Optional, Tuple
import pygame
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_heart,
    BAR_BG,
    GREEN_CORRECT,
    GOLD_STREAK,
    TEXT_WHITE,
    TEXT_MUTED
)

class Header:
    """Header bar rendering the close button, progress bar, streak count, and hearts."""
    
    def __init__(self):
        self.progress: float = 0.0  # 0.0 to 1.0
        self.target_progress: float = 0.0
        self.streak: int = 0
        self.hearts: str = "∞"
        self.close_rect = pygame.Rect(0, 0, 40, 40)
        self.close_hovered: bool = False
        
    def set_progress(self, current: int, total: int, streak: int = 0) -> None:
        self.target_progress = max(0.0, min(1.0, current / max(1, total)))
        self.streak = streak

    def update(self, dt: float) -> None:
        # Smooth lerp to target progress
        lerp_speed = 8.0
        diff = self.target_progress - self.progress
        self.progress += diff * min(1.0, dt * lerp_speed)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Returns 'close' if the close button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.close_hovered = self.close_rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                return "close"
        return None

    def draw(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        """Renders header with close button and centered progress bar."""
        # 1. Close button on left
        self.close_rect = pygame.Rect(rect.x + 24, rect.y + (rect.height - 36) // 2, 36, 36)
        close_col = (180, 200, 210) if self.close_hovered else (100, 120, 130)
        cx, cy = self.close_rect.center
        d = 9
        pygame.draw.line(screen, close_col, (cx - d, cy - d), (cx + d, cy + d), 3)
        pygame.draw.line(screen, close_col, (cx - d, cy + d), (cx + d, cy - d), 3)

        # 2. Clean Centered Progress Bar
        bar_margin = 84
        bar_x = rect.x + bar_margin
        bar_w = rect.width - bar_margin * 2
        bar_h = 16
        bar_y = rect.y + (rect.height - bar_h) // 2

        # Track background
        track_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        draw_rounded_rect(screen, track_rect, BAR_BG, radius=bar_h // 2)

        # Filled progress
        fill_w = int(bar_w * self.progress)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, max(bar_h, fill_w), bar_h)
            draw_rounded_rect(screen, fill_rect, GREEN_CORRECT, radius=bar_h // 2)
            
            # Subtle top sheen highlight on progress bar
            sheen_rect = pygame.Rect(bar_x + 2, bar_y + 2, max(bar_h - 4, fill_w - 4), bar_h // 3)
            sheen_col = tuple(min(255, c + 50) for c in GREEN_CORRECT)
            draw_rounded_rect(screen, sheen_rect, sheen_col, radius=bar_h // 4)
