import math
from typing import Any, Tuple, Optional, List
import pygame

from include import Bits, Relative
from LogicGate_RW.core.ui_node import UINode
from LogicGate_RW.ui.style import shared_style

class UIArrayNode(UINode):
    """Subnode element within an input or output node array."""
    def __init__(
        self,
        parent: "UINodeArray",
        rel_x: float,
        rel_y: float,
        is_transmitter: bool,
        custom_label: str
    ):
        self.parent = parent
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.is_transmitter = is_transmitter

        size = 0.005
        super().__init__(
            pos=(parent.x + rel_x, parent.y + rel_y),
            shape="circle",
            size=size,
            label_prefix=custom_label,
            state=False,
            parent_id=getattr(parent, "id", None)
        )
        self._custom_label = custom_label

    @property
    def x(self) -> float:
        return self.parent.x + self.rel_x

    @x.setter
    def x(self, val: float):
        self.parent.x = val - self.rel_x

    @property
    def y(self) -> float:
        return self.parent.y + self.rel_y

    @y.setter
    def y(self, val: float):
        self.parent.y = val - self.rel_y

    @property
    def label(self) -> str:
        return self._custom_label

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        cw, ch = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        zoom = getattr(app, "zoom_scale", 1.0)
        cx = (self.center[0] * cw) * zoom + ox
        cy = (self.center[1] * ch) * zoom + oy
        abs_r = self.radius * cw * zoom

        active_fill = shared_style.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = shared_style.get_color("node_inactive_fill", (70, 70, 75, 255))
        active_border = shared_style.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))

        fill_color = active_fill if self.state else inactive_fill
        border_color = active_border if self.state else inactive_border

        if self.selected:
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            pygame.draw.circle(screen, sel_color[:3], (int(cx), int(cy)), int(abs_r + 2), 2)

        pygame.draw.circle(screen, fill_color[:3], (int(cx), int(cy)), int(abs_r))
        pygame.draw.circle(screen, border_color[:3], (int(cx), int(cy)), int(abs_r), 1)


