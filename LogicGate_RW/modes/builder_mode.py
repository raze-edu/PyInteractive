import os
import math
from typing import Any, Tuple, List
import pygame

from include import (
    Bits,
    COMPONENT_LIB,
    TableComponentLibraryEntry
)
from LogicGate_RW.core.ui_node import UIGlobalInputNode, UIGlobalOutputNode
from LogicGate_RW.core.ui_arrays import UIArrayNode
from LogicGate_RW.core.circuit_bridge import compile_canvas_to_table, serialize_canvas
from LogicGate_RW.storage.library_adapter import save_component_template
from LogicGate_RW.ui.widgets import draw_slider, draw_button
from LogicGate_RW.ui.style import shared_style

def init_builder_mode(app: Any) -> None:
    """Initializes builder variables from current canvas."""
    app.builder_inputs = [obj for obj in app.objects if isinstance(obj, UIGlobalInputNode) or (isinstance(obj, UIArrayNode) and obj.is_transmitter)]
    app.builder_outputs = [obj for obj in app.objects if isinstance(obj, UIGlobalOutputNode) or (isinstance(obj, UIArrayNode) and not obj.is_transmitter)]

    app.builder_inputs.sort(key=lambda n: n.label)
    app.builder_outputs.sort(key=lambda n: n.label)

    app.builder_error = None
    if not app.builder_inputs or not app.builder_outputs:
        app.builder_error = "Circuit must contain at least 1 input and 1 output node!"

    app.builder_name = "MY_GATE"
    app.builder_width = 110
    app.builder_height = 90
    app.builder_color = [142, 68, 173]
    app.builder_focus = None
    app.builder_dragging_node = None
    app.builder_dragging_slider = None
    app.builder_compile_mode = "table"

    # Setup pin positions in preview
    app.builder_in_positions = []
    space_in = app.builder_height / (len(app.builder_inputs) + 1)
    for i, inp in enumerate(app.builder_inputs):
        app.builder_in_positions.append({
            "name": inp.label,
            "rel_x": 0.0,
            "rel_y": space_in * (i + 1)
        })

    app.builder_out_positions = []
    space_out = app.builder_height / (len(app.builder_outputs) + 1)
    for i, out in enumerate(app.builder_outputs):
        app.builder_out_positions.append({
            "name": out.label,
            "rel_x": float(app.builder_width),
            "rel_y": space_out * (i + 1)
        })

def confirm_builder_compilation(app: Any) -> bool:
    if not app.builder_inputs or not app.builder_outputs:
        return False

    table_bits, table_dict = compile_canvas_to_table(app)

    template = {
        "name": app.builder_name.strip() or "NEW_GATE",
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
        "logic_table": table_dict
    }

    if getattr(app, "builder_compile_mode", "table") == "composite":
        template["type"] = "composite"
        template["inner_circuit"] = serialize_canvas(app)

    # Save to JSON
    save_component_template(template)

    # Also register in COMPONENT_LIB for high-speed Bits simulation
    TableComponentLibraryEntry(
        template["name"],
        (len(template["inputs"]), len(template["outputs"])),
        table_bits
    )

    return True

