import pygame
from typing import List, Tuple, Any, Optional

class StringInput:
    """A single-line text input widget for Pygame.
    
    Supports focus state, printable characters, backspace, and a blinking cursor.
    The text is kept inside bounds using a max_length constraint.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        max_length: int = 15,
        placeholder: str = "Type here..."
    ):
        """Initializes the StringInput.
        
        Args:
            pos: (x, y) coordinates of the top-left corner.
            size: (width, height) of the input box.
            max_length: Maximum allowed string length.
            placeholder: Text displayed when input is empty and not focused.
        """
        self.rect = pygame.Rect(pos, size)
        self.max_length = max_length
        self.placeholder = placeholder
        
        self.text = ""
        self.is_focused = False
        
        # Cursor blink animation states
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes click and keyboard input events.
        
        Args:
            event: A pygame.event.Event instance.
        """
        # Mouse Focus Check
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Get mouse position, fall back to event position if headless testing
                if pygame.display.get_init():
                    mouse_pos = pygame.mouse.get_pos()
                else:
                    mouse_pos = getattr(event, "pos", (0, 0))
                
                self.is_focused = self.rect.collidepoint(mouse_pos)
                if self.is_focused:
                    self.cursor_visible = True
                    self.cursor_timer = 0.0

        # Keyboard Inputs (only active when focused)
        elif event.type == pygame.KEYDOWN and self.is_focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.cursor_visible = True
                self.cursor_timer = 0.0
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                self.is_focused = False
            else:
                # Add printable character if length restriction allows
                if event.unicode and event.unicode.isprintable() and event.unicode != "":
                    if len(self.text) < self.max_length:
                        self.text += event.unicode
                        self.cursor_visible = True
                        self.cursor_timer = 0.0

    def update(self, dt: float) -> None:
        """Blinks the cursor when the input is focused.
        
        Args:
            dt: Delta time in seconds.
        """
        if not self.is_focused:
            return
            
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer -= 0.5
            self.cursor_visible = not self.cursor_visible

    def draw(self, screen: pygame.Surface, app: "PygameApp") -> None:
        """Renders the text box, input text, and cursor on screen.
        
        Args:
            screen: Pygame Surface to render onto.
            app: The PygameApp instance providing colors.
        """
        # Fetch theme colors
        bg_color = app.get_color("wheel_bg", (25, 25, 30, 255))
        text_color = app.get_color("secondary", (230, 230, 230, 255))
        accent_color = app.get_color("accent", (255, 65, 54, 255))
        border_active = app.get_color("primary", (0, 150, 255, 255))
        
        # Border inactive: a darker variation
        border_inactive = (border_active[0] // 2, border_active[1] // 2, border_active[2] // 2, 255)

        # Draw box background
        pygame.draw.rect(screen, bg_color, self.rect)
        
        # Draw frame border based on focus state
        current_border = border_active if self.is_focused else border_inactive
        pygame.draw.rect(screen, current_border, self.rect, 2)

        # Calculate fitted font size based on input height
        font_h = int(self.rect.height * 0.55)
        try:
            font = pygame.font.Font(None, font_h)
        except Exception:
            font = pygame.font.SysFont("arial", font_h)

        # Draw placeholder or active text
        if self.text == "" and not self.is_focused:
            # Draw placeholder (semi-transparent gray text)
            placeholder_color = (text_color[0] // 2, text_color[1] // 2, text_color[2] // 2, 120)
            text_surf = font.render(self.placeholder, True, placeholder_color[:3])
        else:
            text_surf = font.render(self.text, True, text_color[:3])
            
        # Left-align text with a 10px margin and center vertically
        tx = self.rect.x + 10
        ty = self.rect.y + (self.rect.height - text_surf.get_height()) / 2
        screen.blit(text_surf, (tx, int(ty)))

        # Draw blinking cursor if focused
        if self.is_focused and self.cursor_visible:
            # Measure text width to position cursor
            text_w = font.size(self.text)[0]
            cursor_x = tx + text_w + 2
            
            # Position cursor line
            cy_start = ty
            cy_end = ty + text_surf.get_height()
            
            pygame.draw.line(screen, accent_color, (cursor_x, cy_start), (cursor_x, cy_end), 2)


class Slider:
    """A horizontal selection slider widget for Pygame.
    
    Lets users drag a handle knob or click along a track to select a value
    from a discrete list of choices.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        values: List[Any],
        default_index: int = 0
    ):
        """Initializes the Slider.
        
        Args:
            pos: (x, y) coordinates of the top-left corner.
            size: (width, height) of the slider bounding box.
            values: A list of discrete values to choose from.
            default_index: The starting selected value index.
        """
        if not values:
            raise ValueError("Values list cannot be empty.")
            
        self.rect = pygame.Rect(pos, size)
        self.values = values
        self.selected_index = max(0, min(len(values) - 1, default_index))
        
        # Interaction states
        self.is_dragging = False
        
        # Handle dimensions
        self.handle_radius = int(self.rect.height * 0.25)
        if self.handle_radius < 6:
            self.handle_radius = 6

    def _update_index_from_mouse(self, mouse_x: float) -> None:
        """Maps a mouse coordinate to the nearest value index."""
        x_start = self.rect.x + self.handle_radius
        x_end = self.rect.right - self.handle_radius
        slider_width = x_end - x_start
        
        if slider_width <= 0:
            self.selected_index = 0
            return
            
        clamped_x = max(x_start, min(x_end, mouse_x))
        fraction = (clamped_x - x_start) / slider_width
        self.selected_index = int(round(fraction * (len(self.values) - 1)))

    def get_value(self) -> Any:
        """Returns the currently selected value."""
        return self.values[self.selected_index]

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes mouse clicks and dragging gestures.
        
        Args:
            event: A pygame.event.Event instance.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Get mouse position, fall back to event position if headless testing
                if pygame.display.get_init():
                    mouse_pos = pygame.mouse.get_pos()
                else:
                    mouse_pos = getattr(event, "pos", (0, 0))
                
                # Check collision with bounding box
                if self.rect.collidepoint(mouse_pos):
                    self.is_dragging = True
                    self._update_index_from_mouse(mouse_pos[0])

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                if pygame.display.get_init():
                    mouse_x = pygame.mouse.get_pos()[0]
                else:
                    mouse_x = event.pos[0]
                self._update_index_from_mouse(mouse_x)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_dragging:
                self.is_dragging = False

    def update(self, dt: float) -> None:
        """Conforms to GameObject protocol (no periodic logic needed)."""
        pass

    def draw(self, screen: pygame.Surface, app: "PygameApp") -> None:
        """Renders the slider track, progress line, and handle.
        Args:
            screen: Pygame Surface to render onto.
            app: The PygameApp instance providing colors.
        """
        # Fetch theme colors
        text_color = app.get_color("secondary", (230, 230, 230, 255))
        accent_color = app.get_color("accent", (255, 65, 54, 255))
        primary_color = app.get_color("primary", (0, 150, 255, 255))

        # Track parameters
        x_start = self.rect.x + self.handle_radius
        x_end = self.rect.right - self.handle_radius
        slider_width = x_end - x_start
        
        # Center track vertically
        track_y = self.rect.y + self.rect.height * 0.4
        track_thickness = 6

        # Draw background track line (muted gray/secondary)
        muted_track_color = (text_color[0] // 3, text_color[1] // 3, text_color[2] // 3)
        pygame.draw.line(screen, muted_track_color, (x_start, int(track_y)), (x_end, int(track_y)), track_thickness)

        # Calculate handle position
        if len(self.values) > 1:
            fraction = self.selected_index / (len(self.values) - 1)
        else:
            fraction = 0.0
        handle_x = x_start + fraction * slider_width

        # Draw filled active track (primary color)
        if fraction > 0:
            pygame.draw.line(screen, primary_color, (x_start, int(track_y)), (int(handle_x), int(track_y)), track_thickness)

        # Draw handle glow if dragging (premium feel)
        if self.is_dragging:
            glow_surf = pygame.Surface((self.handle_radius * 4, self.handle_radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (primary_color[0], primary_color[1], primary_color[2], 50),
                (self.handle_radius * 2, self.handle_radius * 2),
                self.handle_radius * 1.6
            )
            screen.blit(glow_surf, (int(handle_x - self.handle_radius * 2), int(track_y - self.handle_radius * 2)))

        # Draw handle body
        pygame.draw.circle(screen, accent_color, (int(handle_x), int(track_y)), self.handle_radius)
        # Inner white dot on handle
        pygame.draw.circle(screen, (255, 255, 255), (int(handle_x), int(track_y)), self.handle_radius // 3)

        # Draw active selected value text below the track
        try:
            font = pygame.font.Font(None, int(self.rect.height * 0.4))
        except Exception:
            font = pygame.font.SysFont("arial", int(self.rect.height * 0.4))
            
        val_surf = font.render(str(self.get_value()), True, text_color)
        vx = handle_x - val_surf.get_width() / 2
        vy = self.rect.y + self.rect.height * 0.7
        screen.blit(val_surf, (int(vx), int(vy)))
