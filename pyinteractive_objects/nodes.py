import math
import json
from typing import Any, List, Tuple, Optional, Union
import pygame
from pathlib import Path

LogicComponentLibPath = Path("mode/LogicGate/LogicComponentLib.json")

class NodeRegistry:
    """Manages unique identifiers and number allocation for interactive nodes."""
    _nodes = set()

    @classmethod
    def register(cls, node: "InteractiveNode") -> int:
        """Assigns the next available unique number suffix for the node's prefix and registers it."""
        num = cls.get_next_number(node.label_prefix)
        cls._nodes.add(node)
        return num

    @classmethod
    def unregister(cls, node: "InteractiveNode") -> None:
        """Removes the node from the registry."""
        cls._nodes.discard(node)

    @classmethod
    def get_next_number(cls, prefix: str) -> int:
        """Finds the lowest positive integer not currently taken by nodes with the same prefix."""
        taken = set()
        for n in cls._nodes:
            if n.label_prefix == prefix and hasattr(n, "number") and n.number is not None:
                taken.add(n.number)
        num = 1
        while num in taken:
            num += 1
        return num


class ConnectorNode:
    """Represents a coordinate point inside a connection.
    
    Can have static coordinates, or be linked to an InteractiveNode to dynamically
    track its center coordinates.
    """
    def __init__(
        self,
        identifier: Any,
        x: float = 0.0,
        y: float = 0.0,
        linked_node: Optional["InteractiveNode"] = None
    ):
        self.id = identifier
        self.x = x
        self.y = y
        self.linked_node = linked_node

    @property
    def pos(self) -> Tuple[float, float]:
        """Returns the current coordinates of this connector node."""
        if self.linked_node is not None:
            return self.linked_node.center
        return (self.x, self.y)


