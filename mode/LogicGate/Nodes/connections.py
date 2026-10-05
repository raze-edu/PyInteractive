import math
from typing import Any, List, Tuple, Optional
import pygame
from .style import shared_style

class ConnectorNode:
    """Represents a coordinate point inside a connection in relative coordinates.
    
    Can have static relative coordinates, or be linked to an InteractiveNode to dynamically
    track its center relative coordinates.
    """
    def __init__(
        self,
        identifier: Any,
        x: float = 0.0,
        y: float = 0.0,
        linked_node: Optional[Any] = None
    ):
        self.id = identifier
        self.x = x
        self.y = y
        self.linked_node = linked_node

    @property
    def pos(self) -> Tuple[float, float]:
        """Returns the current relative coordinates of this connector node."""
        if self.linked_node is not None:
            return self.linked_node.center
        return (self.x, self.y)


class Connection:
    """Represents a wire/connection between connector nodes.
    
    Checks linked transmitting nodes to determine state and renders connected lines.
    Coordinates are processed in relative space and mapped to screen space at draw/collision time.
    """
    def __init__(
        self,
        connector_nodes: Optional[List[ConnectorNode]] = None,
        lines: Optional[List[Tuple[Any, Any]]] = None
    ):
        self.connector_nodes = connector_nodes if connector_nodes is not None else []
        self.lines = lines if lines is not None else []
        self.selected_line = None
        self.validate_lines()

    def validate_lines(self) -> None:
        """Removes line tuples if one or both connector node IDs cannot be found, or if they represent a self-connection."""
        valid_ids = {c.id for c in self.connector_nodes}
        conn_map = {c.id: c for c in self.connector_nodes}
        
        filtered_lines = []
        for line in self.lines:
            id1, id2 = line
            if id1 in valid_ids and id2 in valid_ids:
                c1 = conn_map[id1]
                c2 = conn_map[id2]
                if c1.linked_node is not None and c2.linked_node is not None and c1.linked_node is c2.linked_node:
                    # Self-connection
                    continue
                filtered_lines.append(line)
        self.lines = filtered_lines

    @property
    def state(self) -> bool:
        """Returns True if any linked node is a transmitting node and has state=True."""
        for c in self.connector_nodes:
            if c.linked_node is not None:
                if getattr(c.linked_node, "is_transmitter", False):
                    if c.linked_node.state:
                        return True
        return False

    def add_connector_node(self, connector: ConnectorNode) -> None:
        """Adds a connector node and validates lines."""
        self.connector_nodes.append(connector)
        self.validate_lines()

    def add_line(self, id1: Any, id2: Any) -> None:
        """Adds a line segment connecting two connector nodes. Self-connections are blocked."""
        c1 = next((c for c in self.connector_nodes if c.id == id1), None)
        c2 = next((c for c in self.connector_nodes if c.id == id2), None)
        if c1 and c2 and c1.linked_node is not None and c2.linked_node is not None:
            if c1.linked_node is c2.linked_node:
                # Self-connections are not allowed
                return
                
        self.lines.append((id1, id2))
        self.validate_lines()

    def remove_connector_node(self, identifier: Any) -> None:
        """Removes a connector node by ID and invalidates dangling lines."""
        self.connector_nodes = [c for c in self.connector_nodes if c.id != identifier]
        self.validate_lines()

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Renders the connection lines on the screen converted to absolute positions."""
        pos_map = {c.id: c.pos for c in self.connector_nodes}
        canvas_w, canvas_h = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        
        # Colors: Use Style colors
        active_color = shared_style.get_color("connection_active", (0, 255, 240, 255))
        inactive_color = shared_style.get_color("connection_inactive", (80, 80, 95, 255))
        color = active_color if self.state else inactive_color
        
        default_active_th = shared_style.get_size("connection_active_thickness", 4)
        default_inactive_th = shared_style.get_size("connection_inactive_thickness", 2)
        thickness = default_active_th if self.state else default_inactive_th

        zoom = getattr(app, "zoom_scale", 1.0)
        for id1, id2 in self.lines:
            if id1 not in pos_map or id2 not in pos_map:
                continue
            
            p1_rel = pos_map[id1]
            p2_rel = pos_map[id2]
            
            p1 = (int((p1_rel[0] * canvas_w) * zoom + ox), int((p1_rel[1] * canvas_h) * zoom + oy))
            p2 = (int((p2_rel[0] * canvas_w) * zoom + ox), int((p2_rel[1] * canvas_h) * zoom + oy))
            
            # Check if this line is selected (in either direction)
            is_selected = (self.selected_line == (id1, id2) or self.selected_line == (id2, id1))
            if is_selected:
                line_color = shared_style.get_color("connection_selected", (255, 220, 0, 255))
                line_thickness = int((thickness + 3) * zoom)
            else:
                line_color = color
                line_thickness = int(thickness * zoom)
            
            line_thickness = max(1, line_thickness)

            pygame.draw.line(screen, line_color[:3], p1, p2, line_thickness)

    def get_colliding_line(self, pos: Tuple[float, float], canvas_size: Tuple[float, float], threshold: float = 8.0) -> Optional[Tuple[Any, Any]]:
        """Returns the line tuple (id1, id2) if the given absolute pos is within threshold pixels of it."""
        pos_map = {c.id: c.pos for c in self.connector_nodes}
        canvas_w, canvas_h = canvas_size
        
        for id1, id2 in self.lines:
            if id1 not in pos_map or id2 not in pos_map:
                continue
            p1_rel = pos_map[id1]
            p2_rel = pos_map[id2]
            
            p1 = (p1_rel[0] * canvas_w, p1_rel[1] * canvas_h)
            p2 = (p2_rel[0] * canvas_w, p2_rel[1] * canvas_h)
            
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
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        px = x1 + t * dx
        py = y1 + t * dy
        return math.hypot(x - px, y - py)

    def split_if_disconnected(self) -> List["Connection"]:
        """Splits this connection into multiple separate Connection objects if it has become disconnected.
        
        Returns:
            List[Connection]: The new connection objects created, or [self] if no split occurred.
        """
        if not self.lines:
            # No lines at all, dissolve everything
            for c in self.connector_nodes:
                if c.linked_node is not None:
                    c.linked_node.connection = None
            return []

        # Build adjacency list of connector IDs
        adj = {c.id: [] for c in self.connector_nodes}
        for id1, id2 in self.lines:
            if id1 in adj and id2 in adj:
                adj[id1].append(id2)
                adj[id2].append(id1)

        # BFS to find connected components
        visited = set()
        components = []  # list of lists of connector node IDs
        
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

        # If all nodes are in one component, no split is needed
        if len(components) <= 1:
            return [self]

        # Map connector node ID to ConnectorNode object
        node_map = {c.id: c for c in self.connector_nodes}
        new_connections = []
        original_lines = list(self.lines)

        for i, comp in enumerate(components):
            comp_set = set(comp)
            comp_lines = [line for line in original_lines if line[0] in comp_set and line[1] in comp_set]
            comp_connectors = [node_map[cid] for cid in comp]

            if not comp_lines:
                # Isolated node component
                for c in comp_connectors:
                    if c.linked_node is not None:
                        c.linked_node.connection = None
            else:
                # Create a new connection or reuse self for the first component
                if i == 0:
                    self.connector_nodes = comp_connectors
                    self.lines = comp_lines
                    for c in comp_connectors:
                        if c.linked_node is not None:
                            c.linked_node.connection = self
                    new_connections.append(self)
                else:
                    new_conn = Connection(connector_nodes=comp_connectors, lines=comp_lines)
                    for c in comp_connectors:
                        if c.linked_node is not None:
                            c.linked_node.connection = new_conn
                    new_connections.append(new_conn)

        return new_connections
