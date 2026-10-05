"""Exercise type: Complete the equation (draggable and clickable math tiles into slots)."""
from typing import List, Optional, Tuple
import pygame
from .base import BaseExercise
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    ACCENT_BLUE_LIGHT,
    ACCENT_BLUE_DARK,
    TILE_DARK_BG,
    TILE_DARK_BEVEL,
    TILE_DARK_BORDER,
    CARD_BG,
    CARD_BORDER,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class Tile:
    """A tile representing a number or operator."""
    def __init__(self, value: str, is_operator: bool):
        self.value = value
        self.is_operator = is_operator
        self.slot_index: Optional[int] = None  # None if in bank, else index in slots
        self.current_pos: Tuple[float, float] = (0.0, 0.0)
        self.target_pos: Tuple[float, float] = (0.0, 0.0)
        self.is_dragging: bool = False
        self.drag_offset: Tuple[int, int] = (0, 0)
        self.rect = pygame.Rect(0, 0, 60, 56)

class EquationSlotsExercise(BaseExercise):
    """Complete the equation exercise with slots and tile bank."""
    
    def __init__(
        self,
        target_equation: str,   # e.g. "[ ] = 275" or "248 = [ ]"
        target_value: int,
        num_slots: int,
        bank_tokens: List[Tuple[str, bool]],  # list of (token_str, is_operator)
        title: str = "Complete the equation",
        help_tip: str = "Tap or drag numbers and signs into the empty boxes to create an equation that matches the target number."
    ):
        super().__init__(
            title=title,
            help_title="Equation Tips",
            help_tip=help_tip,
            help_faqs=[
                ("How to place tiles?", "Click any tile below to send it to the next empty box. Click a placed tile to remove it."),
                ("How to reach the total?", "Start with the largest number and subtract smaller values to reach the target.")
            ]
        )
        self.target_equation = target_equation
        self.target_value = target_value
        self.num_slots = num_slots
        
        # Initialize tiles
        self.tiles = [Tile(val, is_op) for val, is_op in bank_tokens]
        self.slots: List[Optional[Tile]] = [None] * num_slots
        self.slot_rects: List[pygame.Rect] = []
        self.active_dragging_tile: Optional[Tile] = None

    def is_ready_to_check(self) -> bool:
        # Ready if all slots are filled
        return all(s is not None for s in self.slots)

    def check(self) -> bool:
        if not self.is_ready_to_check():
            return False
            
        # Build expression from slots
        expr_str = "".join(s.value for s in self.slots if s is not None)
        try:
            # Replace unicode operators with python operators
            clean = expr_str.replace("×", "*").replace("÷", "/")
            result = eval(clean)
            self.is_solved = (result == self.target_value)
        except Exception:
            self.is_solved = False
            
        return self.is_solved

    def get_feedback(self) -> Tuple[str, str]:
        if self.is_solved:
            return ("Awesome!", "")
        return ("Not quite.", f"Target is {self.target_value}")

    def reset(self) -> None:
        super().reset()
        for t in self.tiles:
            t.slot_index = None
            t.is_dragging = False
        self.slots = [None] * self.num_slots
        self.active_dragging_tile = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # 1. Check if clicked an occupied slot
            for idx, slot_rect in enumerate(self.slot_rects):
                if slot_rect.collidepoint(pos):
                    placed_tile = self.slots[idx]
                    if placed_tile is not None:
                        # Return to bank
                        self.slots[idx] = None
                        placed_tile.slot_index = None
                        sound_manager.play_snap()
                        return

            # 2. Check if clicked a tile in the bank
            for tile in self.tiles:
                if tile.slot_index is None and tile.rect.collidepoint(pos):
                    # Start dragging or place into first empty slot
                    tile.is_dragging = True
                    tile.drag_offset = (pos[0] - tile.rect.x, pos[1] - tile.rect.y)
                    self.active_dragging_tile = tile
                    return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_dragging_tile is not None:
                tile = self.active_dragging_tile
                tile.is_dragging = False
                self.active_dragging_tile = None
                
                # Check if dropped onto a slot
                dropped_into_slot = False
                for idx, slot_rect in enumerate(self.slot_rects):
                    if slot_rect.collidepoint(event.pos):
                        # If slot is empty, put it in
                        if self.slots[idx] is None:
                            self.slots[idx] = tile
                            tile.slot_index = idx
                            dropped_into_slot = True
                            sound_manager.play_snap()
                            break
                        else:
                            # Swap or reject
                            old_tile = self.slots[idx]
                            old_tile.slot_index = None
                            self.slots[idx] = tile
                            tile.slot_index = idx
                            dropped_into_slot = True
                            sound_manager.play_snap()
                            break

                # If simply clicked without significant drag, place into next available slot
                if not dropped_into_slot:
                    # Find first free slot
                    for idx in range(self.num_slots):
                        if self.slots[idx] is None:
                            self.slots[idx] = tile
                            tile.slot_index = idx
                            sound_manager.play_snap()
                            break

        elif event.type == pygame.MOUSEMOTION:
            if self.active_dragging_tile is not None:
                self.active_dragging_tile.rect.x = event.pos[0] - self.active_dragging_tile.drag_offset[0]
                self.active_dragging_tile.rect.y = event.pos[1] - self.active_dragging_tile.drag_offset[1]

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface, area_rect: pygame.Rect) -> None:
        # Title
        title_font = get_font(32, bold=True)
        title_surf = title_font.render(self.title, True, TEXT_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(area_rect.centerx, area_rect.y + 40)))

        # Target Equation Header
        eq_font = get_font(42, bold=True)
        eq_y = area_rect.y + 115
        
        parts = self.target_equation.split("[ ]")
        box_w = 160
        box_h = 58
        
        if len(parts) == 2:
            left_text = parts[0].strip()
            right_text = parts[1].strip()
            left_surf = eq_font.render(left_text, True, TEXT_WHITE) if left_text else None
            right_surf = eq_font.render(right_text, True, TEXT_WHITE) if right_text else None
            
            total_w = box_w + 24
            if left_surf:
                total_w += left_surf.get_width() + 16
            if right_surf:
                total_w += right_surf.get_width() + 16
                
            cur_x = area_rect.centerx - total_w // 2
            if left_surf:
                screen.blit(left_surf, (cur_x, eq_y - left_surf.get_height() // 2))
                cur_x += left_surf.get_width() + 16
                
            box_rect = pygame.Rect(cur_x, eq_y - box_h // 2, box_w, box_h)
            draw_rounded_rect(screen, box_rect, (24, 39, 46), radius=12, border_color=(43, 61, 71), border_width=2)
            cur_x += box_w + 16
            
            if right_surf:
                screen.blit(right_surf, (cur_x, eq_y - right_surf.get_height() // 2))

        # Target Slots area
        slots_y = area_rect.y + 240
        slot_w = 68
        slot_h = 62
        slot_gap = 14
        total_slots_w = self.num_slots * slot_w + (self.num_slots - 1) * slot_gap
        start_slots_x = area_rect.centerx - total_slots_w // 2

        self.slot_rects = []
        for i in range(self.num_slots):
            sx = start_slots_x + i * (slot_w + slot_gap)
            s_rect = pygame.Rect(sx, slots_y, slot_w, slot_h)
            self.slot_rects.append(s_rect)

            placed = self.slots[i]
            if placed is None:
                # Draw empty dashed / dimmed slot placeholder
                draw_rounded_rect(screen, s_rect, (24, 39, 46), radius=12, border_color=(43, 61, 71), border_width=2)
            else:
                # Placed tile sits here
                if not placed.is_dragging:
                    placed.rect = s_rect
                    self._draw_single_tile(screen, placed, s_rect)

        # Bank of Available Tiles
        bank_y = area_rect.y + 360
        # Arrange bank tiles in 2 rows
        row1_tiles = [t for t in self.tiles if t.slot_index is None and not t.is_dragging]
        # Distribute into rows: operators in row 1, numbers in row 2 or balanced
        op_tiles = [t for t in row1_tiles if t.is_operator]
        num_tiles = [t for t in row1_tiles if not t.is_operator]
        
        # Display Row 1
        tw, th = 64, 58
        tgap = 12
        if op_tiles:
            r1_w = len(op_tiles) * tw + (len(op_tiles) - 1) * tgap
            r1_x = area_rect.centerx - r1_w // 2
            for i, t in enumerate(op_tiles):
                t.rect = pygame.Rect(r1_x + i * (tw + tgap), bank_y, tw, th)
                self._draw_single_tile(screen, t, t.rect)

        # Display Row 2
        if num_tiles:
            r2_w = len(num_tiles) * (tw + 10) + (len(num_tiles) - 1) * tgap
            r2_x = area_rect.centerx - r2_w // 2
            for i, t in enumerate(num_tiles):
                cur_w = max(tw, len(t.value) * 16 + 28)
                t.rect = pygame.Rect(r2_x, bank_y + th + 14, cur_w, th)
                r2_x += cur_w + tgap
                self._draw_single_tile(screen, t, t.rect)

        # Draw the actively dragged tile on top of everything
        if self.active_dragging_tile is not None:
            self._draw_single_tile(screen, self.active_dragging_tile, self.active_dragging_tile.rect)

    def _draw_single_tile(self, screen: pygame.Surface, tile: Tile, rect: pygame.Rect) -> None:
        font = get_font(26, bold=True)
        if tile.is_operator:
            # Bright cyan/blue tile
            draw_bevel_button(
                screen, rect, tile.value,
                bg_color=ACCENT_BLUE_LIGHT,
                bevel_color=ACCENT_BLUE_DARK,
                text_color=(19, 31, 36),
                font=font,
                border_radius=12,
                bevel_depth=4
            )
        else:
            # Dark slate number tile
            draw_bevel_button(
                screen, rect, tile.value,
                bg_color=TILE_DARK_BG,
                bevel_color=TILE_DARK_BEVEL,
                text_color=TEXT_WHITE,
                font=font,
                border_radius=12,
                bevel_depth=4
            )
