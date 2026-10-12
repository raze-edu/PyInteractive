"""EduMath: Gamified interactive educational math application powered by Pygame."""
from .app import EduApp
from .lessons import create_default_curriculum
from .generator import MathGenerator
from .math_renderer import MathRenderer, math_renderer, render_math, draw_math, get_math_size

__all__ = [
    "EduApp",
    "create_default_curriculum",
    "MathGenerator",
    "MathRenderer",
    "math_renderer",
    "render_math",
    "draw_math",
    "get_math_size",
]
