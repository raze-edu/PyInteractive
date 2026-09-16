import math
from typing import Any, List, Dict, Tuple, Optional
import pygame

from include import Color
from LogicGate_RW.ui.style import shared_style

def get_picker_items(app: Any) -> List[dict]:
    """Generates grouped or standalone picker items from the active library and groups."""
    items = [
        {"type": "input", "name": "Input Node", "template": None},
        {"type": "output", "name": "Output Node", "template": None}
    ]

    active_group = getattr(app, "active_picker_group", None)
    if active_group is not None:
        # Show back button and group members
        items.append({"type": "back", "name": "< Back", "template": None})
        group_comps = active_group.get("components", [])
        for item in app.gui_library:
            if item["name"] in group_comps:
                items.append(item)
        return items

    grouped_names = set()
    for g in getattr(app, "groups", []):
        for c in g.get("components", []):
            grouped_names.add(c)

    # Standalone components
    for item in app.gui_library:
        if item["type"] == "gate" and item["name"] not in grouped_names:
            items.append(item)

    # Categories/Groups
    for g in getattr(app, "groups", []):
        items.append({
            "type": "group",
            "name": g["name"],
            "group_dict": g
        })

    return items

def update_bottom_bar(app: Any, dt: float) -> None:
    mouse_pos = pygame.mouse.get_pos()
    screen_h = app.screen.get_height()
    speed = 5.0

    if mouse_pos[1] > screen_h - 60 or (app.bar_slide_ratio > 0.05 and mouse_pos[1] > screen_h - 115):
        app.bar_slide_ratio = min(1.0, app.bar_slide_ratio + speed * dt)
    else:
        app.bar_slide_ratio = max(0.0, app.bar_slide_ratio - speed * dt)

def draw_bottom_bar(screen: pygame.Surface, app: Any) -> None:
    screen_w, screen_h = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()

    # Top-right action buttons
    # 1. Plus / Builder button
    btn_plus = pygame.Rect(screen_w - 60, 20, 40, 40)
    hover_plus = btn_plus.collidepoint(mouse_pos)
    plus_col = (170, 90, 210) if hover_plus else (142, 68, 173)
    pygame.draw.rect(screen, plus_col, btn_plus, border_radius=8)
    try:
        font_plus = pygame.font.Font(None, 36)
    except Exception:
        font_plus = pygame.font.SysFont("arial", 36)
    t_plus = font_plus.render("+", True, (255, 255, 255))
    screen.blit(t_plus, (btn_plus.centerx - t_plus.get_width() / 2, btn_plus.centery - t_plus.get_height() / 2))

    # 2. Manage button
    btn_manage = pygame.Rect(screen_w - 150, 20, 80, 40)
    hover_m = btn_manage.collidepoint(mouse_pos)
    m_col = (170, 90, 210) if hover_m else (142, 68, 173)
    pygame.draw.rect(screen, m_col, btn_manage, border_radius=8)
    try:
        font_btn = pygame.font.Font(None, 20)
    except Exception:
        font_btn = pygame.font.SysFont("arial", 20)
    t_m = font_btn.render("Manage", True, (255, 255, 255))
    screen.blit(t_m, (btn_manage.centerx - t_m.get_width() / 2, btn_manage.centery - t_m.get_height() / 2))

    # 3. Clear button
    btn_clear = pygame.Rect(screen_w - 240, 20, 80, 40)
    hover_c = btn_clear.collidepoint(mouse_pos)
    c_col = (250, 90, 80) if hover_c else (231, 76, 60)
    pygame.draw.rect(screen, c_col, btn_clear, border_radius=8)
    t_c = font_btn.render("Clear", True, (255, 255, 255))
    screen.blit(t_c, (btn_clear.centerx - t_c.get_width() / 2, btn_clear.centery - t_c.get_height() / 2))

    # Placement preview stamp under cursor
    if app.selected_placement_item is not None:
        item = app.selected_placement_item
        prev = pygame.Surface((80, 50), pygame.SRCALPHA)
        if item["type"] == "input":
            pygame.draw.circle(prev, (46, 204, 113, 160), (40, 25), 14)
        elif item["type"] == "output":
            pygame.draw.circle(prev, (70, 70, 75, 160), (40, 25), 14)
        elif item["type"] == "array":
            col = (142, 68, 173) if "Input" in item["name"] else (46, 204, 113)
            pygame.draw.rect(prev, (col[0], col[1], col[2], 160), (10, 10, 60, 30), border_radius=4)
        else:
            pygame.draw.rect(prev, (142, 68, 173, 160), (10, 10, 60, 30), border_radius=4)
        screen.blit(prev, (mouse_pos[0] - 40, mouse_pos[1] - 25))

    # Sliding tray at bottom
    if app.bar_slide_ratio > 0.0:
        bar_h = 110
        bar_y = screen_h - (bar_h * app.bar_slide_ratio)

        bar_surf = pygame.Surface((screen_w, bar_h), pygame.SRCALPHA)
        bar_surf.fill((22, 22, 28, 245))
        screen.blit(bar_surf, (0, int(bar_y)))

        pygame.draw.line(screen, (142, 68, 173), (0, int(bar_y)), (screen_w, int(bar_y)), 2)

        # Scroll buttons
        left_btn = pygame.Rect(10, int(bar_y + 35), 30, 40)
        right_btn = pygame.Rect(screen_w - 40, int(bar_y + 35), 30, 40)
        pygame.draw.rect(screen, (40, 40, 45), left_btn, border_radius=4)
        pygame.draw.rect(screen, (40, 40, 45), right_btn, border_radius=4)

        try:
            f_arrow = pygame.font.Font(None, 24)
            f_label = pygame.font.Font(None, 13)
        except Exception:
            f_arrow = pygame.font.SysFont("arial", 24)
            f_label = pygame.font.SysFont("arial", 13)

        t_lt = f_arrow.render("<", True, (240, 240, 245))
        t_rt = f_arrow.render(">", True, (240, 240, 245))
        screen.blit(t_lt, (left_btn.centerx - t_lt.get_width() / 2, left_btn.centery - t_lt.get_height() / 2))
        screen.blit(t_rt, (right_btn.centerx - t_rt.get_width() / 2, right_btn.centery - t_rt.get_height() / 2))

        # Items list
        items = get_picker_items(app)
        start_x = 55
        item_w = 90
        item_h = 80
        spacing = 105

        clip_w = screen_w - 100
        clip_surf = pygame.Surface((clip_w, bar_h), pygame.SRCALPHA)

        for i, itm in enumerate(items):
            ix = start_x + i * spacing - app.bar_scroll_x
            ir = pygame.Rect(ix, 15, item_w, item_h)

            is_sel = (app.selected_placement_item == itm)
            b_col = (255, 220, 0) if is_sel else (75, 75, 85)

            card_bg = (35, 35, 42)
            pygame.draw.rect(clip_surf, card_bg, ir, border_radius=6)
            pygame.draw.rect(clip_surf, b_col, ir, 2, border_radius=6)

            # Miniature icon
            if itm["type"] == "input":
                pygame.draw.circle(clip_surf, (46, 204, 113), (ir.centerx, ir.y + 30), 12)
            elif itm["type"] == "output":
                pygame.draw.circle(clip_surf, (70, 70, 75), (ir.centerx, ir.y + 30), 12)
            elif itm["type"] == "array":
                col = (142, 68, 173) if "Input" in itm["name"] else (46, 204, 113)
                pygame.draw.rect(clip_surf, col, pygame.Rect(ir.centerx - 16, ir.y + 18, 32, 22), border_radius=3)
            elif itm["type"] == "group":
                g_col = itm.get("group_dict", {}).get("color", [142, 68, 173])
                pygame.draw.rect(clip_surf, g_col[:3], pygame.Rect(ir.centerx - 16, ir.y + 18, 32, 22), border_radius=3)
            elif itm["type"] == "back":
                t_b = f_arrow.render("<<", True, (255, 220, 0))
                clip_surf.blit(t_b, (ir.centerx - t_b.get_width() / 2, ir.y + 20))
            else:
                pygame.draw.rect(clip_surf, (142, 68, 173), pygame.Rect(ir.centerx - 16, ir.y + 18, 32, 22), border_radius=3)

            # Name label
            nl = f_label.render(itm["name"], True, (220, 220, 230))
            clip_surf.blit(nl, (ir.centerx - nl.get_width() / 2, ir.y + 55))

        screen.blit(clip_surf, (50, int(bar_y)))

