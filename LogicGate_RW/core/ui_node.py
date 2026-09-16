import math
import re
from typing import Any, Tuple, Optional, Union
import pygame

from include import Node, Relative, RelPoint, Area, Polygon, Direction, Color
from LogicGate_RW.ui.style import shared_style

def normalize_label(lbl: str) -> str:
    """Normalizes pin and array labels by removing I/O prefixes for mapping."""
    if not lbl:
        return ""
    return re.sub(r'_(I|O)(\d+)', r'_\2', lbl)


class NodeRegistry:
    """Assigns and tracks unique numbering for UI nodes."""
    _nodes = set()

    @classmethod
    def register(cls, node: "UINode") -> int:
        num = cls.get_next_number(node.label_prefix)
        cls._nodes.add(node)
        return num

    @classmethod
    def unregister(cls, node: "UINode") -> None:
        cls._nodes.discard(node)

    @classmethod
    def get_next_number(cls, prefix: str) -> int:
        taken = {n.number for n in cls._nodes if n.label_prefix == prefix and hasattr(n, "number") and n.number is not None}
        num = 1
        while num in taken:
            num += 1
        return num

    @classmethod
    def clear(cls):
        cls._nodes.clear()


class UINode(Node):
    """Base interactive visual node integrating include.Node and include.Relative."""
    is_transmitter: bool = False

    def __init__(
        self,
        pos: Tuple[float, float],
        shape: str = "circle",
        size: Union[float, Tuple[float, float]] = 0.013,
        label_prefix: str = "N",
        state: bool = False,
        connection: Optional[Any] = None,
        parent_id=None
    ):
        # Initialize logic core from include.Node
        if parent_id is not None:
            super().__init__(parent_id=parent_id)
        else:
            super().__init__()

        self.state = state
        self.shape = shape
        self.label_prefix = label_prefix
        self.custom_name = None
        self._custom_label = None

        if shape == "circle":
            self.x, self.y = pos
            self.radius = size if isinstance(size, (int, float)) else size[0]
            self.width = self.radius * 2.0
            self.height = self.radius * 2.0
        else:
            if isinstance(size, (int, float)):
                self.width = size
                self.height = size
            else:
                self.width, self.height = size
            self.x = pos[0] - self.width / 2.0
            self.y = pos[1] - self.height / 2.0
            self.radius = min(self.width, self.height) / 2.0

        self.connection = connection
        self.is_dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        self.drag_start_pos = None
        self.dragged_far = False
        self.selected = False

        self.number = NodeRegistry.register(self)

    def __del__(self):
        try:
            NodeRegistry.unregister(self)
        except Exception:
            pass

    @property
    def label(self) -> str:
        if self._custom_label is not None:
            return self._custom_label
        if self.custom_name is not None:
            return self.custom_name
        return f"{self.label_prefix}{self.number}"

    @label.setter
    def label(self, val: str):
        self._custom_label = val

    @property
    def center(self) -> Tuple[float, float]:
        if self.shape == "circle":
            return (self.x, self.y)
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    def collidepoint(self, pos: Tuple[float, float], canvas_size: Tuple[float, float]) -> bool:
        mx, my = pos
        cw, ch = canvas_size
        if self.shape == "circle":
            abs_cx = self.x * cw
            abs_cy = self.y * ch
            abs_r = self.radius * cw
            return math.hypot(mx - abs_cx, my - abs_cy) <= abs_r
        else:
            abs_x = self.x * cw
            abs_y = self.y * ch
            abs_w = self.width * cw
            abs_h = self.height * ch
            return abs_x <= mx <= abs_x + abs_w and abs_y <= my <= abs_y + abs_h

    def handle_event(self, event: pygame.event.Event, canvas_size: Tuple[float, float]) -> None:
        cw, ch = canvas_size
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = getattr(event, "pos", None)
            if mouse_pos is not None and self.collidepoint(mouse_pos, canvas_size):
                self.is_dragging = True
                self.drag_start_pos = mouse_pos
                self.dragged_far = False
                self.drag_offset_x = (mouse_pos[0] / cw) - self.x
                self.drag_offset_y = (mouse_pos[1] / ch) - self.y

        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            mouse_pos = getattr(event, "pos", None)
            if mouse_pos is not None:
                self.x = (mouse_pos[0] / cw) - self.drag_offset_x
                self.y = (mouse_pos[1] / ch) - self.drag_offset_y
                if self.drag_start_pos is not None:
                    dist = math.hypot(mouse_pos[0] - self.drag_start_pos[0], mouse_pos[1] - self.drag_start_pos[1])
                    if dist > 8:
                        self.dragged_far = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                if not self.dragged_far:
                    self.on_click()
                self.drag_start_pos = None

    def on_click(self) -> None:
        """Triggered on a clean click (mouse release without dragging)."""
        pass

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        pass


