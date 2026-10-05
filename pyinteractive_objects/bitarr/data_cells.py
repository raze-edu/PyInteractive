import pygame
from typing import Tuple, Dict, Optional, List
from .config import BitLayoutConfig, BitLayoutMode, ModularFontCache, BitArrayType
from .info import BitInfoObject


class BitCell:
    """Cell object representing an individual 1-bit container.
    Stores relative cell properties (index, state, colors, mapped info object).
    Receives absolute bounding rect from grid container to draw.
    """

    def __init__(
        self,
        index: int,
        val: bool,
        mode: str,
        chars: Tuple[str, str],
        colors_off_on: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        info_entry: Optional[Tuple[BitInfoObject, int, int]] = None,
        is_hovered: bool = False
    ):
        self.index = index
        self.val = val
        self.mode = mode
        self.chars = chars
        self.colors_off_on = colors_off_on
        self.info_entry = info_entry
        self.is_hovered = is_hovered

    def draw(
        self,
        surface: pygame.Surface,
        abs_box_rect: pygame.Rect,
        config: BitLayoutConfig,
        active_hover_info: Optional[BitInfoObject]
    ) -> None:
        font_size = config.scaled_size(14)
        font = ModularFontCache.get_font(size=font_size, bold=True)
        border_radius = max(2, int(4 * config.zoom))
        bar_height = max(2, int(3 * config.zoom))

        if self.mode == BitLayoutMode.BIT_COLOR:
            box_bg = self.colors_off_on[1] if self.val else self.colors_off_on[0]
            char_val = self.chars[1] if self.val else self.chars[0]
            text_col = (255, 255, 255) if self.val else config.dim_text
        else:  # BIT_CHAR mode
            box_bg = (30, 41, 59) if not self.val else (37, 99, 235)
            char_val = self.chars[1] if self.val else self.chars[0]
            text_col = (255, 255, 255) if self.val else config.dim_text

        # Visual Cue for Info Objects (Border / Tint / Top Accent Bar)
        info_obj = self.info_entry[0] if self.info_entry else None

        if info_obj is not None:
            accent_col = info_obj.color
            tint_bg = (
                int(box_bg[0] * 0.6 + accent_col[0] * 0.4),
                int(box_bg[1] * 0.6 + accent_col[1] * 0.4),
                int(box_bg[2] * 0.6 + accent_col[2] * 0.4)
            )
            pygame.draw.rect(surface, tint_bg, abs_box_rect, border_radius=border_radius)

            accent_bar = pygame.Rect(abs_box_rect.x, abs_box_rect.y, abs_box_rect.width, bar_height)
            pygame.draw.rect(surface, accent_col, accent_bar, border_top_left_radius=border_radius, border_top_right_radius=border_radius)

            if active_hover_info == info_obj:
                pygame.draw.rect(surface, (255, 255, 255), abs_box_rect, width=2, border_radius=border_radius)
            else:
                pygame.draw.rect(surface, accent_col, abs_box_rect, width=1, border_radius=border_radius)
        else:
            pygame.draw.rect(surface, box_bg, abs_box_rect, border_radius=border_radius)
            if self.is_hovered:
                pygame.draw.rect(surface, (255, 255, 255), abs_box_rect, width=2, border_radius=border_radius)

        txt = font.render(char_val, True, text_col)
        surface.blit(txt, txt.get_rect(center=abs_box_rect.center))


