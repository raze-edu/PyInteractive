import os
import json
import pygame
import math
from typing import Any, Tuple, Optional, List

# Define layout rectangles (will be calculated dynamically in draw/events)
def get_layout(screen_w: int, screen_h: int):
    return {
        "groups_panel": pygame.Rect(30, 80, 280, screen_h - 180),
        "details_panel": pygame.Rect(330, 80, 340, screen_h - 180),
        "comps_panel": pygame.Rect(690, 80, screen_w - 720, screen_h - 180),
        "back_btn": pygame.Rect(screen_w - 210, 20, 180, 40),
        "add_group_btn": pygame.Rect(30, screen_h - 85, 130, 40),
        "del_group_btn": pygame.Rect(180, screen_h - 85, 130, 40),
    }

def get_unique_group_name(groups: List[dict], prefix: str = "New Group") -> str:
    names = {g["name"] for g in groups}
    idx = 1
    while f"{prefix} {idx}" in names:
        idx += 1
    return f"{prefix} {idx}"

def is_group_name_unique(groups: List[dict], new_name: str, current_idx: int) -> bool:
    name = new_name.strip()
    if not name:
        return False
    for i, g in enumerate(groups):
        if i != current_idx and g["name"].lower() == name.lower():
            return False
    return True

def check_component_dependencies(app: Any, component_name: str) -> Optional[str]:
    """Checks if a component is used in any other composite component in the library."""
    for item in app.gui_library:
        template = item.get("template")
        if template:
            inner_circuit = template.get("inner_circuit")
            if inner_circuit:
                for node in inner_circuit.get("nodes", []):
                    if node.get("type") == "gate" and node.get("gate_name") == component_name:
                        return item["name"]
    return None

def draw_slider(screen: pygame.Surface, x: int, y: int, w: int, val: float, label: str, font: pygame.font.Font, color: Tuple[int, int, int], enabled: bool = True) -> pygame.Rect:
    lbl_color = (230, 230, 235) if enabled else (100, 100, 105)
    lbl_surf = font.render(f"{label}: {int(val)}", True, lbl_color)
    screen.blit(lbl_surf, (x, y - 20))

    track_color = (60, 60, 65) if enabled else (40, 40, 45)
    pygame.draw.line(screen, track_color, (x, y), (x + w, y), 6)

    hx = x + int(w * (val / 255.0))
    handle_color = color if enabled else (120, 120, 125)
    pygame.draw.circle(screen, handle_color, (hx, y), 10)
    pygame.draw.circle(screen, (240, 240, 245) if enabled else (80, 80, 85), (hx, y), 10, 2)
    
    return pygame.Rect(x - 10, y - 10, w + 20, 20)

