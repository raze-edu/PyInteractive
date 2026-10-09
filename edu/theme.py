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


def draw_dashed_line(
    surface: pygame.Surface,
    color: Tuple[int, int, int],
    p1: Tuple[int, int],
    p2: Tuple[int, int],
    dash_len: int = 6,
    space_len: int = 4,
    width: int = 2
) -> None:
    """Draws a dashed line between two points."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1:
        return
    vx = dx / dist
    vy = dy / dist
    curr = 0.0
    while curr < dist:
        end_d = min(curr + dash_len, dist)
        sp = (int(x1 + vx * curr), int(y1 + vy * curr))
        ep = (int(x1 + vx * end_d), int(y1 + vy * end_d))
        pygame.draw.line(surface, color, sp, ep, width)
        curr += dash_len + space_len


def coord_to_pixel(
    x: float,
    y: float,
    rect: pygame.Rect,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float]
) -> Tuple[int, int]:
    """Converts mathematical Cartesian coordinates (x, y) to surface pixels."""
    x_min, x_max = x_range
    y_min, y_max = y_range
    px = rect.left + int(((x - x_min) / (x_max - x_min)) * rect.width)
    py = rect.bottom - int(((y - y_min) / (y_max - y_min)) * rect.height)
    return px, py


def pixel_to_coord(
    px: int,
    py: int,
    rect: pygame.Rect,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float]
) -> Tuple[float, float]:
    """Converts surface pixels to mathematical Cartesian coordinates (x, y)."""
    x_min, x_max = x_range
    y_min, y_max = y_range
    x = x_min + ((px - rect.left) / max(1, rect.width)) * (x_max - x_min)
    y = y_min + ((rect.bottom - py) / max(1, rect.height)) * (y_max - y_min)
    return x, y


def draw_coordinate_grid(
    surface: pygame.Surface,
    rect: pygame.Rect,
    x_range: Tuple[float, float] = (-5, 5),
    y_range: Tuple[float, float] = (-5, 5),
    points: Optional[List[Tuple[float, float]]] = None,
    lines: Optional[List[List[Tuple[float, float]]]] = None,
    highlight_point: Optional[Tuple[float, float]] = None,
    show_projections: bool = False,
    show_labels: bool = True,
    show_axes: bool = True,
    grid_color: Tuple[int, int, int] = (30, 48, 60),
    axis_color: Tuple[int, int, int] = (140, 160, 180),
    point_color: Tuple[int, int, int] = ACCENT_BLUE,
    point_radius: int = 7,
    font: Optional[pygame.font.Font] = None
) -> None:
    """Draws a Cartesian coordinate grid with optional points, projection lines, and curves."""
    if font is None:
        font = get_font(14, bold=False)

    x_min, x_max = int(x_range[0]), int(x_range[1])
    y_min, y_max = int(y_range[0]), int(y_range[1])

    # Background card
    draw_rounded_rect(surface, rect, CARD_BG, radius=8, border_color=CARD_BORDER, border_width=1)

    # Grid lines
    for x in range(x_min, x_max + 1):
        p_top = coord_to_pixel(x, y_max, rect, x_range, y_range)
        p_bot = coord_to_pixel(x, y_min, rect, x_range, y_range)
        pygame.draw.line(surface, grid_color, p_top, p_bot, 1)

    for y in range(y_min, y_max + 1):
        p_left = coord_to_pixel(x_min, y, rect, x_range, y_range)
        p_right = coord_to_pixel(x_max, y, rect, x_range, y_range)
        pygame.draw.line(surface, grid_color, p_left, p_right, 1)

    # Axes
    if show_axes:
        # X-axis (y = 0)
        if y_min <= 0 <= y_max:
            ax_left = coord_to_pixel(x_min, 0, rect, x_range, y_range)
            ax_right = coord_to_pixel(x_max, 0, rect, x_range, y_range)
            pygame.draw.line(surface, axis_color, ax_left, ax_right, 2)
            # Arrow right
            pygame.draw.polygon(surface, axis_color, [
                (ax_right[0], ax_right[1]),
                (ax_right[0] - 6, ax_right[1] - 4),
                (ax_right[0] - 6, ax_right[1] + 4)
            ])
            # Arrow left
            pygame.draw.polygon(surface, axis_color, [
                (ax_left[0], ax_left[1]),
                (ax_left[0] + 6, ax_left[1] - 4),
                (ax_left[0] + 6, ax_left[1] + 4)
            ])

        # Y-axis (x = 0)
        if x_min <= 0 <= x_max:
            ay_top = coord_to_pixel(0, y_max, rect, x_range, y_range)
            ay_bot = coord_to_pixel(0, y_min, rect, x_range, y_range)
            pygame.draw.line(surface, axis_color, ay_top, ay_bot, 2)
            # Arrow top
            pygame.draw.polygon(surface, axis_color, [
                (ay_top[0], ay_top[1]),
                (ay_top[0] - 4, ay_top[1] + 6),
                (ay_top[0] + 4, ay_top[1] + 6)
            ])
            # Arrow bot
            pygame.draw.polygon(surface, axis_color, [
                (ay_bot[0], ay_bot[1]),
                (ay_bot[0] - 4, ay_bot[1] - 6),
                (ay_bot[0] + 4, ay_bot[1] - 6)
            ])

    # Axis tick numbers
    if show_labels and font:
        axis_y_px = coord_to_pixel(0, 0, rect, x_range, y_range)[1]
        axis_x_px = coord_to_pixel(0, 0, rect, x_range, y_range)[0]
        # X tick marks
        step_x = 2 if (x_max - x_min) > 8 else 1
        for x in range(x_min, x_max + 1, step_x):
            if x == 0:
                continue
            px, py = coord_to_pixel(x, 0, rect, x_range, y_range)
            lbl = font.render(str(x), True, TEXT_MUTED)
            lbl_rect = lbl.get_rect(center=(px, min(rect.bottom - 12, max(rect.top + 12, py + 12))))
            surface.blit(lbl, lbl_rect)

        # Y tick marks
        step_y = 2 if (y_max - y_min) > 8 else 1
        for y in range(y_min, y_max + 1, step_y):
            if y == 0:
                continue
            px, py = coord_to_pixel(0, y, rect, x_range, y_range)
            lbl = font.render(str(y), True, TEXT_MUTED)
            lbl_rect = lbl.get_rect(center=(min(rect.right - 12, max(rect.left + 12, px - 12)), py))
            surface.blit(lbl, lbl_rect)

    # Connected lines
    if lines:
        for polyline in lines:
            if len(polyline) >= 2:
                pts = [coord_to_pixel(pt[0], pt[1], rect, x_range, y_range) for pt in polyline]
                pygame.draw.lines(surface, ACCENT_BLUE, False, pts, 3)

    # Helper to draw a single point with optional projection
    def _draw_pt(x: float, y: float, col: Tuple[int, int, int], r: int, proj: bool):
        px, py = coord_to_pixel(x, y, rect, x_range, y_range)
        if proj:
            # Dashed lines to axes
            ax_x, _ = coord_to_pixel(x, 0, rect, x_range, y_range)
            _, ax_y = coord_to_pixel(0, y, rect, x_range, y_range)
            draw_dashed_line(surface, (100, 160, 210), (px, py), (px, ax_y if 0 in range(x_min, x_max + 1) else py), 4, 3, 2)
            draw_dashed_line(surface, (100, 160, 210), (px, py), (ax_x, py), 4, 3, 2)
        # Point circle
        pygame.draw.circle(surface, (10, 20, 28), (px, py), r + 2)
        pygame.draw.circle(surface, col, (px, py), r)
        pygame.draw.circle(surface, (255, 255, 255), (px, py), max(2, r // 3))

    if points:
        for pt in points:
            _draw_pt(pt[0], pt[1], point_color, point_radius, show_projections)

    if highlight_point:
        _draw_pt(highlight_point[0], highlight_point[1], GOLD_STREAK, point_radius + 2, True)


def draw_cylinder_3d(
    surface: pygame.Surface,
    center: Tuple[int, int],
    radius_px: int = 70,
    height_px: int = 120,
    y_squash: float = 0.35,
    radius_label: Optional[str] = None,
    height_label: Optional[str] = None,
    base_area_label: Optional[str] = None,
    line_color: Tuple[int, int, int] = ACCENT_BLUE,
    fill_color: Tuple[int, int, int] = (25, 45, 60),
    highlight_base: bool = False,
    font: Optional[pygame.font.Font] = None
) -> None:
    """Draws a 3D isometric cylinder matching Duolingo Math geometry lessons."""
    if font is None:
        font = get_font(18, bold=True)

    cx, cy = center
    ry = max(10, int(radius_px * y_squash))
    top_cy = cy - height_px // 2
    bot_cy = cy + height_px // 2

    top_rect = pygame.Rect(cx - radius_px, top_cy - ry, radius_px * 2, ry * 2)
    bot_rect = pygame.Rect(cx - radius_px, bot_cy - ry, radius_px * 2, ry * 2)

    # 1. Body cylinder polygon (sides and bottom fill)
    body_poly = [
        (cx - radius_px, top_cy),
        (cx + radius_px, top_cy),
        (cx + radius_px, bot_cy),
        (cx - radius_px, bot_cy)
    ]
    pygame.draw.polygon(surface, fill_color, body_poly)
    pygame.draw.ellipse(surface, fill_color, bot_rect)

    # 2. Bottom ellipse
    # Back half dashed
    steps = 30
    pts_bot_back = []
    pts_bot_front = []
    for i in range(steps + 1):
        a = math.pi + math.pi * (i / steps)  # top half of bottom ellipse (back side)
        px = cx + radius_px * math.cos(a)
        py = bot_cy + ry * math.sin(a)
        pts_bot_back.append((int(px), int(py)))

    for i in range(steps + 1):
        a = math.pi * (i / steps)  # bottom half of bottom ellipse (front side)
        px = cx + radius_px * math.cos(a)
        py = bot_cy + ry * math.sin(a)
        pts_bot_front.append((int(px), int(py)))

    # Draw dashed back
    for i in range(0, len(pts_bot_back) - 1, 2):
        pygame.draw.line(surface, (80, 110, 130), pts_bot_back[i], pts_bot_back[min(i + 1, len(pts_bot_back) - 1)], 2)
    # Draw solid front
    if len(pts_bot_front) >= 2:
        pygame.draw.lines(surface, line_color, False, pts_bot_front, 3)

    # 3. Side vertical edges
    pygame.draw.line(surface, line_color, (cx - radius_px, top_cy), (cx - radius_px, bot_cy), 3)
    pygame.draw.line(surface, line_color, (cx + radius_px, top_cy), (cx + radius_px, bot_cy), 3)

    # 4. Top ellipse
    top_fill = (35, 75, 100) if highlight_base else (28, 55, 75)
    pygame.draw.ellipse(surface, top_fill, top_rect)
    pygame.draw.ellipse(surface, line_color, top_rect, 3)

    # Radius indicator on top base
    if radius_label is not None:
        # Center dot of top base
        pygame.draw.circle(surface, (255, 255, 255), (cx, top_cy), 4)

        r_line_end = (cx + radius_px, top_cy)
        draw_dashed_line(surface, line_color, (cx, top_cy), r_line_end, dash_len=5, space_len=3, width=2)
        pygame.draw.circle(surface, line_color, r_line_end, 3)

        r_font = get_font(16, bold=True)
        r_lbl = r_font.render(radius_label, True, TEXT_WHITE)
        mid_x = cx + radius_px // 2
        # Position label sitting right above the dashed line, cleanly inside the top ellipse
        lbl_x = mid_x - r_lbl.get_width() // 2
        lbl_y = top_cy - r_lbl.get_height() - 3
        surface.blit(r_lbl, (lbl_x, lbl_y))

    # Base area label inside top base if provided
    if base_area_label is not None:
        ba_font = get_font(15, bold=True)
        ba_lbl = ba_font.render(base_area_label, True, TEXT_WHITE)
        if radius_label is not None:
            # Shift to the left side of the ellipse so it doesn't collide with the center dot or radius line
            ba_x = cx - radius_px // 2 - ba_lbl.get_width() // 2
            ba_y = top_cy - ba_lbl.get_height() // 2
        else:
            ba_x = cx - ba_lbl.get_width() // 2
            ba_y = top_cy - ba_lbl.get_height() // 2
        surface.blit(ba_lbl, (ba_x, ba_y))

    # Height indicator on right side
    if height_label is not None:
        hx = cx + radius_px + 14
        h_font = get_font(16, bold=True)
        h_lbl = h_font.render(height_label, True, line_color)
        draw_dashed_line(surface, (80, 115, 135), (hx, top_cy), (hx, bot_cy), dash_len=4, space_len=3, width=2)
        pygame.draw.line(surface, (80, 115, 135), (hx - 4, top_cy), (hx + 4, top_cy), 2)
        pygame.draw.line(surface, (80, 115, 135), (hx - 4, bot_cy), (hx + 4, bot_cy), 2)
        surface.blit(h_lbl, (hx + 8, cy - h_lbl.get_height() // 2))

