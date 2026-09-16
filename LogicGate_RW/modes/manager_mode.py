from typing import Any, Tuple, Optional, List, Dict
import pygame

from LogicGate_RW.storage.library_adapter import save_groups, save_component_template
from LogicGate_RW.ui.widgets import draw_slider, draw_button
from LogicGate_RW.ui.style import shared_style

def get_layout(screen_w: int, screen_h: int) -> Dict[str, pygame.Rect]:
    return {
        "groups_panel": pygame.Rect(30, 80, 260, screen_h - 180),
        "details_panel": pygame.Rect(310, 80, 320, screen_h - 180),
        "comps_panel": pygame.Rect(650, 80, screen_w - 680, screen_h - 180),
        "back_btn": pygame.Rect(screen_w - 180, 20, 150, 38),
        "add_group_btn": pygame.Rect(30, screen_h - 85, 120, 38),
        "del_group_btn": pygame.Rect(170, screen_h - 85, 120, 38),
    }

def draw_manager(screen: pygame.Surface, app: Any) -> None:
    screen_w, screen_h = screen.get_size()
    layout = get_layout(screen_w, screen_h)
    mouse_pos = pygame.mouse.get_pos()

    try:
        title_font = pygame.font.Font(None, 28)
        lbl_font = pygame.font.Font(None, 20)
        item_font = pygame.font.Font(None, 18)
    except Exception:
        title_font = pygame.font.SysFont("arial", 28)
        lbl_font = pygame.font.SysFont("arial", 20)
        item_font = pygame.font.SysFont("arial", 18)

    # Header
    title = title_font.render("Component Library & Groups Manager", True, (240, 240, 245))
    screen.blit(title, (30, 25))

    # Back button
    draw_button(screen, layout["back_btn"], "Back to Sim", mouse_pos)

    # 1. Groups panel
    gp = layout["groups_panel"]
    pygame.draw.rect(screen, (22, 22, 28), gp, border_radius=6)
    pygame.draw.rect(screen, (50, 50, 65), gp, 1, border_radius=6)
    g_title = lbl_font.render("Groups", True, (200, 200, 210))
    screen.blit(g_title, (gp.x + 15, gp.y + 12))

    y = gp.y + 42
    for i, g in enumerate(getattr(app, "groups", [])):
        r = pygame.Rect(gp.x + 10, y, gp.width - 20, 32)
        is_sel = (getattr(app, "manager_selected_group_idx", 0) == i)
        pygame.draw.rect(screen, (45, 45, 58) if is_sel else (30, 30, 38), r, border_radius=4)
        pygame.draw.rect(screen, (255, 220, 0) if is_sel else (60, 60, 75), r, 1, border_radius=4)

        col = g.get("color", [142, 68, 173])
        pygame.draw.circle(screen, col[:3], (r.x + 16, r.centery), 6)
        nm = item_font.render(g["name"], True, (255, 255, 255))
        screen.blit(nm, (r.x + 30, r.centery - nm.get_height() / 2))
        y += 38

    draw_button(screen, layout["add_group_btn"], "+ Group", mouse_pos)
    draw_button(screen, layout["del_group_btn"], "- Group", mouse_pos, base_color=shared_style.get_color_obj("node_active_border"))

    # 2. Group Details panel
    dp = layout["details_panel"]
    pygame.draw.rect(screen, (22, 22, 28), dp, border_radius=6)
    pygame.draw.rect(screen, (50, 50, 65), dp, 1, border_radius=6)
    d_title = lbl_font.render("Group Settings", True, (200, 200, 210))
    screen.blit(d_title, (dp.x + 15, dp.y + 12))

    cur_idx = getattr(app, "manager_selected_group_idx", 0)
    if 0 <= cur_idx < len(app.groups):
        grp = app.groups[cur_idx]
        g_name = grp["name"]

        # Name text
        nm_box = pygame.Rect(dp.x + 15, dp.y + 45, dp.width - 30, 34)
        is_foc = (getattr(app, "manager_focus", None) == "group_name")
        pygame.draw.rect(screen, (35, 35, 45), nm_box, border_radius=4)
        pygame.draw.rect(screen, (255, 220, 0) if is_foc else (70, 70, 85), nm_box, 1, border_radius=4)
        t_val = app.manager_editing_group_name if is_foc else g_name
        nm_surf = item_font.render(t_val, True, (255, 255, 255))
        screen.blit(nm_surf, (nm_box.x + 10, nm_box.centery - nm_surf.get_height() / 2))

        # Color sliders
        g_color = grp.get("color", [142, 68, 173])
        draw_slider(screen, dp.x + 15, dp.y + 120, dp.width - 30, g_color[0], 0, 255, "Red", lbl_font, (230, 80, 80))
        draw_slider(screen, dp.x + 15, dp.y + 175, dp.width - 30, g_color[1], 0, 255, "Green", lbl_font, (80, 220, 100))
        draw_slider(screen, dp.x + 15, dp.y + 230, dp.width - 30, g_color[2], 0, 255, "Blue", lbl_font, (80, 140, 240))

    # 3. Components in Group panel
    cp = layout["comps_panel"]
    pygame.draw.rect(screen, (22, 22, 28), cp, border_radius=6)
    pygame.draw.rect(screen, (50, 50, 65), cp, 1, border_radius=6)
    c_title = lbl_font.render("Assigned Components", True, (200, 200, 210))
    screen.blit(c_title, (cp.x + 15, cp.y + 12))

    if 0 <= cur_idx < len(app.groups):
        grp = app.groups[cur_idx]
        comps = grp.get("components", [])
        y_c = cp.y + 45
        for c_name in comps:
            cr = pygame.Rect(cp.x + 15, y_c, cp.width - 30, 30)
            pygame.draw.rect(screen, (35, 35, 45), cr, border_radius=4)
            t_c = item_font.render(c_name, True, (220, 220, 230))
            screen.blit(t_c, (cr.x + 10, cr.centery - t_c.get_height() / 2))
            y_c += 35

