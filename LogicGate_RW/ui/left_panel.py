from typing import Any, Tuple, Optional
import pygame

from include import Color
from LogicGate_RW.core.ui_node import UINode, UIGlobalInputNode, UIGlobalOutputNode
from LogicGate_RW.core.ui_component import UILogicComponent
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
    return True

def draw_left_panel(screen: pygame.Surface, app: Any) -> None:
    slide_ratio = getattr(app, "left_panel_slide_ratio", 0.0)
    if slide_ratio <= 0.0:
        return

    screen_w, screen_h = screen.get_size()
    panel_x = -PANEL_WIDTH + (PANEL_WIDTH * slide_ratio)

    panel_surf = pygame.Surface((PANEL_WIDTH, screen_h), pygame.SRCALPHA)
    panel_surf.fill((20, 20, 26, 245))
    screen.blit(panel_surf, (int(panel_x), 0))

    pygame.draw.line(screen, (142, 68, 173), (int(panel_x + PANEL_WIDTH), 0), (int(panel_x + PANEL_WIDTH), screen_h), 2)

    try:
        title_font = pygame.font.Font(None, 24)
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

def handle_left_panel_event(app: Any, event: pygame.event.Event) -> bool:
    slide_ratio = getattr(app, "left_panel_slide_ratio", 0.0)
    if slide_ratio <= 0.0:
        return False

    panel_x = -PANEL_WIDTH + (PANEL_WIDTH * slide_ratio)
    panel_rect = pygame.Rect(int(panel_x), 0, PANEL_WIDTH, app.screen.get_height())

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

    return False
