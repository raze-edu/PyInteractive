"""Storage and library persistence adapters for LogicGate_RW."""
from .library_adapter import (
    load_gui_library,
    save_component_template,
    load_groups,
    save_groups,
    get_component_group_color
)

__all__ = [
    "load_gui_library",
    "save_component_template",
    "load_groups",
    "save_groups",
    "get_component_group_color"
]
