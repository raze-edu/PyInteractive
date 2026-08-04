import json
import os
from typing import Dict, List, Tuple, Union

class ConfigValidationError(ValueError):
    """Raised when the configuration validation fails."""
    pass

class AppConfig:
    """Configuration class for the Pygame application."""
    
    # Supported display modes mapped to their display mode string
    DISPLAY_MODES = ["WINDOWED", "FULLSCREEN", "RESIZABLE", "NOFRAME", "SCALED"]

    def __init__(
        self,
        size: Tuple[int, int] = (800, 600),
        displaymode: str = "WINDOWED",
        fps: int = 60,
        colortheme: Dict[str, Tuple[int, int, int, int]] = None
    ):
        self.size = size
        self.displaymode = displaymode.upper() if isinstance(displaymode, str) else displaymode
        self.fps = fps
        self.colortheme = colortheme or {}
        self.validate()

    def validate(self) -> None:
        """Validates that configuration properties are of correct type and range."""
        # Validate size
        if not isinstance(self.size, (list, tuple)) or len(self.size) != 2:
            raise ConfigValidationError("size must be a list or tuple of 2 elements [width, height].")
        if not all(isinstance(x, int) and x > 0 for x in self.size):
            raise ConfigValidationError("size elements (width and height) must be positive integers.")
        self.size = tuple(self.size)

        # Validate displaymode
        if not isinstance(self.displaymode, str) or self.displaymode.upper() not in self.DISPLAY_MODES:
            raise ConfigValidationError(
                f"displaymode must be one of {self.DISPLAY_MODES}. Got: {self.displaymode}"
            )
        self.displaymode = self.displaymode.upper()

        # Validate fps
        if not isinstance(self.fps, int) or self.fps <= 0:
            raise ConfigValidationError("fps must be a positive integer.")

        # Validate colortheme
        if not isinstance(self.colortheme, dict):
            raise ConfigValidationError("colortheme must be a dictionary.")
        
        validated_theme = {}
        for name, color in self.colortheme.items():
            if not isinstance(name, str):
                raise ConfigValidationError("colortheme keys must be strings (color names).")
            if not isinstance(color, (list, tuple)) or len(color) != 4:
                raise ConfigValidationError(
                    f"Color '{name}' must be an RGBA list or tuple of 4 elements [R, G, B, A]. Got: {color}"
                )
            if not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                raise ConfigValidationError(
                    f"Color '{name}' RGBA elements must be integers between 0 and 255. Got: {color}"
                )
            validated_theme[name] = tuple(color)
        
        # Ensure a background color is defined
        if "background" not in validated_theme:
            validated_theme["background"] = (30, 30, 35, 255)
            
        self.colortheme = validated_theme

    def get_pygame_flags(self) -> int:
        """Resolves the displaymode string into actual Pygame display flags."""
        import pygame
        
        mode_flags = {
            "WINDOWED": 0,
            "FULLSCREEN": pygame.FULLSCREEN,
            "RESIZABLE": pygame.RESIZABLE,
            "NOFRAME": pygame.NOFRAME,
            "SCALED": pygame.SCALED
        }
        return mode_flags.get(self.displaymode, 0)

    @classmethod
    def from_json(cls, file_path: str) -> "AppConfig":
        """Loads and parses the configuration from a JSON file.
        
        Args:
            file_path: Absolute or relative path to the configuration JSON file.
            
        Returns:
            AppConfig: The parsed and validated AppConfig object.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON format: {e.msg} on line {e.lineno}") from e
        except Exception as e:
            raise ConfigValidationError(f"Error reading configuration file: {e}") from e

        # Extract values with fallbacks or pass directly for validation
        size = data.get("size", (800, 600))
        displaymode = data.get("displaymode", "WINDOWED")
        fps = data.get("fps", 60)
        colortheme = data.get("colortheme", {})

        return cls(size=size, displaymode=displaymode, fps=fps, colortheme=colortheme)
