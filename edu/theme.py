"""Theme definitions, color palettes, fonts, and drawing helper functions
tailored to match the Duolingo Math dark aesthetic.
"""
from typing import Dict, List, Optional, Tuple
import math
import pygame

# Color definitions
BG_COLOR = (19, 31, 36)            # #131f24 - Deep dark slate navy
CARD_BG = (24, 39, 46)             # #18272e - Dark card surface
CARD_BORDER = (43, 61, 71)         # #2b3d47 - Dark card border
CARD_HOVER = (35, 56, 66)          # #233842 - Hover card state
CARD_SELECTED_BG = (22, 52, 66)    # #163442 - Selected card bg
CARD_SELECTED_BORDER = (28, 176, 246)  # #1cb0f6 - Vibrant Duolingo blue border

ACCENT_BLUE = (28, 176, 246)       # #1cb0f6 - Primary interactive blue
ACCENT_BLUE_LIGHT = (73, 192, 248) # #49c0f8 - Light blue tile face
ACCENT_BLUE_DARK = (24, 153, 214)  # #1899d6 - Tile bottom 3D bevel

GREEN_CORRECT = (88, 204, 2)       # #58cc02 - Duolingo lime green
GREEN_DARK = (70, 163, 2)          # #46a302 - Green button 3D shadow
BANNER_CORRECT_BG = (20, 41, 33)   # #142921 - Success bottom banner bg

RED_INCORRECT = (255, 75, 75)      # #ff4b4b - Red error
BANNER_INCORRECT_BG = (43, 20, 25) # #2b1419 - Error bottom banner bg

GOLD_STREAK = (255, 200, 0)        # #ffc800 - Streak gold / fire
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (119, 142, 155)       # #778e9b
TEXT_DARK = (19, 31, 36)
BAR_BG = (43, 56, 63)              # #2b383f - Header progress bar track
DIVIDER_COLOR = (32, 47, 54)       # #202f36

# Dark number tiles
TILE_DARK_BG = (32, 47, 54)
TILE_DARK_BEVEL = (20, 33, 39)
TILE_DARK_BORDER = (53, 72, 81)

_FONT_CACHE: Dict[Tuple[str, int, bool], pygame.font.Font] = {}

