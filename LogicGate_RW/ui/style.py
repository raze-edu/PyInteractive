import json
import os
from typing import Any, Dict, Tuple, Optional
from include import Color

class UIColor(Color):
    """Subclass of include.Color that robustly handles both *args and **kwargs arithmetic."""
    def __init__(self, *args, **kwargs):
        if kwargs:
            for k in self.__slots__:
                setattr(self, k, kwargs.get(k, 0 if k != 'A' else 255))
        elif args:
            for i, k in enumerate(self.__slots__):
                val = args[i] if i < len(args) else (0 if k != 'A' else 255)
                setattr(self, k, val)
        else:
            for k in self.__slots__:
                setattr(self, k, 0 if k != 'A' else 255)

    def __add__(self, other):
        return UIColor(*[getattr(self, k) + getattr(other, k) for k in self.__slots__])

    def __sub__(self, other):
        return UIColor(*[getattr(self, k) - getattr(other, k) for k in self.__slots__])

    def __mul__(self, other):
        return UIColor(*[getattr(self, k) * other for k in self.__slots__])

    def __truediv__(self, other):
        return UIColor(*[0 if getattr(self, k) == 0 else getattr(self, k) / other for k in self.__slots__])

class Style:
    """Style manager that utilizes UIColor for sleek, dynamic color math and fading."""

    def __init__(self, style_name: str = "default", json_path: Optional[str] = None):
        self.colors: Dict[str, UIColor] = {}
        self.sizes: Dict[str, Any] = {}
        self.shapes: Dict[str, Any] = {}

        if json_path is None:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(dir_path, "style.json")

        self.json_path = json_path
        self._init_defaults()
        self.load_style(style_name)

    def _init_defaults(self):
        default_colors = {
            "connection_active": Color(R=0, G=255, B=240, A=255),
            "connection_inactive": Color(R=80, G=80, B=95, A=255),
            "connection_selected": Color(R=255, G=220, B=0, A=255),
            "node_active_fill": Color(R=46, G=204, B=113, A=255),
            "node_inactive_fill": Color(R=60, G=60, B=65, A=255),
            "node_active_border": Color(R=50, G=255, B=120, A=255),
            "node_inactive_border": Color(R=140, G=140, B=150, A=255),
            "node_selected_border": Color(R=255, G=220, B=0, A=255),
            "node_active_glow": Color(R=46, G=204, B=113, A=40),
            "node_text": Color(R=240, G=240, B=245, A=255),
            "logic_component_fill": Color(R=142, G=68, B=173, A=255),
            "background": Color(R=15, G=15, B=20, A=255),
            "panel_bg": Color(R=25, G=25, B=32, A=240),
            "panel_border": Color(R=50, G=50, B=65, A=255),
            "primary": Color(R=142, G=68, B=173, A=255),
            "secondary": Color(R=155, G=89, B=182, A=255)
        }
        self.colors.update(default_colors)

        self.sizes = {
            "input_node_size": 0.013,
            "output_node_size": 0.013,
            "node_size": 0.013,
            "connection_active_thickness": 4,
            "connection_inactive_thickness": 2,
            "glow_radius_multiplier": 1.5,
            "connector_handle_radius": 6,
            "font_size_global": 14,
            "font_size_component": 16,
            "font_size_subnode": 12,
            "font_size_array": 12
        }

        self.shapes = {
            "input_node_shape": "circle",
            "output_node_shape": "circle",
            "node_shape": "circle"
        }

    def load_style(self, style_name: str):
        if not os.path.exists(self.json_path):
            return
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
            s_data = data.get(style_name, {})
            if "colors" in s_data:
                for k, v in s_data["colors"].items():
                    if isinstance(v, (list, tuple)) and len(v) >= 3:
                        a = v[3] if len(v) > 3 else 255
                        self.colors[k] = Color(R=v[0], G=v[1], B=v[2], A=a)
            if "sizes" in s_data:
                self.sizes.update(s_data["sizes"])
            if "shapes" in s_data:
                self.shapes.update(s_data["shapes"])
        except Exception as e:
            print(f"Error loading style JSON: {e}")

    def get_color_obj(self, key: str, fallback: Optional[Color] = None) -> Color:
        return self.colors.get(key, fallback or Color(R=255, G=255, B=255, A=255))

    def get_color(self, key: str, fallback: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> Tuple[int, int, int, int]:
        c = self.colors.get(key)
        if c is not None:
            return c.__tuple__()
        return fallback

    def get_size(self, key: str, fallback: Any = None) -> Any:
        return self.sizes.get(key, fallback)

    def get_shape(self, key: str, fallback: Any = None) -> Any:
        return self.shapes.get(key, fallback)

shared_style = Style()
