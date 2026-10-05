from typing import Tuple, Dict, Optional, Any
from .config import BitArrayType


class BitInfoObject:
    """Represents metadata attached to a specific bit or slice of bits in BitLayout.
    
    Attributes:
        name: Name or label of the field/object.
        description: Extended description displayed in the hover frame.
        color: Accent color (RGB) used for visual cues and borders.
        metadata: Key-value metadata pairs to render in hover tooltip.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        color: Optional[Tuple[int, int, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.color = color or (99, 102, 241)  # Default indigo accent color
        self.metadata = metadata or {}

    def get_formatted_value(self, bits: BitArrayType) -> str:
        """Returns formatted string representation of the bit slice value."""
        if len(bits) == 0:
            return ""
        bit_str = bits.to01()
        if len(bits) <= 64:
            try:
                val_int = int(bit_str, 2)
                hex_str = f"0x{val_int:X}"
                return f"{bit_str} (Dec: {val_int}, Hex: {hex_str})"
            except ValueError:
                pass
        return bit_str


class SectionLabel:
    """Represents a section label spanning multiple rows in the 1st left column."""

    def __init__(
        self,
        start_row: int,
        end_row: int,
        text: str,
        color: Optional[Tuple[int, int, int]] = None
    ):
        self.start_row = start_row
        self.end_row = end_row
        self.text = text
        self.color = color or (148, 163, 184)
