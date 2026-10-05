import math
from typing import List, Tuple, Dict, Optional, Union, Any
import pygame

from .config import BitLayoutConfig, BitLayoutMode, BitArrayType, bitarray
from .info import BitInfoObject, SectionLabel
from .table_elements import (
    TableFrameComponent,
    HeaderComponent,
    SectionColumnComponent,
    OffsetColumnComponent
)
from .data_cells import DataGridComponent
from .events import InteractionHandler, TooltipOverlay


class BitLayout:
    """Main object that puts all bitarr components together.
    Computes absolute sizes and positions, manages underlying data and mappings,
    and passes absolute pixel geometry to table_elements, data_cells, and event objects.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        data: Any = None,
        row_size: int = 16,
        mode: str = BitLayoutMode.BIT_CHAR,
        chars: Tuple[str, str] = ("0", "1"),
        colors_off_on: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None,
        col1_width: int = 110,
        col2_width: int = 80,
        show_header: bool = True,
        interactive: bool = True,
        zoom: float = 1.0,
        config: Optional[BitLayoutConfig] = None
    ):
        """Initializes the BitLayout widget.

        Args:
            pos: (x, y) coordinates of the top-left corner.
            size: (width, height) of the widget bounds.
            data: Data to visualize (bitarray, bytes, str, int, list of bools/ints).
            row_size: Number of bits per row (e.g. 8, 16, 32, 64).
            mode: Visualization mode ('bit_char', 'bit_color', 'hex').
            chars: Tuple of 2 characters representing 0 and 1 states.
            colors_off_on: Tuple of 2 RGB colors representing 0 and 1 states.
            col1_width: Base width of the 1st left column (Section labels).
            col2_width: Base width of the 2nd left column (Row offsets).
            show_header: Whether to render the header row with bit position indices.
            interactive: Whether clicking bit boxes toggles bit values.
            zoom: Initial zoom scaling factor (e.g. 1.0).
            config: Optional BitLayoutConfig instance for advanced modular tuning.
        """
        self.rect = pygame.Rect(pos, size)
        self.row_size = max(1, row_size)
        self.mode = mode
        self.chars = chars
        self.colors_off_on = colors_off_on or (
            (30, 41, 59),     # Dark slate (0 state)
            (16, 185, 129)    # Emerald green (1 state)
        )
        self.interactive = interactive

        # Modular Configuration
        if config is not None:
            self.config = config
        else:
            self.config = BitLayoutConfig(
                zoom=zoom,
                base_col1_width=col1_width,
                base_col2_width=col2_width,
                show_header=show_header
            )

        # Modular Sub-Component Renderers & Event Handlers
        self.frame_component = TableFrameComponent()
        self.header_component = HeaderComponent()
        self.section_component = SectionColumnComponent()
        self.offset_component = OffsetColumnComponent()
        self.grid_component = DataGridComponent()
        self.interaction_handler = InteractionHandler()
        self.tooltip_component = TooltipOverlay()

        # Internal bitarray storage
        self.bits = bitarray.bitarray()
        if data is not None:
            self.set_data(data)

        # Mapping structure for Info Objects: dict mapping bit_index -> (BitInfoObject, start_bit, end_bit)
        self.info_mappings: Dict[int, Tuple[BitInfoObject, int, int]] = {}

        # Multi-row section labels: list of SectionLabel objects
        self.section_labels: List[SectionLabel] = []

        # Scrolling
        self.scroll_y = 0.0
        self.max_scroll_y = 0.0

    @property
    def zoom(self) -> float:
        return self.config.zoom

    @zoom.setter
    def zoom(self, val: float) -> None:
        self.config.set_zoom(val)

    def zoom_in(self, step: float = 0.1) -> None:
        """Increases layout zoom level."""
        self.config.set_zoom(self.config.zoom + step)

    def zoom_out(self, step: float = 0.1) -> None:
        """Decreases layout zoom level."""
        self.config.set_zoom(self.config.zoom - step)

    def set_data(self, data: Any, length: Optional[int] = None) -> None:
        """Sets underlying bit data from bitarray, bytes, str, int, or list."""
        ba = bitarray.bitarray()
        if isinstance(data, bitarray.bitarray):
            ba = data.copy()
        elif isinstance(data, (bytes, bytearray)):
            ba.frombytes(bytes(data))
        elif isinstance(data, str):
            clean_str = "".join([c for c in data if c in ("0", "1")])
            ba = bitarray.bitarray(clean_str)
        elif isinstance(data, int):
            if data < 0:
                data = abs(data)
            bit_str = bin(data)[2:]
            if length is not None:
                bit_str = bit_str.zfill(length)
            ba = bitarray.bitarray(bit_str)
        elif isinstance(data, (list, tuple)):
            ba = bitarray.bitarray([bool(x) for x in data])
        else:
            raise TypeError(f"Unsupported data type for BitLayout: {type(data)}")

        self.bits = ba

    def get_bit(self, index: int) -> int:
        if 0 <= index < len(self.bits):
            return int(self.bits[index])
        return 0

    def set_bit(self, index: int, val: Union[bool, int]) -> None:
        if 0 <= index < len(self.bits):
            self.bits[index] = bool(val)

    def toggle_bit(self, index: int) -> None:
        if 0 <= index < len(self.bits):
            self.bits[index] = not self.bits[index]

    def set_mode(self, mode: str) -> None:
        if mode in (BitLayoutMode.BIT_CHAR, BitLayoutMode.BIT_COLOR, BitLayoutMode.HEX):
            self.mode = mode

    def assign_info(
        self,
        start_bit: int,
        end_bit: int,
        info: Union[BitInfoObject, Dict[str, Any], str]
    ) -> BitInfoObject:
        if isinstance(info, str):
            info_obj = BitInfoObject(name=info)
        elif isinstance(info, dict):
            info_obj = BitInfoObject(**info)
        elif isinstance(info, BitInfoObject):
            info_obj = info
        else:
            raise TypeError("info must be BitInfoObject, dict, or str")

        s = max(0, start_bit)
        e = min(max(s + 1, end_bit), max(len(self.bits), end_bit))
        entry = (info_obj, s, e)

        for i in range(s, e):
            self.info_mappings[i] = entry

        return info_obj

    def assign_bit_info(
        self,
        bit_index: int,
        info: Union[BitInfoObject, Dict[str, Any], str]
    ) -> BitInfoObject:
        return self.assign_info(bit_index, bit_index + 1, info)

    def clear_info_mappings(self) -> None:
        self.info_mappings.clear()

    def add_section_label(
        self,
        start_row: int,
        end_row: int,
        text: str,
        color: Optional[Tuple[int, int, int]] = None
    ) -> SectionLabel:
        lbl = SectionLabel(start_row, end_row, text, color)
        self.section_labels.append(lbl)
        return lbl

    def clear_section_labels(self) -> None:
        self.section_labels.clear()

    def get_info_at_bit(self, bit_index: int) -> Optional[Tuple[BitInfoObject, int, int]]:
        return self.info_mappings.get(bit_index)

    @property
    def total_rows(self) -> int:
        total_bits = len(self.bits)
        if total_bits == 0:
            return 1
        return math.ceil(total_bits / self.row_size)

    @property
    def hovered_bit_index(self) -> Optional[int]:
        return self.interaction_handler.hovered_bit_index

    @property
    def hovered_info_tuple(self) -> Optional[Tuple[BitInfoObject, int, int]]:
        return self.interaction_handler.hovered_info_tuple

    def handle_event(self, event: pygame.event.Event) -> None:
        """Main object passes event and absolute bounds to interaction handler."""
        grid_rect, row_height, box_width, boxes_per_row = self._compute_absolute_grid_geometry()

        self.scroll_y, _ = self.interaction_handler.process_event(
            event=event,
            abs_layout_rect=self.rect,
            config=self.config,
            interactive=self.interactive,
            scroll_y=self.scroll_y,
            max_scroll_y=self.max_scroll_y,
            toggle_bit_callback=self.toggle_bit,
            zoom_in_callback=self.zoom_in,
            zoom_out_callback=self.zoom_out
        )

        self.interaction_handler.update_hover(
            abs_layout_rect=self.rect,
            abs_grid_rect=grid_rect,
            config=self.config,
            bits=self.bits,
            mode=self.mode,
            row_size=self.row_size,
            total_rows=self.total_rows,
            row_height=row_height,
            box_width=box_width,
            boxes_per_row=boxes_per_row,
            scroll_y=self.scroll_y,
            info_mappings=self.info_mappings
        )

    def _compute_absolute_grid_geometry(self) -> Tuple[pygame.Rect, float, float, int]:
        """Main object calculates absolute pixel geometry coordinates."""
        h_height = self.config.header_height
        c1_width = self.config.col1_width
        c2_width = self.config.col2_width

        grid_x = self.rect.x + c1_width + c2_width
        grid_y = self.rect.y + h_height
        grid_w = max(10.0, float(self.rect.width - (c1_width + c2_width)))
        grid_h = max(10.0, float(self.rect.height - h_height))

        boxes_per_row = self.row_size if self.mode != BitLayoutMode.HEX else math.ceil(self.row_size / 4)
        box_width = grid_w / max(1, boxes_per_row)
        row_height = self.config.row_height

        return pygame.Rect(grid_x, grid_y, int(grid_w), int(grid_h)), row_height, box_width, boxes_per_row

    def draw(self, surface: pygame.Surface) -> None:
        """Main object computes absolute values and delegates drawing to sub-components."""
        # 1. Outer Frame & Background
        self.frame_component.draw(surface, self.rect, self.config)

        h_height = self.config.header_height
        grid_rect, row_height, box_width, boxes_per_row = self._compute_absolute_grid_geometry()

        # Update max scroll
        total_content_height = self.total_rows * row_height
        self.max_scroll_y = max(0.0, total_content_height - grid_rect.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll_y)

        # Compute absolute clip rect for scrollable area
        grid_clip_rect = pygame.Rect(self.rect.x, self.rect.y + h_height, self.rect.width, self.rect.height - h_height)
        surface.set_clip(grid_clip_rect)

        # 2. Draw Column 1 Section Labels
        abs_col1_rect = pygame.Rect(self.rect.x, self.rect.y + h_height, self.config.col1_width, grid_clip_rect.height)
        self.section_component.draw(
            surface=surface,
            abs_col_rect=abs_col1_rect,
            config=self.config,
            section_labels=self.section_labels,
            total_rows=self.total_rows,
            row_height=row_height,
            scroll_y=self.scroll_y
        )

        # 3. Draw Column 2 Row Offsets
        abs_col2_rect = pygame.Rect(self.rect.x + self.config.col1_width, self.rect.y + h_height, self.config.col2_width, grid_clip_rect.height)
        self.offset_component.draw(
            surface=surface,
            abs_col_rect=abs_col2_rect,
            config=self.config,
            total_rows=self.total_rows,
            row_size=self.row_size,
            row_height=row_height,
            scroll_y=self.scroll_y
        )

        # 4. Draw Data Cells Grid
        self.grid_component.draw(
            surface=surface,
            abs_grid_rect=grid_rect,
            config=self.config,
            bits=self.bits,
            row_size=self.row_size,
            mode=self.mode,
            chars=self.chars,
            colors_off_on=self.colors_off_on,
            info_mappings=self.info_mappings,
            hovered_bit_index=self.hovered_bit_index,
            hovered_info_tuple=self.hovered_info_tuple,
            total_rows=self.total_rows,
            row_height=row_height,
            box_width=box_width,
            boxes_per_row=boxes_per_row,
            scroll_y=self.scroll_y
        )

        # Reset clip
        surface.set_clip(None)

        # 5. Draw Header Row
        abs_header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, h_height)
        self.header_component.draw(
            surface=surface,
            abs_header_rect=abs_header_rect,
            config=self.config,
            box_width=box_width,
            boxes_per_row=boxes_per_row,
            mode=self.mode
        )

        # 6. Draw Hover Tooltip Overlay
        if self.hovered_info_tuple is not None:
            self.tooltip_component.draw(
                surface=surface,
                hovered_info_tuple=self.hovered_info_tuple,
                bits=self.bits,
                mouse_pos=self.interaction_handler.mouse_pos,
                config=self.config
            )
