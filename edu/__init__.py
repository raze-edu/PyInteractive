"""EduMath: Gamified interactive educational math application powered by Pygame."""
from .app import EduApp
from .lessons import create_default_curriculum
from .generator import MathGenerator
from .math_renderer import MathRenderer, math_renderer, render_math, draw_math, get_math_size

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "EduApp",
    "create_default_curriculum",
    "MathGenerator",
    "MathRenderer",
    "math_renderer",
    "render_math",
    "draw_math",
    "get_math_size",
]