def draw_builder(screen: pygame.Surface, app: Any) -> None:
    screen_w, screen_h = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()

    try:
        title_font = pygame.font.Font(None, 28)
        lbl_font = pygame.font.Font(None, 20)
        btn_font = pygame.font.Font(None, 22)
    except Exception:
        title_font = pygame.font.SysFont("arial", 28)
        lbl_font = pygame.font.SysFont("arial", 20)
        btn_font = pygame.font.SysFont("arial", 22)

    # Header
    title = title_font.render("Component Builder Mode", True, (240, 240, 245))
    screen.blit(title, (50, 25))

    if app.builder_error:
        err = lbl_font.render(app.builder_error, True, (255, 90, 80))
        screen.blit(err, (screen_w / 2 - err.get_width() / 2, screen_h / 2 - 40))
        btn_cancel = pygame.Rect(screen_w / 2 - 80, screen_h / 2 + 20, 160, 42)
        draw_button(screen, btn_cancel, "Return to Sim", mouse_pos)
        return

    # 1. Left controls panel: Name textbox, Sliders
    # Name textbox
    tb_rect = pygame.Rect(50, 80, 220, 36)
    is_foc = (app.builder_focus == "name")
    pygame.draw.rect(screen, (35, 35, 45), tb_rect, border_radius=6)
    pygame.draw.rect(screen, (255, 220, 0) if is_foc else (80, 80, 95), tb_rect, 2, border_radius=6)
    name_txt = lbl_font.render(app.builder_name, True, (255, 255, 255))
    screen.blit(name_txt, (tb_rect.x + 10, tb_rect.centery - name_txt.get_height() / 2))

    # Sliders: Width, Height, Red, Green, Blue
    y_s = 150
    w_slider = pygame.Rect(50, y_s, 220, 20)
    draw_slider(screen, 50, y_s, 220, app.builder_width, 60, 260, "Width", lbl_font, (142, 68, 173))
    app.w_slider_rect = pygame.Rect(40, y_s - 10, 240, 25)

    y_s += 50
    draw_slider(screen, 50, y_s, 220, app.builder_height, 60, 260, "Height", lbl_font, (142, 68, 173))
    app.h_slider_rect = pygame.Rect(40, y_s - 10, 240, 25)

    y_s += 50
    draw_slider(screen, 50, y_s, 220, app.builder_color[0], 0, 255, "Color R", lbl_font, (230, 80, 80))
    app.r_slider_rect = pygame.Rect(40, y_s - 10, 240, 25)

    y_s += 45
    draw_slider(screen, 50, y_s, 220, app.builder_color[1], 0, 255, "Color G", lbl_font, (80, 220, 100))
    app.g_slider_rect = pygame.Rect(40, y_s - 10, 240, 25)

    y_s += 45
    draw_slider(screen, 50, y_s, 220, app.builder_color[2], 0, 255, "Color B", lbl_font, (80, 140, 240))
    app.b_slider_rect = pygame.Rect(40, y_s - 10, 240, 25)

    # 2. Center: Component preview box
    pw = app.builder_width
    ph = app.builder_height
    cx = screen_w / 2 + 120
    cy = screen_h / 2 - 20
    prev_box = pygame.Rect(cx - pw / 2, cy - ph / 2, pw, ph)

    col = tuple(app.builder_color)
    pygame.draw.rect(screen, col, prev_box, border_radius=8)
    pygame.draw.rect(screen, (240, 240, 250), prev_box, 2, border_radius=8)

    # Centered preview name
    nm = title_font.render(app.builder_name, True, (255, 255, 255))
    screen.blit(nm, (prev_box.centerx - nm.get_width() / 2, prev_box.centery - nm.get_height() / 2))

    # Draw inputs preview pins
    for i, p_in in enumerate(app.builder_in_positions):
        px = prev_box.x + p_in["rel_x"]
        py = prev_box.y + p_in["rel_y"]
        p_col = (255, 220, 0) if app.builder_dragging_node == ("in", i) else (46, 204, 113)
        pygame.draw.circle(screen, p_col, (int(px), int(py)), 8)
        pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), 8, 1)

        l_surf = lbl_font.render(p_in["name"], True, (220, 220, 230))
        screen.blit(l_surf, (int(px - l_surf.get_width() - 10), int(py - l_surf.get_height() / 2)))

    # Draw outputs preview pins
    for i, p_out in enumerate(app.builder_out_positions):
        px = prev_box.x + p_out["rel_x"]
        py = prev_box.y + p_out["rel_y"]
        p_col = (255, 220, 0) if app.builder_dragging_node == ("out", i) else (231, 76, 60)
        pygame.draw.circle(screen, p_col, (int(px), int(py)), 8)
        pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), 8, 1)

        l_surf = lbl_font.render(p_out["name"], True, (220, 220, 230))
        screen.blit(l_surf, (int(px + 12), int(py - l_surf.get_height() / 2)))

    # 3. Action Buttons
    app.btn_build = pygame.Rect(screen_w / 2 - 10, screen_h - 70, 160, 42)
    app.btn_cancel = pygame.Rect(screen_w / 2 + 170, screen_h - 70, 140, 42)

    draw_button(screen, app.btn_build, "Build Component", mouse_pos)
    draw_button(screen, app.btn_cancel, "Cancel", mouse_pos)