class UIGlobalInputNode(UINode):
    """User-toggleable transmitter input node."""
    is_transmitter = True

    def __init__(self, pos: Tuple[float, float] = (0.1, 0.5), state: bool = False, custom_label: Optional[str] = None):
        super().__init__(
            pos=pos,
            shape="circle",
            size=shared_style.get_size("input_node_size", 0.013),
            label_prefix="I",
            state=state
        )
        if custom_label:
            self._custom_label = custom_label

    def on_click(self) -> None:
        """Toggles logic state on click."""
        self.switch_to()

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        cw, ch = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        zoom = getattr(app, "zoom_scale", 1.0)
        cx = (self.x * cw) * zoom + ox
        cy = (self.y * ch) * zoom + oy
        abs_r = self.radius * cw * zoom

        active_fill = shared_style.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = shared_style.get_color("node_inactive_fill", (60, 60, 65, 255))
        active_border = shared_style.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        glow_color = shared_style.get_color("node_active_glow", (46, 204, 113, 40))

        fill_color = active_fill if self.state else inactive_fill
        border_color = active_border if self.state else inactive_border

        if self.selected:
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            pygame.draw.circle(screen, sel_color[:3], (int(cx), int(cy)), int(abs_r + 3), 2)

        if self.state:
            glow_radius = int(abs_r * shared_style.get_size("glow_radius_multiplier", 1.5))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (glow_color[0], glow_color[1], glow_color[2], 50), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (int(cx - glow_radius), int(cy - glow_radius)))

        pygame.draw.circle(screen, fill_color[:3], (int(cx), int(cy)), int(abs_r))
        pygame.draw.circle(screen, border_color[:3], (int(cx), int(cy)), int(abs_r), 2)

        # Draw label to the left
        font_size = shared_style.get_size("font_size_global", 14)
        try:
            font = pygame.font.Font(None, font_size)
        except Exception:
            font = pygame.font.SysFont("arial", font_size)
        lbl_surf = font.render(self.label, True, shared_style.get_color("node_text", (240, 240, 245)))
        screen.blit(lbl_surf, (int(cx - abs_r - lbl_surf.get_width() - 5), int(cy - lbl_surf.get_height() / 2)))


class UIGlobalOutputNode(UINode):
    """Receiver output node displaying circuit results."""
    is_transmitter = False

    def __init__(self, pos: Tuple[float, float] = (0.8, 0.5), custom_label: Optional[str] = None):
        super().__init__(
            pos=pos,
            shape="circle",
            size=shared_style.get_size("output_node_size", 0.013),
            label_prefix="O",
            state=False
        )
        if custom_label:
            self._custom_label = custom_label

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        cw, ch = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        zoom = getattr(app, "zoom_scale", 1.0)
        cx = (self.x * cw) * zoom + ox
        cy = (self.y * ch) * zoom + oy
        abs_r = self.radius * cw * zoom

        active_fill = shared_style.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = shared_style.get_color("node_inactive_fill", (60, 60, 65, 255))
        active_border = shared_style.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        glow_color = shared_style.get_color("node_active_glow", (46, 204, 113, 40))

        fill_color = active_fill if self.state else inactive_fill
        border_color = active_border if self.state else inactive_border

        if self.selected:
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            pygame.draw.circle(screen, sel_color[:3], (int(cx), int(cy)), int(abs_r + 3), 2)

        if self.state:
            glow_radius = int(abs_r * shared_style.get_size("glow_radius_multiplier", 1.5))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (glow_color[0], glow_color[1], glow_color[2], 50), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (int(cx - glow_radius), int(cy - glow_radius)))

        pygame.draw.circle(screen, fill_color[:3], (int(cx), int(cy)), int(abs_r))
        pygame.draw.circle(screen, border_color[:3], (int(cx), int(cy)), int(abs_r), 2)

        # Draw label to the right
        font_size = shared_style.get_size("font_size_global", 14)
        try:
            font = pygame.font.Font(None, font_size)
        except Exception:
            font = pygame.font.SysFont("arial", font_size)
        lbl_surf = font.render(self.label, True, shared_style.get_color("node_text", (240, 240, 245)))
        screen.blit(lbl_surf, (int(cx + abs_r + 5), int(cy - lbl_surf.get_height() / 2)))


