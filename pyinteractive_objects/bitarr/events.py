import pygame
from typing import Tuple, Optional, Dict, Callable
from .config import BitLayoutConfig, BitLayoutMode, ModularFontCache, BitArrayType
from .info import BitInfoObject


class InteractionHandler:
    """Object handling mouse motion, click toggling, scrolling, and zooming events.
    Translates absolute screen mouse events into relative bit/row/column grid indices.
    """

    def __init__(self):
        self.mouse_pos: Tuple[int, int] = (0, 0)
        self.hovered_bit_index: Optional[int] = None
        self.hovered_info_tuple: Optional[Tuple[BitInfoObject, int, int]] = None

    def process_event(
        self,
        event: pygame.event.Event,
        abs_layout_rect: pygame.Rect,
        config: BitLayoutConfig,
        interactive: bool,
        scroll_y: float,
        max_scroll_y: float,
        toggle_bit_callback: Callable[[int], None],
        zoom_in_callback: Callable[[float], None],
        zoom_out_callback: Callable[[float], None]
    ) -> Tuple[float, Optional[int]]:
        """Processes a Pygame event. Returns updated (scroll_y, clicked_bit_index)."""
        clicked_bit = None

        if event.type == pygame.MOUSEMOTION:
            if pygame.display.get_init():
                self.mouse_pos = pygame.mouse.get_pos()
            else:
                self.mouse_pos = getattr(event, "pos", (0, 0))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.display.get_init():
                m_pos = pygame.mouse.get_pos()
            else:
                m_pos = getattr(event, "pos", (0, 0))

            if abs_layout_rect.collidepoint(m_pos):
                keys = pygame.key.get_pressed()
                ctrl_held = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

                if event.button == 4:  # Wheel up
                    if ctrl_held:
                        zoom_in_callback(0.1)
                    else:
                        scroll_y = max(0.0, scroll_y - 20.0)
                elif event.button == 5:  # Wheel down
                    if ctrl_held:
                        zoom_out_callback(0.1)
                    else:
                        scroll_y = min(max_scroll_y, scroll_y + 20.0)
                elif event.button == 1 and interactive:
                    if self.hovered_bit_index is not None:
                        toggle_bit_callback(self.hovered_bit_index)
                        clicked_bit = self.hovered_bit_index

        return scroll_y, clicked_bit

    def update_hover(
        self,
        abs_layout_rect: pygame.Rect,
        abs_grid_rect: pygame.Rect,
        config: BitLayoutConfig,
        bits: BitArrayType,
        mode: str,
        row_size: int,
        total_rows: int,
        row_height: float,
        box_width: float,
        boxes_per_row: int,
        scroll_y: float,
        info_mappings: Dict[int, Tuple[BitInfoObject, int, int]]
    ) -> None:
        """Updates relative hover index given absolute mouse position and grid bounds."""
        mx, my = self.mouse_pos

        if not abs_layout_rect.collidepoint(mx, my) or not abs_grid_rect.collidepoint(mx, my):
            self.hovered_bit_index = None
            self.hovered_info_tuple = None
            return

        rel_x = mx - abs_grid_rect.x
        rel_y = my - abs_grid_rect.y + scroll_y

        col_idx = int(rel_x // box_width)
        row_idx = int(rel_y // row_height)

        if 0 <= col_idx < boxes_per_row and 0 <= row_idx < total_rows:
            if mode == BitLayoutMode.HEX:
                start_bit = (row_idx * row_size) + (col_idx * 4)
                if start_bit < len(bits):
                    self.hovered_bit_index = start_bit
                    self.hovered_info_tuple = info_mappings.get(start_bit)
                else:
                    self.hovered_bit_index = None
                    self.hovered_info_tuple = None
            else:
                bit_idx = (row_idx * row_size) + col_idx
                if bit_idx < len(bits):
                    self.hovered_bit_index = bit_idx
                    self.hovered_info_tuple = info_mappings.get(bit_idx)
                else:
                    self.hovered_bit_index = None
                    self.hovered_info_tuple = None
        else:
            self.hovered_bit_index = None
            self.hovered_info_tuple = None


class TooltipOverlay:
    """Component that renders the hover tooltip card.
    Receives absolute mouse coordinates and target info object to draw.
    """

    def draw(
        self,
        surface: pygame.Surface,
        hovered_info_tuple: Tuple[BitInfoObject, int, int],
        bits: BitArrayType,
        mouse_pos: Tuple[int, int],
        config: BitLayoutConfig
    ) -> None:
        info_obj, start_b, end_b = hovered_info_tuple
        bits_slice = bits[start_b:end_b]

        title_font_size = config.scaled_size(14)
        body_font_size = config.scaled_size(12)
        title_font = ModularFontCache.get_font(size=title_font_size, bold=True)
        body_font = ModularFontCache.get_font(size=body_font_size, bold=False)

        lines = [
            f"Field: {info_obj.name}",
            f"Bits: [{start_b}:{end_b}] ({end_b - start_b} bits)",
            f"Value: {info_obj.get_formatted_value(bits_slice)}"
        ]
        if info_obj.description:
            lines.append(f"Desc: {info_obj.description}")

        for k, v in info_obj.metadata.items():
            lines.append(f"{k}: {v}")

        max_w = max(title_font.render(l, True, (255, 255, 255)).get_width() for l in lines) + int(24 * config.zoom)
        box_w = max(int(220 * config.zoom), max_w)
        line_h = int(20 * config.zoom)
        box_h = int(16 * config.zoom) + len(lines) * line_h

        mx, my = mouse_pos
        tx = mx + 15
        ty = my + 15

        scr_w, scr_h = surface.get_size()
        if tx + box_w > scr_w:
            tx = mx - box_w - 10
        if ty + box_h > scr_h:
            ty = my - box_h - 10

        tip_rect = pygame.Rect(tx, ty, box_w, box_h)
        border_radius = max(3, int(6 * config.zoom))

        pygame.draw.rect(surface, (15, 23, 42), tip_rect, border_radius=border_radius)
        pygame.draw.rect(surface, info_obj.color, tip_rect, width=2, border_radius=border_radius)

        top_bar = pygame.Rect(tip_rect.x, tip_rect.y, tip_rect.width, max(2, int(4 * config.zoom)))
        pygame.draw.rect(surface, info_obj.color, top_bar, border_top_left_radius=border_radius, border_top_right_radius=border_radius)

        curr_y = tip_rect.y + int(10 * config.zoom)
        for i, line_str in enumerate(lines):
            f = title_font if i == 0 else body_font
            col = (255, 255, 255) if i == 0 else (226, 232, 240)
            txt_s = f.render(line_str, True, col)
            surface.blit(txt_s, (tip_rect.x + int(12 * config.zoom), curr_y))
            curr_y += line_h
