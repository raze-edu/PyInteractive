import os
import json
import math
import itertools
import pygame
from typing import Any, Tuple, List
from pyinteractive_objects.nodes import GlobalInputNode, GlobalOutputNode


def init_builder_mode(app: Any):
    """Initializes the Builder Mode variables by scanning the canvas."""
    # Find all inputs and outputs on the canvas, sorted alphabetically
    app.builder_inputs = [obj for obj in app.objects if isinstance(obj, GlobalInputNode)]
    app.builder_outputs = [obj for obj in app.objects if isinstance(obj, GlobalOutputNode)]
    app.builder_inputs.sort(key=lambda n: n.label)
    app.builder_outputs.sort(key=lambda n: n.label)

    app.builder_error = None
    if not app.builder_inputs or not app.builder_outputs:
        app.builder_error = "Circuit must contain at least 1 input node and 1 output node!"

    # Default settings
    app.builder_name = "MY_GATE"
    app.builder_width = 100
    app.builder_height = 80
    app.builder_color = [142, 68, 173]  # Vibrant purple
    app.builder_focus = None
    app.builder_dragging_node = None  # Tuple: ("in"/"out", index)
    app.builder_dragging_slider = None

    # Distribute inputs along left edge, outputs along right edge
    app.builder_in_positions = []
    num_inputs = len(app.builder_inputs)
    for i, inp in enumerate(app.builder_inputs):
        spacing = app.builder_height / (num_inputs + 1)
        app.builder_in_positions.append({
            "name": inp.label,
            "rel_x": 0.0,
            "rel_y": (i + 1) * spacing
        })

    app.builder_out_positions = []
    num_outputs = len(app.builder_outputs)
    for i, out in enumerate(app.builder_outputs):
        spacing = app.builder_height / (num_outputs + 1)
        app.builder_out_positions.append({
            "name": out.label,
            "rel_x": float(app.builder_width),
            "rel_y": (i + 1) * spacing
        })

def draw_slider(screen: pygame.Surface, x: int, y: int, w: int, val: float, min_val: float, max_val: float, label: str, font: pygame.font.Font, color: Tuple[int, int, int]) -> pygame.Rect:
    """Helper to draw a slider and return the collision bounding rect for interaction."""
    # Label and value text
    lbl_surf = font.render(f"{label}: {int(val)}", True, (230, 230, 235))
    screen.blit(lbl_surf, (x, y - 20))

    # Track line
    pygame.draw.line(screen, (60, 60, 65), (x, y), (x + w, y), 6)

    # Handle circle Y
    hx = x + int(w * (val - min_val) / (max_val - min_val))
    pygame.draw.circle(screen, color, (hx, y), 10)
    pygame.draw.circle(screen, (240, 240, 245), (hx, y), 10, 2)
    
    return pygame.Rect(x - 10, y - 10, w + 20, 20)

def snap_to_outline(mx: float, my: float, pw: float, ph: float) -> Tuple[float, float]:
    """Snaps canvas-space coordinates (mx, my) to the nearest border of the rectangle (0, 0, pw, ph)."""
    # Clamp inputs inside borders
    cx = max(0.0, min(pw, mx))
    cy = max(0.0, min(ph, my))

    # Distance to 4 borders
    d_left = abs(cx - 0.0)
    d_right = abs(cx - pw)
    d_top = abs(cy - 0.0)
    d_bottom = abs(cy - ph)

    min_d = min(d_left, d_right, d_top, d_bottom)
    if min_d == d_left:
        return 0.0, cy
    elif min_d == d_right:
        return pw, cy
    elif min_d == d_top:
        return cx, 0.0
    else:
        return cx, ph

