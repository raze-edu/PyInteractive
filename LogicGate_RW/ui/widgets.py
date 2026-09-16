from typing import Tuple, Optional
import pygame

from include import Color
from LogicGate_RW.ui.style import shared_style

def draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    mouse_pos: Tuple[int, int],
    base_color: Optional[Color] = None,
    text_color: Optional[Color] = None,
    font_size: int = 16,
    border_radius: int = 6
) -> bool:
    """Renders a sleek interactive button using include.Color."""
    hovered = rect.collidepoint(mouse_pos)
    if base_color is None:
        base_color = shared_style.get_color_obj("primary")

    draw_col = base_color + Color(20, 20, 25, 0) if hovered else base_color
    pygame.draw.rect(screen, draw_col.__tuple__()[:3], rect, border_radius=border_radius)
    pygame.draw.rect(screen, (255, 255, 255), rect, 1, border_radius=border_radius)

    try:
        font = pygame.font.Font(None, font_size)
    except Exception:
        font = pygame.font.SysFont("arial", font_size)

    tc = text_color.__tuple__() if text_color else (255, 255, 255)
    t_surf = font.render(text, True, tc[:3])
    screen.blit(t_surf, (rect.centerx - t_surf.get_width() / 2, rect.centery - t_surf.get_height() / 2))
    return hovered

def draw_slider(
    screen: pygame.Surface,
    x: int,
    y: int,
    w: int,
    val: float,
    min_val: float,
    max_val: float,
    label: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    enabled: bool = True
) -> pygame.Rect:
    """Renders a modern horizontal slider track and handle."""
    lbl_color = (230, 230, 235) if enabled else (100, 100, 105)
    lbl_surf = font.render(f"{label}: {int(val)}", True, lbl_color)
    screen.blit(lbl_surf, (x, y - 20))

    track_color = (60, 60, 65) if enabled else (40, 40, 45)
    pygame.draw.line(screen, track_color, (x, y), (x + w, y), 6)

    ratio = (val - min_val) / max(1e-5, (max_val - min_val))
    hx = x + int(w * max(0.0, min(1.0, ratio)))
    handle_color = color if enabled else (120, 120, 125)
    pygame.draw.circle(screen, handle_color, (hx, y), 9)
    pygame.draw.circle(screen, (240, 240, 245) if enabled else (80, 80, 85), (hx, y), 9, 2)

    return pygame.Rect(x - 10, y - 10, w + 20, 20)
