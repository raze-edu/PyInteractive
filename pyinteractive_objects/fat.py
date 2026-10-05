import sys
import os
import math
from typing import List, Tuple, Dict, Optional, Union, Any, Callable
import pygame

import bitarray
from bitarray import bitarray as BitArrayType

from pyinteractive_objects.bitarr import (
    BitLayout,
    BitLayoutConfig,
    BitLayoutMode,
    BitInfoObject,
    ModularFontCache
)


class FATTable(BitLayout):
    """FAT (File Allocation Table) Visualizer.
    Inherits from BitLayout and visualizes FAT12, FAT16, or FAT32 cluster entry tables.
    
    Features:
    - Rows of 12-bit (FAT12), 16-bit (FAT16), or 32-bit (FAT32) entries.
    - Only row offset column and bit index header row are shown.
    - Hovering over a row follows cluster pointers recursively and renders non-overlapping
      pointing arrows on the side of the table for each hop in the cluster chain.
    """

    CHAIN_COLORS = [
        (59, 130, 246),   # Blue (Hop 0)
        (16, 185, 129),   # Emerald Green (Hop 1)
        (245, 158, 11),   # Amber (Hop 2)
        (236, 72, 153),   # Pink (Hop 3)
        (168, 85, 247),   # Purple (Hop 4)
        (14, 165, 233),   # Sky Blue (Hop 5+)
    ]

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        data: Any = None,
        entry_size: int = 16,                  # 12, 16, or 32 bits
        mode: str = BitLayoutMode.BIT_CHAR,
        chars: Tuple[str, str] = ("0", "1"),
        colors_off_on: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None,
        col2_width: int = 100,
        arrow_margin: int = 140,               # Margin on right for chain arrows
        zoom: float = 1.0,
        interactive: bool = True
    ):
        """Initializes FATTable widget."""
        if entry_size not in (12, 16, 32):
            raise ValueError(f"entry_size must be 12, 16, or 32 bits (got {entry_size})")

        self.entry_size = entry_size
        self.arrow_margin = arrow_margin

        # Custom config: disable section column (Col 1), show row offset column (Col 2)
        config = BitLayoutConfig(
            zoom=zoom,
            base_col1_width=0,                 # Disabled section column
            base_col2_width=col2_width,        # Offset column width
            show_header=True,
            show_section_col=False,            # Only offset column + bit header
            show_offset_col=True,
            offset_format="custom",
            custom_offset_formatter=self._format_fat_offset
        )

        # Pre-process integer cluster array if provided as list
        processed_data = self._pack_fat_data(data, entry_size)

        super().__init__(
            pos=pos,
            size=size,
            data=processed_data,
            row_size=entry_size,               # 1 row per FAT entry
            mode=mode,
            chars=chars,
            colors_off_on=colors_off_on,
            col1_width=0,
            col2_width=col2_width,
            show_header=True,
            interactive=interactive,
            zoom=zoom,
            config=config
        )

        # Hovered row index and computed cluster chain hops: list of (src_row, dst_row)
        self.hovered_row_idx: Optional[int] = None
        self.cluster_chain: List[Tuple[int, int]] = []

    def _format_fat_offset(self, row_idx: int, bit_offset: int) -> str:
        """Formats row offset column label as Cluster # index."""
        return f"Cls #{row_idx}"

    def _pack_fat_data(self, data: Any, entry_size: int) -> Any:
        """Packs list of integer cluster pointers into a bitarray."""
        if isinstance(data, (list, tuple)) and len(data) > 0 and isinstance(data[0], int):
            ba = bitarray.bitarray()
            for val in data:
                v = max(0, val)
                b_str = bin(v)[2:].zfill(entry_size)
                if len(b_str) > entry_size:
                    b_str = b_str[-entry_size:]
                ba.extend(bitarray.bitarray(b_str))
            return ba
        return data

    def set_fat_entries(self, entries: List[int]) -> None:
        """Updates FAT table data with a list of cluster integer values."""
        ba = self._pack_fat_data(entries, self.entry_size)
        self.set_data(ba)

    def get_row_value(self, row_index: int) -> Optional[int]:
        """Extracts the integer cluster pointer value of row_index."""
        if row_index < 0 or row_index >= self.total_rows:
            return None
        start_b = row_index * self.entry_size
        end_b = min(start_b + self.entry_size, len(self.bits))
        if start_b >= len(self.bits):
            return None
        bits_slice = self.bits[start_b:end_b]
        if len(bits_slice) == 0:
            return None
        try:
            return int(bits_slice.to01(), 2)
        except ValueError:
            return None

    def is_valid_cluster_pointer(self, val: Optional[int]) -> bool:
        """Checks if integer value can be interpreted as a valid cluster row index."""
        if val is None:
            return False

        tot_rows = self.total_rows
        if not (0 <= val < tot_rows):
            return False

        if self.entry_size == 12 and val >= 0xFF8:
            return False
        if self.entry_size == 16 and val >= 0xFFF8:
            return False
        if self.entry_size == 32 and val >= 0x0FFFFFF8:
            return False

        return True

    def _compute_absolute_grid_geometry(self) -> Tuple[pygame.Rect, float, float, int]:
        """Override geometry calculation to reserve space on the right for chain arrows."""
        h_height = self.config.header_height
        c1_width = self.config.col1_width
        c2_width = self.config.col2_width
        arr_margin = int(self.arrow_margin * self.config.zoom)

        grid_x = self.rect.x + c1_width + c2_width
        grid_y = self.rect.y + h_height
        avail_w = max(10, self.rect.width - (c1_width + c2_width + arr_margin))
        grid_h = max(10.0, float(self.rect.height - h_height))

        boxes_per_row = self.row_size if self.mode != BitLayoutMode.HEX else math.ceil(self.row_size / 4)
        box_width = avail_w / max(1, boxes_per_row)
        row_height = self.config.row_height

        return pygame.Rect(grid_x, grid_y, int(avail_w), int(grid_h)), row_height, box_width, boxes_per_row

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handles events and computes cluster chain hops when hovering over a row."""
        super().handle_event(event)
        self._update_cluster_chain()

    def _update_cluster_chain(self) -> None:
        """Calculates recursive cluster chain arrows when mouse hovers over a row."""
        m_pos = self.interaction_handler.mouse_pos
        if not self.rect.collidepoint(m_pos):
            self.hovered_row_idx = None
            self.cluster_chain.clear()
            return

        grid_rect, row_height, box_width, boxes_per_row = self._compute_absolute_grid_geometry()
        h_height = self.config.header_height

        rel_y = m_pos[1] - (self.rect.y + h_height) + self.scroll_y
        row_idx = int(rel_y // row_height)

        if 0 <= row_idx < self.total_rows:
            self.hovered_row_idx = row_idx
            self.cluster_chain = self._trace_cluster_chain(row_idx)
        else:
            self.hovered_row_idx = None
            self.cluster_chain.clear()

    def _trace_cluster_chain(self, start_row: int) -> List[Tuple[int, int]]:
        """Recursively traces cluster pointers starting at start_row."""
        chain: List[Tuple[int, int]] = []
        visited = {start_row}
        curr_row = start_row

        while True:
            val = self.get_row_value(curr_row)
            if self.is_valid_cluster_pointer(val):
                dst_row = int(val)
                if dst_row in visited:
                    chain.append((curr_row, dst_row))
                    break
                chain.append((curr_row, dst_row))
                visited.add(dst_row)
                curr_row = dst_row
            else:
                break

        return chain

    def draw(self, surface: pygame.Surface) -> None:
        """Renders FATTable and draws cluster chain arrows on the right side of the table."""
        super().draw(surface)

        if len(self.cluster_chain) > 0:
            self._draw_cluster_chain_arrows(surface)

    def _draw_cluster_chain_arrows(self, surface: pygame.Surface) -> None:
        """Renders curved / bracketed arrows on the right side of the table for each hop."""
        grid_rect, row_height, box_width, boxes_per_row = self._compute_absolute_grid_geometry()
        h_height = self.config.header_height
        table_top_y = self.rect.y + h_height

        base_right_x = grid_rect.right + 6
        step_offset = int(16 * self.config.zoom)

        for hop_idx, (src_row, dst_row) in enumerate(self.cluster_chain):
            src_y = table_top_y + (src_row * row_height) + (row_height / 2.0) - self.scroll_y
            dst_y = table_top_y + (dst_row * row_height) + (row_height / 2.0) - self.scroll_y

            if (src_y < table_top_y and dst_y < table_top_y) or (src_y > self.rect.bottom and dst_y > self.rect.bottom):
                continue

            offset_x = base_right_x + (hop_idx * step_offset) + int(10 * self.config.zoom)
            color = self.CHAIN_COLORS[hop_idx % len(self.CHAIN_COLORS)]

            line_width = max(2, int(2.5 * self.config.zoom))

            # 1. Horizontal line out from src_row
            pygame.draw.line(surface, color, (base_right_x, src_y), (offset_x, src_y), line_width)

            # 2. Vertical line spanning src_row to dst_row
            pygame.draw.line(surface, color, (offset_x, src_y), (offset_x, dst_y), line_width)

            # 3. Horizontal line pointing into dst_row
            pygame.draw.line(surface, color, (offset_x, dst_y), (base_right_x + int(8 * self.config.zoom), dst_y), line_width)

            # 4. Arrow head pointing left towards dst_row
            head_size = max(4, int(6 * self.config.zoom))
            tip_x = base_right_x
            tip_y = dst_y
            p1 = (tip_x, tip_y)
            p2 = (tip_x + head_size + 2, tip_y - head_size)
            p3 = (tip_x + head_size + 2, tip_y + head_size)
            pygame.draw.polygon(surface, color, [p1, p2, p3])

            # Small indicator circle at src_row
            pygame.draw.circle(surface, color, (int(base_right_x), int(src_y)), max(2, int(3 * self.config.zoom)))


# ============================================================================
# FAT DIRECTORY ENTRY OBJECT (dir_entry)
# ============================================================================

class dir_entry(BitLayout):
    """32-byte (256-bit) FAT Directory Entry visualizer object reflecting standard FAT12/FAT16/FAT32 specifications.
    
    Renders 32 byte rows (offsets 0..31), multi-row section labels, bit field colors,
    custom bit container character letters ('h', 'm', 's', 'y', 'd', '/', 'A', 'D', 'V', 'S', 'H', 'W'),
    and side callout annotation note boxes as specified in the FAT directory entry layout diagram.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        data: Any = None,
        filename: str = "FILENAME.TXT",
        attributes: int = 0x20,                 # Archive flag default
        first_cluster: int = 2,
        filesize: int = 4096,
        show_annotations: bool = True,
        annotation_margin: int = 280,
        zoom: float = 1.0,
        interactive: bool = True
    ):
        self.show_annotations = show_annotations
        self.annotation_margin = annotation_margin

        config = BitLayoutConfig(
            zoom=zoom,
            base_col1_width=150,                # Column 1 width for multi-row section titles
            base_col2_width=50,                 # Column 2 width for byte offset (0..31)
            base_row_height=26,                 # 26px height per byte row
            show_header=True,
            show_section_col=True,
            show_offset_col=True,
            offset_format="custom",
            custom_offset_formatter=self._format_byte_offset
        )

        if data is None:
            data = self._build_fat_directory_bytes(filename, attributes, first_cluster, filesize)

        super().__init__(
            pos=pos,
            size=size,
            data=data,
            row_size=8,                         # 8 bits (1 byte) per row (32 rows total)
            mode=BitLayoutMode.BIT_CHAR,
            col1_width=150,
            col2_width=50,
            show_header=True,
            interactive=interactive,
            zoom=zoom,
            config=config
        )

        self.char_overrides: Dict[int, str] = {}
        self.box_color_overrides: Dict[int, Tuple[int, int, int]] = {}
        self._setup_dir_entry_sections()

    def _format_byte_offset(self, row_idx: int, bit_offset: int) -> str:
        return f"{row_idx}"

    def _build_fat_directory_bytes(self, filename: str, attributes: int, first_cluster: int, filesize: int) -> bytes:
        parts = filename.upper().split(".")
        name_part = (parts[0][:8]).ljust(8, ' ')
        ext_part = (parts[1][:3]).ljust(3, ' ') if len(parts) > 1 else "   "

        buf = bytearray(32)
        buf[0:8] = name_part.encode('ascii', 'ignore')
        buf[8:11] = ext_part.encode('ascii', 'ignore')
        buf[11] = attributes & 0xFF
        buf[12] = 0x00
        buf[13] = 0x00

        buf[14:16] = (0x6000).to_bytes(2, 'little')
        buf[16:18] = ((46 << 9) | (1 << 5) | 1).to_bytes(2, 'little')
        buf[18:20] = ((46 << 9) | (1 << 5) | 1).to_bytes(2, 'little')

        msb = (first_cluster >> 16) & 0xFFFF
        lsb = first_cluster & 0xFFFF
        buf[20:22] = msb.to_bytes(2, 'little')
        buf[22:24] = (0x6000).to_bytes(2, 'little')
        buf[24:26] = ((46 << 9) | (1 << 5) | 1).to_bytes(2, 'little')
        buf[26:28] = lsb.to_bytes(2, 'little')

        buf[28:32] = (filesize & 0xFFFFFFFF).to_bytes(4, 'little')
        return bytes(buf)

    def _setup_dir_entry_sections(self) -> None:
        self.clear_section_labels()
        self.clear_info_mappings()

        self.add_section_label(0, 7, "Name", (30, 41, 59))
        self.add_section_label(8, 10, "Ext.", (30, 41, 59))
        self.add_section_label(11, 11, "Flags", (47, 63, 86))
        self.add_section_label(12, 12, "reserved", (30, 41, 59))
        self.add_section_label(13, 13, "create 10ms", (30, 41, 59))
        self.add_section_label(14, 15, "create h/m/s", (20, 70, 70))
        self.add_section_label(16, 17, "create y/m/d", (20, 70, 70))
        self.add_section_label(18, 19, "access y/m/d", (20, 70, 70))
        self.add_section_label(20, 21, "cluster index msb", (47, 63, 86))
        self.add_section_label(22, 23, "change h/m/s", (20, 70, 70))
        self.add_section_label(24, 25, "change y/m/d", (20, 70, 70))
        self.add_section_label(26, 27, "cluster index lsb", (47, 63, 86))
        self.add_section_label(28, 31, "Filesize\n(bytes)", (30, 41, 59))

        self.assign_info(0, 64, BitInfoObject("Name", "8-byte ASCII Filename", (59, 130, 246)))
        self.assign_info(64, 88, BitInfoObject("Ext.", "3-byte ASCII Extension", (14, 165, 233)))
        self.assign_info(88, 96, BitInfoObject("Flags", "Attribute Flags (R, H, S, V, D, A)", (236, 72, 153)))
        self.assign_info(96, 104, BitInfoObject("Reserved", "Reserved / NT VFAT Flags", (148, 163, 184)))
        self.assign_info(104, 112, BitInfoObject("Create 10ms", "Fine resolution creation time (0-199)", (168, 85, 247)))
        self.assign_info(112, 128, BitInfoObject("Create h/m/s", "Creation Time (Hours 5b, Minutes 6b, Seconds 5b)", (20, 180, 180)))
        self.assign_info(128, 144, BitInfoObject("Create y/m/d", "Creation Date (Year 7b, Month 4b, Day 5b)", (20, 180, 180)))
        self.assign_info(144, 160, BitInfoObject("Access y/m/d", "Last Access Date", (20, 180, 180)))
        self.assign_info(160, 176, BitInfoObject("Cluster MSB", "High 16 bits of First Cluster Index (FAT32)", (99, 102, 241)))
        self.assign_info(176, 192, BitInfoObject("Change h/m/s", "Last Modification Time", (20, 180, 180)))
        self.assign_info(192, 208, BitInfoObject("Change y/m/d", "Last Modification Date", (20, 180, 180)))
        self.assign_info(208, 224, BitInfoObject("Cluster LSB", "Low 16 bits of First Cluster Index", (99, 102, 241)))
        self.assign_info(224, 256, BitInfoObject("Filesize", "32-bit File Size in Bytes", (34, 197, 94)))

        teal_col = (15, 118, 118)
        brown_col = (130, 65, 15)
        slate_col = (45, 60, 80)

        flag_letters = ["write protection", "hidden", "system", "Vol. Label", "Dir", "Archive", "/", "/"]
        for i in range(8):
            bit_i = 88 + i
            self.char_overrides[bit_i] = str(flag_letters[i])

        self.char_overrides[99] = "name"
        self.char_overrides[100] = "ext"

        def apply_time_colors_and_chars(start_bit: int):
            for b in range(11, 16):
                self.char_overrides[start_bit + b] = "h"
                self.box_color_overrides[start_bit + b] = teal_col
            for b in range(5, 11):
                self.char_overrides[start_bit + b] = "m"
                self.box_color_overrides[start_bit + b] = brown_col
            for b in range(0, 5):
                self.char_overrides[start_bit + b] = "s"
                self.box_color_overrides[start_bit + b] = brown_col

        def apply_date_colors_and_chars(start_bit: int):
            for b in range(9, 16):
                self.char_overrides[start_bit + b] = "y"
                self.box_color_overrides[start_bit + b] = teal_col
            for b in range(5, 9):
                self.char_overrides[start_bit + b] = "m"
                self.box_color_overrides[start_bit + b] = brown_col
            for b in range(0, 5):
                self.char_overrides[start_bit + b] = "d"
                self.box_color_overrides[start_bit + b] = brown_col

        apply_time_colors_and_chars(112)
        apply_date_colors_and_chars(128)
        apply_date_colors_and_chars(144)
        apply_time_colors_and_chars(176)
        apply_date_colors_and_chars(192)

        for b in range(160, 176):
            self.box_color_overrides[b] = slate_col
        self.char_overrides[175] = "bit 31"
        self.char_overrides[160] = "bit 16"

        for b in range(208, 224):
            self.box_color_overrides[b] = slate_col
        self.char_overrides[223] = "bit 15"
        self.char_overrides[208] = "bit 0"

    def _compute_absolute_grid_geometry(self) -> Tuple[pygame.Rect, float, float, int]:
        h_height = self.config.header_height
        c1_width = self.config.col1_width
        c2_width = self.config.col2_width
        ann_margin = int(self.annotation_margin * self.config.zoom) if self.show_annotations else 0

        grid_x = self.rect.x + c1_width + c2_width
        grid_y = self.rect.y + h_height
        avail_w = max(10, self.rect.width - (c1_width + c2_width + ann_margin))
        grid_h = max(10.0, float(self.rect.height - h_height))

        boxes_per_row = 8
        box_width = avail_w / max(1, boxes_per_row)
        row_height = self.config.row_height

        return pygame.Rect(grid_x, grid_y, int(avail_w), int(grid_h)), row_height, box_width, boxes_per_row

    def draw(self, surface: pygame.Surface) -> None:
        self.frame_component.draw(surface, self.rect, self.config)

        h_height = self.config.header_height
        grid_rect, row_height, box_width, boxes_per_row = self._compute_absolute_grid_geometry()

        total_content_height = self.total_rows * row_height
        self.max_scroll_y = max(0.0, total_content_height - grid_rect.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll_y)

        grid_clip_rect = pygame.Rect(self.rect.x, self.rect.y + h_height, self.rect.width, self.rect.height - h_height)
        surface.set_clip(grid_clip_rect)

        abs_col1_rect = pygame.Rect(self.rect.x, self.rect.y + h_height, self.config.col1_width, grid_clip_rect.height)
        self.section_component.draw(
            surface=surface, abs_col_rect=abs_col1_rect, config=self.config,
            section_labels=self.section_labels, total_rows=self.total_rows,
            row_height=row_height, scroll_y=self.scroll_y
        )

        abs_col2_rect = pygame.Rect(self.rect.x + self.config.col1_width, self.rect.y + h_height, self.config.col2_width, grid_clip_rect.height)
        self.offset_component.draw(
            surface=surface, abs_col_rect=abs_col2_rect, config=self.config,
            total_rows=self.total_rows, row_size=self.row_size,
            row_height=row_height, scroll_y=self.scroll_y
        )

        self._draw_dir_entry_grid(surface, grid_rect, row_height, box_width)

        surface.set_clip(None)

        abs_header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, h_height)
        self.header_component.draw(
            surface=surface, abs_header_rect=abs_header_rect, config=self.config,
            box_width=box_width, boxes_per_row=boxes_per_row, mode=self.mode
        )

        if self.show_annotations:
            self._draw_side_annotations(surface, grid_rect, row_height, h_height)

        if self.hovered_info_tuple is not None:
            self.tooltip_component.draw(
                surface=surface, hovered_info_tuple=self.hovered_info_tuple,
                bits=self.bits, mouse_pos=self.interaction_handler.mouse_pos, config=self.config
            )

    def _draw_dir_entry_grid(self, surface: pygame.Surface, grid_rect: pygame.Rect, row_height: float, box_width: float) -> None:
        font_size = self.config.scaled_size(11)
        font = ModularFontCache.get_font(size=font_size, bold=True)
        padding = max(1, int(2 * self.config.zoom))
        border_radius = max(2, int(4 * self.config.zoom))

        active_hover_info = self.hovered_info_tuple[0] if self.hovered_info_tuple else None

        for row_i in range(self.total_rows):
            ry = grid_rect.y + (row_i * row_height) - self.scroll_y
            if ry + row_height < grid_rect.y or ry > grid_rect.bottom:
                continue

            for col_i in range(8):
                bx = grid_rect.x + col_i * box_width
                box_rect = pygame.Rect(bx + padding, ry + padding, box_width - (padding * 2), row_height - (padding * 2))

                bit_i = (row_i * 8) + col_i
                if bit_i >= len(self.bits):
                    continue

                bit_val = bool(self.bits[bit_i])
                info_entry = self.info_mappings.get(bit_i)
                is_hovered = (self.hovered_bit_index == bit_i)

                box_bg = self.box_color_overrides.get(bit_i, (30, 41, 59))
                if bit_val and bit_i not in self.box_color_overrides:
                    box_bg = (37, 99, 235)

                char_val = self.char_overrides.get(bit_i, self.chars[1] if bit_val else self.chars[0])
                text_col = (255, 255, 255)

                info_obj = info_entry[0] if info_entry else None
                if info_obj is not None:
                    accent_col = info_obj.color
                    tint_bg = (
                        int(box_bg[0] * 0.6 + accent_col[0] * 0.4),
                        int(box_bg[1] * 0.6 + accent_col[1] * 0.4),
                        int(box_bg[2] * 0.6 + accent_col[2] * 0.4)
                    )
                    pygame.draw.rect(surface, tint_bg, box_rect, border_radius=border_radius)
                    if active_hover_info == info_obj:
                        pygame.draw.rect(surface, (255, 255, 255), box_rect, width=2, border_radius=border_radius)
                    else:
                        pygame.draw.rect(surface, accent_col, box_rect, width=1, border_radius=border_radius)
                else:
                    pygame.draw.rect(surface, box_bg, box_rect, border_radius=border_radius)
                    if is_hovered:
                        pygame.draw.rect(surface, (255, 255, 255), box_rect, width=2, border_radius=border_radius)

                txt_s = font.render(char_val, True, text_col)
                if txt_s.get_width() > box_rect.width - 2:
                    txt_s = pygame.transform.smoothscale(txt_s, (max(1, box_rect.width - 2), txt_s.get_height()))
                surface.blit(txt_s, txt_s.get_rect(center=box_rect.center))

    def _draw_side_annotations(self, surface: pygame.Surface, grid_rect: pygame.Rect, row_height: float, h_height: int) -> None:
        font_size = self.config.scaled_size(11)
        font = ModularFontCache.get_font(size=font_size, bold=False)
        bold_font = ModularFontCache.get_font(size=font_size, bold=True)

        table_top_y = self.rect.y + h_height
        right_x = grid_rect.right + int(15 * self.config.zoom)
        card_bg = (20, 27, 38)
        border_col = (71, 85, 105)

        notes = [
            (0, 0, [
                "The 1st byte is also a additional Flag",
                "0000 0000 : There are no more following DIR entries",
                "1110 0101 : The File was deleted",
                "01xx xxxx : Means this is a long name entry and the x",
                "are the number of the entry. These entrys are positioned",
                "in befor the actual file entry in reversed order."
            ]),
            (2, 5, ["ASCII UPPERCASE"]),
            (8, 10, ["ASCII UPPERCASE"]),
            (12, 12, ["name lowercase bit 4", "ext lowercase bit 5"]),
            (14, 15, ["seconds resolution 2"]),
            (16, 17, ["Year since 1980"]),
            (20, 27, [
                "The first cluster the file occupies inside the data area.",
                "The FAT is used to get all clusters by following there link chain."
            ]),
            (28, 31, [
                "This 4 bytes cause the filesize limitation of 4 GiB in FAT32"
            ])
        ]

        for s_row, e_row, lines in notes:
            sy = table_top_y + (s_row * row_height) - self.scroll_y
            ey = table_top_y + ((e_row + 1) * row_height) - self.scroll_y
            h = ey - sy

            if ey < table_top_y or sy > self.rect.bottom:
                continue

            max_line_w = max(font.render(l, True, (255, 255, 255)).get_width() for l in lines) + 16
            card_w = max(int(140 * self.config.zoom), max_line_w)
            card_h = max(int(22 * self.config.zoom), len(lines) * int(16 * self.config.zoom) + 8)

            card_y = sy + (h / 2.0) - (card_h / 2.0)
            card_rect = pygame.Rect(right_x, card_y, card_w, card_h)

            pygame.draw.rect(surface, card_bg, card_rect, border_radius=4)
            pygame.draw.rect(surface, border_col, card_rect, width=1, border_radius=4)

            mid_y = sy + (h / 2.0)
            pygame.draw.line(surface, border_col, (grid_rect.right + 2, mid_y), (right_x, mid_y), 1)

            curr_y = card_rect.y + 4
            for idx, line_str in enumerate(lines):
                f = bold_font if idx == 0 and len(lines) > 2 else font
                txt_s = f.render(line_str, True, (226, 232, 240))
                surface.blit(txt_s, (card_rect.x + 8, curr_y))
                curr_y += int(16 * self.config.zoom)


