import pygame
from typing import List, Tuple, Optional
from .config import BitLayoutConfig, BitLayoutMode, ModularFontCache
from .info import SectionLabel


class HeaderComponent:
    """Header element object. Holds relative column positions and title metadata.
    Receives absolute coordinates from main container to draw.
    """

    def __init__(self, title_section: str = "SECTION", title_offset: str = "OFFSET"):
        self.title_section = title_section
        self.title_offset = title_offset

    def draw(
        self,
        surface: pygame.Surface,
        abs_header_rect: pygame.Rect,
        config: BitLayoutConfig,
        box_width: float,
        boxes_per_row: int,
        mode: str
    ) -> None:
        if not config.show_header or abs_header_rect.height <= 0:
            return

        pygame.draw.rect(surface, config.header_bg, abs_header_rect, border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.line(surface, config.border_color, (abs_header_rect.x, abs_header_rect.bottom), (abs_header_rect.right, abs_header_rect.bottom), 1)

        font_size = config.scaled_size(12)
        font = ModularFontCache.get_font(size=font_size, bold=True)

        curr_x = abs_header_rect.x

        # Section Column Header (Col 1)
        if config.show_section_col:
            c1_rect = pygame.Rect(curr_x, abs_header_rect.y, config.col1_width, abs_header_rect.height)
            txt1 = font.render(self.title_section, True, config.header_text)
            surface.blit(txt1, txt1.get_rect(center=c1_rect.center))
            curr_x += config.col1_width

        # Offset Column Header (Col 2)
        if config.show_offset_col:
            c2_rect = pygame.Rect(curr_x, abs_header_rect.y, config.col2_width, abs_header_rect.height)
            txt2 = font.render(self.title_offset, True, config.header_text)
            surface.blit(txt2, txt2.get_rect(center=c2_rect.center))
            curr_x += config.col2_width

        # Bit position headers
        grid_x = curr_x
        for col_i in range(boxes_per_row):
            bx = grid_x + col_i * box_width
            box_r = pygame.Rect(bx, abs_header_rect.y, box_width, abs_header_rect.height)
            idx_str = f"N{col_i}" if mode == BitLayoutMode.HEX else f"{col_i}"
            lbl = font.render(idx_str, True, config.header_text)
            surface.blit(lbl, lbl.get_rect(center=box_r.center))


class SectionColumnComponent:
    """Multi-row section label column component (Column 1).
    Stores relative row spans and section definitions.
    Receives absolute column bounds from main container to draw.
    """

    def draw(
        self,
        surface: pygame.Surface,
        abs_col_rect: pygame.Rect,
        config: BitLayoutConfig,
        section_labels: List[SectionLabel],
        total_rows: int,
        row_height: float,
        scroll_y: float
    ) -> None:
        if not config.show_section_col or abs_col_rect.width <= 0:
            return

        pygame.draw.rect(surface, config.col_bg, abs_col_rect)
        pygame.draw.line(surface, config.border_color, (abs_col_rect.right, abs_col_rect.top), (abs_col_rect.right, abs_col_rect.bottom), 1)

        font_size = config.scaled_size(13)
        font = ModularFontCache.get_font(size=font_size, bold=True)

        for lbl in section_labels:
            if lbl.start_row >= total_rows:
                continue
            e_row = min(lbl.end_row, total_rows - 1)
            sy = abs_col_rect.y + (lbl.start_row * row_height) - scroll_y
            ey = abs_col_rect.y + ((e_row + 1) * row_height) - scroll_y
            h = ey - sy

            pad = max(2, int(4 * config.zoom))
            lbl_rect = pygame.Rect(abs_col_rect.x + pad, sy + pad // 2, abs_col_rect.width - (pad * 2), max(4, h - pad))

            if lbl_rect.bottom < abs_col_rect.top or lbl_rect.top > abs_col_rect.bottom:
                continue

            lbl_bg = lbl.color or (51, 65, 85)
            pygame.draw.rect(surface, lbl_bg, lbl_rect, border_radius=4)
            pygame.draw.rect(surface, (148, 163, 184), lbl_rect, width=1, border_radius=4)

            txt_surf = font.render(lbl.text, True, (255, 255, 255))
            if txt_surf.get_width() > lbl_rect.width - 4:
                txt_surf = pygame.transform.smoothscale(
                    txt_surf, (max(1, lbl_rect.width - 4), txt_surf.get_height())
                )
            surface.blit(txt_surf, txt_surf.get_rect(center=lbl_rect.center))


class OffsetColumnComponent:
    """Row offset column component (Column 2).
    Stores relative formatting style and padding.
    Receives absolute column bounds from main container to draw.
    """

    def draw(
        self,
        surface: pygame.Surface,
        abs_col_rect: pygame.Rect,
        config: BitLayoutConfig,
        total_rows: int,
        row_size: int,
        row_height: float,
        scroll_y: float
    ) -> None:
        if not config.show_offset_col or abs_col_rect.width <= 0:
            return

        pygame.draw.rect(surface, config.col_bg, abs_col_rect)
        pygame.draw.line(surface, config.border_color, (abs_col_rect.right, abs_col_rect.top), (abs_col_rect.right, abs_col_rect.bottom), 1)

        font_size = config.scaled_size(12)
        font = ModularFontCache.get_font(size=font_size, bold=False)

        for row_i in range(total_rows):
            ry = abs_col_rect.y + (row_i * row_height) - scroll_y
            row_box = pygame.Rect(abs_col_rect.x, ry, abs_col_rect.width, row_height)
            if row_box.bottom < abs_col_rect.top or row_box.top > abs_col_rect.bottom:
                continue

            bit_offset = row_i * row_size

            # Modular offset formatting
            if config.custom_offset_formatter:
                offset_str = config.custom_offset_formatter(row_i, bit_offset)
            elif config.offset_format == "dec":
                offset_str = f"+{bit_offset}"
            elif config.offset_format == "byte":
                offset_str = f"[{bit_offset // 8}]"
            elif config.offset_format == "bit":
                offset_str = f"bit {bit_offset}"
            else:  # "hex" default
                offset_str = f"0x{bit_offset:04X}"

            txt = font.render(offset_str, True, config.dim_text)
            surface.blit(txt, txt.get_rect(center=row_box.center))


class TableFrameComponent:
    """Outer framing and background component for the table container.
    Receives absolute widget bounds to draw background and borders.
    """

    def draw(self, surface: pygame.Surface, abs_widget_rect: pygame.Rect, config: BitLayoutConfig) -> None:
        pygame.draw.rect(surface, config.bg_color, abs_widget_rect, border_radius=6)
        pygame.draw.rect(surface, config.border_color, abs_widget_rect, width=2, border_radius=6)