class Connection:
    """Represents a wire/connection between connector nodes.
    
    Checks linked transmitting nodes to determine state and renders connected lines.
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
                # Node is transmitting if it has is_transmitter=True
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
        """Renders the connection lines on the screen."""
        pos_map = {c.id: c.pos for c in self.connector_nodes}
        
        # Colors: Use AppConfig theme colors if present, else fallback to neon colors
        active_color = app.get_color("connection_active", (0, 255, 240, 255))
        inactive_color = app.get_color("connection_inactive", (80, 80, 90, 255))
        color = active_color if self.state else inactive_color
        thickness = 4 if self.state else 2

        for id1, id2 in self.lines:
            if id1 not in pos_map or id2 not in pos_map:
                continue
            
            p1 = pos_map[id1]
            p2 = pos_map[id2]
            
            # Check if this line is selected (in either direction)
            is_selected = (self.selected_line == (id1, id2) or self.selected_line == (id2, id1))
            if is_selected:
                line_color = app.get_color("connection_selected", (255, 220, 0, 255))
                line_thickness = thickness + 3
            else:
                line_color = color
                line_thickness = thickness

            pygame.draw.line(
                screen,
                line_color[:3],
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                line_thickness
            )

    def get_colliding_line(self, pos: Tuple[float, float], threshold: float = 8.0) -> Optional[Tuple[Any, Any]]:
        """Returns the line tuple (id1, id2) if the given pos is within threshold pixels of it."""
        pos_map = {c.id: c.pos for c in self.connector_nodes}
        for id1, id2 in self.lines:
            if id1 not in pos_map or id2 not in pos_map:
                continue
            p1 = pos_map[id1]
            p2 = pos_map[id2]
            
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
                    # Update backreferences
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


class InteractiveNode:
    """Base class for interactive nodes that can be placed and dragged.
    
    Supports states (True/False) and holds a single connection object.
    """
    is_transmitter = False

    def __init__(
        self,
        pos: Tuple[float, float],
        shape: str = "circle",
        size: Union[float, Tuple[float, float]] = 20.0,
        label_prefix: str = "N",
        state: bool = False,
        connection: Optional[Connection] = None
    ):
        self.shape = shape
        self.label_prefix = label_prefix
        self.custom_name = None
        
        if shape == "circle":
            self.x, self.y = pos  # representing center coords
            self.radius = size if isinstance(size, (int, float)) else size[0]
            self.width = self.radius * 2
            self.height = self.radius * 2
        else:
            self.x, self.y = pos  # representing top-left coords
            if isinstance(size, (int, float)):
                self.width = size
                self.height = size
            else:
                self.width, self.height = size
            self.radius = min(self.width, self.height) / 2
            
        self._state = state
        self.connection = connection
        
        self.is_dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        
        # Click detection helper
        self.drag_start_pos = None
        self.dragged_far = False
        
        # Selection state
        self.selected = False

        # Register unique number
        self.number = NodeRegistry.register(self)

    def __del__(self) -> None:
        NodeRegistry.unregister(self)

    @property
    def label(self) -> str:
        """Returns the identifying label (e.g. prefix + unique number)."""
        if getattr(self, "custom_name", None) is not None:
            return self.custom_name
        return f"{self.label_prefix}{self.number}"

    @property
    def center(self) -> Tuple[float, float]:
        """Returns the center coordinates of this node."""
        if self.shape == "circle":
            return (self.x, self.y)
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, val: bool) -> None:
        self._state = val

    def collidepoint(self, pos: Tuple[float, float]) -> bool:
        """Checks if a screen point lies within the node boundary."""
        mx, my = pos
        if self.shape == "circle":
            return math.hypot(mx - self.x, my - self.y) <= self.radius
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes clicks and drag events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Handle possible headless event position
                mouse_pos = getattr(event, "pos", None)
                if mouse_pos is None:
                    if pygame.display.get_init():
                        mouse_pos = pygame.mouse.get_pos()
                    else:
                        mouse_pos = (0, 0)
                
                if self.collidepoint(mouse_pos):
                    self.is_dragging = True
                    self.drag_start_pos = mouse_pos
                    self.dragged_far = False
                    self.drag_offset_x = mouse_pos[0] - self.x
                    self.drag_offset_y = mouse_pos[1] - self.y

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_pos = getattr(event, "pos", None)
                if mouse_pos is None:
                    if pygame.display.get_init():
                        mouse_pos = pygame.mouse.get_pos()
                    else:
                        mouse_pos = (0, 0)
                
                self.x = mouse_pos[0] - self.drag_offset_x
                self.y = mouse_pos[1] - self.drag_offset_y
                
                if self.drag_start_pos is not None:
                    dist = math.hypot(mouse_pos[0] - self.drag_start_pos[0], mouse_pos[1] - self.drag_start_pos[1])
                    if dist > 5:
                        self.dragged_far = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_dragging:
                self.is_dragging = False
                mouse_pos = getattr(event, "pos", None)
                if mouse_pos is None:
                    if pygame.display.get_init():
                        mouse_pos = pygame.mouse.get_pos()
                    else:
                        mouse_pos = (0, 0)
                
                if not self.dragged_far:
                    self.on_click()
                self.drag_start_pos = None

    def on_click(self) -> None:
        """Triggered on click (mouse release without moving)."""
        pass

    def update(self, dt: float) -> None:
        """Subclasses can override this for frame-by-frame updates."""
        pass

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Renders the node and its connection lines (connection drawn underneath)."""
        # 1. Draw connection first (visually under the node)
        if self.connection is not None and not getattr(self, "skip_connection_draw", False):
            self.connection.draw(screen, app)

        # 2. Draw node body
        active_fill = app.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = app.get_color("node_inactive_fill", (70, 70, 75, 255))
        active_border = app.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = app.get_color("node_inactive_border", (140, 140, 150, 255))
        glow_color = app.get_color("node_active_glow", (46, 204, 113, 40))
        text_color = app.get_color("node_text", (240, 240, 245, 255))

        fill_color = active_fill if self.state else inactive_fill
        border_color = active_border if self.state else inactive_border

        # Center coordinates
        cx, cy = self.center

        # Selection highlight (yellow border)
        if getattr(self, "selected", False):
            sel_color = app.get_color("node_selected_border", (255, 220, 0, 255))
            if self.shape == "circle":
                pygame.draw.circle(screen, sel_color[:3], (int(cx), int(cy)), int(self.radius) + 4, 3)
            else:
                rect_sel = pygame.Rect(int(self.x) - 4, int(self.y) - 4, int(self.width) + 8, int(self.height) + 8)
                try:
                    pygame.draw.rect(screen, sel_color[:3], rect_sel, 3, border_radius=8)
                except TypeError:
                    pygame.draw.rect(screen, sel_color[:3], rect_sel, 3)

        # Visual Glow for premium feel
        if self.state:
            glow_radius = int(self.radius * 1.5)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (glow_color[0], glow_color[1], glow_color[2], 60),
                (glow_radius, glow_radius),
                glow_radius
            )
            screen.blit(glow_surf, (int(cx - glow_radius), int(cy - glow_radius)))

        # Draw actual body shape
        if self.shape == "circle":
            pygame.draw.circle(screen, fill_color[:3], (int(cx), int(cy)), int(self.radius))
            pygame.draw.circle(screen, border_color[:3], (int(cx), int(cy)), int(self.radius), 2)
        else:
            rect_obj = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
            # Pygame 2+ supports border_radius
            try:
                pygame.draw.rect(screen, fill_color[:3], rect_obj, border_radius=6)
                pygame.draw.rect(screen, border_color[:3], rect_obj, 2, border_radius=6)
            except TypeError:
                pygame.draw.rect(screen, fill_color[:3], rect_obj)
                pygame.draw.rect(screen, border_color[:3], rect_obj, 2)

        # Draw Label Text centered
        if not pygame.font.get_init():
            pygame.font.init()
        font_h = int(self.radius * 1.0) if self.shape == "circle" else int(self.height * 0.55)
        try:
            font = pygame.font.Font(None, max(12, font_h))
        except Exception:
            font = pygame.font.SysFont("arial", max(12, font_h))
            
        text_surf = font.render(self.label, True, text_color[:3])
        tx = cx - text_surf.get_width() / 2.0
        ty = cy - text_surf.get_height() / 2.0
        screen.blit(text_surf, (int(tx), int(ty)))


