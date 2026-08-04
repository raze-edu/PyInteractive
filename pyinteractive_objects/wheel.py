import math
from typing import List, Tuple, Optional
import pygame

class VerticalWheel:
    """A vertical scrolling wheel selector widget for Pygame.
    Displays a list of strings inside a bounded rectangle, projecting them
    on a simulated cylinder. Text labels are auto-scaled to fit inside the slots.
    Supports mouse dragging, mouse wheel, and keyboard arrow key navigation.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        items: List[str],
        visible_items: int = 5
    ):
        """Initializes the VerticalWheel.
        
        Args:
            pos: (x, y) coordinates of the top-left corner.
            size: (width, height) of the bounding box.
            items: A list of strings to populate the slots.
            visible_items: Number of slots shown simultaneously (must be odd, >= 3).
        """
        if not items:
            raise ValueError("Items list cannot be empty.")
        if visible_items < 3 or visible_items % 2 == 0:
            raise ValueError("visible_items must be an odd integer greater than or equal to 3.")
            
        self.rect = pygame.Rect(pos, size)
        self.items = items
        self.visible_items = visible_items
        
        # Selection states
        self.selected_index = 0
        self.current_scroll = 0.0  # Float representing the current scroll position
        
        # Dimensions
        self.slot_height = self.rect.height / self.visible_items
        
        # Interaction states
        self.is_dragging = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0.0
        self.scroll_direction = 0  # 1 for forward/increment, -1 for backward/decrement
        
        # Pre-calculated font sizes to fit items in their slots
        self.font_sizes = []
        self._precalculate_font_sizes()

    def _precalculate_font_sizes(self) -> None:
        """Determines the maximum font size for each item so it fits inside the center slot."""
        pygame.font.init()
        
        # Target slot boundaries (with 10% safety margin, center slot height is 50% of total height)
        max_w = int(self.rect.width * 0.9)
        max_h = int(self.rect.height * 0.5 * 0.85)
        
        self.font_sizes = []
        for item in self.items:
            # Simple linear search to find the best font size
            best_size = 12
            for size in range(12, int(self.rect.height * 0.5) * 2):
                try:
                    font = pygame.font.Font(None, size)
                except Exception:
                    font = pygame.font.SysFont("arial", size)
                    
                w, h = font.size(item)
                if w <= max_w and h <= max_h:
                    best_size = size
                else:
                    break
            self.font_sizes.append(best_size)

    def get_selected_item(self) -> str:
        """Returns the currently selected string."""
        return self.items[self.selected_index]

    def set_selected_index(self, index: int) -> None:
        """Set the selected index, wrapping around if out of bounds."""
        if len(self.items) > 0:
            self.selected_index = index % len(self.items)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes user input for scroll and selection.
        
        Args:
            event: A pygame.event.Event instance.
        """
        L = len(self.items)
        if L == 0:
            return
            
        if pygame.display.get_init():
            mouse_pos = pygame.mouse.get_pos()
        elif hasattr(event, "pos"):
            mouse_pos = event.pos
        else:
            mouse_pos = (0, 0)
        is_hovered = self.rect.collidepoint(mouse_pos)

        # Keyboard Navigation (always active if app passes events)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.scroll_direction = 1
                self.set_selected_index(self.selected_index + 1)
            elif event.key == pygame.K_UP:
                self.scroll_direction = -1
                self.set_selected_index(self.selected_index - 1)

        # Mouse Hover Scroll Wheel & Click Above/Below/Center
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if is_hovered:
                if event.button == 4:  # Scroll Up
                    self.scroll_direction = -1
                    self.set_selected_index(self.selected_index - 1)
                elif event.button == 5:  # Scroll Down
                    self.scroll_direction = 1
                    self.set_selected_index(self.selected_index + 1)
                elif event.button == 1:  # Left Click
                    local_y = event.pos[1] - self.rect.y
                    if local_y < 0.25 * self.rect.height:
                        # Clicked above the center slot: select previous
                        self.scroll_direction = -1
                        self.set_selected_index(self.selected_index - 1)
                    elif local_y > 0.75 * self.rect.height:
                        # Clicked below the center slot: select next
                        self.scroll_direction = 1
                        self.set_selected_index(self.selected_index + 1)
                    else:
                        # Clicked inside the center slot: Start Drag
                        self.is_dragging = True
                        self.drag_start_y = event.pos[1]
                        self.drag_start_scroll = self.current_scroll

        # Mouse Dragging
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                delta_y = event.pos[1] - self.drag_start_y
                # Convert pixel difference to relative slot count delta
                delta_scroll = delta_y / self.slot_height
                new_scroll = (self.drag_start_scroll - delta_scroll) % L
                
                # Deduce scroll direction from change in scroll position
                diff = new_scroll - self.current_scroll
                diff = (diff + L / 2.0) % L - L / 2.0
                if diff > 0.001:
                    self.scroll_direction = 1
                elif diff < -0.001:
                    self.scroll_direction = -1
                
                self.current_scroll = new_scroll
                # Set closest index as target selected
                self.selected_index = int(round(self.current_scroll)) % L

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_dragging:
                self.is_dragging = False
                # Snap to the nearest integer index
                self.selected_index = int(round(self.current_scroll)) % L

    def update(self, dt: float) -> None:
        """Smoothly interpolates scroll position toward target selection.
        
        Args:
            dt: Delta time in seconds since the last frame.
        """
        if self.is_dragging:
            return
            
        L = len(self.items)
        if L == 0:
            return
            
        # Modulo distance calculation to find the shortest wrap-around path
        diff = self.selected_index - self.current_scroll
        diff = (diff + L / 2.0) % L - L / 2.0
        
        # Smooth interpolation (lerp speed scales with dt, clamped at 1.0 to prevent overshoot)
        interpolation_speed = 12.0
        lerp_factor = min(1.0, interpolation_speed * dt)
        if abs(diff) > 0.001:
            self.current_scroll += diff * lerp_factor
            self.current_scroll = self.current_scroll % L
        else:
            self.current_scroll = float(self.selected_index)

    def draw(self, screen: pygame.Surface, app: "PygameApp") -> None:
        """Draws the selection wheel onto the given Pygame screen.
        
        Args:
            screen: Pygame Surface to render onto.
            app: The PygameApp instance providing colors and clock.
        """
        # Create a subsurface for clipping to our bounding rect
        try:
            wheel_surf = screen.subsurface(self.rect)
        except ValueError:
            # Subsurface can raise ValueError if rect is outside screen bounds
            # Fall back to screen with clipping rect
            original_clip = screen.get_clip()
            screen.set_clip(self.rect)
            wheel_surf = screen
        
        # Fetch theme colors
        bg_color = app.get_color("wheel_bg", (25, 25, 30, 255))
        text_color = app.get_color("secondary", (230, 230, 230, 255))
        accent_color = app.get_color("accent", (255, 65, 54, 255))
        highlight_border = app.get_color("primary", (0, 150, 255, 255))

        # Fill background of the wheel widget
        # If blending transparent surfaces, use alpha or draw solid
        wheel_rect_local = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        if wheel_surf is not screen:
            wheel_surf.fill(bg_color)
        else:
            pygame.draw.rect(screen, bg_color, self.rect)

        # Draw selection indicators (highlight brackets/bars for the center slot)
        mid_y = self.rect.height / 2.0
        h_center = self.rect.height * 0.5
        h_half = h_center / 2.0
        
        # Draw transparent background highlight block in the center slot
        highlight_bg = pygame.Surface((self.rect.width, int(h_center)), pygame.SRCALPHA)
        highlight_bg.fill((highlight_border[0], highlight_border[1], highlight_border[2], 30))
        
        if wheel_surf is not screen:
            wheel_surf.blit(highlight_bg, (0, int(mid_y - h_half)))
            pygame.draw.line(wheel_surf, highlight_border, (0, mid_y - h_half), (self.rect.width, mid_y - h_half), 2)
            pygame.draw.line(wheel_surf, highlight_border, (0, mid_y + h_half), (self.rect.width, mid_y + h_half), 2)
        else:
            screen.blit(highlight_bg, (self.rect.x, int(self.rect.y + mid_y - h_half)))
            pygame.draw.line(screen, highlight_border, (self.rect.x, self.rect.y + mid_y - h_half), (self.rect.right, self.rect.y + mid_y - h_half), 2)
            pygame.draw.line(screen, highlight_border, (self.rect.x, self.rect.y + mid_y + h_half), (self.rect.right, self.rect.y + mid_y + h_half), 2)

        # Render visible items on a curved cylinder projection
        L = len(self.items)
        k = (self.visible_items - 1) / 2.0
        h_side = (self.rect.height * 0.25) / k

        for i in range(L):
            diff = i - self.current_scroll
            # Shortest wrap-around distance
            diff = (diff + L / 2.0) % L - L / 2.0
            
            # Skip items that are too far from the visible viewport
            max_visible_diff = (self.visible_items + 1.0) / 2.0
            if abs(diff) > max_visible_diff:
                continue

            # Calculate flat vertical position relative to mid_y
            if diff >= 0:
                if diff <= 0.5:
                    y_flat = mid_y + diff * h_center
                else:
                    y_flat = mid_y + 0.5 * h_center + (diff - 0.5) * h_side
            else:
                if diff >= -0.5:
                    y_flat = mid_y + diff * h_center
                else:
                    y_flat = mid_y - 0.5 * h_center + (diff + 0.5) * h_side
            
            # Map flat offset to cylinder angle theta
            offset_y = y_flat - mid_y
            theta = (offset_y / (self.rect.height / 2.0)) * (math.pi / 2.2)
            
            # y projection on the cylindrical curve
            y_proj = mid_y + math.sin(theta) * (self.rect.height / 2.2)
            scale = max(0.0, math.cos(theta))
            
            # Opacity fades out towards the top/bottom cylinder edges
            alpha = max(0, min(255, int(255 * scale ** 1.5)))

            # Select active color based on position (closer to center = selected color)
            # If within 0.5 slots from center, blend to accent color
            dist_to_center = abs(diff)
            if dist_to_center < 0.5:
                # Blend secondary (text_color) and accent_color
                blend_ratio = 1.0 - (dist_to_center / 0.5)  # 1.0 at center, 0.0 at edge
                c_r = int(text_color[0] + (accent_color[0] - text_color[0]) * blend_ratio)
                c_g = int(text_color[1] + (accent_color[1] - text_color[1]) * blend_ratio)
                c_b = int(text_color[2] + (accent_color[2] - text_color[2]) * blend_ratio)
                c_a = int(text_color[3] + (accent_color[3] - text_color[3]) * blend_ratio)
                color = (c_r, c_g, c_b, c_a)
            else:
                color = text_color

            # Render text
            try:
                font = pygame.font.Font(None, self.font_sizes[i])
            except Exception:
                font = pygame.font.SysFont("arial", self.font_sizes[i])
                
            # Render text with alpha transparency support
            # Use pygame's AA rendering, then adjust alpha if needed
            text_surf = font.render(self.items[i], True, color[:3])
            
            # Apply scaling for perspective 3D cylinder effect
            if scale < 0.98:
                new_w = max(1, int(text_surf.get_width() * scale))
                new_h = max(1, int(text_surf.get_height() * scale))
                try:
                    text_surf = pygame.transform.smoothscale(text_surf, (new_w, new_h))
                except pygame.error:
                    text_surf = pygame.transform.scale(text_surf, (new_w, new_h))

            # Apply transparency (fade)
            text_surf.set_alpha(alpha)

            # Draw centered in the slot
            text_w = text_surf.get_width()
            text_h = text_surf.get_height()
            
            # Offset pos based on whether we are using a subsurface
            if wheel_surf is not screen:
                x_pos = (self.rect.width - text_w) / 2
                y_pos = y_proj - (text_h / 2)
                wheel_surf.blit(text_surf, (int(x_pos), int(y_pos)))
            else:
                x_pos = self.rect.x + (self.rect.width - text_w) / 2
                y_pos = self.rect.y + y_proj - (text_h / 2)
                screen.blit(text_surf, (int(x_pos), int(y_pos)))

        # Restore clipping if we fallback
        if wheel_surf is screen:
            screen.set_clip(original_clip)
            
        # Draw outer container border
        if wheel_surf is not screen:
            pygame.draw.rect(wheel_surf, highlight_border, wheel_rect_local, 2)
        else:
            pygame.draw.rect(screen, highlight_border, self.rect, 2)