def draw_manager(screen: pygame.Surface, app: Any):
    screen_w, screen_h = screen.get_size()
    layout = get_layout(screen_w, screen_h)
    mouse_pos = pygame.mouse.get_pos()

    # Initialize state variables if not defined on app
    if not hasattr(app, "manager_groups_scroll_y"):
        app.manager_groups_scroll_y = 0.0
    if not hasattr(app, "manager_comps_scroll_y"):
        app.manager_comps_scroll_y = 0.0
    if not hasattr(app, "manager_warning"):
        app.manager_warning = None
    if not hasattr(app, "manager_warning_time"):
        app.manager_warning_time = 0
    if not hasattr(app, "manager_focus"):
        app.manager_focus = None
    if not hasattr(app, "manager_dragging_slider"):
        app.manager_dragging_slider = None

    # Load fonts
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        title_font = pygame.font.Font(None, 36)
        sec_font = pygame.font.Font(None, 24)
        lbl_font = pygame.font.Font(None, 20)
        btn_font = pygame.font.Font(None, 22)
        warn_font = pygame.font.Font(None, 20)
    except Exception:
        title_font = pygame.font.SysFont("arial", 36)
        sec_font = pygame.font.SysFont("arial", 24)
        lbl_font = pygame.font.SysFont("arial", 20)
        btn_font = pygame.font.SysFont("arial", 22)
        warn_font = pygame.font.SysFont("arial", 20)

    # 1. Clear warning if expired (after 4 seconds)
    if app.manager_warning and pygame.time.get_ticks() - app.manager_warning_time > 4000:
        app.manager_warning = None

    # 2. Draw Title
    title_surf = title_font.render("Components & Groups Manager", True, app.get_color("primary", (142, 68, 173, 255)))
    screen.blit(title_surf, (30, 25))

    # 3. Draw Back Button
    b_hover = layout["back_btn"].collidepoint(mouse_pos)
    b_color = (min(255, app.get_color("primary")[0] + 20), min(255, app.get_color("primary")[1] + 20), min(255, app.get_color("primary")[2] + 20)) if b_hover else app.get_color("primary")[:3]
    try:
        pygame.draw.rect(screen, b_color, layout["back_btn"], border_radius=6)
    except TypeError:
        pygame.draw.rect(screen, b_color, layout["back_btn"])
    
    back_surf = btn_font.render("Back to Simulation", True, (255, 255, 255))
    screen.blit(back_surf, (layout["back_btn"].centerx - back_surf.get_width() / 2, layout["back_btn"].centery - back_surf.get_height() / 2))

    # 4. Draw Groups Panel (Left)
    pygame.draw.rect(screen, (25, 25, 30), layout["groups_panel"], border_radius=8)
    pygame.draw.rect(screen, (50, 50, 55), layout["groups_panel"], 2, border_radius=8)
    
    g_title = sec_font.render("Groups", True, (200, 200, 205))
    screen.blit(g_title, (layout["groups_panel"].x + 10, layout["groups_panel"].y - 25))

    # Groups clip surface
    g_rect = layout["groups_panel"].inflate(-10, -10)
    g_clip_surf = pygame.Surface((g_rect.width, g_rect.height), pygame.SRCALPHA)
    
    item_h = 50
    for idx, group in enumerate(app.groups):
        item_y = idx * item_h - app.manager_groups_scroll_y
        if item_y + item_h < 0 or item_y > g_rect.height:
            continue

        bg_color = (35, 35, 40)
        border_color = (65, 65, 70)
        if idx == app.manager_selected_group_idx:
            bg_color = (50, 45, 60)
            border_color = app.get_color("primary")[:3]

        item_rect = pygame.Rect(5, int(item_y), g_rect.width - 10, item_h - 8)
        
        # Hover check
        mouse_rel = (mouse_pos[0] - g_rect.x, mouse_pos[1] - g_rect.y)
        if item_rect.collidepoint(mouse_rel) and idx != app.manager_selected_group_idx:
            border_color = (100, 100, 105)

        try:
            pygame.draw.rect(g_clip_surf, bg_color, item_rect, border_radius=6)
            pygame.draw.rect(g_clip_surf, border_color, item_rect, 2, border_radius=6)
        except TypeError:
            pygame.draw.rect(g_clip_surf, bg_color, item_rect)
            pygame.draw.rect(g_clip_surf, border_color, item_rect, 2)

        # Draw group color square
        color_rect = pygame.Rect(item_rect.x + 10, item_rect.y + (item_rect.height - 18) // 2, 18, 18)
        if group.get("color") is not None:
            g_c = group["color"]
            pygame.draw.rect(g_clip_surf, (g_c[0], g_c[1], g_c[2]), color_rect, border_radius=4)
        else:
            # Draw gray box with diagonal slash to show no color
            pygame.draw.rect(g_clip_surf, (70, 70, 75), color_rect, border_radius=4)
            pygame.draw.line(g_clip_surf, (150, 50, 50), (color_rect.left, color_rect.top), (color_rect.right, color_rect.bottom), 2)

        # Draw group label
        lbl_surf = lbl_font.render(group["name"], True, (240, 240, 245))
        g_clip_surf.blit(lbl_surf, (color_rect.right + 12, item_rect.centery - lbl_surf.get_height() / 2))

        # Show size of members
        size_lbl = lbl_font.render(str(len(group.get("components", []))), True, (130, 130, 135))
        g_clip_surf.blit(size_lbl, (item_rect.right - 25, item_rect.centery - size_lbl.get_height() / 2))

    screen.blit(g_clip_surf, (g_rect.x, g_rect.y))

    # Add & Delete Group buttons
    add_h = layout["add_group_btn"].collidepoint(mouse_pos)
    add_bg = (50, 150, 50) if add_h else (40, 120, 40)
    try:
        pygame.draw.rect(screen, add_bg, layout["add_group_btn"], border_radius=6)
    except TypeError:
        pygame.draw.rect(screen, add_bg, layout["add_group_btn"])
    add_txt = btn_font.render("+ Add Group", True, (255, 255, 255))
    screen.blit(add_txt, (layout["add_group_btn"].centerx - add_txt.get_width() / 2, layout["add_group_btn"].centery - add_txt.get_height() / 2))

    del_h = layout["del_group_btn"].collidepoint(mouse_pos)
    del_bg = (170, 50, 50) if del_h else (130, 40, 40)
    if app.manager_selected_group_idx < 0:
        del_bg = (60, 60, 65)
    try:
        pygame.draw.rect(screen, del_bg, layout["del_group_btn"], border_radius=6)
    except TypeError:
        pygame.draw.rect(screen, del_bg, layout["del_group_btn"])
    del_txt = btn_font.render("Delete Group", True, (255, 255, 255) if app.manager_selected_group_idx >= 0 else (130, 130, 135))
    screen.blit(del_txt, (layout["del_group_btn"].centerx - del_txt.get_width() / 2, layout["del_group_btn"].centery - del_txt.get_height() / 2))

    # 5. Draw Details Panel (Middle)
    pygame.draw.rect(screen, (25, 25, 30), layout["details_panel"], border_radius=8)
    pygame.draw.rect(screen, (50, 50, 55), layout["details_panel"], 2, border_radius=8)
    
    d_title = sec_font.render("Group Details", True, (200, 200, 205))
    screen.blit(d_title, (layout["details_panel"].x + 10, layout["details_panel"].y - 25))

    if 0 <= app.manager_selected_group_idx < len(app.groups):
        group = app.groups[app.manager_selected_group_idx]
        
        # Name Input label
        name_lbl = lbl_font.render("Group Label:", True, (180, 180, 185))
        screen.blit(name_lbl, (layout["details_panel"].x + 20, layout["details_panel"].y + 20))

        # Text input box
        name_box = pygame.Rect(layout["details_panel"].x + 20, layout["details_panel"].y + 45, layout["details_panel"].width - 40, 35)
        border_col = app.get_color("primary")[:3] if app.manager_focus == "group_name" else (65, 65, 70)
        
        # Validation visual check
        name_valid = is_group_name_unique(app.groups, app.manager_editing_group_name, app.manager_selected_group_idx)
        if app.manager_editing_group_name.strip() == "":
            name_valid = False
        if not name_valid and app.manager_editing_group_name.strip() != "":
            border_col = (200, 50, 50)

        pygame.draw.rect(screen, (30, 30, 35), name_box, border_radius=6)
        pygame.draw.rect(screen, border_col, name_box, 2, border_radius=6)

        cursor = "|" if app.manager_focus == "group_name" and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        txt_surf = btn_font.render(app.manager_editing_group_name + cursor, True, (255, 255, 255))
        screen.blit(txt_surf, (name_box.x + 10, name_box.centery - txt_surf.get_height() / 2))

        if not name_valid and app.manager_editing_group_name.strip() != "":
            err_lbl = warn_font.render("Name must be unique and non-empty", True, (200, 50, 50))
            screen.blit(err_lbl, (name_box.x, name_box.bottom + 5))

        # Color Override Checkbox
        checkbox_rect = pygame.Rect(layout["details_panel"].x + 20, layout["details_panel"].y + 110, 20, 20)
        has_color = group.get("color") is not None
        pygame.draw.rect(screen, (40, 40, 45), checkbox_rect, border_radius=4)
        pygame.draw.rect(screen, (100, 100, 105), checkbox_rect, 1, border_radius=4)
        if has_color:
            pygame.draw.rect(screen, app.get_color("primary")[:3], checkbox_rect.inflate(-6, -6), border_radius=2)
            
        chk_lbl = lbl_font.render("Assign Group Color Override", True, (220, 220, 225))
        screen.blit(chk_lbl, (checkbox_rect.right + 12, checkbox_rect.centery - chk_lbl.get_height() / 2))

        # Color Sliders
        # Store sliders rects on app to collide against
        app.slider_r_rect = pygame.Rect(0,0,0,0)
        app.slider_g_rect = pygame.Rect(0,0,0,0)
        app.slider_b_rect = pygame.Rect(0,0,0,0)
        
        g_c = group.get("color", [142, 68, 173])
        # Make sure g_c has 3 elements
        if not g_c or len(g_c) < 3:
            g_c = [142, 68, 173]

        app.slider_r_rect = draw_slider(screen, layout["details_panel"].x + 25, layout["details_panel"].y + 175, layout["details_panel"].width - 50, g_c[0], "Override R", lbl_font, (231, 76, 60), has_color)
        app.slider_g_rect = draw_slider(screen, layout["details_panel"].x + 25, layout["details_panel"].y + 235, layout["details_panel"].width - 50, g_c[1], "Override G", lbl_font, (46, 204, 113), has_color)
        app.slider_b_rect = draw_slider(screen, layout["details_panel"].x + 25, layout["details_panel"].y + 295, layout["details_panel"].width - 50, g_c[2], "Override B", lbl_font, (52, 152, 219), has_color)

        # Show preview color box
        preview_title = lbl_font.render("Preview Color Overlay:", True, (180, 180, 185))
        screen.blit(preview_title, (layout["details_panel"].x + 20, layout["details_panel"].y + 340))
        
        pbox = pygame.Rect(layout["details_panel"].x + 20, layout["details_panel"].y + 365, layout["details_panel"].width - 40, 50)
        if has_color:
            pygame.draw.rect(screen, (g_c[0], g_c[1], g_c[2]), pbox, border_radius=6)
            pygame.draw.rect(screen, (240, 240, 245), pbox, 2, border_radius=6)
        else:
            pygame.draw.rect(screen, (30, 30, 35), pbox, border_radius=6)
            pygame.draw.rect(screen, (55, 55, 60), pbox, 2, border_radius=6)
            no_c_lbl = lbl_font.render("No Color Override Assigned", True, (120, 120, 125))
            screen.blit(no_c_lbl, (pbox.centerx - no_c_lbl.get_width() / 2, pbox.centery - no_c_lbl.get_height() / 2))
    else:
        # No group selected
        no_sel = lbl_font.render("Select a group or create a new", True, (120, 120, 125))
        no_sel2 = lbl_font.render("one to configure properties.", True, (120, 120, 125))
        screen.blit(no_sel, (layout["details_panel"].centerx - no_sel.get_width() / 2, layout["details_panel"].centery - 20))
        screen.blit(no_sel2, (layout["details_panel"].centerx - no_sel2.get_width() / 2, layout["details_panel"].centery + 5))

    # 6. Draw Library Components list (Right)
    pygame.draw.rect(screen, (25, 25, 30), layout["comps_panel"], border_radius=8)
    pygame.draw.rect(screen, (50, 50, 55), layout["comps_panel"], 2, border_radius=8)

    c_title = sec_font.render("Library Components", True, (200, 200, 205))
    screen.blit(c_title, (layout["comps_panel"].x + 10, layout["comps_panel"].y - 25))

    # Filter out input/output nodes from standard library definitions
    custom_gates = [item for item in app.gui_library if item["type"] == "gate"]

    # Component list clip surface
    c_rect = layout["comps_panel"].inflate(-10, -10)
    c_clip_surf = pygame.Surface((c_rect.width, c_rect.height), pygame.SRCALPHA)
    
    comp_item_h = 52
    
    # Store list of item delete buttons for click handling
    app.manager_comp_buttons = []
    
    for idx, item in enumerate(custom_gates):
        item_y = idx * comp_item_h - app.manager_comps_scroll_y
        if item_y + comp_item_h < 0 or item_y > c_rect.height:
            continue

        comp_name = item["name"]
        
        # Card body
        card_rect = pygame.Rect(5, int(item_y), c_rect.width - 10, comp_item_h - 6)
        bg_col = (32, 32, 37)
        border_col = (55, 55, 60)
        
        try:
            pygame.draw.rect(c_clip_surf, bg_col, card_rect, border_radius=6)
            pygame.draw.rect(c_clip_surf, border_col, card_rect, 1, border_radius=6)
        except TypeError:
            pygame.draw.rect(c_clip_surf, bg_col, card_rect)
            pygame.draw.rect(c_clip_surf, border_col, card_rect, 1)

        # Draw component preview thumbnail box
        thumb_rect = pygame.Rect(card_rect.x + 8, card_rect.y + (card_rect.height - 20) // 2, 32, 20)
        g_c = app.get_component_group_color(comp_name)
        comp_color = g_c if g_c is not None else item["template"].get("color", [142, 68, 173])
        pygame.draw.rect(c_clip_surf, (comp_color[0], comp_color[1], comp_color[2]), thumb_rect, border_radius=4)

        # Draw name
        lbl_surf = lbl_font.render(comp_name, True, (240, 240, 245))
        c_clip_surf.blit(lbl_surf, (thumb_rect.right + 12, card_rect.centery - lbl_surf.get_height() / 2))

        # Group membership label
        member_group_name = "No Group"
        group_lbl_color = (130, 130, 135)
        for g in app.groups:
            if comp_name in g.get("components", []):
                member_group_name = g["name"]
                group_lbl_color = app.get_color("primary")[:3]
                break

        group_lbl = lbl_font.render(member_group_name, True, group_lbl_color)
        c_clip_surf.blit(group_lbl, (card_rect.x + 180, card_rect.centery - group_lbl.get_height() / 2))

        # Checkbox to assign/remove from selected group
        cb_rect = pygame.Rect(card_rect.x + 310, card_rect.y + (card_rect.height - 18) // 2, 18, 18)
        group_selected = 0 <= app.manager_selected_group_idx < len(app.groups)
        
        if group_selected:
            active_group = app.groups[app.manager_selected_group_idx]
            is_member = comp_name in active_group.get("components", [])
            pygame.draw.rect(c_clip_surf, (20, 20, 25), cb_rect, border_radius=4)
            pygame.draw.rect(c_clip_surf, (100, 100, 105), cb_rect, 1, border_radius=4)
            if is_member:
                pygame.draw.rect(c_clip_surf, app.get_color("primary")[:3], cb_rect.inflate(-6, -6), border_radius=2)
        else:
            # Draw grayed out checkbox
            pygame.draw.rect(c_clip_surf, (40, 40, 45), cb_rect, border_radius=4)
            pygame.draw.rect(c_clip_surf, (60, 60, 65), cb_rect, 1, border_radius=4)

        # Delete Component button
        del_btn = pygame.Rect(card_rect.right - 70, card_rect.y + (card_rect.height - 26) // 2, 60, 26)
        
        # Hover state check for absolute coordinates
        abs_del_btn = pygame.Rect(c_rect.x + del_btn.x, c_rect.y + del_btn.y, del_btn.width, del_btn.height)
        d_hover = abs_del_btn.collidepoint(mouse_pos)
        del_btn_color = (200, 60, 60) if d_hover else (140, 40, 40)
        
        try:
            pygame.draw.rect(c_clip_surf, del_btn_color, del_btn, border_radius=4)
        except TypeError:
            pygame.draw.rect(c_clip_surf, del_btn_color, del_btn)

        del_lbl = warn_font.render("Delete", True, (255, 255, 255))
        c_clip_surf.blit(del_lbl, (del_btn.centerx - del_lbl.get_width() / 2, del_btn.centery - del_lbl.get_height() / 2))

        # Store button metadata
        app.manager_comp_buttons.append({
            "name": comp_name,
            "cb_rect": pygame.Rect(c_rect.x + cb_rect.x, c_rect.y + cb_rect.y, cb_rect.width, cb_rect.height),
            "del_rect": abs_del_btn
        })

    screen.blit(c_clip_surf, (c_rect.x, c_rect.y))

    # 7. Draw Warnings / Instructions at bottom Y = screen_h - 45
    if app.manager_warning:
        w_surf = warn_font.render(app.manager_warning, True, (230, 70, 70))
        screen.blit(w_surf, (layout["details_panel"].x, screen_h - 45))
    else:
        inst_surf = lbl_font.render("Press ESC to exit manager | Select group on left | Click checkbox to assign component", True, (140, 140, 145))
        screen.blit(inst_surf, (30, screen_h - 45))


def handle_manager_event(app: Any, event: pygame.event.Event) -> bool:
    screen_w, screen_h = app.screen.get_size()
    layout = get_layout(screen_w, screen_h)
    
    # Defaults
    if not hasattr(app, "manager_groups_scroll_y"):
        app.manager_groups_scroll_y = 0.0
    if not hasattr(app, "manager_comps_scroll_y"):
        app.manager_comps_scroll_y = 0.0
    if not hasattr(app, "manager_selected_group_idx"):
        app.manager_selected_group_idx = -1
    if not hasattr(app, "manager_editing_group_name"):
        app.manager_editing_group_name = ""
    if not hasattr(app, "manager_focus"):
        app.manager_focus = None
    if not hasattr(app, "manager_comp_buttons"):
        app.manager_comp_buttons = []

    # 1. Back out with ESC
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        # Commit group name edit first
        commit_group_name_edit(app)
        app.switch_to_sim()
        return True

    # 2. Key typing input
    if app.manager_focus == "group_name" and event.type == pygame.KEYDOWN:
        group_selected = 0 <= app.manager_selected_group_idx < len(app.groups)
        if group_selected:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                commit_group_name_edit(app)
                return True
            elif event.key == pygame.K_BACKSPACE:
                app.manager_editing_group_name = app.manager_editing_group_name[:-1]
                return True
            elif event.unicode and len(app.manager_editing_group_name) < 20:
                # Allow letters, numbers, spaces, underscores, and hyphens
                if event.unicode.isalnum() or event.unicode in (' ', '_', '-'):
                    app.manager_editing_group_name += event.unicode
                return True
        return True

    # 3. Mouse Clicks
    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos

        # Back Button Click
        if layout["back_btn"].collidepoint(event.pos):
            commit_group_name_edit(app)
            app.switch_to_sim()
            return True

        # Left Panel (Groups list) Click
        if layout["groups_panel"].collidepoint(event.pos):
            if event.button == 4: # Scroll Up
                app.manager_groups_scroll_y = max(0.0, app.manager_groups_scroll_y - 25.0)
                return True
            elif event.button == 5: # Scroll Down
                max_scroll = max(0.0, len(app.groups) * 50 - (layout["groups_panel"].height - 20))
                app.manager_groups_scroll_y = min(max_scroll, app.manager_groups_scroll_y + 25.0)
                return True

            if event.button == 1:
                # Commit previous name edit
                commit_group_name_edit(app)
                
                # Check group item click
                g_rect = layout["groups_panel"].inflate(-10, -10)
                rel_my = my - g_rect.y
                clicked_idx = int((rel_my + app.manager_groups_scroll_y) // 50)
                if 0 <= clicked_idx < len(app.groups):
                    app.manager_selected_group_idx = clicked_idx
                    app.manager_editing_group_name = app.groups[clicked_idx]["name"]
                    app.manager_focus = None
                return True

        # Add Group Click
        if layout["add_group_btn"].collidepoint(event.pos) and event.button == 1:
            commit_group_name_edit(app)
            new_name = get_unique_group_name(app.groups)
            new_group = {
                "name": new_name,
                "color": None,
                "components": []
            }
            app.groups.append(new_group)
            app.save_groups()
            app.manager_selected_group_idx = len(app.groups) - 1
            app.manager_editing_group_name = new_name
            app.manager_focus = "group_name" # Focus directly for easy naming
            return True

        # Delete Group Click
        if layout["del_group_btn"].collidepoint(event.pos) and event.button == 1:
            if 0 <= app.manager_selected_group_idx < len(app.groups):
                app.groups.pop(app.manager_selected_group_idx)
                app.save_groups()
                app.manager_selected_group_idx = 0 if app.groups else -1
                if app.manager_selected_group_idx >= 0:
                    app.manager_editing_group_name = app.groups[0]["name"]
                else:
                    app.manager_editing_group_name = ""
                app.manager_focus = None
            return True

        # Middle Panel (Group Details) Click
        if layout["details_panel"].collidepoint(event.pos) and event.button == 1:
            group_selected = 0 <= app.manager_selected_group_idx < len(app.groups)
            if group_selected:
                # Name text box focus
                name_box = pygame.Rect(layout["details_panel"].x + 20, layout["details_panel"].y + 45, layout["details_panel"].width - 40, 35)
                if name_box.collidepoint(event.pos):
                    app.manager_focus = "group_name"
                else:
                    commit_group_name_edit(app)
                    app.manager_focus = None

                # Checkbox toggle
                checkbox_rect = pygame.Rect(layout["details_panel"].x + 20, layout["details_panel"].y + 110, 20, 20)
                if checkbox_rect.collidepoint(event.pos):
                    group = app.groups[app.manager_selected_group_idx]
                    if group.get("color") is not None:
                        group["color"] = None
                    else:
                        group["color"] = [142, 68, 173]
                    app.save_groups()
                    return True

                # Check Slider Handles collision
                # Red Slider
                if getattr(app, "slider_r_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
                    group = app.groups[app.manager_selected_group_idx]
                    if group.get("color") is not None:
                        app.manager_dragging_slider = "R"
                        update_slider_val(app, mx)
                    return True
                # Green Slider
                elif getattr(app, "slider_g_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
                    group = app.groups[app.manager_selected_group_idx]
                    if group.get("color") is not None:
                        app.manager_dragging_slider = "G"
                        update_slider_val(app, mx)
                    return True
                # Blue Slider
                elif getattr(app, "slider_b_rect", pygame.Rect(0,0,0,0)).collidepoint(event.pos):
                    group = app.groups[app.manager_selected_group_idx]
                    if group.get("color") is not None:
                        app.manager_dragging_slider = "B"
                        update_slider_val(app, mx)
                    return True

            return True

        # Right Panel (Components list) Click
        if layout["comps_panel"].collidepoint(event.pos):
            if event.button == 4: # Scroll Up
                app.manager_comps_scroll_y = max(0.0, app.manager_comps_scroll_y - 25.0)
                return True
            elif event.button == 5: # Scroll Down
                custom_gates = [item for item in app.gui_library if item["type"] == "gate"]
                max_scroll = max(0.0, len(custom_gates) * 52 - (layout["comps_panel"].height - 20))
                app.manager_comps_scroll_y = min(max_scroll, app.manager_comps_scroll_y + 25.0)
                return True

            if event.button == 1:
                commit_group_name_edit(app)
                # Check button clicks in comps
                for btn in app.manager_comp_buttons:
                    # Checkbox click (membership assign/remove)
                    if btn["cb_rect"].collidepoint(event.pos):
                        group_selected = 0 <= app.manager_selected_group_idx < len(app.groups)
                        if group_selected:
                            active_group = app.groups[app.manager_selected_group_idx]
                            comp_name = btn["name"]
                            
                            # Toggle membership
                            if comp_name in active_group.get("components", []):
                                active_group["components"].remove(comp_name)
                            else:
                                # Remove from any other group first
                                for g in app.groups:
                                    if comp_name in g.get("components", []):
                                        g["components"].remove(comp_name)
                                active_group["components"].append(comp_name)
                            app.save_groups()
                        return True

                    # Delete button click
                    if btn["del_rect"].collidepoint(event.pos):
                        comp_name = btn["name"]
                        
                        # Dependency safety check!
                        dependency = check_component_dependencies(app, comp_name)
                        if dependency:
                            app.manager_warning = f"Cannot delete '{comp_name}': used in composite gate '{dependency}'!"
                            app.manager_warning_time = pygame.time.get_ticks()
                        else:
                            # Proceed with deletion
                            delete_component_from_library(app, comp_name)
                        return True
                return True

    # 4. Slider Dragging (Mouse Motion)
    elif event.type == pygame.MOUSEMOTION:
        if getattr(app, "manager_dragging_slider", None) is not None:
            mx, my = event.pos
            update_slider_val(app, mx)
            return True

    # 5. Mouse release clears slider dragging
    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            app.manager_dragging_slider = None
            return True

    return False

def commit_group_name_edit(app: Any):
    """Commits the group name changes if unique and non-empty."""
    if 0 <= app.manager_selected_group_idx < len(app.groups):
        new_name = app.manager_editing_group_name.strip()
        if new_name != "" and is_group_name_unique(app.groups, new_name, app.manager_selected_group_idx):
            app.groups[app.manager_selected_group_idx]["name"] = new_name
            app.save_groups()
        else:
            # Revert to original
            app.manager_editing_group_name = app.groups[app.manager_selected_group_idx]["name"]

def update_slider_val(app: Any, mouse_x: int):
    """Calculates slider values dynamically based on mouse drag coordinates."""
    layout = get_layout(app.screen.get_width(), app.screen.get_height())
    slider_width = layout["details_panel"].width - 50
    slider_x = layout["details_panel"].x + 25
    
    ratio = max(0.0, min(1.0, (mouse_x - slider_x) / slider_width))
    val = int(ratio * 255.0)

    group = app.groups[app.manager_selected_group_idx]
    if group.get("color") is not None:
        if app.manager_dragging_slider == "R":
            group["color"][0] = val
        elif app.manager_dragging_slider == "G":
            group["color"][1] = val
        elif app.manager_dragging_slider == "B":
            group["color"][2] = val
        app.save_groups()

def delete_component_from_library(app: Any, component_name: str):
    """Removes a component template completely from LogicComponentLib.json and group memberships."""
    # 1. Load from file
    lib_path = 'D:\\PyInteractive\\mode\\LogicGate\\LogicComponentLib.json'
    templates = []
    if os.path.exists(lib_path):
        try:
            with open(lib_path, "r") as f:
                templates = json.load(f)
        except Exception:
            templates = []
            
    # Filter out component
    templates = [t for t in templates if t.get("name") != component_name]

    # Save local file
    try:
        with open(lib_path, "w") as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"Error saving updated library: {e}")
        return

    # Sync to root file
    root_lib_path = 'D:\\PyInteractive\\LogicComponentLib.json'
    try:
        with open(root_lib_path, "w") as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"Error syncing updated library to root: {e}")

    # 2. Remove from groups
    for g in app.groups:
        if component_name in g.get("components", []):
            g["components"].remove(component_name)
    app.save_groups()

    # 3. Reload app library templates
    from mode.LogicGate.gui import load_gui_library
    app.gui_library = load_gui_library()
    app.manager_warning = f"Successfully deleted component '{component_name}'."
    app.manager_warning_time = pygame.time.get_ticks()
