import sys
import subprocess
from typing import Dict, Tuple, Optional, Callable

# Ensure bitarray library is available
try:
    import bitarray
    from bitarray import bitarray as BitArrayType
except ImportError:
    print("bitarray package not found. Installing bitarray...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bitarray"])
    import bitarray
    from bitarray import bitarray as BitArrayType

import pygame


class BitLayoutMode:
    BIT_CHAR = "bit_char"    # Container for each bit with 2 chars (e.g. '0'/'1')
    BIT_COLOR = "bit_color"  # Container for each bit with 2 different colors
    HEX = "hex"              # Container for each 4 bits (nibble) as hex digit


class BitLayoutConfig:
    """Configuration class for BitLayout theme, dimensions, zoom, and modular settings."""

    def __init__(
        self,
        zoom: float = 1.0,
        min_zoom: float = 0.4,
        max_zoom: float = 3.0,
        base_row_height: int = 28,
        base_col1_width: int = 110,
        base_col2_width: int = 80,
        base_header_height: int = 28,
        show_header: bool = True,
        show_section_col: bool = True,
        show_offset_col: bool = True,
        offset_format: str = "hex",  # "hex", "dec", "byte", "bit"
        custom_offset_formatter: Optional[Callable[[int, int], str]] = None,
        bg_color: Tuple[int, int, int] = (15, 23, 42),
        border_color: Tuple[int, int, int] = (51, 65, 85),
        header_bg: Tuple[int, int, int] = (30, 41, 59),
        header_text: Tuple[int, int, int] = (148, 163, 184),
        col_bg: Tuple[int, int, int] = (23, 32, 51),
        text_color: Tuple[int, int, int] = (241, 245, 249),
        dim_text: Tuple[int, int, int] = (148, 163, 184)
    ):
        self.zoom = zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.base_row_height = base_row_height
        self.base_col1_width = base_col1_width
        self.base_col2_width = base_col2_width
        self.base_header_height = base_header_height
        self.show_header = show_header
        self.show_section_col = show_section_col
        self.show_offset_col = show_offset_col
        self.offset_format = offset_format
        self.custom_offset_formatter = custom_offset_formatter

        # Colors & Theme styling
        self.bg_color = bg_color
        self.border_color = border_color
        self.header_bg = header_bg
        self.header_text = header_text
        self.col_bg = col_bg
        self.text_color = text_color
        self.dim_text = dim_text

    def set_zoom(self, zoom: float) -> None:
        """Sets zoom factor bounded within min_zoom and max_zoom."""
        self.zoom = max(self.min_zoom, min(self.max_zoom, zoom))

    @property
    def header_height(self) -> int:
        return int(self.base_header_height * self.zoom) if self.show_header else 0

    @property
    def col1_width(self) -> int:
        return int(self.base_col1_width * self.zoom) if self.show_section_col else 0

    @property
    def col2_width(self) -> int:
        return int(self.base_col2_width * self.zoom) if self.show_offset_col else 0

    @property
    def row_height(self) -> float:
        return max(16.0, self.base_row_height * self.zoom)

    def scaled_size(self, base_size: int) -> int:
        """Scales integer dimension by zoom factor."""
        return max(8, int(base_size * self.zoom))


class ModularFontCache:
    """Font cache helper that scales font sizes dynamically with zoom."""
    _cache: Dict[Tuple[str, int, bool], pygame.font.Font] = {}

    @classmethod
    def get_font(cls, name: str = "Segoe UI", size: int = 14, bold: bool = False) -> pygame.font.Font:
        key = (name, max(8, size), bold)
        if key not in cls._cache:
            try:
                font = pygame.font.SysFont(name, key[1], bold=bold)
            except Exception:
                font = pygame.font.Font(None, key[1])
            cls._cache[key] = font
        return cls._cache[key]
