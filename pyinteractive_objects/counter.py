import pygame
from typing import List, Tuple, Optional
from .wheel import VerticalWheel

class MultiWheelCounter:
    """A horizontal collection of connected VerticalWheel objects that forms a counter.
    The wheels are ordered right-to-left (wheel 0 is rightmost).
    Rotations are connected: wrapping forward triggers a carry to the left neighbor,
    while wrapping backward triggers a borrow from the right neighbor.
    Displays positional values below each wheel and the total sum on the right side.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        items: List[str],
        num_wheels: int
    ):
        """Initializes the MultiWheelCounter.
        
        Args:
            pos: (x, y) coordinates of the top-left of the entire widget.
            size: (width, height) of the entire widget.
            items: The list of strings each wheel displays.
            num_wheels: The amount of wheels to display.
        """
        if num_wheels < 1:
            raise ValueError("Must have at least 1 wheel.")
            
        self.rect = pygame.Rect(pos, size)
        self.items = items
        self.num_wheels = num_wheels
        
        # Dimensions
        # Reserve 15% width on the right for the sum display
        self.sum_width = self.rect.width * 0.18
        self.wheels_width_total = self.rect.width - self.sum_width
        self.wheel_width = self.wheels_width_total / self.num_wheels
        
        # 80% height for the wheels, 20% for the individual values below
        self.wheel_height = self.rect.height * 0.78
        self.value_height = self.rect.height * 0.22
        
        # Create and position wheels (from right-to-left)
        # Wheel 0 is the rightmost wheel
        self.wheels: List[VerticalWheel] = []
        for i in range(self.num_wheels):
            # Horizontal column index from left-to-right (0 to num_wheels - 1)
            col_idx = self.num_wheels - 1 - i
            wheel_x = self.rect.x + col_idx * self.wheel_width
            wheel_y = self.rect.y
            
            # Instantiate each wheel (using 3 visible slots to fit height nicely)
            wheel = VerticalWheel(
                pos=(int(wheel_x), int(wheel_y)),
                size=(int(self.wheel_width), int(self.wheel_height)),
                items=items,
                visible_items=3
            )
            self.wheels.append(wheel)
            
        # Cache for detecting wrap-arounds
        self.last_selected_indices = [w.selected_index for w in self.wheels]

    def step_wheel_up(self, idx: int) -> None:
        """Increments the wheel index and carries over to the left neighbor if wrapped.
        
        Args:
            idx: The index of the wheel to increment (0 is rightmost).
        """
        w = self.wheels[idx]
        L = len(w.items)
        prev = w.selected_index
        w.scroll_direction = 1
        w.set_selected_index(prev + 1)
        
        # Propagate carry if wrapped from last (L-1) to first (0)
        if prev == L - 1 and w.selected_index == 0:
            left_neighbor = (idx + 1) % self.num_wheels
            self.step_wheel_up(left_neighbor)

    def step_wheel_down(self, idx: int) -> None:
        """Decrements the wheel index and borrows from the right neighbor if wrapped.
        
        Args:
            idx: The index of the wheel to decrement (0 is rightmost).
        """
        w = self.wheels[idx]
        L = len(w.items)
        prev = w.selected_index
        w.scroll_direction = -1
        w.set_selected_index(prev - 1)
        
        # Propagate borrow if wrapped from first (0) to last (L-1)
        if prev == 0 and w.selected_index == L - 1:
            right_neighbor = (idx - 1) % self.num_wheels
            self.step_wheel_down(right_neighbor)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes events and forwards key/mouse events to the appropriate wheels."""
        # Find which wheel is currently hovered by the mouse
        mouse_pos = pygame.mouse.get_pos()
        hovered_wheel = None
        for w in self.wheels:
            if w.rect.collidepoint(mouse_pos):
                hovered_wheel = w
                break

        # Forward events
        for w in self.wheels:
            # Prevent key inputs from scrolling all wheels at once:
            # only forward KEYDOWN/KEYUP to the hovered wheel (or rightmost by default)
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                if hovered_wheel:
                    if w is hovered_wheel:
                        w.handle_event(event)
                else:
                    if w is self.wheels[0]:  # Default to rightmost wheel
                        w.handle_event(event)
            else:
                # Mouse events check hover inside w.handle_event
                w.handle_event(event)

    def update(self, dt: float) -> None:
        """Updates all wheels and triggers carry/borrow propagation on value wraps."""
        # Update wheels
        for w in self.wheels:
            w.update(dt)

        # Detect wrap-arounds from input changes
        for i in range(self.num_wheels):
            w = self.wheels[i]
            prev = self.last_selected_indices[i]
            curr = w.selected_index
            if prev != curr:
                L = len(w.items)
                direction = w.scroll_direction
                
                # If direction is not specified, fall back to shortest path logic
                if direction == 0:
                    diff = (curr - prev + L/2.0) % L - L/2.0
                    direction = 1 if diff > 0 else -1
                
                # wrapped forward (last -> first)
                if direction == 1 and prev == L - 1 and curr == 0:
                    self.step_wheel_up((i + 1) % self.num_wheels)
                # wrapped backward (first -> last)
                elif direction == -1 and prev == 0 and curr == L - 1:
                    self.step_wheel_down((i - 1) % self.num_wheels)
                
                w.scroll_direction = 0  # Reset direction to neutral after processing
                break  # Process one rotation transition at a time to keep recursion clean

        # Sync the indices cache
        for i in range(self.num_wheels):
            self.last_selected_indices[i] = self.wheels[i].selected_index

    def get_wheel_value(self, idx: int) -> int:
        """Calculates the positional value of wheel idx: L^idx * v_idx.
        
        Args:
            idx: The index of the wheel (0 is rightmost).
            
        Returns:
            int: The calculated positional value.
        """
        L = len(self.items)
        v = self.wheels[idx].selected_index
        return (L ** idx) * v

    def get_total_sum(self) -> int:
        """Calculates the total decimal sum of all wheels.
        
        Returns:
            int: The total sum.
        """
        return sum(self.get_wheel_value(i) for i in range(self.num_wheels))

    def draw(self, screen: pygame.Surface, app: "PygameApp") -> None:
        """Draws the connected wheels, individual wheel values, and total sum.
        
        Args:
            screen: Pygame Surface to render onto.
            app: The PygameApp instance providing theme colors.
        """
        # Fetch theme colors
        bg_color = app.get_color("wheel_bg", (25, 25, 30, 255))
        text_color = app.get_color("secondary", (230, 230, 230, 255))
        accent_color = app.get_color("accent", (255, 65, 54, 255))
        highlight_border = app.get_color("primary", (0, 150, 255, 255))

        # 1. Draw outer boundary background for the entire widget
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, highlight_border, self.rect, 2)

        # 2. Draw each sub-wheel
        for w in self.wheels:
            w.draw(screen, app)

        # Initialize font for number drawing
        try:
            font = pygame.font.Font(None, 22)
            large_font = pygame.font.Font(None, 36)
        except Exception:
            font = pygame.font.SysFont("arial", 22)
            large_font = pygame.font.SysFont("arial", 36)

        # 3. Draw individual values below each wheel
        L = len(self.items)
        for i in range(self.num_wheels):
            w = self.wheels[i]
            val = self.get_wheel_value(i)
            
            # Position of the value slot below the wheel
            val_rect = pygame.Rect(
                w.rect.x,
                w.rect.bottom,
                w.rect.width,
                int(self.value_height)
            )
            
            # Format text: e.g. "5¹×2 = 10" or "L^i * v_i"
            # Format: e.g. "5^i * v"
            formula_str = f"{L}^{i}*{w.selected_index}"
            val_str = f"= {val}"
            
            formula_surf = font.render(formula_str, True, text_color)
            val_surf = font.render(val_str, True, accent_color)
            
            # Center the texts inside val_rect
            fx = val_rect.x + (val_rect.width - formula_surf.get_width()) / 2
            fy = val_rect.y + (val_rect.height / 2 - formula_surf.get_height())
            screen.blit(formula_surf, (int(fx), int(fy)))
            
            vx = val_rect.x + (val_rect.width - val_surf.get_width()) / 2
            vy = val_rect.y + (val_rect.height / 2)
            screen.blit(val_surf, (int(vx), int(vy)))

        # 4. Draw vertical division line before the sum display
        sum_x = self.rect.x + self.wheels_width_total
        pygame.draw.line(screen, highlight_border, (sum_x, self.rect.y), (sum_x, self.rect.bottom), 2)

        # 5. Draw the total sum display on the right
        sum_rect = pygame.Rect(
            sum_x,
            self.rect.y,
            self.sum_width,
            self.rect.height
        )
        
        # Transparent block highlighting the sum area
        highlight_bg = pygame.Surface((int(self.sum_width), self.rect.height), pygame.SRCALPHA)
        highlight_bg.fill((highlight_border[0], highlight_border[1], highlight_border[2], 15))
        screen.blit(highlight_bg, (int(sum_x), self.rect.y))

        # Title: "SUM"
        title_surf = font.render("SUM (Base 10)", True, text_color)
        tx = sum_rect.x + (sum_rect.width - title_surf.get_width()) / 2
        ty = sum_rect.y + 15
        screen.blit(title_surf, (int(tx), int(ty)))

        # Large Sum Value
        total_sum = self.get_total_sum()
        sum_surf = large_font.render(str(total_sum), True, highlight_border)
        sx = sum_rect.x + (sum_rect.width - sum_surf.get_width()) / 2
        sy = sum_rect.y + (sum_rect.height - sum_surf.get_height()) / 2
        screen.blit(sum_surf, (int(sx), int(sy)))
