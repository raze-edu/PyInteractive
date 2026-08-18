import math
import json
from typing import Any, List, Tuple, Optional, Union
import pygame
from .style import shared_style

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


class InteractiveNode:
    """Base class for interactive nodes that can be placed and dragged.
    
    Coordinates (x, y) and size parameters are stored as relative values (0.0 to 1.0)
    of the canvas screen dimensions.
    """
    is_transmitter = False

    def __init__(
        self,
        pos: Tuple[float, float],
        shape: str = "circle",
        size: Union[float, Tuple[float, float]] = 0.013,
        label_prefix: str = "N",
        state: bool = False,
        connection: Optional[Any] = None
    ):
        self.shape = shape
        self.label_prefix = label_prefix
        self.custom_name = None
        
        if shape == "circle":
            self.x, self.y = pos  # representing relative center coords
            self.radius = size if isinstance(size, (int, float)) else size[0]
            self.width = self.radius * 2
            self.height = self.radius * 2
        else:
            self.x, self.y = pos  # representing relative top-left coords
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
        """Returns the relative center coordinates of this node."""
        if self.shape == "circle":
            return (self.x, self.y)
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, val: bool) -> None:
        self._state = val

    def collidepoint(self, pos: Tuple[float, float], canvas_size: Tuple[float, float]) -> bool:
        """Checks if an absolute canvas coordinate point lies within the node boundary."""
        mx, my = pos
        canvas_w, canvas_h = canvas_size
        if self.shape == "circle":
            abs_cx = self.x * canvas_w
            abs_cy = self.y * canvas_h
            abs_r = self.radius * canvas_w
            return math.hypot(mx - abs_cx, my - abs_cy) <= abs_r
        else:
            abs_x = self.x * canvas_w
            abs_y = self.y * canvas_h
            abs_w = self.width * canvas_w
            abs_h = self.height * canvas_h
            return abs_x <= mx <= abs_x + abs_w and abs_y <= my <= abs_y + abs_h

    def handle_event(self, event: pygame.event.Event, canvas_size: Tuple[float, float]) -> None:
        """Processes clicks and drag events in relative coordinates."""
        canvas_w, canvas_h = canvas_size
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = getattr(event, "pos", None)
                if mouse_pos is None:
                    if pygame.display.get_init():
                        mouse_pos = pygame.mouse.get_pos()
                    else:
                        mouse_pos = (0, 0)
                
                if self.collidepoint(mouse_pos, canvas_size):
                    self.is_dragging = True
                    self.drag_start_pos = mouse_pos
                    self.dragged_far = False
                    self.drag_offset_x = (mouse_pos[0] / canvas_w) - self.x
                    self.drag_offset_y = (mouse_pos[1] / canvas_h) - self.y

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_pos = getattr(event, "pos", None)
                if mouse_pos is None:
                    if pygame.display.get_init():
                        mouse_pos = pygame.mouse.get_pos()
                    else:
                        mouse_pos = (0, 0)
                
                self.x = (mouse_pos[0] / canvas_w) - self.drag_offset_x
                self.y = (mouse_pos[1] / canvas_h) - self.drag_offset_y
                
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
        """Renders the node converted to absolute dimensions, including pan offsets."""
        if self.connection is not None and not getattr(self, "skip_connection_draw", False):
            self.connection.draw(screen, app)

        canvas_w, canvas_h = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        cx = self.center[0] * canvas_w + ox
        cy = self.center[1] * canvas_h + oy
        abs_r = self.radius * canvas_w
        abs_w = self.width * canvas_w
        abs_h = self.height * canvas_h

        active_fill = shared_style.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = shared_style.get_color("node_inactive_fill", (70, 70, 75, 255))
        active_border = shared_style.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        glow_color = shared_style.get_color("node_active_glow", (46, 204, 113, 40))
        text_color = shared_style.get_color("node_text", (240, 240, 245, 255))

        fill_color = active_fill if self.state else inactive_fill
        border_color = active_border if self.state else inactive_border

        # Selection highlight (yellow border)
        if getattr(self, "selected", False):
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            if self.shape == "circle":
                pygame.draw.circle(screen, sel_color[:3], (int(cx), int(cy)), int(abs_r) + 4, 3)
            else:
                rect_sel = pygame.Rect(int(self.x * canvas_w + ox) - 4, int(self.y * canvas_h + oy) - 4, int(abs_w) + 8, int(abs_h) + 8)
                try:
                    pygame.draw.rect(screen, sel_color[:3], rect_sel, 3, border_radius=8)
                except TypeError:
                    pygame.draw.rect(screen, sel_color[:3], rect_sel, 3)

        # Visual Glow for premium feel
        if self.state:
            glow_mult = shared_style.get_size("glow_radius_multiplier", 1.5)
            glow_radius = int(abs_r * glow_mult)
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
            pygame.draw.circle(screen, fill_color[:3], (int(cx), int(cy)), int(abs_r))
            pygame.draw.circle(screen, border_color[:3], (int(cx), int(cy)), int(abs_r), 2)
        else:
            rect_obj = pygame.Rect(int(self.x * canvas_w + ox), int(self.y * canvas_h + oy), int(abs_w), int(abs_h))
            try:
                pygame.draw.rect(screen, fill_color[:3], rect_obj, border_radius=6)
                pygame.draw.rect(screen, border_color[:3], rect_obj, 2, border_radius=6)
            except TypeError:
                pygame.draw.rect(screen, fill_color[:3], rect_obj)
                pygame.draw.rect(screen, border_color[:3], rect_obj, 2)

        # Draw Label Text centered
        if not pygame.font.get_init():
            pygame.font.init()
        font_h = int(abs_r * 1.0) if self.shape == "circle" else int(abs_h * 0.55)
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
        shape: Optional[str] = None,
        size: Optional[Union[float, Tuple[float, float]]] = None,
        label_prefix: str = "I",
        state: bool = False,
        connection: Optional[Any] = None
    ):
        if shape is None:
            shape = shared_style.get_shape("input_node_shape", "circle")
        if size is None:
            size = shared_style.get_size("input_node_size", 0.013)
        super().__init__(
            pos=pos,
            shape=shape,
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
        shape: Optional[str] = None,
        size: Optional[Union[float, Tuple[float, float]]] = None,
        label_prefix: str = "O",
        connection: Optional[Any] = None
    ):
        if shape is None:
            shape = shared_style.get_shape("output_node_shape", "rectangle")
        if size is None:
            size = shared_style.get_size("output_node_size", 0.026)
        super().__init__(
            pos=pos,
            shape=shape,
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
        size: float = 0.005,
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
                return getattr(self, "_state", False)
        finally:
            self._evaluating = False

    @state.setter
    def state(self, val: bool) -> None:
        self._state = val

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Draws the sub-node triangle and handles glow effect."""
        if self.connection is not None and not getattr(self, "skip_connection_draw", False):
            self.connection.draw(screen, app)

        canvas_w, canvas_h = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        cx = self.center[0] * canvas_w + ox
        cy = self.center[1] * canvas_h + oy
        abs_r = self.radius * canvas_w

        active_fill = shared_style.get_color("node_active_fill", (46, 204, 113, 255))
        inactive_fill = shared_style.get_color("node_inactive_fill", (70, 70, 75, 255))
        active_border = shared_style.get_color("node_active_border", (50, 255, 120, 255))
        inactive_border = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        glow_color = shared_style.get_color("node_active_glow", (46, 204, 113, 40))

        state_active = self.state
        fill_color = active_fill if state_active else inactive_fill
        border_color = active_border if state_active else inactive_border

        # Calculate parent relative center (for pointing direction)
        pc_x = self.parent.width / 2.0
        pc_y = self.parent.height / 2.0
        dx = pc_x - self.rel_x
        dy = pc_y - self.rel_y
        
        # Scale to canvas size for correct aspect ratio vector
        dx_abs = dx * canvas_w
        dy_abs = dy * canvas_h
        length = math.hypot(dx_abs, dy_abs)
        if length > 0:
            ux, uy = dx_abs / length, dy_abs / length
        else:
            ux, uy = 1.0, 0.0

        if self.is_transmitter:
            px, py = -ux, -uy
        else:
            px, py = ux, uy

        # Selection outline (yellow border)
        if getattr(self, "selected", False):
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            r_sel = abs_r + 3
            V1_s = (cx + r_sel * px, cy + r_sel * py)
            bc_x_s = cx - 0.5 * r_sel * px
            bc_y_s = cy - 0.5 * r_sel * py
            V2_s = (bc_x_s - r_sel * py, bc_y_s + r_sel * px)
            V3_s = (bc_x_s + r_sel * py, bc_y_s - r_sel * px)
            pygame.draw.polygon(screen, sel_color[:3], [V1_s, V2_s, V3_s], 2)

        # Visual glow
        if state_active:
            glow_mult = shared_style.get_size("glow_radius_multiplier", 1.5)
            glow_radius = int(abs_r * glow_mult)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (glow_color[0], glow_color[1], glow_color[2], 60),
                (glow_radius, glow_radius),
                glow_radius
            )
            screen.blit(glow_surf, (int(cx - glow_radius), int(cy - glow_radius)))

        # Draw actual triangle shape
        V1 = (cx + abs_r * px, cy + abs_r * py)
        bc_x = cx - 0.5 * abs_r * px
        bc_y = cy - 0.5 * abs_r * py
        V2 = (bc_x - abs_r * py, bc_y + abs_r * px)
        V3 = (bc_x + abs_r * py, bc_y - abs_r * px)

        pygame.draw.polygon(screen, fill_color[:3], [V1, V2, V3])
        pygame.draw.polygon(screen, border_color[:3], [V1, V2, V3], 1)


class LogicComponent(InteractiveNode):
    """A rectangular component containing input and output edge sub-nodes.
    
    Evaluates its output states based on current input states and a logic table
    or by simulating its internal custom sub-circuit.
    """
    def __init__(
        self,
        name: str,
        size: Tuple[float, float],
        inputs_def: List[dict],
        outputs_def: List[dict],
        logic_table: dict,
        pos: Tuple[float, float] = (0.1, 0.1),
        color: Optional[Tuple[int, int, int, int]] = None,
        inner_circuit: Optional[dict] = None
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

        self.inner_circuit = inner_circuit
        self.is_composite = inner_circuit is not None

        # Parse logic table only if not a composite gate
        self.parsed_table = {}
        if not self.is_composite:
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

        # Reconstruct composite inner circuit if applicable
        if self.is_composite:
            self.internal_objects, self.internal_connections = deserialize_inner_circuit(self.inner_circuit)
            self.input_mapping = {}
            self.output_mapping = {}

            # Map external pins to internal nodes by matching name/label
            internal_inputs = [obj for obj in self.internal_objects if isinstance(obj, GlobalInputNode)]
            for ext_in in self.inputs:
                match = next((i for i in internal_inputs if i.label == ext_in.label), None)
                if match:
                    self.input_mapping[ext_in] = match

            internal_outputs = [obj for obj in self.internal_objects if isinstance(obj, GlobalOutputNode)]
            for ext_out in self.outputs:
                match = next((o for o in internal_outputs if o.label == ext_out.label), None)
                if match:
                    self.output_mapping[ext_out] = match

    def get_output_state(self, subnode: ComponentSubNode) -> bool:
        if self.is_composite:
            int_out = self.output_mapping.get(subnode)
            if not int_out:
                return False

            # Propagate current states of external inputs to internal input nodes
            for ext_in, int_in in self.input_mapping.items():
                int_in.state = ext_in.state

            # Pull output state from internal receiver output node
            return int_out.state
        else:
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

    def handle_event(self, event: pygame.event.Event, canvas_size: Tuple[float, float]) -> None:
        """Ignores drag initialization if mouse click lands directly on a child sub-node."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = getattr(event, "pos", None)
            if mouse_pos is None:
                if pygame.display.get_init():
                    mouse_pos = pygame.mouse.get_pos()
                else:
                    mouse_pos = (0, 0)
            if any(inp.collidepoint(mouse_pos, canvas_size) for inp in self.inputs) or any(out.collidepoint(mouse_pos, canvas_size) for out in self.outputs):
                return
        super().handle_event(event, canvas_size)

    def draw(self, screen: pygame.Surface, app: Any) -> None:
        """Renders the component's rectangular body, name, and inside node labels."""
        canvas_w, canvas_h = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        abs_x = self.x * canvas_w + ox
        abs_y = self.y * canvas_h + oy
        abs_w = self.width * canvas_w
        abs_h = self.height * canvas_h

        bg_fill = self.color if self.color else shared_style.get_color("logic_component_fill", (142, 68, 173, 255))
        border_color = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        
        rect_obj = pygame.Rect(int(abs_x), int(abs_y), int(abs_w), int(abs_h))
        
        # Highlight selected
        if getattr(self, "selected", False):
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            try:
                pygame.draw.rect(screen, sel_color[:3], pygame.Rect(int(abs_x) - 4, int(abs_y) - 4, int(abs_w) + 8, int(abs_h) + 8), 3, border_radius=8)
            except TypeError:
                pygame.draw.rect(screen, sel_color[:3], pygame.Rect(int(abs_x) - 4, int(abs_y) - 4, int(abs_w) + 8, int(abs_h) + 8), 3)

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
        font_h = int(abs_h * 0.35)
        try:
            font = pygame.font.Font(None, max(14, font_h))
        except Exception:
            font = pygame.font.SysFont("arial", max(14, font_h))
            
        text_surf = font.render(self.label_prefix, True, (255, 255, 255))
        cx = abs_x + abs_w / 2.0
        cy = abs_y + abs_h / 2.0
        tx = cx - text_surf.get_width() / 2.0
        ty = cy - text_surf.get_height() / 2.0
        screen.blit(text_surf, (int(tx), int(ty)))

        # Draw inside labels for the sub-nodes
        try:
            label_font = pygame.font.Font(None, max(12, int(abs_h * 0.25)))
        except Exception:
            label_font = pygame.font.SysFont("arial", max(12, int(abs_h * 0.25)))
            
        # Draw input sub-node labels
        for inp in self.inputs:
            lbl_surf = label_font.render(inp.label, True, (220, 220, 225))
            ox_lbl = 10 if inp.rel_x < self.width / 2 else -10 - lbl_surf.get_width()
            oy_lbl = -lbl_surf.get_height() / 2
            abs_inp_x = inp.x * canvas_w + ox
            abs_inp_y = inp.y * canvas_h + oy
            screen.blit(lbl_surf, (int(abs_inp_x + ox_lbl), int(abs_inp_y + oy_lbl)))

        # Draw output sub-node labels
        for out in self.outputs:
            lbl_surf = label_font.render(out.label, True, (220, 220, 225))
            ox_lbl = 10 if out.rel_x < self.width / 2 else -10 - lbl_surf.get_width()
            oy_lbl = -lbl_surf.get_height() / 2
            abs_out_x = out.x * canvas_w + ox
            abs_out_y = out.y * canvas_h + oy
            screen.blit(lbl_surf, (int(abs_out_x + ox_lbl), int(abs_out_y + oy_lbl)))

    @classmethod
    def from_json(cls, source: Union[str, dict], pos: Tuple[float, float] = (0.1, 0.1)) -> "LogicComponent":
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
                from pathlib import Path
                lib_path = Path("mode/LogicGate/LogicComponentLib.json")
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

        # Convert sizes to relative coordinates if they are absolute pixels
        if width > 1.0:
            width_rel = width / 1920.0
        else:
            width_rel = width

        if height > 1.0:
            height_rel = height / 1080.0
        else:
            height_rel = height

        # Convert position
        instance_pos_abs = (data.get("x", pos[0]), data.get("y", pos[1]))
        if instance_pos_abs[0] > 1.0 or instance_pos_abs[1] > 1.0:
            instance_pos = (instance_pos_abs[0] / 1920.0, instance_pos_abs[1] / 1080.0)
        else:
            instance_pos = instance_pos_abs

        # Convert pin configurations
        inputs_def = []
        for inp in data.get("inputs", []):
            inp_rel_x = float(inp["rel_x"])
            inp_rel_y = float(inp["rel_y"])
            if inp_rel_x > 1.0 or inp_rel_y > 1.0 or width > 1.0:
                rx = (inp_rel_x / width) * width_rel
                ry = (inp_rel_y / height) * height_rel
            else:
                rx = inp_rel_x
                ry = inp_rel_y
            inputs_def.append({
                "name": inp["name"],
                "rel_x": rx,
                "rel_y": ry,
                "color": inp.get("color")
            })

        outputs_def = []
        for out in data.get("outputs", []):
            out_rel_x = float(out["rel_x"])
            out_rel_y = float(out["rel_y"])
            if out_rel_x > 1.0 or out_rel_y > 1.0 or width > 1.0:
                rx = (out_rel_x / width) * width_rel
                ry = (out_rel_y / height) * height_rel
            else:
                rx = out_rel_x
                ry = out_rel_y
            outputs_def.append({
                "name": out["name"],
                "rel_x": rx,
                "rel_y": ry,
                "color": out.get("color")
            })

        logic_table = data.get("logic_table", {})
        inner_circuit = data.get("inner_circuit")

        return cls(
            name=name,
            size=(width_rel, height_rel),
            inputs_def=inputs_def,
            outputs_def=outputs_def,
            logic_table=logic_table,
            pos=instance_pos,
            color=color,
            inner_circuit=inner_circuit
        )

    def to_dict(self) -> dict:
        """Serializes the LogicComponent into a dictionary in absolute coordinates."""
        # Convert back to absolute pixels using reference size (1920, 1080)
        abs_width = self.width * 1920.0
        abs_height = self.height * 1080.0

        d = {
            "name": self.label_prefix,
            "width": int(abs_width),
            "height": int(abs_height),
            "x": int(self.x * 1920.0),
            "y": int(self.y * 1080.0),
            "color": list(self.color) if self.color else None,
            "inputs": [
                {
                    "name": inp._custom_label,
                    "rel_x": int((inp.rel_x / self.width) * abs_width),
                    "rel_y": int((inp.rel_y / self.height) * abs_height),
                    "color": list(inp.color) if inp.color else None
                }
                for inp in self.inputs
            ],
            "outputs": [
                {
                    "name": out._custom_label,
                    "rel_x": int((out.rel_x / self.width) * abs_width),
                    "rel_y": int((out.rel_y / self.height) * abs_height),
                    "color": list(out.color) if out.color else None
                }
                for out in self.outputs
            ]
        }

        if self.is_composite:
            d["type"] = "composite"
            d["inner_circuit"] = self.inner_circuit
        else:
            # Convert parsed_table keys back to comma-separated strings
            serializable_table = {}
            for k, v in self.parsed_table.items():
                k_str = ",".join("1" if b else "0" for b in k)
                v_str = ",".join("1" if b else "0" for b in v)
                serializable_table[k_str] = v_str
            d["logic_table"] = serializable_table

        return d

    def to_json(self, json_path: str) -> None:
        """Saves the LogicComponent to a JSON file."""
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


def serialize_canvas(app: Any) -> dict:
    """Serializes all playground components and connections into relative coordinates."""
    nodes_serialized = []
    
    for obj in app.objects:
        if isinstance(obj, GlobalInputNode):
            nodes_serialized.append({
                "type": "input",
                "label": obj.label,
                "custom_name": obj.custom_name,
                "x": obj.x,
                "y": obj.y
            })
        elif isinstance(obj, GlobalOutputNode):
            nodes_serialized.append({
                "type": "output",
                "label": obj.label,
                "custom_name": obj.custom_name,
                "x": obj.x,
                "y": obj.y
            })
        elif isinstance(obj, LogicComponent):
            nodes_serialized.append({
                "type": "gate",
                "label": obj.label,
                "gate_name": obj.label_prefix,
                "x": obj.x,
                "y": obj.y,
                "width": obj.width,
                "height": obj.height,
                "color": list(obj.color) if obj.color else None
            })

    connections_serialized = []
    for conn in app.connections:
        conn_nodes = []
        for c in conn.connector_nodes:
            c_dict = {
                "id": c.id,
                "x": c.x,
                "y": c.y
            }
            if c.linked_node is not None:
                if isinstance(c.linked_node, (GlobalInputNode, GlobalOutputNode)):
                    c_dict["linked_to"] = {
                        "type": "global",
                        "label": c.linked_node.label
                    }
                elif isinstance(c.linked_node, ComponentSubNode):
                    gate = c.linked_node.parent
                    if c.linked_node in gate.inputs:
                        idx = gate.inputs.index(c.linked_node)
                        pin_type = "input"
                    else:
                        idx = gate.outputs.index(c.linked_node)
                        pin_type = "output"
                    c_dict["linked_to"] = {
                        "type": "gate_pin",
                        "gate_label": gate.label,
                        "pin_type": pin_type,
                        "pin_index": idx
                    }
            conn_nodes.append(c_dict)
            
        connections_serialized.append({
            "connector_nodes": conn_nodes,
            "lines": conn.lines
        })

    return {
        "nodes": nodes_serialized,
        "connections": connections_serialized
    }


def deserialize_inner_circuit(inner_circuit_def: dict) -> Tuple[List[Any], List[Any]]:
    """Reconstructs internal node and connection objects from a composite gate template."""
    from .connections import ConnectorNode, Connection
    
    objects = []
    connections = []
    label_map = {}
    
    # 1. Recreate nodes
    for node_def in inner_circuit_def.get("nodes", []):
        ntype = node_def["type"]
        x, y = node_def["x"], node_def["y"]
        label = node_def["label"]
        custom_name = node_def.get("custom_name")
        
        if ntype == "input":
            inp = GlobalInputNode(pos=(x, y))
            inp.custom_name = custom_name
            label_map[label] = inp
            objects.append(inp)
        elif ntype == "output":
            out = GlobalOutputNode(pos=(x, y))
            out.custom_name = custom_name
            label_map[label] = out
            objects.append(out)
        elif ntype == "gate":
            gate_name = node_def["gate_name"]
            width = node_def["width"]
            height = node_def["height"]
            color = node_def.get("color")
            if color:
                color = tuple(color)
            
            gate = LogicComponent.from_json(gate_name, pos=(x, y))
            gate.width = width
            gate.height = height
            if color:
                gate.color = color
                
            label_map[label] = gate
            objects.append(gate)
            for inp in gate.inputs:
                objects.append(inp)
            for out in gate.outputs:
                objects.append(out)

    # 2. Recreate connections
    for conn_def in inner_circuit_def.get("connections", []):
        conn_nodes = []
        for c_def in conn_def.get("connector_nodes", []):
            cid = c_def["id"]
            cx, cy = c_def["x"], c_def["y"]
            linked_def = c_def.get("linked_to")
            
            linked_node = None
            if linked_def:
                ltype = linked_def["type"]
                if ltype == "global":
                    linked_node = label_map.get(linked_def["label"])
                elif ltype == "gate_pin":
                    gate = label_map.get(linked_def["gate_label"])
                    if gate:
                        ptype = linked_def["pin_type"]
                        pidx = linked_def["pin_index"]
                        if ptype == "input" and pidx < len(gate.inputs):
                            linked_node = gate.inputs[pidx]
                        elif ptype == "output" and pidx < len(gate.outputs):
                            linked_node = gate.outputs[pidx]
                            
            c_node = ConnectorNode(identifier=cid, x=cx, y=cy, linked_node=linked_node)
            conn_nodes.append(c_node)
            
        lines = []
        for line in conn_def.get("lines", []):
            lines.append((line[0], line[1]))
            
        conn = Connection(connector_nodes=conn_nodes, lines=lines)
        connections.append(conn)
        
        for c_node in conn_nodes:
            if c_node.linked_node:
                c_node.linked_node.connection = conn

    return objects, connections
