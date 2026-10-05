"""EduMath: Gamified interactive educational math application powered by Pygame."""
from .app import EduApp
from .lessons import create_default_curriculum
from .generator import MathGenerator

__all__ = [
    "EduApp",
    "create_default_curriculum",
    "MathGenerator",
]