def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Returns a cached pygame font with fallback mechanism."""
    key = ("default", size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    
    font = None
    # Preferred system fonts for clean modern UI
    preferred_fonts = ["Segoe UI", "SF Pro Display", "Ubuntu", "Helvetica Neue", "Arial", "DejaVu Sans"]
    for font_name in preferred_fonts:
        try:
            font = pygame.font.SysFont(font_name, size, bold=bold)
            if font is not None:
                break
        except Exception:
            continue
            
    if font is None:
        try:
            font = pygame.font.Font(None, size)
            if bold:
                font.set_bold(True)
        except Exception:
            font = pygame.font.SysFont(None, size, bold=bold)
            
    _FONT_CACHE[key] = font
    return font


def draw_rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: Tuple[int, int, int],
    radius: int = 12,
    border_color: Optional[Tuple[int, int, int]] = None,
    border_width: int = 2
) -> None:
    """Draws a smooth rounded rectangle with optional border."""
    if rect.width <= 0 or rect.height <= 0:
        return
    r = min(radius, rect.width // 2, rect.height // 2)
    pygame.draw.rect(surface, color, rect, border_radius=r)
    if border_color is not None and border_width > 0:
        pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=r)


def draw_bevel_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    bg_color: Tuple[int, int, int],
    bevel_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int],
    font: pygame.font.Font,
    is_hovered: bool = False,
    is_pressed: bool = False,
    is_disabled: bool = False,
    border_radius: int = 14,
    bevel_depth: int = 4
) -> None:
    """Draws a modern Duolingo 3D beveled button with pop effect."""
    if is_disabled:
        draw_rounded_rect(surface, rect, (43, 56, 63), border_radius)
        txt_surf = font.render(text, True, (82, 101, 109))
        surface.blit(txt_surf, txt_surf.get_rect(center=rect.center))
        return

    offset = bevel_depth if is_pressed else 0
    top_rect = pygame.Rect(rect.x, rect.y + offset, rect.width, rect.height - bevel_depth)

    # 1. Bevel base shadow
    draw_rounded_rect(surface, rect, bevel_color, border_radius)

    # 2. Top button face
    face_color = bg_color
    if is_hovered and not is_pressed:
        face_color = tuple(min(255, int(c * 1.08)) for c in bg_color)
    draw_rounded_rect(surface, top_rect, face_color, border_radius)

    # 3. Label text
    txt_surf = font.render(text, True, text_color)
    surface.blit(txt_surf, txt_surf.get_rect(center=top_rect.center))


def draw_heart(surface: pygame.Surface, center: Tuple[int, int], size: int) -> None:
    """Draws a cute stylized Duolingo heart with rainbow/gradient sheen."""
    cx, cy = center
    hs = size // 2
    # Draw two overlapping circles and a polygon
    r = size // 3.2
    c1 = (int(cx - r * 0.9), int(cy - r * 0.4))
    c2 = (int(cx + r * 0.9), int(cy - r * 0.4))
    
    # Heart vibrant color
    color_top = (28, 200, 246)
    color_main = (0, 218, 175)
    color_pink = (255, 75, 140)
    
    pts = [
        (cx - size * 0.48, cy - r * 0.2),
        (cx, cy + size * 0.5),
        (cx + size * 0.48, cy - r * 0.2),
    ]
    pygame.draw.circle(surface, color_pink, c1, int(r))
    pygame.draw.circle(surface, color_top, c2, int(r))
    pygame.draw.polygon(surface, color_main, pts)
    pygame.draw.polygon(surface, color_pink, [c1, (cx, cy), pts[0]])


def draw_lightbulb(surface: pygame.Surface, center: Tuple[int, int], size: int, color: Tuple[int, int, int]) -> None:
    """Draws a cute lightbulb icon."""
    cx, cy = center
    r = int(size * 0.36)
    pygame.draw.circle(surface, color, (cx, int(cy - size * 0.1)), r, width=2)
    # Bulb base
    base_w = int(size * 0.35)
    base_h = int(size * 0.25)
    base_rect = pygame.Rect(cx - base_w // 2, cy + int(size * 0.15), base_w, base_h)
    pygame.draw.rect(surface, color, base_rect, width=2, border_radius=3)
    # Filaments / rays
    pygame.draw.line(surface, color, (cx, cy - int(size * 0.55)), (cx, cy - int(size * 0.7)), 2)
    pygame.draw.line(surface, color, (cx - int(size * 0.5), cy - int(size * 0.35)), (cx - int(size * 0.65), cy - int(size * 0.45)), 2)
    pygame.draw.line(surface, color, (cx + int(size * 0.5), cy - int(size * 0.35)), (cx + int(size * 0.65), cy - int(size * 0.45)), 2)


def draw_calculator_icon(surface: pygame.Surface, center: Tuple[int, int], size: int, color: Tuple[int, int, int]) -> None:
    """Draws a mini calculator icon."""
    cx, cy = center
    w = int(size * 0.7)
    h = int(size * 0.85)
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    draw_rounded_rect(surface, rect, (0, 0, 0, 0), radius=5, border_color=color, border_width=2)
    # Display screen
    screen_rect = pygame.Rect(cx - w // 2 + 4, cy - h // 2 + 5, w - 8, int(h * 0.22))
    draw_rounded_rect(surface, screen_rect, color, radius=2)
    # 4 keypad dots
    for row in range(2):
        for col in range(2):
            bx = cx - w // 2 + 7 + col * (w - 14) // 2 + 3
            by = cy - h // 2 + int(h * 0.38) + row * int(h * 0.25) + 3
            pygame.draw.circle(surface, color, (bx, by), 2)


def draw_check_badge(surface: pygame.Surface, center: Tuple[int, int], radius: int) -> None:
    """Draws a green circular badge with crisp white checkmark."""
    cx, cy = center
    pygame.draw.circle(surface, GREEN_CORRECT, (cx, cy), radius)
    # Draw checkmark path
    pts = [
        (cx - int(radius * 0.45), cy - int(radius * 0.05)),
        (cx - int(radius * 0.1), cy + int(radius * 0.35)),
        (cx + int(radius * 0.5), cy - int(radius * 0.35))
    ]
    pygame.draw.lines(surface, (255, 255, 255), False, pts, width=max(3, int(radius * 0.2)))


def draw_cross_badge(surface: pygame.Surface, center: Tuple[int, int], radius: int) -> None:
    """Draws a red circular badge with white X."""
    cx, cy = center
    pygame.draw.circle(surface, RED_INCORRECT, (cx, cy), radius)
    d = int(radius * 0.35)
    w = max(3, int(radius * 0.2))
    pygame.draw.line(surface, (255, 255, 255), (cx - d, cy - d), (cx + d, cy + d), width=w)
    pygame.draw.line(surface, (255, 255, 255), (cx - d, cy + d), (cx + d, cy - d), width=w)


def draw_pie_chart(
    surface: pygame.Surface,
    center: Tuple[int, int],
    radius: int,
    total_slices: int,
    selected_indices: List[bool],
    base_color: Tuple[int, int, int] = (24, 39, 46),
    fill_color: Tuple[int, int, int] = ACCENT_BLUE,
    border_color: Tuple[int, int, int] = (43, 61, 71),
    hovered_slice: int = -1
) -> None:
    """Draws a fractional pie chart matching the examples."""
    cx, cy = center
    if total_slices <= 0:
        return
        
    angle_per_slice = (2.0 * math.pi) / total_slices
    
    # Draw slices
    for i in range(total_slices):
        start_angle = -math.pi / 2.0 + i * angle_per_slice
        end_angle = -math.pi / 2.0 + (i + 1) * angle_per_slice
        
        is_selected = selected_indices[i] if i < len(selected_indices) else False
        color = fill_color if is_selected else base_color
        if hovered_slice == i:
            color = tuple(min(255, int(c * 1.25) + 20) for c in color)
            
        pts = [(cx, cy)]
        steps = max(6, int(60 / total_slices))
        for step in range(steps + 1):
            a = start_angle + (end_angle - start_angle) * (step / steps)
            px = cx + radius * math.cos(a)
            py = cy + radius * math.sin(a)
            pts.append((int(px), int(py)))
            
        pygame.draw.polygon(surface, color, pts)
        
    # Draw dividing lines
    for i in range(total_slices):
        a = -math.pi / 2.0 + i * angle_per_slice
        px = cx + radius * math.cos(a)
        py = cy + radius * math.sin(a)
        pygame.draw.line(surface, border_color, (cx, cy), (int(px), int(py)), 2)
        
    # Draw outer ring
    pygame.draw.circle(surface, border_color, (cx, cy), radius, width=2)