class GlobalInputNode(InteractiveNode):
    """A node that acts as a pure transmitter.
    
    Its state is toggled by user click. Always represented as a circle (round).
    """
    is_transmitter = True

    def __init__(
        self,
        pos: Tuple[float, float],
        shape: str = "circle",
        size: Union[float, Tuple[float, float]] = 20.0,
        label_prefix: str = "I",
        state: bool = False,
        connection: Optional[Connection] = None
    ):
        super().__init__(
            pos=pos,
            shape="circle", # Enforce round circle shape
            size=size,
            label_prefix=label_prefix,
            state=state,
            connection=connection
        )

    def on_click(self) -> None:
        """Toggles state upon user click."""
        self.state = not self.state


class GlobalOutputNode(InteractiveNode):
    """A node that acts as a pure receiver.
    
    Its state is determined solely by the state of its connection. Always represented as a rectangle (square).
    """
    is_transmitter = False

    def __init__(
        self,
        pos: Tuple[float, float],
        shape: str = "rectangle",
        size: Union[float, Tuple[float, float]] = 20.0,
        label_prefix: str = "O",
        connection: Optional[Connection] = None
    ):
        super().__init__(
            pos=pos,
            shape="rectangle", # Enforce square rectangle shape
            size=size,
            label_prefix=label_prefix,
            state=False,
            connection=connection
        )

    @property
    def state(self) -> bool:
        """State is True if there is a connection and that connection is active."""
        if self.connection is not None:
            return self.connection.state
        return False

    @state.setter
    def state(self, val: bool) -> None:
        """Ignores external sets since output node state is receiver-only."""
        pass