def handle_builder_event(app: Any, event: pygame.event.Event) -> bool:
    if getattr(app, "builder_error", None):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            app.switch_to_sim()
            return True
        return False

    mouse_pos = pygame.mouse.get_pos()

    # Slider dragging
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # Check text box
        if pygame.Rect(50, 80, 220, 36).collidepoint(event.pos):
            app.builder_focus = "name"
            return True
        else:
            app.builder_focus = None

        # Check sliders
        if hasattr(app, "w_slider_rect") and app.w_slider_rect.collidepoint(event.pos):
            app.builder_dragging_slider = "width"
            return True
        if hasattr(app, "h_slider_rect") and app.h_slider_rect.collidepoint(event.pos):
            app.builder_dragging_slider = "height"
            return True
        if hasattr(app, "r_slider_rect") and app.r_slider_rect.collidepoint(event.pos):
            app.builder_dragging_slider = "r"
            return True
        if hasattr(app, "g_slider_rect") and app.g_slider_rect.collidepoint(event.pos):
            app.builder_dragging_slider = "g"
            return True
        if hasattr(app, "b_slider_rect") and app.b_slider_rect.collidepoint(event.pos):
            app.builder_dragging_slider = "b"
            return True

        # Check pin dragging in preview
        screen_w, screen_h = app.screen.get_size()
        cx = screen_w / 2 + 120
        cy = screen_h / 2 - 20
        bx = cx - app.builder_width / 2
        by = cy - app.builder_height / 2

        for i, pin in enumerate(app.builder_in_positions):
            px = bx + pin["rel_x"]
            py = by + pin["rel_y"]
            if math.hypot(event.pos[0] - px, event.pos[1] - py) <= 12:
                app.builder_dragging_node = ("in", i)
                return True

        for i, pin in enumerate(app.builder_out_positions):
            px = bx + pin["rel_x"]
            py = by + pin["rel_y"]
            if math.hypot(event.pos[0] - px, event.pos[1] - py) <= 12:
                app.builder_dragging_node = ("out", i)
                return True

        # Check action buttons
        if hasattr(app, "btn_build") and app.btn_build.collidepoint(event.pos):
            if confirm_builder_compilation(app):
                app.switch_to_sim()
            return True
        if hasattr(app, "btn_cancel") and app.btn_cancel.collidepoint(event.pos):
            app.switch_to_sim()
            return True

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        app.builder_dragging_slider = None
        app.builder_dragging_node = None

    elif event.type == pygame.MOUSEMOTION:
        # Update dragging slider
        if app.builder_dragging_slider:
            ratio = max(0.0, min(1.0, (event.pos[0] - 50) / 220.0))
            if app.builder_dragging_slider == "width":
                app.builder_width = int(60 + ratio * 200)
                # Update output pin x positions to match new width
                for out_p in app.builder_out_positions:
                    out_p["rel_x"] = float(app.builder_width)
            elif app.builder_dragging_slider == "height":
                app.builder_height = int(60 + ratio * 200)
            elif app.builder_dragging_slider == "r":
                app.builder_color[0] = int(ratio * 255)
            elif app.builder_dragging_slider == "g":
                app.builder_color[1] = int(ratio * 255)
            elif app.builder_dragging_slider == "b":
                app.builder_color[2] = int(ratio * 255)
            return True

        # Update dragging pin along edge
        if app.builder_dragging_node:
            screen_w, screen_h = app.screen.get_size()
            cy = screen_h / 2 - 20
            by = cy - app.builder_height / 2
            rel_y = max(8.0, min(app.builder_height - 8.0, event.pos[1] - by))
            ntype, idx = app.builder_dragging_node
            if ntype == "in":
                app.builder_in_positions[idx]["rel_y"] = rel_y
            else:
                app.builder_out_positions[idx]["rel_y"] = rel_y
            return True

    elif event.type == pygame.KEYDOWN and app.builder_focus == "name":
        if event.key == pygame.K_BACKSPACE:
            app.builder_name = app.builder_name[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            app.builder_focus = None
        else:
            if len(app.builder_name) < 14 and event.unicode.isprintable():
                app.builder_name += event.unicode
        return True

    return False