class UIComponentPin(UINode):
    """Sub-node pin attached to an edge of a UILogicComponent, drawn as an oriented triangle with Polygon."""
    def __init__(
        self,
        parent: Any,
        rel_x: float,
        rel_y: float,
        is_transmitter: bool,
        custom_label: str,
        color: Optional[Tuple[int, int, int, int]] = None,
        direction: Optional[Direction] = None
    ):
        self.parent = parent
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.is_transmitter = is_transmitter
        self.pin_color = color
        self.direction = direction

        size = shared_style.get_size("node_size", 0.01)
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
        glow_color = shared_style.get_color("node_active_glow", (46, 204, 113, 40))

        fill_color = active_fill if self.state else inactive_fill
        border_color = active_border if self.state else inactive_border

        # Direction vector for triangle orientation pointing in/out
        pc_x = self.parent.width / 2.0
        pc_y = self.parent.height / 2.0
        dx = pc_x - self.rel_x
        dy = pc_y - self.rel_y
        dx_abs = dx * cw * zoom
        dy_abs = dy * ch * zoom
        length = math.hypot(dx_abs, dy_abs)
        if length > 0:
            ux, uy = dx_abs / length, dy_abs / length
        else:
            ux, uy = 1.0, 0.0

        if self.is_transmitter:
            px, py = -ux, -uy
        else:
            px, py = ux, uy

        # Selection outline
        if self.selected:
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            r_sel = abs_r + 3
            V1_s = (cx + r_sel * px, cy + r_sel * py)
            bc_x_s = cx - 0.5 * r_sel * px
            bc_y_s = cy - 0.5 * r_sel * py
            V2_s = (bc_x_s - r_sel * py, bc_y_s + r_sel * px)
            V3_s = (bc_x_s + r_sel * py, bc_y_s - r_sel * px)
            pygame.draw.polygon(screen, sel_color[:3], [V1_s, V2_s, V3_s], 2)

        if self.state:
            glow_radius = int(abs_r * shared_style.get_size("glow_radius_multiplier", 1.5))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (glow_color[0], glow_color[1], glow_color[2], 60), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (int(cx - glow_radius), int(cy - glow_radius)))

        V1 = (cx + abs_r * px, cy + abs_r * py)
        bc_x = cx - 0.5 * abs_r * px
        bc_y = cy - 0.5 * abs_r * py
        V2 = (bc_x - abs_r * py, bc_y + abs_r * px)
        V3 = (bc_x + abs_r * py, bc_y - abs_r * px)

        pygame.draw.polygon(screen, fill_color[:3], [V1, V2, V3])
        pygame.draw.polygon(screen, border_color[:3], [V1, V2, V3], 1)


class UIConnectorPoint:
    """Waypoint connector node inside a visual wire connection."""
    def __init__(
        self,
        identifier: Any,
        x: float = 0.0,
        y: float = 0.0,
        linked_node: Optional[UINode] = None
    ):
        self.id = identifier
        self.x = x
        self.y = y
        self.linked_node = linked_node

    @property
    def pos(self) -> Tuple[float, float]:
        if self.linked_node is not None:
            return self.linked_node.center
        return (self.x, self.y)