class HexCell:
    """Cell object representing a 4-bit nibble container displayed in Hex.
    Stores relative cell properties (start bit index, hex char value, mapped info object).
    Receives absolute bounding rect from grid container to draw.
    """

    def __init__(
        self,
        start_bit: int,
        char_val: str,
        info_entry: Optional[Tuple[BitInfoObject, int, int]] = None,
        is_hovered: bool = False
    ):
        self.start_bit = start_bit
        self.char_val = char_val
        self.info_entry = info_entry
        self.is_hovered = is_hovered

    def draw(
        self,
        surface: pygame.Surface,
        abs_box_rect: pygame.Rect,
        config: BitLayoutConfig,
        active_hover_info: Optional[BitInfoObject]
    ) -> None:
        font_size = config.scaled_size(14)
        font = ModularFontCache.get_font(size=font_size, bold=True)
        border_radius = max(2, int(4 * config.zoom))
        bar_height = max(2, int(3 * config.zoom))

        box_bg = (30, 41, 59)
        text_col = config.text_color
        info_obj = self.info_entry[0] if self.info_entry else None

        if info_obj is not None:
            accent_col = info_obj.color
            tint_bg = (
                int(box_bg[0] * 0.6 + accent_col[0] * 0.4),
                int(box_bg[1] * 0.6 + accent_col[1] * 0.4),
                int(box_bg[2] * 0.6 + accent_col[2] * 0.4)
            )
            pygame.draw.rect(surface, tint_bg, abs_box_rect, border_radius=border_radius)

            accent_bar = pygame.Rect(abs_box_rect.x, abs_box_rect.y, abs_box_rect.width, bar_height)
            pygame.draw.rect(surface, accent_col, accent_bar, border_top_left_radius=border_radius, border_top_right_radius=border_radius)

            if active_hover_info == info_obj:
                pygame.draw.rect(surface, (255, 255, 255), abs_box_rect, width=2, border_radius=border_radius)
            else:
                pygame.draw.rect(surface, accent_col, abs_box_rect, width=1, border_radius=border_radius)
        else:
            pygame.draw.rect(surface, box_bg, abs_box_rect, border_radius=border_radius)
            if self.is_hovered:
                pygame.draw.rect(surface, (255, 255, 255), abs_box_rect, width=2, border_radius=border_radius)

        txt = font.render(self.char_val, True, text_col)
        surface.blit(txt, txt.get_rect(center=abs_box_rect.center))


class DataGridComponent:
    """Component that arranges bit and hex cells in a grid layout.
    Stores relative grid parameters (relative row size, mode, cell mappings).
    Receives absolute grid rect from main container to draw.
    """

    def draw(
        self,
        surface: pygame.Surface,
        abs_grid_rect: pygame.Rect,
        config: BitLayoutConfig,
        bits: BitArrayType,
        row_size: int,
        mode: str,
        chars: Tuple[str, str],
        colors_off_on: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        info_mappings: Dict[int, Tuple[BitInfoObject, int, int]],
        hovered_bit_index: Optional[int],
        hovered_info_tuple: Optional[Tuple[BitInfoObject, int, int]],
        total_rows: int,
        row_height: float,
        box_width: float,
        boxes_per_row: int,
        scroll_y: float
    ) -> None:
        total_bits = len(bits)
        active_hover_info = hovered_info_tuple[0] if hovered_info_tuple else None
        padding = max(1, int(2 * config.zoom))
        border_radius = max(2, int(4 * config.zoom))

        for row_i in range(total_rows):
            ry = abs_grid_rect.y + (row_i * row_height) - scroll_y
            if ry + row_height < abs_grid_rect.y or ry > abs_grid_rect.bottom:
                continue

            for col_i in range(boxes_per_row):
                bx = abs_grid_rect.x + col_i * box_width
                box_rect = pygame.Rect(bx + padding, ry + padding, box_width - (padding * 2), row_height - (padding * 2))

                if mode == BitLayoutMode.HEX:
                    start_bit = (row_i * row_size) + (col_i * 4)
                    end_bit = min(start_bit + 4, total_bits)

                    if start_bit >= total_bits:
                        pygame.draw.rect(surface, (20, 27, 44), box_rect, border_radius=border_radius)
                        continue

                    nibble = bits[start_bit:end_bit]
                    nibble_val = int(nibble.to01(), 2) if len(nibble) > 0 else 0
                    char_val = f"{nibble_val:X}"
                    info_entry = info_mappings.get(start_bit)
                    is_hovered = (hovered_bit_index is not None and start_bit <= hovered_bit_index < end_bit)

                    cell = HexCell(
                        start_bit=start_bit,
                        char_val=char_val,
                        info_entry=info_entry,
                        is_hovered=is_hovered
                    )
                    cell.draw(surface, box_rect, config, active_hover_info)

                else:
                    bit_i = (row_i * row_size) + col_i
                    if bit_i >= total_bits:
                        pygame.draw.rect(surface, (20, 27, 44), box_rect, border_radius=border_radius)
                        continue

                    bit_val = bool(bits[bit_i]) if bit_i < len(bits) else False
                    info_entry = info_mappings.get(bit_i)
                    is_hovered = (hovered_bit_index == bit_i)

                    cell = BitCell(
                        index=bit_i,
                        val=bit_val,
                        mode=mode,
                        chars=chars,
                        colors_off_on=colors_off_on,
                        info_entry=info_entry,
                        is_hovered=is_hovered
                    )
                    cell.draw(surface, box_rect, config, active_hover_info)
