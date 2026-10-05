import json
import os
from typing import Any, Dict

class Style:
    """Manages design styles, including colors, sizes, and shapes for nodes and connections."""
    def __init__(self, style_name: str = "default", json_path: str = None):
        self.colors = {}
        self.sizes = {}
        self.shapes = {}
        
        if json_path is None:
            # Locate style.json in the same directory as this file
            dir_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(dir_path, "style.json")
            
        self.json_path = json_path
        self.load_style(style_name)

    def load_style(self, style_name: str):
        # Always load "default" first
        default_data = self._read_json_style("default")
        self.update_from_dict(default_data)
        
        # If loading a different style, override values
        if style_name != "default":
            custom_data = self._read_json_style(style_name)
            self.update_from_dict(custom_data)

    def _read_json_style(self, style_name: str) -> Dict[str, Any]:
        if not os.path.exists(self.json_path):
            return {}
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
                return data.get(style_name, {})
        except Exception as e:
            print(f"Error reading style JSON: {e}")
            return {}

    def update_from_dict(self, data: Dict[str, Any]):
        if not data:
            return
        if "colors" in data:
            self.colors.update(data["colors"])
        if "sizes" in data:
            self.sizes.update(data["sizes"])
        if "shapes" in data:
            self.shapes.update(data["shapes"])

    def get_color(self, key: str, fallback: Any = None) -> Any:
        return self.colors.get(key, fallback)

    def get_size(self, key: str, fallback: Any = None) -> Any:
        return self.sizes.get(key, fallback)

    def get_shape(self, key: str, fallback: Any = None) -> Any:
        return self.shapes.get(key, fallback)

# Shared global Style instance
shared_style = Style()