def handle_manager_event(app: Any, event: pygame.event.Event) -> bool:
    screen_w, screen_h = app.screen.get_size()
    layout = get_layout(screen_w, screen_h)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # Back button
        if layout["back_btn"].collidepoint(event.pos):
            app.switch_to_sim()
            return True

        # Group selection
        gp = layout["groups_panel"]
        if gp.collidepoint(event.pos):
            y = gp.y + 42
            for i, g in enumerate(getattr(app, "groups", [])):
                r = pygame.Rect(gp.x + 10, y, gp.width - 20, 32)
                if r.collidepoint(event.pos):
                    app.manager_selected_group_idx = i
                    app.manager_editing_group_name = g["name"]
                    return True
                y += 38

        # Add Group
        if layout["add_group_btn"].collidepoint(event.pos):
            new_name = f"Group {len(app.groups) + 1}"
            app.groups.append({
                "name": new_name,
                "color": [142, 68, 173],
                "components": []
            })
            app.save_groups()
            app.manager_selected_group_idx = len(app.groups) - 1
            return True

        # Delete Group
        if layout["del_group_btn"].collidepoint(event.pos):
            cur = getattr(app, "manager_selected_group_idx", 0)
            if 0 <= cur < len(app.groups):
                # Don't delete Inputs or Outputs
                if app.groups[cur]["name"] not in ("Inputs", "Outputs"):
                    app.groups.pop(cur)
                    app.save_groups()
                    app.manager_selected_group_idx = max(0, cur - 1)
            return True

        # Name textbox
        dp = layout["details_panel"]
        nm_box = pygame.Rect(dp.x + 15, dp.y + 45, dp.width - 30, 34)
        if nm_box.collidepoint(event.pos):
            app.manager_focus = "group_name"
            return True
        else:
            app.manager_focus = None

        # Sliders
        cur = getattr(app, "manager_selected_group_idx", 0)
        if 0 <= cur < len(app.groups):
            w = dp.width - 30
            if pygame.Rect(dp.x + 5, dp.y + 110, w + 20, 25).collidepoint(event.pos):
                app.manager_dragging_slider = "r"
                return True
            if pygame.Rect(dp.x + 5, dp.y + 165, w + 20, 25).collidepoint(event.pos):
                app.manager_dragging_slider = "g"
                return True
            if pygame.Rect(dp.x + 5, dp.y + 220, w + 20, 25).collidepoint(event.pos):
                app.manager_dragging_slider = "b"
                return True

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        if getattr(app, "manager_dragging_slider", None):
            app.manager_dragging_slider = None
            app.save_groups()

    elif event.type == pygame.MOUSEMOTION:
        slider = getattr(app, "manager_dragging_slider", None)
        cur = getattr(app, "manager_selected_group_idx", 0)
        if slider and 0 <= cur < len(app.groups):
            dp = layout["details_panel"]
            ratio = max(0.0, min(1.0, (event.pos[0] - (dp.x + 15)) / float(dp.width - 30)))
            val = int(ratio * 255)
            grp = app.groups[cur]
            if "color" not in grp:
                grp["color"] = [142, 68, 173]
            if slider == "r":
                grp["color"][0] = val
            elif slider == "g":
                grp["color"][1] = val
            elif slider == "b":
                grp["color"][2] = val
            return True

    elif event.type == pygame.KEYDOWN and getattr(app, "manager_focus", None) == "group_name":
        cur = getattr(app, "manager_selected_group_idx", 0)
        if 0 <= cur < len(app.groups):
            if event.key == pygame.K_BACKSPACE:
                app.manager_editing_group_name = app.manager_editing_group_name[:-1]
                app.groups[cur]["name"] = app.manager_editing_group_name
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                app.manager_focus = None
                app.save_groups()
            else:
                if len(app.manager_editing_group_name) < 20 and event.unicode.isprintable():
                    app.manager_editing_group_name += event.unicode
                    app.groups[cur]["name"] = app.manager_editing_group_name
            return True

    return False
