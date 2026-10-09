"""Sprite sheet icon manager for EduMath.
Loads, crops, and caches transparent glossy icons from the 4x8 UI icon spreadsheet.
"""
import os
from typing import Dict, Optional, Tuple, Union
import pygame

class IconManager:
    """Manages icon extraction and cached scaling from the 4x8 icons sprite sheet."""

    GRID_COLS = 4
    GRID_ROWS = 8
    CELL_SIZE = 128

    ICON_COORDS: Dict[str, Tuple[int, int]] = {
        # Row 0: Basic Operations
        "addition": (0, 0),
        "add": (0, 0),
        "+": (0, 0),
        "subtraction": (1, 0),
        "sub": (1, 0),
        "-": (1, 0),
        "−": (1, 0),
        "multiplication": (2, 0),
        "mul": (2, 0),
        "×": (2, 0),
        "*": (2, 0),
        "division": (3, 0),
        "div": (3, 0),
        "÷": (3, 0),
        "/": (3, 0),

        # Row 1: Graphs & Curriculum
        "coordinates": (0, 1),
        "xy": (0, 1),
        "graph": (0, 1),
        "logarithms": (1, 1),
        "log": (1, 1),
        "mixed": (2, 1),
        "mixed_ops": (2, 1),
        "curriculum": (3, 1),
        "all": (3, 1),
        "all_lessons": (3, 1),
        "grad_cap": (3, 1),
        "school": (3, 1),

        # Row 2: Difficulty & Shields
        "easy": (0, 2),
        "baby": (0, 2),
        "medium": (1, 2),
        "nerd": (1, 2),
        "glasses": (1, 2),
        "hard": (2, 2),
        "skull": (2, 2),
        "expert": (2, 2),
        "shield_ops": (3, 2),

        # Row 3: 3D Shapes
        "cylinder": (0, 3),
        "3d": (0, 3),
        "cylinder_3d": (0, 3),
        "cube": (1, 3),
        "cone": (2, 3),
        "sphere": (3, 3),

        # Row 4: Geometry & Construction
        "angle": (0, 4),
        "geometry": (0, 4),
        "theta": (0, 4),
        "compass": (1, 4),
        "ruler": (1, 4),
        "area": (2, 4),
        "square_area": (2, 4),
        "blocks": (3, 4),
        "isometric": (3, 4),

        # Row 5: Logic & Relations
        "logic": (0, 5),
        "and_gate": (0, 5),
        "tf": (1, 5),
        "boolean": (1, 5),
        "venn": (2, 5),
        "sets": (2, 5),
        "inequality": (3, 5),

        # Row 6: Statistics & Probability
        "dice": (0, 6),
        "probability": (0, 6),
        "barchart": (1, 6),
        "chart": (1, 6),
        "stats": (1, 6),
        "piechart": (2, 6),
        "pie": (2, 6),
        "distribution": (3, 6),
        "normal_dist": (3, 6),
        "bell_curve": (3, 6),

        # Row 7: Advanced Math & Symbols
        "fractions": (0, 7),
        "half": (0, 7),
        "1/2": (0, 7),
        "measurements": (1, 7),
        "units": (1, 7),
        "infinity": (2, 7),
        "inf": (2, 7),
        "root": (3, 7),
        "sqrt": (3, 7),
    }

    def __init__(self, asset_path: Optional[str] = None):
        if asset_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            asset_path = os.path.join(base_dir, "assets", "icons.jpg")
        self.asset_path = asset_path
        self._raw_icons: Dict[Tuple[int, int], pygame.Surface] = {}
        self._scaled_cache: Dict[Tuple[int, int, int, int], pygame.Surface] = {}
        self._is_loaded = False

    def load(self) -> bool:
        """Loads and prepares transparent icon surfaces from the sheet."""
        if self._is_loaded:
            return True

        if not os.path.exists(self.asset_path):
            return False

        try:
            raw_sheet = pygame.image.load(self.asset_path)
            w, h = raw_sheet.get_size()
            cols = w // self.CELL_SIZE
            rows = h // self.CELL_SIZE

            # Extract alpha transparency based on luminance
            try:
                import numpy as np
                rgb = pygame.surfarray.array3d(raw_sheet)
                max_c = np.max(rgb, axis=2).astype(np.float32)
                alpha = np.clip((max_c - 8.0) * (255.0 / 24.0), 0.0, 255.0).astype(np.uint8)

                processed_sheet = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.surfarray.blit_array(processed_sheet, rgb)
                pygame.surfarray.pixels_alpha(processed_sheet)[:] = alpha
                del processed_sheet # unlocks surface
                sheet_to_slice = pygame.Surface((w, h), pygame.SRCALPHA)
                sheet_to_slice.blit(raw_sheet, (0, 0))
                pygame.surfarray.pixels_alpha(sheet_to_slice)[:] = alpha
                del sheet_to_slice
            except Exception:
                sheet_to_slice = raw_sheet.convert_alpha() if pygame.display.get_surface() else raw_sheet.copy()
                sheet_to_slice.set_colorkey((0, 0, 0))

            # Slice each 128x128 cell into memory
            for r in range(rows):
                for c in range(cols):
                    rect = pygame.Rect(c * self.CELL_SIZE, r * self.CELL_SIZE, self.CELL_SIZE, self.CELL_SIZE)
                    icon_surf = pygame.Surface((self.CELL_SIZE, self.CELL_SIZE), pygame.SRCALPHA)
                    icon_surf.blit(raw_sheet, (0, 0), rect)
                    
                    # Apply smooth alpha if numpy is available
                    try:
                        import numpy as np
                        cell_rgb = pygame.surfarray.array3d(icon_surf)
                        cell_max = np.max(cell_rgb, axis=2).astype(np.float32)
                        cell_alpha = np.clip((cell_max - 8.0) * (255.0 / 24.0), 0.0, 255.0).astype(np.uint8)
                        pygame.surfarray.pixels_alpha(icon_surf)[:] = cell_alpha
                    except Exception:
                        icon_surf.set_colorkey((0, 0, 0))

                    self._raw_icons[(c, r)] = icon_surf

            self._is_loaded = True
            return True
        except Exception:
            return False

    def get_icon(
        self,
        key_or_coord: Union[str, Tuple[int, int]],
        size: Optional[Tuple[int, int]] = None
    ) -> Optional[pygame.Surface]:
        """Returns the requested icon, optionally scaled and cached."""
        if not self._is_loaded:
            if not self.load():
                return None

        if isinstance(key_or_coord, str):
            coord = self.ICON_COORDS.get(key_or_coord.lower())
            if coord is None:
                return None
        else:
            coord = key_or_coord

        if coord not in self._raw_icons:
            return None

        raw_surf = self._raw_icons[coord]
        if size is None or size == (self.CELL_SIZE, self.CELL_SIZE):
            return raw_surf

        cache_key = (coord[0], coord[1], size[0], size[1])
        if cache_key not in self._scaled_cache:
            scaled = pygame.transform.smoothscale(raw_surf, size)
            self._scaled_cache[cache_key] = scaled

        return self._scaled_cache[cache_key]


# Global singleton instance
icon_manager = IconManager()