class ComponentSubNode(InteractiveNode):
    """A sub-node of a LogicComponent, positioned on its edge.
    
    Can be an input (receiver) or output (transmitter).
    Translates absolute coordinates to/from relative offsets from the parent component.
    """
    def __init__(
        self,
        parent: "LogicComponent",
        rel_x: float,
        rel_y: float,
        is_transmitter: bool,
        custom_label: str,
        size: float = 10.0,
        color: Optional[Tuple[int, int, int, int]] = None
    ):
        self.parent = parent
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.is_transmitter = is_transmitter
        self._custom_label = custom_label
        self.color = color
        
        super().__init__(
            pos=(parent.x + rel_x, parent.y + rel_y),
            shape="circle",
            size=size,
            label_prefix=custom_label,
            state=False
        )
        self._evaluating = False

    @property
    def x(self) -> float:
        return self.parent.x + self.rel_x

    @x.setter
    def x(self, val: float) -> None:
        # Dragging the subnode moves the parent logic component
        self.parent.x = val - self.rel_x

    @property
    def y(self) -> float:
        return self.parent.y + self.rel_y

    @y.setter
    def y(self, val: float) -> None:
        # Dragging the subnode moves the parent logic component
        self.parent.y = val - self.rel_y

    @property
    def label(self) -> str:
        return self._custom_label

    @property
    def state(self) -> bool:
        if getattr(self, "_evaluating", False):
            return False
        self._evaluating = True
        try:
            if self.is_transmitter:
                return self.parent.get_output_state(self)
            else:
                if self.connection is not None:
                    return self.connection.state
                return False
        finally:
            self._evaluating = False

    @state.setter
    def state(self, val: bool) -> None:
        # Ignore setting state externally
        pass

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Draws the sub-node triangle and handles glow effect."""
        # 1. Draw connection line if any (connection drawn underneath)
        if self.connection is not None and not getattr(self, "skip_connection_draw", False):
            self.connection.draw(screen, app)

        # 2. Draw subnode body
        active_fill = app.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = app.get_color("node_inactive_fill", (70, 70, 75, 255))
        active_border = app.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = app.get_color("node_inactive_border", (140, 140, 150, 255))
        glow_color = app.get_color("node_active_glow", (46, 204, 113, 40))

        state_active = self.state
        fill_color = active_fill if state_active else inactive_fill
        border_color = active_border if state_active else inactive_border

        cx, cy = self.center

        # Calculate triangle orientation: pointing inwards (input) or outwards (output)
        pc_x = self.parent.width / 2.0
        pc_y = self.parent.height / 2.0
        dx = pc_x - self.rel_x
        dy = pc_y - self.rel_y
        length = math.hypot(dx, dy)
        if length > 0:
            ux, uy = dx / length, dy / length
        else:
            ux, uy = 1.0, 0.0

        # Inputs point inwards (towards center), outputs point away (away from center)
        if self.is_transmitter:
            px, py = -ux, -uy
        else:
            px, py = ux, uy

        r = self.radius

        # Selection outline (yellow border)
        if getattr(self, "selected", False):
            sel_color = app.get_color("node_selected_border", (255, 220, 0, 255))
            r_sel = r + 3
            V1_s = (cx + r_sel * px, cy + r_sel * py)
            bc_x_s = cx - 0.5 * r_sel * px
            bc_y_s = cy - 0.5 * r_sel * py
            V2_s = (bc_x_s - r_sel * py, bc_y_s + r_sel * px)
            V3_s = (bc_x_s + r_sel * py, bc_y_s - r_sel * px)
            pygame.draw.polygon(screen, sel_color[:3], [V1_s, V2_s, V3_s], 2)

        # Visual glow
        if state_active:
            glow_radius = int(r * 1.5)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (glow_color[0], glow_color[1], glow_color[2], 60),
                (glow_radius, glow_radius),
                glow_radius
            )
            screen.blit(glow_surf, (int(cx - glow_radius), int(cy - glow_radius)))

        # Draw actual triangle shape
        V1 = (cx + r * px, cy + r * py)
        bc_x = cx - 0.5 * r * px
        bc_y = cy - 0.5 * r * py
        V2 = (bc_x - r * py, bc_y + r * px)
        V3 = (bc_x + r * py, bc_y - r * px)

        pygame.draw.polygon(screen, fill_color[:3], [V1, V2, V3])
        pygame.draw.polygon(screen, border_color[:3], [V1, V2, V3], 1)


class LogicComponent(InteractiveNode):
    """A rectangular component containing input and output edge sub-nodes.
    
    Evaluates its output states based on current input states and a logic table.
    """
    def __init__(
        self,
        name: str,
        size: Tuple[float, float],
        inputs_def: List[dict],
        outputs_def: List[dict],
        logic_table: dict,
        pos: Tuple[float, float] = (100, 100),
        color: Optional[Tuple[int, int, int, int]] = None
    ):
        self.color = color
        
        # Initialize base InteractiveNode as a rectangle
        super().__init__(
            pos=pos,
            shape="rectangle",
            size=size,
            label_prefix=name,
            state=False
        )

        # Parse logic table
        self.parsed_table = {}
        for k, v in logic_table.items():
            # Standardize keys into a tuple of bools
            if "," in k:
                bits = [b.strip() for b in k.split(",")]
            elif " " in k:
                bits = [b.strip() for b in k.split()]
            else:
                bits = list(k)
            input_tuple = tuple(b in ('1', 'True', 'true', True) for b in bits)
            
            # Standardize values into a tuple of bools
            if isinstance(v, (list, tuple)):
                output_vals = tuple(bool(x) for x in v)
            elif isinstance(v, str):
                if "," in v:
                    o_bits = [b.strip() for b in v.split(",")]
                elif " " in v:
                    o_bits = [b.strip() for b in v.split()]
                else:
                    o_bits = list(v)
                output_vals = tuple(b in ('1', 'True', 'true', True) for b in o_bits)
            else:
                output_vals = (bool(v),)
                
            self.parsed_table[input_tuple] = output_vals

        # Create input and output ComponentSubNodes
        self.inputs = []
        for inp in inputs_def:
            sub = ComponentSubNode(
                parent=self,
                rel_x=float(inp["rel_x"]),
                rel_y=float(inp["rel_y"]),
                is_transmitter=False,
                custom_label=inp["name"],
                color=tuple(inp["color"]) if inp.get("color") else None
            )
            self.inputs.append(sub)

        self.outputs = []
        for out in outputs_def:
            sub = ComponentSubNode(
                parent=self,
                rel_x=float(out["rel_x"]),
                rel_y=float(out["rel_y"]),
                is_transmitter=True,
                custom_label=out["name"],
                color=tuple(out["color"]) if out.get("color") else None
            )
            self.outputs.append(sub)

    def get_output_state(self, subnode: ComponentSubNode) -> bool:
        # Collect current input states
        input_states = tuple(inp.state for inp in self.inputs)
        
        # Look up in parsed_table
        output_states = self.parsed_table.get(input_states)
        if output_states is None:
            # Fallback if key not found: all False
            output_states = (False,) * len(self.outputs)
            
        if subnode in self.outputs:
            idx = self.outputs.index(subnode)
            if idx < len(output_states):
                return output_states[idx]
        return False

    @property
    def state(self) -> bool:
        """Returns True if any output sub-node has state=True."""
        return any(out.state for out in self.outputs)

    @state.setter
    def state(self, val: bool) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Ignores drag initialization if mouse click lands directly on a child sub-node."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = getattr(event, "pos", None)
            if mouse_pos is None:
                if pygame.display.get_init():
                    mouse_pos = pygame.mouse.get_pos()
                else:
                    mouse_pos = (0, 0)
            if any(inp.collidepoint(mouse_pos) for inp in self.inputs) or any(out.collidepoint(mouse_pos) for out in self.outputs):
                return
        super().handle_event(event)

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Renders the component's rectangular body, name, and inside node labels."""
        # Draw background rectangle
        bg_fill = self.color if self.color else app.get_color("logic_component_fill", (142, 68, 173, 255))
        border_color = app.get_color("node_inactive_border", (140, 140, 150, 255))
        
        rect_obj = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
        
        # Draw yellow border if component is selected
        if getattr(self, "selected", False):
            sel_color = app.get_color("node_selected_border", (255, 220, 0, 255))
            try:
                pygame.draw.rect(screen, sel_color[:3], pygame.Rect(int(self.x) - 4, int(self.y) - 4, int(self.width) + 8, int(self.height) + 8), 3, border_radius=8)
            except TypeError:
                pygame.draw.rect(screen, sel_color[:3], pygame.Rect(int(self.x) - 4, int(self.y) - 4, int(self.width) + 8, int(self.height) + 8), 3)

        # Draw actual body
        try:
            pygame.draw.rect(screen, bg_fill[:3], rect_obj, border_radius=6)
            pygame.draw.rect(screen, border_color[:3], rect_obj, 2, border_radius=6)
        except TypeError:
            pygame.draw.rect(screen, bg_fill[:3], rect_obj)
            pygame.draw.rect(screen, border_color[:3], rect_obj, 2)

        # Draw Component Name centered inside the body
        if not pygame.font.get_init():
            pygame.font.init()
        font_h = int(self.height * 0.35)
        try:
            font = pygame.font.Font(None, max(14, font_h))
        except Exception:
            font = pygame.font.SysFont("arial", max(14, font_h))
            
        text_surf = font.render(self.label_prefix, True, (255, 255, 255))
        cx, cy = self.center
        tx = cx - text_surf.get_width() / 2.0
        ty = cy - text_surf.get_height() / 2.0
        screen.blit(text_surf, (int(tx), int(ty)))

        # Draw inside labels for the sub-nodes
        try:
            label_font = pygame.font.Font(None, max(12, int(self.height * 0.25)))
        except Exception:
            label_font = pygame.font.SysFont("arial", max(12, int(self.height * 0.25)))
            
        # Draw input sub-node labels
        for inp in self.inputs:
            lbl_surf = label_font.render(inp.label, True, (220, 220, 225))
            # Position offset inside the body: rel_x < width/2 means it's on left, offset right
            ox = 10 if inp.rel_x < self.width / 2 else -10 - lbl_surf.get_width()
            oy = -lbl_surf.get_height() / 2
            screen.blit(lbl_surf, (int(inp.x + ox), int(inp.y + oy)))

        # Draw output sub-node labels
        for out in self.outputs:
            lbl_surf = label_font.render(out.label, True, (220, 220, 225))
            ox = 10 if out.rel_x < self.width / 2 else -10 - lbl_surf.get_width()
            oy = -lbl_surf.get_height() / 2
            screen.blit(lbl_surf, (int(out.x + ox), int(out.y + oy)))

    @classmethod
    def from_json(cls, source: Union[str, dict], pos: Tuple[float, float] = (100, 100)) -> "LogicComponent":
        """Loads and returns a LogicComponent from a JSON library component name, file path, or dictionary."""
        data = None
        if isinstance(source, dict):
            data = source
        elif isinstance(source, str):
            import os
            # If it points to an existing file, load it directly
            if os.path.exists(source):
                with open(source, "r") as f:
                    data = json.load(f)
            else:
                # Otherwise, treat as component name in LogicComponentLib.json
                lib_path = LogicComponentLibPath
                if lib_path.exists():
                    with open(lib_path, "r") as f:
                        for item in json.load(f):
                            if item.get("name") == source:
                                data = item
                                break
        if not data:
            data = {}

        # Extract values
        name = data.get("name", "Logic Gate")
        width = data.get("width", 80)
        height = data.get("height", 50)
        color = data.get("color")
        if color:
            color = tuple(color)
        inputs_def = data.get("inputs", [])
        outputs_def = data.get("outputs", [])
        logic_table = data.get("logic_table", {})
        
        # If position is saved in JSON, use it, otherwise use pos arg
        instance_pos = (data.get("x", pos[0]), data.get("y", pos[1]))

        return cls(
            name=name,
            size=(width, height),
            inputs_def=inputs_def,
            outputs_def=outputs_def,
            logic_table=logic_table,
            pos=instance_pos,
            color=color
        )

    def to_dict(self) -> dict:
        """Serializes the LogicComponent into a dictionary."""
        # Convert parsed_table keys back to comma-separated strings
        serializable_table = {}
        for k, v in self.parsed_table.items():
            k_str = ",".join("1" if b else "0" for b in k)
            v_str = ",".join("1" if b else "0" for b in v)
            serializable_table[k_str] = v_str

        return {
            "name": self.label_prefix,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "color": list(self.color) if self.color else None,
            "inputs": [
                {
                    "name": inp._custom_label,
                    "rel_x": inp.rel_x,
                    "rel_y": inp.rel_y,
                    "color": list(inp.color) if inp.color else None
                }
                for inp in self.inputs
            ],
            "outputs": [
                {
                    "name": out._custom_label,
                    "rel_x": out.rel_x,
                    "rel_y": out.rel_y,
                    "color": list(out.color) if out.color else None
                }
                for out in self.outputs
            ],
            "logic_table": serializable_table
        }

    def to_json(self, json_path: str) -> None:
        """Saves the LogicComponent to a JSON file."""
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
