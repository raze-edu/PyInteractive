import os
from typing import Any, List, Optional, Tuple, Protocol

import pygame
from .config import AppConfig

class GameObject(Protocol):
    """Protocol for objects that can be added to the PygameApp."""
    def update(self, dt: float) -> None:
        ...
        
    def draw(self, screen: pygame.Surface, app: "PygameApp") -> None:
        ...

class PygameApp:
    """A generic Pygame application runner class."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        config: Optional[AppConfig] = None,
        title: str = "Pygame Application"
    ):
        """Initializes the Pygame application.
        
        Args:
            config_path: Optional path to a JSON configuration file.
            config: Optional pre-loaded AppConfig instance.
            title: The title of the Pygame window.
        """
        # Load configuration
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.config = AppConfig.from_json(config_path)
        else:
            # Look for default config.json in working directory, else use default AppConfig
            default_path = "config.json"
            if os.path.exists(default_path):
                self.config = AppConfig.from_json(default_path)
            else:
                self.config = AppConfig()

        self.title = title
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.is_running = False
        
        # A list to store added game objects
        self.objects: List[Any] = []
        
        # Initialize internal Pygame systems
        self._init_pygame()

    def _init_pygame(self) -> None:
        """Initializes Pygame modules and sets up the screen/clock."""
        pygame.init()
        
        # Set window title
        pygame.display.set_caption(self.title)
        
        # Apply display mode and size from config
        flags = self.config.get_pygame_flags()
        self.screen = pygame.display.set_mode(self.config.size, flags)
        
        # Create game clock
        self.clock = pygame.time.Clock()

    def get_color(self, name: str, default: Optional[Tuple[int, int, int, int]] = None) -> Tuple[int, int, int, int]:
        """Retrieves a named color from the loaded color theme as an RGBA tuple.
        
        Args:
            name: The name of the color in the color theme.
            default: The fallback color if the name is not found. Defaults to magenta (255, 0, 255, 255)
                     to indicate a missing color visually if drawn.
                     
        Returns:
            Tuple[int, int, int, int]: An RGBA color tuple.
        """
        fallback = default if default is not None else (255, 0, 255, 255)
        return self.config.colortheme.get(name, fallback)

    def add_object(self, obj: Any) -> None:
        """Adds a custom object to the game. The object can optionally implement
        'update(self, dt)' and 'draw(self, screen, app)'.
        
        Args:
            obj: The object to add.
        """
        if obj not in self.objects:
            self.objects.append(obj)

    def remove_object(self, obj: Any) -> None:
        """Removes a custom object from the game.
        
        Args:
            obj: The object to remove.
        """
        if obj in self.objects:
            self.objects.remove(obj)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes a single Pygame event. Can be overridden in subclasses.
        
        Args:
            event: The pygame event.
        """
        pass

    def update(self, dt: float) -> None:
        """Updates the game state. Can be overridden in subclasses.
        
        Args:
            dt: Delta time in seconds since the last frame.
        """
        # Automatically update all objects that have an 'update' method
        for obj in self.objects:
            if hasattr(obj, "update") and callable(getattr(obj, "update")):
                # Check signature or just call with dt (accepting custom update signatures)
                try:
                    obj.update(dt)
                except Exception as e:
                    print(f"Error updating object {obj}: {e}")

    def draw(self) -> None:
        """Renders all game objects. Can be overridden in subclasses."""
        # Draw all objects that have a 'draw' method
        for obj in self.objects:
            if hasattr(obj, "draw") and callable(getattr(obj, "draw")):
                try:
                    # Provide screen and self (app) so the object can access colors or app properties
                    obj.draw(self.screen, self)
                except Exception as e:
                    print(f"Error drawing object {obj}: {e}")

    def run(self) -> None:
        """Starts and runs the main loop of the Pygame application."""
        self.is_running = True
        
        while self.is_running:
            # Calculate delta time (dt is in seconds)
            # tick() returns milliseconds elapsed
            dt = self.clock.tick(self.config.fps) / 1000.0
            
            # Event polling loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                else:
                    self.handle_event(event)
            
            # Update state
            self.update(dt)
            
            # Clear screen with background color from theme
            bg_color = self.get_color("background")
            self.screen.fill(bg_color)
            
            # Render
            self.draw()
            
            # Update display
            pygame.display.flip()
            
        # Clean up pygame on exit
        pygame.quit()