class UINodeArray(UINode):
    """Array bus component containing 2, 4, or 8 nodes with Bits-backed integer conversion."""
    def __init__(
        self,
        array_type: str,  # "input" or "output"
        size: int = 4,    # 2, 4, 8
        alignment: str = "V",  # "H" or "V"
        pos: Tuple[float, float] = (0.2, 0.2)
    ):
        self.array_type = array_type
        self.array_size = size
        self.alignment = alignment
        self._input_value = 0

        # Physical sizing in relative coordinates
        if alignment == "V":
            w_rel = 10.0 / 1920.0
            h_rel = (size * 19.2) / 1080.0
        else:
            w_rel = (size * 19.2) / 1920.0
            h_rel = 10.0 / 1080.0

        super().__init__(
            pos=pos,
            shape="rectangle",
            size=(w_rel, h_rel),
            label_prefix="A" if array_type == "input" else "Q",
            state=False
        )

        self.nodes: List[UIArrayNode] = []
        for i in range(size):
            if alignment == "V":
                rel_x = w_rel / 2.0
                rel_y = ((i + 0.5) * 19.2) / 1080.0
            else:
                rel_x = ((i + 0.5) * 19.2) / 1920.0
                rel_y = h_rel / 2.0

            sub = UIArrayNode(
                parent=self,
                rel_x=rel_x,
                rel_y=rel_y,
                is_transmitter=(array_type == "input"),
                custom_label=f"I{i}" if array_type == "input" else f"O{i}"
            )
            self.nodes.append(sub)

    @property
    def value(self) -> int:
        if self.array_type == "input":
            return self._input_value
        else:
            bits = Bits([n.state for n in self.nodes])
            return int(bits)

    @value.setter
    def value(self, val: int):
        max_val = (1 << self.array_size) - 1
        clamped = max(0, min(max_val, val))
        if self.array_type == "input":
            self._input_value = clamped
            bits = Bits.from_int(clamped, self.array_size)
            # Sync to nodes
            for n, b in zip(self.nodes, bits):
                n.state = bool(b)

    def run(self):
        """Syncs bits to states for input arrays."""
        if self.array_type == "input":
            bits = Bits.from_int(self._input_value, self.array_size)
            for n, b in zip(self.nodes, bits):
                n.state = bool(b)

    def collidepoint(self, pos: Tuple[float, float], canvas_size: Tuple[float, float]) -> bool:
        mx, my = pos
        cw, ch = canvas_size
        abs_x = self.x * cw
        abs_y = self.y * ch
        abs_w = self.width * cw
        abs_h = self.height * ch
        abs_r = 0.005 * cw

        if self.alignment == "V":
            x_min = abs_x + abs_w / 2.0 - abs_r
            y_min = abs_y
            box_w = abs_r * 2.0
            box_h = abs_h
        else:
            x_min = abs_x
            y_min = abs_y + abs_h / 2.0 - abs_r
            box_w = abs_w
            box_h = abs_r * 2.0

        return x_min <= mx <= x_min + box_w and y_min <= my <= y_min + box_h

    def handle_event(self, event: pygame.event.Event, canvas_size: Tuple[float, float]) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if any(n.collidepoint(event.pos, canvas_size) for n in self.nodes):
                return
        super().handle_event(event, canvas_size)

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        cw, ch = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        zoom = getattr(app, "zoom_scale", 1.0)
        abs_x = (self.x * cw) * zoom + ox
        abs_y = (self.y * ch) * zoom + oy
        abs_w = self.width * cw * zoom
        abs_h = self.height * ch * zoom
        abs_r = 0.005 * cw * zoom

        group_color = None
        if hasattr(app, "get_component_group_color"):
            group_color = app.get_component_group_color(self.label)
            if group_color is None:
                prefix = "Inputs" if self.array_type == "input" else "Outputs"
                group_color = app.get_component_group_color(prefix)

        bg_fill = group_color if group_color is not None else ((142, 68, 173, 255) if self.array_type == "input" else (46, 204, 113, 255))
        border_color = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        rect_obj = pygame.Rect(int(abs_x), int(abs_y), int(abs_w), int(abs_h))

        if self.selected:
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            pygame.draw.rect(screen, sel_color[:3], pygame.Rect(int(abs_x) - 4, int(abs_y) - 4, int(abs_w) + 8, int(abs_h) + 8), 3, border_radius=6)

        pygame.draw.rect(screen, bg_fill[:3], rect_obj, border_radius=4)
        pygame.draw.rect(screen, border_color[:3], rect_obj, 1, border_radius=4)

        font_size = shared_style.get_size("font_size_array", 12)
        try:
            font = pygame.font.Font(None, font_size)
        except Exception:
            font = pygame.font.SysFont("arial", font_size)

        is_editing = getattr(app, "editing_array_value_node", None) is self
        cursor = "|" if is_editing and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        val_str = app.editing_array_value_str if is_editing else str(self.value)

        name_text = font.render(self.label, True, (255, 255, 255))
        val_text = font.render(val_str + cursor, True, (255, 255, 0) if is_editing else (255, 255, 255))

        if self.alignment == "V":
            tx = abs_x + abs_w / 2.0 - name_text.get_width() / 2.0
            ty = abs_y - name_text.get_height() - 5
            screen.blit(name_text, (int(tx), int(ty)))

            vx = abs_x + abs_w / 2.0 - val_text.get_width() / 2.0
            vy = abs_y + abs_h + 5
            screen.blit(val_text, (int(vx), int(vy)))
        else:
            tx = abs_x - name_text.get_width() - 5
            ty = abs_y + abs_h / 2.0 - name_text.get_height() / 2.0
            screen.blit(name_text, (int(tx), int(ty)))

            vx = abs_x + abs_w + 5
            vy = abs_y + abs_h / 2.0 - val_text.get_height() / 2.0
            screen.blit(val_text, (int(vx), int(vy)))
