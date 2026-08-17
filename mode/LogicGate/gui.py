import os
import json
import pygame
from typing import Any, Tuple, List

# List of available components inside the GUI picker
# Structured as list of dicts: {"type": "input"/"output"/"gate", "name": str, "template": dict/None}
def load_gui_library(lib_path: str = 'D:\\PyInteractive\\mode\\LogicGate\\LogicComponentLib.json') -> List[dict]:
    """Loads all logic component templates from the local library file."""
    items = [
        {"type": "input", "name": "Input Node", "template": None},
        {"type": "output", "name": "Output Node", "template": None}
    ]
    if os.path.exists(lib_path):
        try:
            with open(lib_path, "r") as f:
                templates = json.load(f)
                for t in templates:
                    items.append({
                        "type": "gate",
                        "name": t.get("name", "Gate"),
                        "template": t
                    })
        except Exception as e:
            print(f"Error loading GUI library JSON: {e}")
    return items

def update_gui(app: Any, dt: float):
    """Updates the GUI animations (sliding bottom bar)."""
    mouse_pos = pygame.mouse.get_pos()
    screen_h = app.screen.get_height()

    # Hover detection at the bottom area (bottom 100 pixels)
    is_hovered = (mouse_pos[1] >= screen_h - 100)
    
    # Smooth slide-in / slide-out transition
    speed = 6.0
    if is_hovered:
        app.bar_slide_ratio = min(1.0, app.bar_slide_ratio + speed * dt)
    else:
        app.bar_slide_ratio = max(0.0, app.bar_slide_ratio - speed * dt)

def draw_gui(screen: pygame.Surface, app: Any):
    """Renders the top-right Builder transition button and the bottom hover component picker."""
    screen_w, screen_h = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()

    # 1. Draw top-right transition plus button
    btn_rect = pygame.Rect(screen_w - 60, 20, 40, 40)
    hover_plus = btn_rect.collidepoint(mouse_pos)
    btn_color = app.get_color("primary", (142, 68, 173, 255))
    if hover_plus:
        btn_color = (min(255, btn_color[0] + 30), min(255, btn_color[1] + 30), min(255, btn_color[2] + 30), 255)
        
    try:
        pygame.draw.rect(screen, btn_color[:3], btn_rect, border_radius=8)
    except TypeError:
        pygame.draw.rect(screen, btn_color[:3], btn_rect)
        
    # Draw '+' sign
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        font = pygame.font.Font(None, 36)
    except Exception:
        font = pygame.font.SysFont("arial", 36)
    plus_surf = font.render("+", True, (255, 255, 255))
    screen.blit(plus_surf, (btn_rect.centerx - plus_surf.get_width() / 2, btn_rect.centery - plus_surf.get_height() / 2))

    # 2. Draw floating placement preview if an item is selected
    if app.selected_placement_item is not None:
        item = app.selected_placement_item
        prev_surf = pygame.Surface((80, 50), pygame.SRCALPHA)
        # semi-transparent preview box
        if item["type"] == "input":
            pygame.draw.circle(prev_surf, (46, 204, 113, 150), (40, 25), 15)
        elif item["type"] == "output":
            pygame.draw.rect(prev_surf, (70, 70, 75, 150), (25, 15, 30, 20))
        else:
            t = item["template"]
            color = t.get("color", [142, 68, 173])
            pygame.draw.rect(prev_surf, (color[0], color[1], color[2], 150), (10, 10, 60, 30))
        screen.blit(prev_surf, (mouse_pos[0] - 40, mouse_pos[1] - 25))

    # 3. Draw bottom hover component bar if slide ratio is greater than zero
    if app.bar_slide_ratio > 0.0:
        bar_height = 110
        bar_y = screen_h - (bar_height * app.bar_slide_ratio)
        
        # Draw background bar panel (semi-transparent dark)
        bar_panel = pygame.Surface((screen_w, bar_height), pygame.SRCALPHA)
        bar_panel.fill((25, 25, 30, 240))
        screen.blit(bar_panel, (0, int(bar_y)))
        
        # Top neon border line
        pygame.draw.line(screen, (142, 68, 173), (0, int(bar_y)), (screen_w, int(bar_y)), 2)

        # Setup scroll buttons
        scroll_btn_w = 30
        left_btn = pygame.Rect(10, int(bar_y + 35), scroll_btn_w, 40)
        right_btn = pygame.Rect(screen_w - 40, int(bar_y + 35), scroll_btn_w, 40)
        
        # Render left/right scroll buttons
        btn_bg = (40, 40, 45)
        pygame.draw.rect(screen, btn_bg, left_btn)
        pygame.draw.rect(screen, btn_bg, right_btn)
        
        try:
            lbl_font = pygame.font.Font(None, 24)
            name_font = pygame.font.Font(None, 14)
        except Exception:
            lbl_font = pygame.font.SysFont("arial", 24)
            name_font = pygame.font.SysFont("arial", 14)
            
        lt_surf = lbl_font.render("<", True, (240, 240, 245))
        rt_surf = lbl_font.render(">", True, (240, 240, 245))
        screen.blit(lt_surf, (left_btn.centerx - lt_surf.get_width() / 2, left_btn.centery - lt_surf.get_height() / 2))
        screen.blit(rt_surf, (right_btn.centerx - rt_surf.get_width() / 2, right_btn.centery - rt_surf.get_height() / 2))

        # Render items within scroll clip boundary
        item_spacing = 110
        start_x = 55
        
        # Setup item clipping surface
        clip_w = screen_w - 100
        clip_surf = pygame.Surface((clip_w, bar_height), pygame.SRCALPHA)
        
        for i, item in enumerate(app.gui_library):
            item_x = start_x + i * item_spacing - app.bar_scroll_x
            item_rect = pygame.Rect(item_x, 15, 90, 80)
            
            # Highlight selected item
            is_selected = (app.selected_placement_item == item)
            border_color = (255, 220, 0) if is_selected else (80, 80, 85)
            
            # Hover highlight
            rel_mouse_pos = (mouse_pos[0] - 50, mouse_pos[1] - bar_y)
            is_hovered_item = item_rect.collidepoint(rel_mouse_pos)
            if is_hovered_item and not is_selected:
                border_color = (142, 68, 173)

            # Draw item thumbnail slot outline
            try:
                pygame.draw.rect(clip_surf, (35, 35, 40), (item_x, 10, 90, 60), border_radius=6)
                pygame.draw.rect(clip_surf, border_color, (item_x, 10, 90, 60), 2, border_radius=6)
            except TypeError:
                pygame.draw.rect(clip_surf, (35, 35, 40), (item_x, 10, 90, 60))
                pygame.draw.rect(clip_surf, border_color, (item_x, 10, 90, 60), 2)
            
            # Draw actual thumbnail shape inside slot
            thumb_cx = item_x + 45
            thumb_cy = 40
            
            if item["type"] == "input":
                # Green circular input node representation
                pygame.draw.circle(clip_surf, (46, 204, 113), (thumb_cx, thumb_cy), 12)
            elif item["type"] == "output":
                # Grey square output node representation
                pygame.draw.rect(clip_surf, (70, 70, 75), (thumb_cx - 12, thumb_cy - 10, 24, 20))
            else:
                # Custom gate purple template box
                color = item["template"].get("color", [142, 68, 173])
                pygame.draw.rect(clip_surf, (color[0], color[1], color[2]), (thumb_cx - 20, thumb_cy - 12, 40, 24))
            
            # Draw label below slot
            lbl_surf = name_font.render(item["name"], True, (220, 220, 225))
            clip_surf.blit(lbl_surf, (item_x + 45 - lbl_surf.get_width() / 2, 72))

        # Blit clipped item list onto screen
        screen.blit(clip_surf, (50, int(bar_y)))

