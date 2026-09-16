import os
import json
from typing import List, Dict, Any, Optional, Tuple

from include import (
    COMPONENT_LIB,
    TableComponentLibraryEntry,
    SimComponentLibraryEntry,
    Bits
)

DEFAULT_LIB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "LogicComponentLib.json")
DEFAULT_GROUPS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "LogicComponentGroups.json")

def load_gui_library(lib_path: str = DEFAULT_LIB_PATH) -> List[Dict[str, Any]]:
    """Loads all standard array items and component templates."""
    items = [
        {"type": "array", "name": "Input Array 2H", "template": None},
        {"type": "array", "name": "Input Array 2V", "template": None},
        {"type": "array", "name": "Input Array 4H", "template": None},
        {"type": "array", "name": "Input Array 4V", "template": None},
        {"type": "array", "name": "Input Array 8H", "template": None},
        {"type": "array", "name": "Input Array 8V", "template": None},
        {"type": "array", "name": "Output Array 2H", "template": None},
        {"type": "array", "name": "Output Array 2V", "template": None},
        {"type": "array", "name": "Output Array 4H", "template": None},
        {"type": "array", "name": "Output Array 4V", "template": None},
        {"type": "array", "name": "Output Array 8H", "template": None},
        {"type": "array", "name": "Output Array 8V", "template": None},
    ]

    # Ensure primitive gates exist in COMPONENT_LIB
    if "NOT" not in COMPONENT_LIB.Table:
        TableComponentLibraryEntry("NOT", (1, 1), Bits("01"))
    if "AND" not in COMPONENT_LIB.Table:
        TableComponentLibraryEntry("AND", (2, 1), Bits("0001"))
    if "OR" not in COMPONENT_LIB.Table:
        TableComponentLibraryEntry("OR", (2, 1), Bits("0111"))
    if "XOR" not in COMPONENT_LIB.Table:
        TableComponentLibraryEntry("XOR", (2, 1), Bits("0110"))

    if os.path.exists(lib_path):
        try:
            with open(lib_path, "r") as f:
                templates = json.load(f)
            for t in templates:
                name = t.get("name", "Gate")
                items.append({
                    "type": "gate",
                    "name": name,
                    "template": t
                })
                # Register into COMPONENT_LIB Table if has logic_table
                if "logic_table" in t and name not in COMPONENT_LIB.Table:
                    t_dict = t["logic_table"]
                    n_in = len(t.get("inputs", []))
                    n_out = len(t.get("outputs", []))
                    if n_in > 0 and n_out > 0:
                        bits_str = ""
                        for i in range(2 ** n_in):
                            key = bin(i)[2:].zfill(n_in)
                            val = t_dict.get(key, "0" * n_out)
                            bits_str += str(val)
                        TableComponentLibraryEntry(name, (n_in, n_out), Bits(bits_str))
        except Exception as e:
            print(f"Error loading GUI library JSON: {e}")

    return items

def save_component_template(template: Dict[str, Any], lib_path: str = DEFAULT_LIB_PATH) -> bool:
    """Appends/updates a component template in the library JSON and syncs to root."""
    templates = []
    if os.path.exists(lib_path):
        try:
            with open(lib_path, "r") as f:
                templates = json.load(f)
        except Exception:
            templates = []

    name = template.get("name")
    templates = [t for t in templates if t.get("name") != name]
    templates.append(template)

    try:
        with open(lib_path, "w") as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"Error saving component template: {e}")
        return False

    return True

def load_groups(path: str = DEFAULT_GROUPS_PATH) -> List[Dict[str, Any]]:
    """Loads group classifications and colors from JSON."""
    groups = []
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                groups = json.load(f)
        except Exception as e:
            print(f"Error loading groups: {e}")

    # Ensure default Inputs and Outputs groups exist
    has_inputs = any(g["name"] == "Inputs" for g in groups)
    has_outputs = any(g["name"] == "Outputs" for g in groups)

    default_inputs = [
        "Input Array 2H", "Input Array 2V",
        "Input Array 4H", "Input Array 4V",
        "Input Array 8H", "Input Array 8V"
    ]
    default_outputs = [
        "Output Array 2H", "Output Array 2V",
        "Output Array 4H", "Output Array 4V",
        "Output Array 8H", "Output Array 8V"
    ]

    changed = False
    if not has_inputs:
        groups.append({
            "name": "Inputs",
            "color": [142, 68, 173],
            "components": default_inputs
        })
        changed = True

    if not has_outputs:
        groups.append({
            "name": "Outputs",
            "color": [46, 204, 113],
            "components": default_outputs
        })
        changed = True

    if changed:
        save_groups(groups, path)

    return groups

def save_groups(groups: List[Dict[str, Any]], path: str = DEFAULT_GROUPS_PATH) -> bool:
    try:
        with open(path, "w") as f:
            json.dump(groups, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving groups: {e}")
        return False

def get_component_group_color(groups: List[Dict[str, Any]], component_name: str) -> Optional[Tuple[int, int, int, int]]:
    for g in groups:
        if component_name in g.get("components", []):
            color = g.get("color")
            if color:
                if len(color) == 3:
                    return (color[0], color[1], color[2], 255)
                elif len(color) >= 4:
                    return (color[0], color[1], color[2], color[3])
    return None