def draw_builder(screen: pygame.Surface, app: Any):
    """Renders the Builder mode layout: sliders, previews, text fields, and action buttons."""
    screen_w, screen_h = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()

    # Fonts
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        title_font = pygame.font.Font(None, 36)
        lbl_font = pygame.font.Font(None, 20)
        btn_font = pygame.font.Font(None, 24)
        warn_font = pygame.font.Font(None, 24)
    except Exception:
        title_font = pygame.font.SysFont("arial", 36)
        lbl_font = pygame.font.SysFont("arial", 20)
        btn_font = pygame.font.SysFont("arial", 24)
        warn_font = pygame.font.SysFont("arial", 24)

    # 1. Background clearing
    screen.fill((20, 20, 25))

    # Title
    title_surf = title_font.render("Logic Component Builder", True, app.get_color("primary", (142, 68, 173, 255)))
    screen.blit(title_surf, (30, 25))

    if app.builder_error:
        # Render error box and block building
        err_box = pygame.Rect(30, 80, screen_w - 60, 50)
        pygame.draw.rect(screen, (150, 40, 40), err_box, border_radius=6)
        err_surf = warn_font.render(app.builder_error, True, (255, 255, 255))
        screen.blit(err_surf, (err_box.centerx - err_surf.get_width() / 2, err_box.centery - err_surf.get_height() / 2))

        # Cancel button
        cancel_rect = pygame.Rect(screen_w / 2 - 90, screen_h - 100, 180, 45)
        pygame.draw.rect(screen, (70, 70, 75), cancel_rect, border_radius=6)
        c_surf = btn_font.render("Back to Simulation", True, (240, 240, 245))
        screen.blit(c_surf, (cancel_rect.centerx - c_surf.get_width() / 2, cancel_rect.centery - c_surf.get_height() / 2))
        return

    # 2. Draw Left Configuration Panel (Sliders and Inputs)
    px_x = 50
    # Name input field Y=110
    name_lbl = lbl_font.render("Component Name:", True, (200, 200, 205))
    screen.blit(name_lbl, (px_x, 80))
    name_box = pygame.Rect(px_x, 105, 220, 35)
    border_color = (142, 68, 173) if app.builder_focus == "name" else (60, 60, 65)
    pygame.draw.rect(screen, (30, 30, 35), name_box, border_radius=6)
    pygame.draw.rect(screen, border_color, name_box, 2, border_radius=6)
    text_surf = btn_font.render(app.builder_name + ("|" if app.builder_focus == "name" and (pygame.time.get_ticks() // 500) % 2 == 0 else ""), True, (255, 255, 255))
    screen.blit(text_surf, (name_box.x + 10, name_box.centery - text_surf.get_height() / 2))

    # Width Slider Y=180
    app.width_rect = draw_slider(screen, px_x, 185, 220, app.builder_width, 60.0, 200.0, "Width", lbl_font, (142, 68, 173))
    # Height Slider Y=240
    app.height_rect = draw_slider(screen, px_x, 245, 220, app.builder_height, 60.0, 200.0, "Height", lbl_font, (142, 68, 173))
    
    # RGB color sliders
    app.r_rect = draw_slider(screen, px_x, 315, 220, app.builder_color[0], 0.0, 255.0, "Color R", lbl_font, (231, 76, 60))
    app.g_rect = draw_slider(screen, px_x, 375, 220, app.builder_color[1], 0.0, 255.0, "Color G", lbl_font, (46, 204, 113))
    app.b_rect = draw_slider(screen, px_x, 435, 220, app.builder_color[2], 0.0, 255.0, "Color B", lbl_font, (52, 152, 219))

    # 3. Draw Center Preview Logic component
    pw = app.builder_width
    ph = app.builder_height
    # center offset
    cx = screen_w / 2 + 150
    cy = screen_h / 2 - 30
    preview_box = pygame.Rect(cx - pw / 2, cy - ph / 2, pw, ph)
    
    # Draw body rectangle
    pygame.draw.rect(screen, app.builder_color, preview_box, border_radius=6)
    pygame.draw.rect(screen, (220, 220, 225), preview_box, 2, border_radius=6)
    
    # Render component name centered
    name_title = lbl_font.render(app.builder_name, True, (255, 255, 255))
    screen.blit(name_title, (preview_box.centerx - name_title.get_width() / 2, preview_box.centery - name_title.get_height() / 2))

    # Draw preview subnodes (triangles pointing inwards/outwards)
    # Inputs: Point towards center
    for i, p_in in enumerate(app.builder_in_positions):
        sub_cx = preview_box.x + p_in["rel_x"]
        sub_cy = preview_box.y + p_in["rel_y"]
        # Pointing vector to center
        dx = pw / 2.0 - p_in["rel_x"]
        dy = ph / 2.0 - p_in["rel_y"]
        length = math.hypot(dx, dy)
        ux, uy = (dx / length, dy / length) if length > 0 else (1.0, 0.0)

        # Draw outline triangle (pointed inwards)
        r = 10.0
        V1 = (sub_cx + r * ux, sub_cy + r * uy)
        bc_x = sub_cx - 0.5 * r * ux
        bc_y = sub_cy - 0.5 * r * uy
        V2 = (bc_x - r * uy, bc_y + r * ux)
        V3 = (bc_x + r * uy, bc_y - r * ux)
        
        # Color based on hovered or dragging state
        node_color = (255, 220, 0) if app.builder_dragging_node == ("in", i) else (46, 204, 113)
        pygame.draw.polygon(screen, node_color, [V1, V2, V3])
        pygame.draw.polygon(screen, (255, 255, 255), [V1, V2, V3], 1)
        
        # Node label Y
        lbl = lbl_font.render(p_in["name"], True, (220, 220, 225))
        ox = 12 if p_in["rel_x"] < pw / 2 else -12 - lbl.get_width()
        screen.blit(lbl, (sub_cx + ox, sub_cy - lbl.get_height() / 2))

    # Outputs: Point away from center
    for i, p_out in enumerate(app.builder_out_positions):
        sub_cx = preview_box.x + p_out["rel_x"]
        sub_cy = preview_box.y + p_out["rel_y"]
        # Pointing vector away from center
        dx = pw / 2.0 - p_out["rel_x"]
        dy = ph / 2.0 - p_out["rel_y"]
        length = math.hypot(dx, dy)
        ux, uy = (-dx / length, -dy / length) if length > 0 else (-1.0, 0.0)

        # Draw outline triangle (pointed away)
        r = 10.0
        V1 = (sub_cx + r * ux, sub_cy + r * uy)
        bc_x = sub_cx - 0.5 * r * ux
        bc_y = sub_cy - 0.5 * r * uy
        V2 = (bc_x - r * uy, bc_y + r * ux)
        V3 = (bc_x + r * uy, bc_y - r * ux)
        
        node_color = (255, 220, 0) if app.builder_dragging_node == ("out", i) else (231, 76, 60)
        pygame.draw.polygon(screen, node_color, [V1, V2, V3])
        pygame.draw.polygon(screen, (255, 255, 255), [V1, V2, V3], 1)
        
        lbl = lbl_font.render(p_out["name"], True, (220, 220, 225))
        ox = 12 if p_out["rel_x"] < pw / 2 else -12 - lbl.get_width()
        screen.blit(lbl, (sub_cx + ox, sub_cy - lbl.get_height() / 2))

    # 4. Action Buttons at the bottom Y=screen_h-80
    app.build_btn = pygame.Rect(screen_w / 2 - 110, screen_h - 70, 160, 45)
    app.cancel_btn = pygame.Rect(screen_w / 2 + 70, screen_h - 70, 160, 45)
    
    # Draw build button
    hb = app.build_btn.collidepoint(mouse_pos)
    bb_color = (min(255, app.get_color("primary")[0] + 20), min(255, app.get_color("primary")[1] + 20), min(255, app.get_color("primary")[2] + 20)) if hb else app.get_color("primary")[:3]
    pygame.draw.rect(screen, bb_color, app.build_btn, border_radius=6)
    b_surf = btn_font.render("Build Component", True, (255, 255, 255))
    screen.blit(b_surf, (app.build_btn.centerx - b_surf.get_width() / 2, app.build_btn.centery - b_surf.get_height() / 2))

    # Draw cancel button
    hc = app.cancel_btn.collidepoint(mouse_pos)
    bc = (90, 90, 95) if hc else (70, 70, 75)
    pygame.draw.rect(screen, bc, app.cancel_btn, border_radius=6)
    c_surf = btn_font.render("Cancel", True, (240, 240, 245))
    screen.blit(c_surf, (app.cancel_btn.centerx - c_surf.get_width() / 2, app.cancel_btn.centery - c_surf.get_height() / 2))

def compile_truth_table(app: Any) -> dict:
    """Evaluates the state combinations of GlobalInputNodes to compile the LogicComponent truth table."""
    inputs = app.builder_inputs
    outputs = app.builder_outputs

    # Save current states to restore them later
    original_input_states = [inp.state for inp in inputs]

    truth_table = {}
    
    # 2^N combinations
    for combo in itertools.product([False, True], repeat=len(inputs)):
        # Apply input state combination
        for inp, val in zip(inputs, combo):
            inp.state = val
            
        # Read propagated output states
        out_states = tuple(out.state for out in outputs)

        # Build bitstrings as key/value strings
        key_str = "".join("1" if b else "0" for b in combo)
        val_str = "".join("1" if b else "0" for b in out_states)
        truth_table[key_str] = val_str

    # Restore initial states
    for inp, val in zip(inputs, original_input_states):
        inp.state = val

    return truth_table

def confirm_builder_compilation(app: Any) -> bool:
    """Compiles truth table, serializes component dictionary, and appends to LogicComponentLib.json."""
    if not app.builder_inputs or not app.builder_outputs:
        return False

    table = compile_truth_table(app)
    
    # Build component template dictionary
    component_def = {
        "name": app.builder_name,
        "width": app.builder_width,
        "height": app.builder_height,
        "color": list(app.builder_color) + [255],
        "inputs": [
            {
                "name": p["name"],
                "rel_x": int(p["rel_x"]),
                "rel_y": int(p["rel_y"]),
                "color": [231, 76, 60, 255]
            }
            for p in app.builder_in_positions
        ],
        "outputs": [
            {
                "name": p["name"],
                "rel_x": int(p["rel_x"]),
                "rel_y": int(p["rel_y"]),
                "color": [46, 204, 113, 255]
            }
            for p in app.builder_out_positions
        ],
        "logic_table": table
    }

    # Append to LogicComponentLib.json
    lib_path = 'D:\\PyInteractive\\mode\\LogicGate\\LogicComponentLib.json'
    templates = []
    if os.path.exists(lib_path):
        try:
            with open(lib_path, "r") as f:
                templates = json.load(f)
        except Exception:
            templates = []
            
    # Remove existing template with the same name if any
    templates = [t for t in templates if t.get("name") != app.builder_name]
    templates.append(component_def)

    try:
        with open(lib_path, "w") as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"Error saving to LogicComponentLib.json: {e}")
        return False

    # Also copy to root directory file to keep it synced
    root_lib_path = 'D:\\PyInteractive\\LogicComponentLib.json'
    try:
        with open(root_lib_path, "w") as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"Error copying to root LogicComponentLib.json: {e}")

    return True

def handle_builder_event(app: Any, event: pygame.event.Event) -> bool:
    """Processes slider drags, textbox inputs, outline snappings, and buttons in Builder Mode."""
    screen_w, screen_h = app.screen.get_size()
    mouse_pos = pygame.mouse.get_pos()

    if app.builder_error:
        # Error page only accepts back/cancel button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cancel_rect = pygame.Rect(screen_w / 2 - 90, screen_h - 100, 180, 45)
            if cancel_rect.collidepoint(event.pos):
                app.switch_to_sim()
                return True
        return False

    pw = app.builder_width
    ph = app.builder_height
    cx = screen_w / 2 + 150
    cy = screen_h / 2 - 30
    preview_box = pygame.Rect(cx - pw / 2, cy - ph / 2, pw, ph)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # 1. Check textbox focus Y=105
        name_box = pygame.Rect(50, 105, 220, 35)
        if name_box.collidepoint(event.pos):
            app.builder_focus = "name"
        else:
            app.builder_focus = None

        # 2. Check Action Buttons
        if app.build_btn.collidepoint(event.pos):
            if confirm_builder_compilation(app):
                app.switch_to_sim()
            return True
        elif app.cancel_btn.collidepoint(event.pos):
            app.switch_to_sim()
            return True

        # 3. Check Sliders click/drag
        if getattr(app, "width_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
            app.builder_dragging_slider = "width"
        elif getattr(app, "height_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
            app.builder_dragging_slider = "height"
        elif getattr(app, "r_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
            app.builder_dragging_slider = "R"
        elif getattr(app, "g_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
            app.builder_dragging_slider = "G"
        elif getattr(app, "b_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
            app.builder_dragging_slider = "B"

        # 4. Check sub-nodes click/drag
        # Inputs
        for i, p_in in enumerate(app.builder_in_positions):
            sub_cx = preview_box.x + p_in["rel_x"]
            sub_cy = preview_box.y + p_in["rel_y"]
            if math.hypot(event.pos[0] - sub_cx, event.pos[1] - sub_cy) <= 12:
                app.builder_dragging_node = ("in", i)
                return True
        # Outputs
        for i, p_out in enumerate(app.builder_out_positions):
            sub_cx = preview_box.x + p_out["rel_x"]
            sub_cy = preview_box.y + p_out["rel_y"]
            if math.hypot(event.pos[0] - sub_cx, event.pos[1] - sub_cy) <= 12:
                app.builder_dragging_node = ("out", i)
                return True

    elif event.type == pygame.MOUSEMOTION:
        # Handle Sliders movement
        if app.builder_dragging_slider:
            # Map mouse X coordinates between slider range (50 to 270)
            ratio = max(0.0, min(1.0, (event.pos[0] - 50.0) / 220.0))
            if app.builder_dragging_slider == "width":
                # Width slider Y=185
                app.builder_width = int(60.0 + ratio * (200.0 - 60.0))
                # Adjust rel_x positions on the right edge dynamically
                for p_out in app.builder_out_positions:
                    if p_out["rel_x"] > 0.0:
                        p_out["rel_x"] = float(app.builder_width)
            elif app.builder_dragging_slider == "height":
                # Height slider Y=245
                app.builder_height = int(60.0 + ratio * (200.0 - 60.0))
                # clamp node relative positions inside new height
                for p in app.builder_in_positions + app.builder_out_positions:
                    if p["rel_y"] > app.builder_height:
                        p["rel_y"] = float(app.builder_height)
            elif app.builder_dragging_slider == "R":
                app.builder_color[0] = int(ratio * 255.0)
            elif app.builder_dragging_slider == "G":
                app.builder_color[1] = int(ratio * 255.0)
            elif app.builder_dragging_slider == "B":
                app.builder_color[2] = int(ratio * 255.0)

        # Handle subnodes sliding outline snaps
        elif app.builder_dragging_node:
            rel_x = event.pos[0] - preview_box.x
            rel_y = event.pos[1] - preview_box.y
            snapped_x, snapped_y = snap_to_outline(rel_x, rel_y, pw, ph)
            
            node_type, idx = app.builder_dragging_node
            if node_type == "in":
                app.builder_in_positions[idx]["rel_x"] = snapped_x
                app.builder_in_positions[idx]["rel_y"] = snapped_y
            else:
                app.builder_out_positions[idx]["rel_x"] = snapped_x
                app.builder_out_positions[idx]["rel_y"] = snapped_y

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            app.builder_dragging_slider = None
            app.builder_dragging_node = None

    elif event.type == pygame.KEYDOWN:
        # Handle typing gate name
        if app.builder_focus == "name":
            if event.key == pygame.K_BACKSPACE:
                app.builder_name = app.builder_name[:-1]
            elif event.unicode and event.unicode.isprintable() and len(app.builder_name) < 18:
                # Disallow spacing or commas in name to keep key formats clean
                if event.unicode not in (",", " "):
                    app.builder_name += event.unicode

    return False