def handle_gui_event(app: Any, event: pygame.event.Event) -> bool:
    """Handles click events on the bottom component picker bar and transition buttons."""
    screen_w, screen_h = app.screen.get_size()
    mouse_pos = pygame.mouse.get_pos()

    # 1. Check top-right Builder transition button click
    btn_rect = pygame.Rect(screen_w - 60, 20, 40, 40)
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if btn_rect.collidepoint(event.pos):
            app.switch_to_builder()
            return True

    # 2. Check bottom hover bar click events
    if app.bar_slide_ratio > 0.0:
        bar_height = 110
        bar_y = screen_h - (bar_height * app.bar_slide_ratio)
        
        # If event is within bottom bar Y coordinate
        if event.type == pygame.MOUSEBUTTONDOWN and event.pos[1] >= bar_y:
            # Check Left/Right scroll clicks
            left_btn = pygame.Rect(10, int(bar_y + 35), 30, 40)
            right_btn = pygame.Rect(screen_w - 40, int(bar_y + 35), 30, 40)
            
            if left_btn.collidepoint(event.pos):
                app.bar_scroll_x = max(0.0, app.bar_scroll_x - 150.0)
                return True
            elif right_btn.collidepoint(event.pos):
                max_scroll = max(0.0, (len(app.gui_library) * 110) - (screen_w - 100))
                app.bar_scroll_x = min(max_scroll, app.bar_scroll_x + 150.0)
                return True

            # Check click on item slots
            # Translate coordinates relative to content clip space Y
            rel_mouse_x = event.pos[0] - 50
            rel_mouse_y = event.pos[1] - bar_y
            
            if 0 <= rel_mouse_x <= screen_w - 100:
                start_x = 55
                item_spacing = 110
                for i, item in enumerate(app.gui_library):
                    item_x = start_x + i * item_spacing - app.bar_scroll_x
                    item_rect = pygame.Rect(item_x, 10, 90, 80) # total item slot box Y offset
                    if item_rect.collidepoint(rel_mouse_x, rel_mouse_y):
                        app.selected_placement_item = item
                        return True
            return True # Consume click inside the bottom bar Y area

        # Right click to deselect items
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            app.selected_placement_item = None
            return True

    return False
