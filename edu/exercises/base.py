"""Base class and interface for educational exercises."""
from typing import List, Optional, Tuple
import pygame

class BaseExercise:
    """Base class for all interactive math learning exercises."""
    
    def __init__(
        self,
        title: str,
        help_title: str = "Need a hand?",
        help_tip: str = "Follow the instructions on the screen.",
        help_faqs: Optional[List[Tuple[str, str]]] = None
    ):
        self.title = title
        self.help_title = help_title
        self.help_tip = help_tip
        self.help_faqs = help_faqs or []
        self.is_solved = False

    def is_ready_to_check(self) -> bool:
        """Returns True if the user has provided an answer and is ready to check."""
        return True

    def check(self) -> bool:
        """Evaluates whether the user's answer is correct."""
        return False

    def get_feedback(self) -> Tuple[str, str]:
        """Returns (message, solution_hint) for the bottom banner."""
        return ("Good job!", "")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes user input events."""
        pass

    def update(self, dt: float) -> None:
        """Per-frame animation or state update."""
        pass

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        """Draws the exercise inside the main exercise area."""
        pass

    def reset(self) -> None:
        """Resets the exercise state for retry."""
        self.is_solved = False