# Alias export
FATDirEntry = dir_entry


# ============================================================================
# FAT DIRECTORY CLUSTER OBJECT (dir_cluster)
# ============================================================================

class dir_cluster:
    """Represents a FAT Directory Cluster containing multiple 32-byte Directory Entries.
    
    Features:
    - Displays 32-byte directory entries as summary blocks labeled with Name.Ext.
    - Clicking on an entry summary block switches to the detailed 32-byte dir_entry view.
    - Offers back-navigation to return to the cluster summary block list.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        entries: Optional[List[Union[Dict[str, Any], dir_entry]]] = None,
        cluster_index: int = 2,
        on_entry_select: Optional[Callable[[int, dir_entry], None]] = None,
        zoom: float = 1.0
    ):
        """Initializes dir_cluster widget.

        Args:
            pos: (x, y) top-left corner coordinates.
            size: (width, height) widget bounds.
            entries: List of directory entry parameter dictionaries or dir_entry instances.
            cluster_index: Integer cluster index (e.g. Cluster #2).
            on_entry_select: Optional callback triggered when an entry is selected.
            zoom: Layout zoom scale.
        """
        self.rect = pygame.Rect(pos, size)
        self.cluster_index = cluster_index
        self.on_entry_select = on_entry_select
        self.zoom = max(0.4, min(3.0, zoom))

        # Active view state: None for Cluster Summary Overview, or int entry_index for Detailed View
        self.selected_entry_index: Optional[int] = None
        self.active_detail_widget: Optional[dir_entry] = None

        # Hover state
        self.hovered_entry_index: Optional[int] = None

        # Scroll state for overview grid
        self.scroll_y = 0.0
        self.max_scroll_y = 0.0

        # Process entries into dir_entry objects
        self.dir_entries: List[dir_entry] = []
        self._init_dir_entries(entries)

    def _init_dir_entries(self, entries: Optional[List[Union[Dict[str, Any], dir_entry]]]) -> None:
        """Initializes internal dir_entry list from parameters or default sample entries."""
        if entries is not None and len(entries) > 0:
            for item in entries:
                if isinstance(item, dir_entry):
                    self.dir_entries.append(item)
                elif isinstance(item, dict):
                    # Construct dir_entry from kwargs dict
                    kwargs = item.copy()
                    kwargs["pos"] = self.rect.topleft
                    kwargs["size"] = self.rect.size
                    kwargs["zoom"] = self.zoom
                    self.dir_entries.append(dir_entry(**kwargs))
        else:
            # Default sample cluster entries
            samples = [
                {"filename": "DOCUMENTS", "attributes": 0x10, "first_cluster": 3, "filesize": 0},
                {"filename": "README.TXT", "attributes": 0x20, "first_cluster": 4, "filesize": 1024},
                {"filename": "PHOTO.JPG", "attributes": 0x20, "first_cluster": 7, "filesize": 524288},
                {"filename": "SYSTEM.SYS", "attributes": 0x06, "first_cluster": 12, "filesize": 4096},
                {"filename": "OLD_DATA.TMP", "attributes": 0x20, "first_cluster": 0, "filesize": 0},
                {"filename": "CONFIG.INI", "attributes": 0x20, "first_cluster": 15, "filesize": 256},
            ]
            for s in samples:
                self.dir_entries.append(dir_entry(
                    pos=self.rect.topleft,
                    size=self.rect.size,
                    filename=s["filename"],
                    attributes=s["attributes"],
                    first_cluster=s["first_cluster"],
                    filesize=s["filesize"],
                    zoom=self.zoom
                ))

    def zoom_in(self, step: float = 0.1) -> None:
        self.zoom = min(3.0, self.zoom + step)
        for e in self.dir_entries:
            e.zoom_in(step)

    def zoom_out(self, step: float = 0.1) -> None:
        self.zoom = max(0.4, self.zoom - step)
        for e in self.dir_entries:
            e.zoom_out(step)

    def select_entry(self, index: int) -> None:
        """Selects directory entry at index and switches to detailed 32-byte view."""
        if 0 <= index < len(self.dir_entries):
            self.selected_entry_index = index
            widget = self.dir_entries[index]

            # Fit detail widget nicely inside container bounds below top nav bar
            nav_height = int(36 * self.zoom)
            widget.rect = pygame.Rect(
                self.rect.x,
                self.rect.y + nav_height,
                self.rect.width,
                self.rect.height - nav_height
            )
            self.active_detail_widget = widget

            if self.on_entry_select:
                self.on_entry_select(index, widget)

    def deselect_entry(self) -> None:
        """Returns to cluster overview summary list view."""
        self.selected_entry_index = None
        self.active_detail_widget = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handles Pygame mouse motion, click selection, scrolling, and navigation events."""
        m_pos = getattr(event, "pos", pygame.mouse.get_pos() if pygame.display.get_init() else (0, 0))

        # Detailed View mode handling
        if self.selected_entry_index is not None and self.active_detail_widget is not None:
            # Check Back Button click in top navigation bar
            nav_height = int(36 * self.zoom)
            back_btn_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 4, int(180 * self.zoom), nav_height - 8)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(m_pos):
                    self.deselect_entry()
                    return

            # Pass events to detailed dir_entry widget
            self.active_detail_widget.handle_event(event)
            return

        # Cluster Overview Mode handling
        if event.type == pygame.MOUSEMOTION:
            self._update_overview_hover(m_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(m_pos):
                if event.button == 4:  # Wheel up
                    self.scroll_y = max(0.0, self.scroll_y - 25.0)
                elif event.button == 5:  # Wheel down
                    self.scroll_y = min(self.max_scroll_y, self.scroll_y + 25.0)
                elif event.button == 1:
                    if self.hovered_entry_index is not None:
                        self.select_entry(self.hovered_entry_index)

    def _update_overview_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Calculates which summary block card is currently hovered by the mouse."""
        if not self.rect.collidepoint(mouse_pos):
            self.hovered_entry_index = None
            return

        cols = max(1, int(self.rect.width // (340 * self.zoom)))
        card_w = (self.rect.width - (cols + 1) * 12) / cols
        card_h = int(80 * self.zoom)
        header_h = int(36 * self.zoom)

        mx, my = mouse_pos
        rel_y = my - (self.rect.y + header_h) + self.scroll_y
        rel_x = mx - self.rect.x

        if rel_y < 0:
            self.hovered_entry_index = None
            return

        for idx, _ in enumerate(self.dir_entries):
            row_i = idx // cols
            col_i = idx % cols

            cx = 12 + col_i * (card_w + 12)
            cy = 12 + row_i * (card_h + 12)
            card_rect = pygame.Rect(cx, cy, card_w, card_h)

            if card_rect.collidepoint(rel_x, rel_y):
                self.hovered_entry_index = idx
                return

        self.hovered_entry_index = None

    def draw(self, surface: pygame.Surface) -> None:
        """Renders dir_cluster overview or detailed dir_entry view."""
        # Detailed View Mode
        if self.selected_entry_index is not None and self.active_detail_widget is not None:
            self._draw_detail_view(surface)
            return

        # Cluster Overview Summary Mode
        self._draw_overview_view(surface)

    def _draw_overview_view(self, surface: pygame.Surface) -> None:
        """Renders cluster summary blocks with Name.Ext labels."""
        # Background & Frame
        pygame.draw.rect(surface, (15, 23, 42), self.rect, border_radius=6)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=6)

        header_h = int(36 * self.zoom)
        font_size = ModularFontCache.get_font(size=max(8, int(14 * self.zoom)), bold=True)
        small_font = ModularFontCache.get_font(size=max(8, int(11 * self.zoom)), bold=False)

        # Header Bar
        header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, header_h)
        pygame.draw.rect(surface, (30, 41, 59), header_rect, border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.line(surface, (51, 65, 85), (header_rect.x, header_rect.bottom), (header_rect.right, header_rect.bottom), 1)

        title_txt = font_size.render(f"Directory Cluster #{self.cluster_index} ({len(self.dir_entries)} 32-Byte Entries)", True, (241, 245, 249))
        surface.blit(title_txt, (header_rect.x + 14, header_rect.y + int(8 * self.zoom)))

        # Summary Block Cards Grid
        content_rect = pygame.Rect(self.rect.x, self.rect.y + header_h, self.rect.width, self.rect.height - header_h)
        surface.set_clip(content_rect)

        cols = max(1, int(self.rect.width // (340 * self.zoom)))
        card_w = (self.rect.width - (cols + 1) * 12) / cols
        card_h = int(80 * self.zoom)

        total_rows = math.ceil(len(self.dir_entries) / cols)
        total_content_h = 12 + total_rows * (card_h + 12)
        self.max_scroll_y = max(0.0, total_content_h - content_rect.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll_y)

        for idx, entry in enumerate(self.dir_entries):
            row_i = idx // cols
            col_i = idx % cols

            cx = content_rect.x + 12 + col_i * (card_w + 12)
            cy = content_rect.y + 12 + row_i * (card_h + 12) - self.scroll_y
            card_rect = pygame.Rect(cx, cy, card_w, card_h)

            if card_rect.bottom < content_rect.top or card_rect.top > content_rect.bottom:
                continue

            # Extract Name.Ext
            raw_bits = entry.bits
            name_str = "UNKNOWN"
            if len(raw_bits) >= 88:
                try:
                    name_bytes = raw_bits[0:64].tobytes()
                    ext_bytes = raw_bits[64:88].tobytes()
                    n_clean = name_bytes.decode('ascii', 'ignore').strip()
                    e_clean = ext_bytes.decode('ascii', 'ignore').strip()
                    name_str = f"{n_clean}.{e_clean}" if e_clean else n_clean
                except Exception:
                    pass

            # Detect file type / attributes
            attr_byte = int(raw_bits[88:96].to01(), 2) if len(raw_bits) >= 96 else 0
            is_dir = bool(attr_byte & 0x10)
            is_vol = bool(attr_byte & 0x08)
            is_sys = bool(attr_byte & 0x04)

            card_bg = (23, 32, 51)
            accent_col = (59, 130, 246)  # Default file blue
            type_tag = "FILE"

            if is_dir:
                accent_col = (99, 102, 241)  # Indigo
                type_tag = "DIR"
            elif is_vol:
                accent_col = (245, 158, 11)  # Amber
                type_tag = "VOL"
            elif is_sys:
                accent_col = (236, 72, 153)  # Pink
                type_tag = "SYS"

            is_hovered = (self.hovered_entry_index == idx)

            # Draw card
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=6)
            if is_hovered:
                pygame.draw.rect(surface, (255, 255, 255), card_rect, width=2, border_radius=6)
            else:
                pygame.draw.rect(surface, (51, 65, 85), card_rect, width=1, border_radius=6)

            # Top accent stripe
            top_bar = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, int(4 * self.zoom))
            pygame.draw.rect(surface, accent_col, top_bar, border_top_left_radius=6, border_top_right_radius=6)

            # Slot header line: [Entry #0] + Badge
            slot_str = f"Slot #{idx} [Offset 0x{idx*32:04X}]"
            slot_txt = small_font.render(slot_str, True, (148, 163, 184))
            surface.blit(slot_txt, (card_rect.x + 10, card_rect.y + int(8 * self.zoom)))

            # Name.Ext main label
            name_txt = font_size.render(name_str, True, (241, 245, 249))
            surface.blit(name_txt, (card_rect.x + 10, card_rect.y + int(24 * self.zoom)))

            # Subtitle summary line
            sub_str = f"Type: {type_tag} | Click to view 32-Byte Specs"
            sub_txt = small_font.render(sub_str, True, (148, 163, 184))
            surface.blit(sub_txt, (card_rect.x + 10, card_rect.y + int(52 * self.zoom)))

        surface.set_clip(None)

    def _draw_detail_view(self, surface: pygame.Surface) -> None:
        """Renders navigation header bar and detailed 32-byte dir_entry view."""
        # Background
        pygame.draw.rect(surface, (15, 23, 42), self.rect, border_radius=6)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=6)

        nav_height = int(36 * self.zoom)
        font_size = ModularFontCache.get_font(size=max(8, int(13 * self.zoom)), bold=True)

        # Top Navigation Bar
        nav_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, nav_height)
        pygame.draw.rect(surface, (30, 41, 59), nav_rect, border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.line(surface, (51, 65, 85), (nav_rect.x, nav_rect.bottom), (nav_rect.right, nav_rect.bottom), 1)

        # Back Button
        back_btn_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 4, int(180 * self.zoom), nav_height - 8)
        m_pos = pygame.mouse.get_pos() if pygame.display.get_init() else (0, 0)
        btn_bg = (59, 130, 246) if back_btn_rect.collidepoint(m_pos) else (51, 65, 85)

        pygame.draw.rect(surface, btn_bg, back_btn_rect, border_radius=4)
        pygame.draw.rect(surface, (148, 163, 184), back_btn_rect, width=1, border_radius=4)

        back_txt = font_size.render("< Back to Cluster", True, (255, 255, 255))
        surface.blit(back_txt, back_txt.get_rect(center=back_btn_rect.center))

        # Entry Title
        title_str = f"Detailed 32-Byte Specs for Entry #{self.selected_entry_index}"
        title_txt = font_size.render(title_str, True, (241, 245, 249))
        surface.blit(title_txt, (back_btn_rect.right + 16, nav_rect.y + int(8 * self.zoom)))

        # Render Active Detailed dir_entry Widget
        if self.active_detail_widget:
            self.active_detail_widget.draw(surface)


# Aliases
FATDirCluster = dir_cluster
