<<<<<<< HEAD
import re
=======
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d
from typing import Any, Tuple, Optional
import pygame

from include import Color
from LogicGate_RW.core.ui_node import UINode, UIGlobalInputNode, UIGlobalOutputNode
from LogicGate_RW.core.ui_component import UILogicComponent
<<<<<<< HEAD
from LogicGate_RW.core.ui_arrays import UIArrayNode, UINodeArray
from LogicGate_RW.ui.style import shared_style

PANEL_WIDTH = 300

def is_name_valid_and_unique(app: Any, node: Any, name: str) -> bool:
    """Checks if a proposed label/name is non-empty, valid alphanumeric/underscore, and unique."""
    name = name.strip()
    if not name:
        return False
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        return False

    proposed_label = name

    for obj in app.objects:
        if isinstance(obj, (UIGlobalInputNode, UIGlobalOutputNode, UINodeArray, UIArrayNode, UILogicComponent)) and obj is not node:
            if obj.label == proposed_label:
                return False

=======
from LogicGate_RW.core.ui_arrays import UINodeArray
from LogicGate_RW.ui.style import shared_style

PANEL_WIDTH = 260

def is_name_valid_and_unique(app: Any, node: Any, name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    for obj in app.objects:
        if obj is not node and getattr(obj, "label", None) == name:
            return False
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d
    return True

def draw_left_panel(screen: pygame.Surface, app: Any) -> None:
    slide_ratio = getattr(app, "left_panel_slide_ratio", 0.0)
    if slide_ratio <= 0.0:
        return

    screen_w, screen_h = screen.get_size()
    panel_x = -PANEL_WIDTH + (PANEL_WIDTH * slide_ratio)

    panel_surf = pygame.Surface((PANEL_WIDTH, screen_h), pygame.SRCALPHA)
<<<<<<< HEAD
    panel_surf.fill((20, 20, 25, 245))
=======
    panel_surf.fill((20, 20, 26, 245))
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d
    screen.blit(panel_surf, (int(panel_x), 0))

    pygame.draw.line(screen, (142, 68, 173), (int(panel_x + PANEL_WIDTH), 0), (int(panel_x + PANEL_WIDTH), screen_h), 2)

    try:
        title_font = pygame.font.Font(None, 24)
<<<<<<< HEAD
        lbl_font = pygame.font.Font(None, 18)
        warn_font = pygame.font.Font(None, 14)
    except Exception:
        title_font = pygame.font.SysFont("arial", 24)
        lbl_font = pygame.font.SysFont("arial", 18)
        warn_font = pygame.font.SysFont("arial", 14)

    title = title_font.render("Global Nodes & Components (F2)", True, (142, 68, 173))
    screen.blit(title, (int(panel_x + 20), 20))

    sub_txt = lbl_font.render("Click item to view | Click edit to rename", True, (140, 140, 150))
    screen.blit(sub_txt, (int(panel_x + 20), 45))

    pygame.draw.line(screen, (50, 50, 55), (int(panel_x + 15), 70), (int(panel_x + PANEL_WIDTH - 15), 70), 1)

    # Collect nodes
    targets = []
    for obj in app.objects:
        if isinstance(obj, (UIGlobalInputNode, UIGlobalOutputNode, UINodeArray, UILogicComponent)):
            targets.append(obj)
            if isinstance(obj, UINodeArray):
                for sub in obj.nodes:
                    targets.append(sub)

    y_offset = 80 - getattr(app, "left_panel_scroll_y", 0.0)
    mouse_pos = pygame.mouse.get_pos()

    for obj in targets:
        if 40 <= y_offset <= screen_h - 40:
            is_sub = isinstance(obj, UIArrayNode)
            indent = 30 if is_sub else 15
            w = PANEL_WIDTH - 30 - (15 if is_sub else 0)
            item_rect = pygame.Rect(int(panel_x + indent), int(y_offset), w, 36)

            is_sel = (getattr(app, "selected_node", None) is obj)
            is_editing = (getattr(app, "editing_node", None) is obj)
            is_hovered = item_rect.collidepoint(mouse_pos)

            bg_col = (45, 40, 60) if is_editing else ((38, 38, 48) if is_sel else ((32, 32, 38) if is_hovered else (25, 25, 30)))
            b_col = (255, 220, 0) if is_editing else ((142, 68, 173) if is_sel else (60, 60, 70))

            pygame.draw.rect(screen, bg_col, item_rect, border_radius=5)
            pygame.draw.rect(screen, b_col, item_rect, 1, border_radius=5)

            if is_editing:
                # Text input box when editing
                val_str = getattr(app, "editing_name", "")
                is_valid = is_name_valid_and_unique(app, obj, val_str)
                cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                txt_surf = lbl_font.render(val_str + cursor, True, (255, 255, 255) if is_valid else (255, 100, 100))
                screen.blit(txt_surf, (item_rect.x + 10, item_rect.centery - txt_surf.get_height() / 2))

                if not is_valid and val_str.strip():
                    err_surf = warn_font.render("Name taken or invalid", True, (255, 90, 80))
                    screen.blit(err_surf, (item_rect.right - err_surf.get_width() - 8, item_rect.centery - err_surf.get_height() / 2))
            else:
                # Static display
                disp_name = obj.label
                txt_surf = lbl_font.render(disp_name, True, (240, 240, 245))
                screen.blit(txt_surf, (item_rect.x + 10, item_rect.centery - txt_surf.get_height() / 2))

                # Edit button on right edge
                edit_btn_rect = pygame.Rect(item_rect.right - 45, item_rect.y + 6, 38, 24)
                hover_edit = edit_btn_rect.collidepoint(mouse_pos)
                pygame.draw.rect(screen, (70, 70, 85) if hover_edit else (45, 45, 55), edit_btn_rect, border_radius=3)
                e_txt = warn_font.render("edit", True, (255, 255, 255) if hover_edit else (180, 180, 190))
                screen.blit(e_txt, (edit_btn_rect.centerx - e_txt.get_width() / 2, edit_btn_rect.centery - e_txt.get_height() / 2))

        y_offset += 42
=======
        item_font = pygame.font.Font(None, 18)
    except Exception:
        title_font = pygame.font.SysFont("arial", 24)
        item_font = pygame.font.SysFont("arial", 18)

    title = title_font.render("Canvas Nodes (F2)", True, (240, 240, 245))
    screen.blit(title, (int(panel_x + 20), 20))

    # List nodes
    y_offset = 60 - getattr(app, "left_panel_scroll_y", 0.0)
    mouse_pos = pygame.mouse.get_pos()

    for obj in app.objects:
        if isinstance(obj, (UIGlobalInputNode, UIGlobalOutputNode, UINodeArray, UILogicComponent)):
            item_rect = pygame.Rect(int(panel_x + 15), int(y_offset), PANEL_WIDTH - 30, 32)
            if 40 <= y_offset <= screen_h - 40:
                is_hovered = item_rect.collidepoint(mouse_pos)
                is_sel = (getattr(app, "selected_node", None) is obj)
                bg_col = (45, 45, 55) if is_sel else ((35, 35, 42) if is_hovered else (28, 28, 34))
                pygame.draw.rect(screen, bg_col, item_rect, border_radius=4)
                pygame.draw.rect(screen, (255, 220, 0) if is_sel else (60, 60, 70), item_rect, 1, border_radius=4)

                lbl_text = obj.label
                txt = item_font.render(lbl_text, True, (255, 255, 255))
                screen.blit(txt, (item_rect.x + 10, item_rect.centery - txt.get_height() / 2))

            y_offset += 38
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d

def handle_left_panel_event(app: Any, event: pygame.event.Event) -> bool:
    slide_ratio = getattr(app, "left_panel_slide_ratio", 0.0)
    if slide_ratio <= 0.0:
        return False

    panel_x = -PANEL_WIDTH + (PANEL_WIDTH * slide_ratio)
    panel_rect = pygame.Rect(int(panel_x), 0, PANEL_WIDTH, app.screen.get_height())

<<<<<<< HEAD
    # 1. Text typing when editing a node name
    if getattr(app, "editing_node", None) is not None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                val_to_commit = getattr(app, "editing_name", "").strip()
                if is_name_valid_and_unique(app, app.editing_node, val_to_commit):
                    app.editing_node.custom_name = val_to_commit
                    app.editing_node = None
                return True
            elif event.key == pygame.K_ESCAPE:
                app.editing_node = None
                return True
            elif event.key == pygame.K_BACKSPACE:
                app.editing_name = app.editing_name[:-1]
                return True
            elif event.unicode and event.unicode.isprintable() and len(getattr(app, "editing_name", "")) < 18:
                if event.unicode.isalnum() or event.unicode == "_":
                    app.editing_name = getattr(app, "editing_name", "") + event.unicode
                return True
            return True

    # 2. Panel click interactions
    if event.type == pygame.MOUSEBUTTONDOWN:
        if panel_rect.collidepoint(event.pos):
            if event.button == 1:
                targets = []
                for obj in app.objects:
                    if isinstance(obj, (UIGlobalInputNode, UIGlobalOutputNode, UINodeArray, UILogicComponent)):
                        targets.append(obj)
                        if isinstance(obj, UINodeArray):
                            for sub in obj.nodes:
                                targets.append(sub)

                y_offset = 80 - getattr(app, "left_panel_scroll_y", 0.0)
                for obj in targets:
                    is_sub = isinstance(obj, UIArrayNode)
                    indent = 30 if is_sub else 15
                    w = PANEL_WIDTH - 30 - (15 if is_sub else 0)
                    item_rect = pygame.Rect(int(panel_x + indent), int(y_offset), w, 36)
                    edit_btn_rect = pygame.Rect(item_rect.right - 45, item_rect.y + 6, 38, 24)

                    if edit_btn_rect.collidepoint(event.pos):
                        app.editing_node = obj
                        app.editing_name = obj.label
                        app.select_node(obj)
                        return True
                    elif item_rect.collidepoint(event.pos):
                        app.select_node(obj)
                        # Center canvas viewport on node
                        screen_w = app.screen.get_width()
                        screen_h = app.screen.get_height()
                        app.offset[0] = screen_w / 2.0 - (obj.center[0] * screen_w * app.zoom_scale)
                        app.offset[1] = screen_h / 2.0 - (obj.center[1] * screen_h * app.zoom_scale)
                        return True

                    y_offset += 42
            elif event.button == 4:
                app.left_panel_scroll_y = max(0.0, getattr(app, "left_panel_scroll_y", 0.0) - 30.0)
                return True
            elif event.button == 5:
                app.left_panel_scroll_y = getattr(app, "left_panel_scroll_y", 0.0) + 30.0
                return True
            return True
=======
    if event.type == pygame.MOUSEBUTTONDOWN:
        if panel_rect.collidepoint(event.pos):
            if event.button == 1:
                # Check item click
                y_offset = 60 - getattr(app, "left_panel_scroll_y", 0.0)
                for obj in app.objects:
                    if isinstance(obj, (UIGlobalInputNode, UIGlobalOutputNode, UINodeArray, UILogicComponent)):
                        item_rect = pygame.Rect(int(panel_x + 15), int(y_offset), PANEL_WIDTH - 30, 32)
                        if item_rect.collidepoint(event.pos):
                            app.select_node(obj)
                            # Center canvas viewport on node
                            screen_w = app.screen.get_width()
                            screen_h = app.screen.get_height()
                            app.offset[0] = screen_w / 2.0 - (obj.center[0] * screen_w * app.zoom_scale)
                            app.offset[1] = screen_h / 2.0 - (obj.center[1] * screen_h * app.zoom_scale)
                            return True
                        y_offset += 38
            elif event.button == 4:
                app.left_panel_scroll_y = max(0.0, app.left_panel_scroll_y - 30.0)
                return True
            elif event.button == 5:
                app.left_panel_scroll_y += 30.0
                return True
            return True  # Absorb click inside panel
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d

    return False