def handle_bottom_bar_event(app: Any, event: pygame.event.Event) -> bool:
    screen_w, screen_h = app.screen.get_size()

    # 1. Top action buttons
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if pygame.Rect(screen_w - 60, 20, 40, 40).collidepoint(event.pos):
            app.switch_to_builder()
            return True
        if pygame.Rect(screen_w - 150, 20, 80, 40).collidepoint(event.pos):
            app.switch_to_manager()
            return True
        if pygame.Rect(screen_w - 240, 20, 80, 40).collidepoint(event.pos):
            app.objects.clear()
            app.connections.clear()
            app.clear_selection()
            return True

    # 2. Bottom tray interactions
    if app.bar_slide_ratio > 0.0:
        bar_h = 110
        bar_y = screen_h - (bar_h * app.bar_slide_ratio)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Scroll buttons
                if pygame.Rect(10, int(bar_y + 35), 30, 40).collidepoint(event.pos):
                    app.bar_scroll_x = max(0.0, app.bar_scroll_x - 120.0)
                    return True
                if pygame.Rect(screen_w - 40, int(bar_y + 35), 30, 40).collidepoint(event.pos):
                    app.bar_scroll_x += 120.0
                    return True

                # Check items in tray
                if event.pos[1] >= bar_y:
                    rel_mx = event.pos[0] - 50
                    rel_my = event.pos[1] - bar_y
                    items = get_picker_items(app)
                    start_x = 55
                    spacing = 105
                    for i, itm in enumerate(items):
                        ix = start_x + i * spacing - app.bar_scroll_x
                        ir = pygame.Rect(ix, 15, 90, 80)
                        if ir.collidepoint((rel_mx, rel_my)):
                            if itm["type"] == "back":
                                app.active_picker_group = None
                            elif itm["type"] == "group":
                                app.active_picker_group = itm["group_dict"]
                            else:
                                app.selected_placement_item = itm
                            return True
                    return True  # Absorb click inside tray

            elif event.button in (4, 5):  # Mouse wheel scroll on tray
                if event.pos[1] >= bar_y:
                    if event.button == 4:
                        app.bar_scroll_x = max(0.0, app.bar_scroll_x - 60.0)
                    else:
                        app.bar_scroll_x += 60.0
                    return True

    return False
