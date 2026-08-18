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

def is_name_valid_and_unique(app: Any, node: Any, name: str) -> bool:
    """Checks if a name is valid (alphanumeric + underscore) and unique among global nodes."""
    name = name.strip()
    if not name:
        return False
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        return False
    from mode.LogicGate.Nodes import GlobalInputNode, GlobalOutputNode
    for obj in app.objects:
        if isinstance(obj, (GlobalInputNode, GlobalOutputNode)) and obj is not node:
            if obj.label == name:
                return False
    return True

def draw_left_panel(screen: pygame.Surface, app: Any):
    """Renders the scrollable nodes list on the left side of the screen."""
    from mode.LogicGate.Nodes import GlobalInputNode, GlobalOutputNode
    in_nodes = [obj for obj in app.objects if isinstance(obj, GlobalInputNode)]
    out_nodes = [obj for obj in app.objects if isinstance(obj, GlobalOutputNode)]
    nodes = sorted(in_nodes, key=lambda n: n.label) + sorted(out_nodes, key=lambda n: n.label)

    screen_w, screen_h = screen.get_size()
    PANEL_WIDTH = 300
    
    # Calculate panel X coordinate based on slide ratio
    panel_x = int(-PANEL_WIDTH + PANEL_WIDTH * app.left_panel_slide_ratio)
    
    # Draw panel surface
    panel_surf = pygame.Surface((PANEL_WIDTH, screen_h), pygame.SRCALPHA)
    # Slate dark background with high opacity
    panel_surf.fill((20, 20, 25, 245))
    
    # Render right neon border
    pygame.draw.line(panel_surf, (142, 68, 173), (PANEL_WIDTH - 2, 0), (PANEL_WIDTH - 2, screen_h), 2)
    
    # Initialize fonts
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        title_font = pygame.font.Font(None, 26)
        label_font = pygame.font.Font(None, 20)
        warn_font = pygame.font.Font(None, 14)
    except Exception:
        title_font = pygame.font.SysFont("arial", 26)
        label_font = pygame.font.SysFont("arial", 20)
        warn_font = pygame.font.SysFont("arial", 14)
        
    # Draw Title
    title_text = title_font.render("Global In/Out Nodes", True, (142, 68, 173))
    panel_surf.blit(title_text, (20, 25))
    
    # Subtitle or instructions
    sub_text = label_font.render("F2 to toggle | Click to edit name", True, (130, 130, 135))
    panel_surf.blit(sub_text, (20, 50))
    
    # Draw horizontal divider
    pygame.draw.line(panel_surf, (50, 50, 55), (15, 75), (PANEL_WIDTH - 15, 75), 1)
    
    # Setup scroll boundary and content surface
    clip_h = screen_h - 80
    clip_surf = pygame.Surface((PANEL_WIDTH, clip_h), pygame.SRCALPHA)
    
    ITEM_HEIGHT = 60
    
    for i, node in enumerate(nodes):
        item_y = i * ITEM_HEIGHT - app.left_panel_scroll_y
        
        # Calculate item rectangle relative to clip surf
        item_rect = pygame.Rect(10, int(item_y + 10), PANEL_WIDTH - 20, 48)
        
        # Highlight selected / active node
        is_active = (app.selected_node == node)
        is_editing = (getattr(app, "editing_node", None) == node)
        
        # Background fill based on state
        if is_active or is_editing:
            bg_color = (35, 30, 45, 200)
            border_color = (142, 68, 173)
        else:
            bg_color = (28, 28, 33, 150)
            border_color = (55, 55, 60)
            
        try:
            pygame.draw.rect(clip_surf, bg_color, item_rect, border_radius=6)
            pygame.draw.rect(clip_surf, border_color, item_rect, 1, border_radius=6)
        except TypeError:
            pygame.draw.rect(clip_surf, bg_color, item_rect)
            pygame.draw.rect(clip_surf, border_color, item_rect, 1)
            
        # Draw node icon type
        icon_cx = 35
        icon_cy = int(item_y + 34)
        if isinstance(node, GlobalInputNode):
            # Input: Green circle
            pygame.draw.circle(clip_surf, (46, 204, 113), (icon_cx, icon_cy), 10)
            pygame.draw.circle(clip_surf, (240, 240, 245), (icon_cx, icon_cy), 10, 1)
        else:
            # Output: Grey square
            pygame.draw.rect(clip_surf, (70, 70, 75), (icon_cx - 8, icon_cy - 8, 16, 16))
            pygame.draw.rect(clip_surf, (240, 240, 245), (icon_cx - 8, icon_cy - 8, 16, 16), 1)
            
        # Draw label/text
        text_x = 60
        text_y = int(item_y + 24)
        
        if is_editing:
            # Render editable input text box
            input_box = pygame.Rect(text_x, int(item_y + 18), PANEL_WIDTH - text_x - 20, 30)
            
            # Perform validation to show warning colors
            name_valid = is_name_valid_and_unique(app, node, app.editing_name)
            box_border_color = (46, 204, 113) if name_valid else (231, 76, 60)
            
            try:
                pygame.draw.rect(clip_surf, (15, 15, 20), input_box, border_radius=4)
                pygame.draw.rect(clip_surf, box_border_color, input_box, 1, border_radius=4)
            except TypeError:
                pygame.draw.rect(clip_surf, (15, 15, 20), input_box)
                pygame.draw.rect(clip_surf, box_border_color, input_box, 1)
                
            # Blinking cursor
            cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            txt_surf = label_font.render(app.editing_name + cursor, True, (255, 255, 255))
            clip_surf.blit(txt_surf, (input_box.x + 8, input_box.centery - txt_surf.get_height() / 2))
            
            # Show error/collision feedback if invalid
            if not name_valid and app.editing_name.strip() != "":
                warn_txt = "Name taken or invalid characters"
                # If name is blank or standard check
                if not app.editing_name.strip():
                    warn_txt = "Name cannot be empty"
                elif not app.editing_name.isalnum() and "_" not in app.editing_name:
                    warn_txt = "Use letters/numbers/underscores"
                warn_surf = warn_font.render(warn_txt, True, (231, 76, 60))
                clip_surf.blit(warn_surf, (text_x, int(item_y + 47)))
        else:
            # Static name display
            txt_surf = label_font.render(node.label, True, (240, 240, 245))
            clip_surf.blit(txt_surf, (text_x, text_y))
            
            # Pencil edit icon hint on the right
            edit_txt = label_font.render("edit", True, (80, 80, 85))
            clip_surf.blit(edit_txt, (PANEL_WIDTH - 25 - edit_txt.get_width(), text_y))
            
    # Blit clipped surface onto main panel surface
    panel_surf.blit(clip_surf, (0, 80))
    
    # Blit panel onto screen at sliding position
    screen.blit(panel_surf, (panel_x, 0))

