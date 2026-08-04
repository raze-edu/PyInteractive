import math
import pygame
from typing import List, Tuple, Optional

class FractionSelect:
    """An interactive widget representing a list of boolean selections.
    
    Supports two visualization modes:
    - circle: Draws a pie chart with slices.
    - square: Draws a grid of squares (only if the length is a perfect square).
    
    Interactive selection allows clicking a part to toggle it, or dragging
    across parts to toggle them as the mouse enters/re-enters.
    """

    def __init__(
        self,
        pos: Tuple[float, float],
        size: Tuple[float, float],
        length: int,
        mode: str = "circle",
        preselected: int = 0
    ):
        """Initializes the FractionSelect widget.
        
        Args:
            pos: (x, y) relative position values (typically 0.0 to 1.0).
            size: (width, height) relative size values (typically 0.0 to 1.0).
            length: Number of selection items.
            mode: Visualization mode, either "circle" or "square".
        """
        if length <= 0:
            raise ValueError("Length must be greater than 0.")

        self.pos = pos
        self.size = size
        self._selected = [False] * length
        self._mode = "circle" # default temporary to allow setter validation
        self.mode = mode  # Setter handles validation

        # Interaction states
        self.last_hovered_index: Optional[int] = None
        self.hovered_index: Optional[int] = None
        self.is_mouse_down: bool = False
        self.abs_rect: Optional[pygame.Rect] = None

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in ("circle", "square"):
            raise ValueError("Mode must be either 'circle' or 'square'.")
        if value == "square":
            N = len(self._selected)
            root = math.isqrt(N)
            if root * root != N:
                raise ValueError("Square mode is only possible if the square root of the length is an integer.")
        self._mode = value

    @property
    def selected(self) -> List[bool]:
        return self._selected

    @selected.setter
    def selected(self, value: List[bool]) -> None:
        if not isinstance(value, list):
            raise TypeError("selected must be a list of boolean values.")
        # Cast/check all items as bools
        if not all(isinstance(x, bool) for x in value):
            raise TypeError("All items in selected must be booleans.")
        if len(value) == 0:
            raise ValueError("selected list cannot be empty.")
        if self._mode == "square":
            root = math.isqrt(len(value))
            if root * root != len(value):
                raise ValueError("Square mode is only possible if the square root of the length is an integer.")
        self._selected = value

    def __len__(self) -> int:
        return len(self._selected)

    def __float__(self) -> float:
        if not self._selected:
            return 0.0
        return sum(self._selected) / len(self._selected)

    def _get_hovered_index(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Maps absolute mouse coordinates to a sub-part index if hovered."""
        if self.abs_rect is None:
            return None

        mx, my = mouse_pos
        N = len(self._selected)

        if self._mode == "circle":
            cx = self.abs_rect.centerx
            cy = self.abs_rect.centery
            r = min(self.abs_rect.width, self.abs_rect.height) / 2.0

            dx = mx - cx
            dy = my - cy
            dist = math.hypot(dx, dy)
            if dist > r:
                return None

            # Slices start at 12 o'clock (-pi/2) and go clockwise
            theta = math.atan2(dy, dx)
            angle = theta - (-math.pi / 2.0)
            angle = angle % (2.0 * math.pi)

            angle_per_slice = (2.0 * math.pi) / N
            idx = int(angle // angle_per_slice)
            return min(max(0, idx), N - 1)

        elif self._mode == "square":
            root = math.isqrt(N)
            s = min(self.abs_rect.width, self.abs_rect.height)
            sx = self.abs_rect.x + (self.abs_rect.width - s) / 2.0
            sy = self.abs_rect.y + (self.abs_rect.height - s) / 2.0

            square_rect = pygame.Rect(int(sx), int(sy), int(s), int(s))
            if not square_rect.collidepoint(mx, my):
                return None

            cell_size = s / root
            col = int((mx - sx) // cell_size)
            row = int((my - sy) // cell_size)

            col = min(max(0, col), root - 1)
            row = min(max(0, row), root - 1)

            return row * root + col

        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes mouse clicks and drags to toggle part selection states."""
        # Retrieve mouse position, preferring event position, falling back to pygame.mouse.get_pos()
        if hasattr(event, "pos"):
            mouse_pos = event.pos
        elif pygame.display.get_init():
            mouse_pos = pygame.mouse.get_pos()
        else:
            mouse_pos = (0, 0)

        # Update hover status
        self.hovered_index = self._get_hovered_index(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.hovered_index is not None:
                    self.is_mouse_down = True
                    self._selected[self.hovered_index] = not self._selected[self.hovered_index]
                    self.last_hovered_index = self.hovered_index

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_mouse_down = False
                self.last_hovered_index = None

        elif event.type == pygame.MOUSEMOTION:
            # If left mouse button is pressed, handle click-drag behavior
            is_pressed = False
            if hasattr(event, "buttons"):
                is_pressed = event.buttons[0] == 1
            else:
                is_pressed = pygame.mouse.get_pressed()[0] == 1

            if is_pressed:
                if self.hovered_index is not None:
                    # Toggle selection if moving into a different part
                    if self.hovered_index != self.last_hovered_index:
                        self._selected[self.hovered_index] = not self._selected[self.hovered_index]
                        self.last_hovered_index = self.hovered_index
                else:
                    self.last_hovered_index = None
            else:
                self.is_mouse_down = False
                self.last_hovered_index = None

    def update(self, dt: float) -> None:
        """Required by the GameObject protocol, does nothing."""
        pass

    def draw(self, screen: pygame.Surface, app: "PygameApp", rect: Optional[pygame.Rect] = None) -> None:
        """Renders the FractionSelect widget.
        
        Args:
            screen: Pygame Surface to render onto.
            app: The PygameApp instance providing colors.
            rect: Bounding rect to fit the widget inside. Defaults to screen.get_rect().
        """
        if rect is None:
            rect = screen.get_rect()

        # Fit within the outer rectangle based on relative pos and size
        abs_x = rect.x + self.pos[0] * rect.width
        abs_y = rect.y + self.pos[1] * rect.height
        abs_w = self.size[0] * rect.width
        abs_h = self.size[1] * rect.height
        self.abs_rect = pygame.Rect(int(abs_x), int(abs_y), int(abs_w), int(abs_h))

        # Fetch theme colors with defaults
        accent_color = app.get_color("accent", (255, 65, 54, 255))
        bg_color = app.get_color("wheel_bg", (25, 25, 30, 255))
        border_color = app.get_color("primary", (0, 150, 255, 255))

        N = len(self._selected)

        if self._mode == "circle":
            cx = self.abs_rect.centerx
            cy = self.abs_rect.centery
            r = min(self.abs_rect.width, self.abs_rect.height) / 2.0

            angle_per_slice = (2.0 * math.pi) / N

            # 1. Draw filled slices
            for i in range(N):
                start_angle = -math.pi / 2.0 + i * angle_per_slice
                end_angle = -math.pi / 2.0 + (i + 1) * angle_per_slice

                # Select base color
                if self._selected[i]:
                    base_col = accent_color
                else:
                    base_col = bg_color

                # Apply hover effect
                if self.hovered_index == i:
                    color = tuple(min(255, c + 35) for c in base_col)
                else:
                    color = base_col

                # Approximate pie slice with polygon points
                points = [(cx, cy)]
                num_steps = max(4, int(40 / N))
                for step in range(num_steps + 1):
                    a = start_angle + (end_angle - start_angle) * (step / num_steps)
                    px = cx + r * math.cos(a)
                    py = cy + r * math.sin(a)
                    points.append((int(px), int(py)))

                pygame.draw.polygon(screen, color[:3], points)

            # 2. Draw separators/radial lines
            for i in range(N):
                a = -math.pi / 2.0 + i * angle_per_slice
                px = cx + r * math.cos(a)
                py = cy + r * math.sin(a)
                pygame.draw.line(screen, border_color[:3], (int(cx), int(cy)), (int(px), int(py)), 1)

            # 3. Draw outer boundary circle
            pygame.draw.circle(screen, border_color[:3], (int(cx), int(cy)), int(r), 2)

        elif self._mode == "square":
            root = math.isqrt(N)
            s = min(self.abs_rect.width, self.abs_rect.height)
            sx = self.abs_rect.x + (self.abs_rect.width - s) / 2.0
            sy = self.abs_rect.y + (self.abs_rect.height - s) / 2.0

            cell_size = s / root

            # 1. Draw filled cells
            for i in range(N):
                row = i // root
                col = i % root
                cx = sx + col * cell_size
                cy = sy + row * cell_size

                cell_rect = pygame.Rect(int(cx), int(cy), int(cell_size), int(cell_size))

                # Select base color
                if self._selected[i]:
                    base_col = accent_color
                else:
                    base_col = bg_color

                # Apply hover effect
                if self.hovered_index == i:
                    color = tuple(min(255, c + 35) for c in base_col)
                else:
                    color = base_col

                pygame.draw.rect(screen, color[:3], cell_rect)

            # 2. Draw cell borders
            for i in range(N):
                row = i // root
                col = i % root
                cx = sx + col * cell_size
                cy = sy + row * cell_size

                cell_rect = pygame.Rect(int(cx), int(cy), int(cell_size), int(cell_size))
                pygame.draw.rect(screen, border_color[:3], cell_rect, 1)

            # 3. Draw outer boundary rectangle
            outer_square = pygame.Rect(int(sx), int(sy), int(s), int(s))
            pygame.draw.rect(screen, border_color[:3], outer_square, 2)

# Alias to support lowercase name directly
fraction_select = FractionSelect
