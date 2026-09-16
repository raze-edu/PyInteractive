import math
from typing import Any, List, Tuple, Optional, Set
import pygame

from include import Connection as LogicConnection
from LogicGate_RW.core.ui_node import UIConnectorPoint, UINode
from LogicGate_RW.ui.style import shared_style

class UIConnection:
    """Visual wire connection bridging Pygame rendering and include.Connection logic."""

    def __init__(
        self,
        connector_nodes: Optional[List[UIConnectorPoint]] = None,
        lines: Optional[List[Tuple[Any, Any]]] = None
    ):
        self.logic_conn = LogicConnection()
        self.connector_nodes: List[UIConnectorPoint] = connector_nodes if connector_nodes is not None else []
        self.lines: List[Tuple[Any, Any]] = lines if lines is not None else []
        self.selected_line: Optional[Tuple[Any, Any]] = None

        self._sync_logic()
        self.validate_lines()

    def _sync_logic(self):
        """Registers all currently linked transmitters and receivers with the underlying include.Connection."""
        for c in self.connector_nodes:
            if c.linked_node is not None:
                if getattr(c.linked_node, "is_transmitter", False):
                    self.logic_conn.add_tx(c.linked_node)
                else:
                    self.logic_conn.add_rx(c.linked_node)

    def validate_lines(self) -> None:
        """Removes dangling lines or self-connections."""
        valid_ids = {c.id for c in self.connector_nodes}
        conn_map = {c.id: c for c in self.connector_nodes}

        filtered = []
        for id1, id2 in self.lines:
            if id1 in valid_ids and id2 in valid_ids:
                c1 = conn_map[id1]
                c2 = conn_map[id2]
                if c1.linked_node is not None and c2.linked_node is not None and c1.linked_node is c2.linked_node:
                    continue
                filtered.append((id1, id2))
        self.lines = filtered

    @property
    def state(self) -> bool:
        """Returns True if any linked transmitter is active via include.Connection."""
        return self.logic_conn.state

    def run(self) -> None:
        """Propagates signal state to all linked receiver nodes using include.Connection.run()."""
        self.logic_conn.run()

    def add_connector_node(self, connector: UIConnectorPoint) -> None:
        self.connector_nodes.append(connector)
        if connector.linked_node is not None:
            if getattr(connector.linked_node, "is_transmitter", False):
                self.logic_conn.add_tx(connector.linked_node)
            else:
                self.logic_conn.add_rx(connector.linked_node)
        self.validate_lines()

    def add_line(self, id1: Any, id2: Any) -> None:
        c1 = next((c for c in self.connector_nodes if c.id == id1), None)
        c2 = next((c for c in self.connector_nodes if c.id == id2), None)
        if c1 and c2 and c1.linked_node is not None and c2.linked_node is not None:
            if c1.linked_node is c2.linked_node:
                return
        self.lines.append((id1, id2))
        self.validate_lines()

    def remove_connector_node(self, identifier: Any) -> None:
        self.connector_nodes = [c for c in self.connector_nodes if c.id != identifier]
        self.validate_lines()

    def get_lines_with_points(self) -> List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[Any, Any]]]:
        pos_map = {c.id: c.pos for c in self.connector_nodes}
        result = []
        for id1, id2 in self.lines:
            if id1 in pos_map and id2 in pos_map:
                result.append((pos_map[id1], pos_map[id2], (id1, id2)))
        return result

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        canvas_w, canvas_h = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        zoom = getattr(app, "zoom_scale", 1.0)

        active_color = shared_style.get_color("connection_active", (0, 255, 240, 255))
        inactive_color = shared_style.get_color("connection_inactive", (80, 80, 95, 255))
        selected_color = shared_style.get_color("connection_selected", (255, 220, 0, 255))

        line_color = active_color if self.state else inactive_color
        thick_active = shared_style.get_size("connection_active_thickness", 4)
        thick_inactive = shared_style.get_size("connection_inactive_thickness", 2)
        base_thick = thick_active if self.state else thick_inactive
        thickness = max(1, int(base_thick * zoom))

        lines_with_pts = self.get_lines_with_points()

        # Render glow for active wires
        if self.state and lines_with_pts:
            glow_surf = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)
            glow_color = (line_color[0], line_color[1], line_color[2], 40)
            glow_thick = max(2, int((base_thick + 4) * zoom))
            for p1_rel, p2_rel, _ in lines_with_pts:
                p1_scr = (p1_rel[0] * canvas_w * zoom + ox, p1_rel[1] * canvas_h * zoom + oy)
                p2_scr = (p2_rel[0] * canvas_w * zoom + ox, p2_rel[1] * canvas_h * zoom + oy)
                pygame.draw.line(glow_surf, glow_color, p1_scr, p2_scr, glow_thick)
            screen.blit(glow_surf, (0, 0))

        # Render wire lines
        for p1_rel, p2_rel, line_tuple in lines_with_pts:
            p1_scr = (p1_rel[0] * canvas_w * zoom + ox, p1_rel[1] * canvas_h * zoom + oy)
            p2_scr = (p2_rel[0] * canvas_w * zoom + ox, p2_rel[1] * canvas_h * zoom + oy)

            if self.selected_line == line_tuple or self.selected_line == (line_tuple[1], line_tuple[0]):
                pygame.draw.line(screen, selected_color[:3], p1_scr, p2_scr, thickness + 2)
            else:
                pygame.draw.line(screen, line_color[:3], p1_scr, p2_scr, thickness)

        # Render free-floating connector handles
        handle_r = int(shared_style.get_size("connector_handle_radius", 6) * zoom)
        for c in self.connector_nodes:
            if c.linked_node is None:
                cx_scr = c.x * canvas_w * zoom + ox
                cy_scr = c.y * canvas_h * zoom + oy
                is_selected = getattr(app, "selected_start_point", None) is c
                col = selected_color if is_selected else line_color
                pygame.draw.circle(screen, col[:3], (int(cx_scr), int(cy_scr)), max(2, handle_r))
                pygame.draw.circle(screen, (255, 255, 255), (int(cx_scr), int(cy_scr)), max(2, handle_r), 1)

    def get_colliding_line(self, pos: Tuple[float, float], canvas_size: Tuple[float, float], threshold: float = 8.0) -> Optional[Tuple[Any, Any]]:
        """Returns the line tuple (id1, id2) if the given absolute pos is within threshold pixels of it."""
        pos_map = {c.id: c.pos for c in self.connector_nodes}
        canvas_w, canvas_h = canvas_size

        for id1, id2 in self.lines:
            if id1 not in pos_map or id2 not in pos_map:
                continue
            p1 = (pos_map[id1][0] * canvas_w, pos_map[id1][1] * canvas_h)
            p2 = (pos_map[id2][0] * canvas_w, pos_map[id2][1] * canvas_h)

            dist = self._distance_to_segment(pos, p1, p2)
            if dist <= threshold:
                return (id1, id2)
        return None

    def _distance_to_segment(self, p: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        x, y = p
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x - x1, y - y1)
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        px = x1 + t * dx
        py = y1 + t * dy
        return math.hypot(x - px, y - py)

    def split_if_disconnected(self) -> List["UIConnection"]:
        """Splits this connection into multiple separate UIConnection objects if disconnected."""
        if not self.lines:
            for c in self.connector_nodes:
                if c.linked_node is not None:
                    c.linked_node.connection = None
            return []

        adj = {c.id: [] for c in self.connector_nodes}
        for id1, id2 in self.lines:
            if id1 in adj and id2 in adj:
                adj[id1].append(id2)
                adj[id2].append(id1)

        visited = set()
        components = []
        for c_node in self.connector_nodes:
            if c_node.id not in visited:
                comp = []
                queue = [c_node.id]
                visited.add(c_node.id)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        if len(components) <= 1:
            return [self]

        node_map = {c.id: c for c in self.connector_nodes}
        new_connections = []
        original_lines = list(self.lines)

        for i, comp in enumerate(components):
            comp_set = set(comp)
            comp_lines = [line for line in original_lines if line[0] in comp_set and line[1] in comp_set]
            comp_connectors = [node_map[cid] for cid in comp]

            if not comp_lines:
                for c in comp_connectors:
                    if c.linked_node is not None:
                        c.linked_node.connection = None
            else:
                if i == 0:
                    self.connector_nodes = comp_connectors
                    self.lines = comp_lines
                    self._sync_logic()
                    for c in comp_connectors:
                        if c.linked_node is not None:
                            c.linked_node.connection = self
                    new_connections.append(self)
                else:
                    new_conn = UIConnection(connector_nodes=comp_connectors, lines=comp_lines)
                    for c in comp_connectors:
                        if c.linked_node is not None:
                            c.linked_node.connection = new_conn
                    new_connections.append(new_conn)

        return new_connections