def handle_left_panel_event(app: Any, event: pygame.event.Event) -> bool:
    """Handles event interactions for the left nodes management panel."""
    # 1. Handle typing if currently editing a node name
    if getattr(app, "editing_node", None) is not None and event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            name_to_commit = app.editing_name.strip()
            if is_name_valid_and_unique(app, app.editing_node, name_to_commit):
                app.editing_node.custom_name = name_to_commit
                if app.mode == "builder":
                    from mode.LogicGate.builder import init_builder_mode
                    init_builder_mode(app)
            app.editing_node = None
            return True
        elif event.key == pygame.K_ESCAPE:
            app.editing_node = None
            return True
        elif event.key == pygame.K_BACKSPACE:
            app.editing_name = app.editing_name[:-1]
            return True
        elif event.unicode and event.unicode.isprintable() and len(app.editing_name) < 18:
            if event.unicode.isalnum() or event.unicode == "_":
                app.editing_name += event.unicode
            return True
        return True # Consume keys while editing node name

    # 2. Check mouse events
    if event.type == pygame.MOUSEBUTTONDOWN:
        from mode.LogicGate.Nodes import GlobalInputNode, GlobalOutputNode
        in_nodes = [obj for obj in app.objects if isinstance(obj, GlobalInputNode)]
        out_nodes = [obj for obj in app.objects if isinstance(obj, GlobalOutputNode)]
        nodes = sorted(in_nodes, key=lambda n: n.label) + sorted(out_nodes, key=lambda n: n.label)
        
        # Calculate max vertical scroll
        screen_h = app.screen.get_height()
        content_h = 80 + len(nodes) * 60
        max_scroll = max(0.0, content_h - screen_h)
        
        # Click position
        mx, my = event.pos
        PANEL_WIDTH = 300
        
        # If click is inside left panel width
        if mx <= PANEL_WIDTH:
            # Check scroll wheel
            if event.button == 4: # Scroll Up
                app.left_panel_scroll_y = max(0.0, app.left_panel_scroll_y - 40.0)
                return True
            elif event.button == 5: # Scroll Down
                app.left_panel_scroll_y = min(max_scroll, app.left_panel_scroll_y + 40.0)
                return True
                
            # Check list item click (only left clicks)
            if event.button == 1:
                # Header height is 80
                if my >= 80:
                    clicked_idx = int((my - 80 + app.left_panel_scroll_y) // 60)
                    if 0 <= clicked_idx < len(nodes):
                        clicked_node = nodes[clicked_idx]
                        
                        # If clicking the already editing node, just keep editing
                        if getattr(app, "editing_node", None) is clicked_node:
                            return True
                            
                        # Commit previous edit if there was one
                        if getattr(app, "editing_node", None) is not None:
                            name_to_commit = app.editing_name.strip()
                            if is_name_valid_and_unique(app, app.editing_node, name_to_commit):
                                app.editing_node.custom_name = name_to_commit
                                if app.mode == "builder":
                                    from mode.LogicGate.builder import init_builder_mode
                                    init_builder_mode(app)
                        
                        # Start editing new node
                        app.editing_node = clicked_node
                        app.editing_name = clicked_node.label
                        
                        # Center & select on canvas if in sym mode
                        if app.mode == "sim":
                            screen_w = app.screen.get_width()
                            app.offset[0] = screen_w / 2.0 - clicked_node.center[0]
                            app.offset[1] = screen_h / 2.0 - clicked_node.center[1]
                            app.select_node(clicked_node)
                        return True
            return True # Consume click inside left panel width area
            
        else:
            # Click is OUTSIDE the left panel width
            # If editing, commit/revert and stop editing
            if getattr(app, "editing_node", None) is not None:
                name_to_commit = app.editing_name.strip()
                if is_name_valid_and_unique(app, app.editing_node, name_to_commit):
                    app.editing_node.custom_name = name_to_commit
                    if app.mode == "builder":
                        from mode.LogicGate.builder import init_builder_mode
                        init_builder_mode(app)
                app.editing_node = None
                # Do NOT return True here, so the click can interact with the canvas/builder!

    return False
