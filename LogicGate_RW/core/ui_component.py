import json
import os
import math
from typing import Any, List, Tuple, Optional, Dict
import pygame

from include import (
    Bits,
    Relative,
    RelPoint,
    Area,
    Polygon,
    Direction,
    Color,
    LogicTable,
    SimComponent,
    COMPONENT_LIB,
    create_node_constructor
)
from LogicGate_RW.core.ui_node import UINode, UIComponentPin, normalize_label
from LogicGate_RW.ui.style import shared_style

class UILogicComponent(UINode):
    """Visual gate component backed by an include.LogicTable or include.SimComponent."""

    def __init__(
        self,
        name: str,
        size: Tuple[float, float],
        inputs_def: List[dict],
        outputs_def: List[dict],
        logic_backend: Any,
        pos: Tuple[float, float] = (0.1, 0.1),
        color: Optional[Tuple[int, int, int, int]] = None,
        inner_circuit: Optional[dict] = None
    ):
        self.component_name = name
        self.color = color
        self.logic_backend = logic_backend
        self.inner_circuit = inner_circuit
        self.is_composite = inner_circuit is not None

        # Setup base UINode as rectangle
        super().__init__(
            pos=pos,
            shape="rectangle",
            size=size,
            label_prefix=name,
            state=False
        )

        # Setup Relative layout descriptor from include.py
        self.rel_layout = Relative(rel_size=size, rel_center_pos=(0.5, 0.5))

        # Create input and output pins
        self.inputs: List[UIComponentPin] = []
        for inp in inputs_def:
            pin = UIComponentPin(
                parent=self,
                rel_x=float(inp["rel_x"]),
                rel_y=float(inp["rel_y"]),
                is_transmitter=False,
                custom_label=inp.get("name", "I"),
                color=tuple(inp["color"]) if inp.get("color") else None,
                direction=Direction.W
            )
            self.inputs.append(pin)

        self.outputs: List[UIComponentPin] = []
        for out in outputs_def:
            pin = UIComponentPin(
                parent=self,
                rel_x=float(out["rel_x"]),
                rel_y=float(out["rel_y"]),
                is_transmitter=True,
                custom_label=out.get("name", "O"),
                color=tuple(out["color"]) if out.get("color") else None,
                direction=Direction.E
            )
            self.outputs.append(pin)

        # Setup composite inner circuit if provided
        if self.is_composite:
            from LogicGate_RW.core.circuit_bridge import deserialize_inner_circuit
            from LogicGate_RW.core.ui_node import UIGlobalInputNode, UIGlobalOutputNode
            from LogicGate_RW.core.ui_arrays import UIArrayNode
            self.internal_objects, self.internal_connections = deserialize_inner_circuit(self.inner_circuit)
            self.input_mapping = {}
            self.output_mapping = {}

            internal_inputs = [obj for obj in self.internal_objects if isinstance(obj, UIGlobalInputNode) or (isinstance(obj, UIArrayNode) and obj.is_transmitter)]
            for ext_in in self.inputs:
                ext_norm = normalize_label(ext_in.label)
                match = next((i for i in internal_inputs if normalize_label(i.label) == ext_norm), None)
                if match:
                    self.input_mapping[ext_in] = match

            internal_outputs = [obj for obj in self.internal_objects if isinstance(obj, UIGlobalOutputNode) or (isinstance(obj, UIArrayNode) and not obj.is_transmitter)]
            for ext_out in self.outputs:
                ext_norm = normalize_label(ext_out.label)
                match = next((o for o in internal_outputs if normalize_label(o.label) == ext_norm), None)
                if match:
                    self.output_mapping[ext_out] = match

    def run(self) -> None:
        """Executes simulation step using inner circuit or logic_backend."""
        if self.is_composite and hasattr(self, "internal_objects"):
            # 1. Update internal input nodes from external pins
            for ext_in, int_in in self.input_mapping.items():
                int_in.state = ext_in.state

            # 2. Run multi-pass simulation over inner components and connections
            for _ in range(4):
                for obj in self.internal_objects:
                    if isinstance(obj, UILogicComponent):
                        obj.run()
                    elif hasattr(obj, "run"):
                        obj.run()
                for conn in self.internal_connections:
                    if hasattr(conn, "run"):
                        conn.run()

            # 3. Update external output pins from internal output nodes
            for ext_out, int_out in self.output_mapping.items():
                ext_out.state = int_out.state

        elif self.logic_backend is not None:
            # Transfer input pin states into logic backend
            in_states = [p.state for p in self.inputs]
            if hasattr(self.logic_backend, "set_input_state"):
                self.logic_backend.set_input_state(in_states)

            # Run backend evaluation step
            self.logic_backend.run()

            # Transfer output states back to output pins
            out_states = getattr(self.logic_backend, "output_state", [])
            for pin, state in zip(self.outputs, out_states):
                pin.state = bool(state)

    @property
    def state(self) -> bool:
        return any(out.state for out in self.outputs)

    @state.setter
    def state(self, val: bool):
        pass

    def handle_event(self, event: pygame.event.Event, canvas_size: Tuple[float, float]) -> None:
        # Don't drag component if clicking directly on a pin
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mpos = event.pos
            if any(p.collidepoint(mpos, canvas_size) for p in self.inputs + self.outputs):
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

        group_color = None
        if hasattr(app, "get_component_group_color"):
            group_color = app.get_component_group_color(self.label_prefix)

        bg_fill = group_color if group_color is not None else (self.color if self.color else shared_style.get_color("logic_component_fill", (142, 68, 173, 255)))
        border_color = shared_style.get_color("node_inactive_border", (140, 140, 150, 255))
        rect_obj = pygame.Rect(int(abs_x), int(abs_y), int(abs_w), int(abs_h))

        # Highlight selection
        if self.selected:
            sel_color = shared_style.get_color("node_selected_border", (255, 220, 0, 255))
            pygame.draw.rect(screen, sel_color[:3], pygame.Rect(int(abs_x) - 4, int(abs_y) - 4, int(abs_w) + 8, int(abs_h) + 8), 3, border_radius=8)

        # Component Body
        pygame.draw.rect(screen, bg_fill[:3], rect_obj, border_radius=6)
        pygame.draw.rect(screen, border_color[:3], rect_obj, 2, border_radius=6)

        # Centered label
        font_size = shared_style.get_size("font_size_component", 16)
        try:
            font = pygame.font.Font(None, font_size)
        except Exception:
            font = pygame.font.SysFont("arial", font_size)
        text_surf = font.render(self.label_prefix, True, (255, 255, 255))
        tx = abs_x + (abs_w - text_surf.get_width()) / 2.0
        ty = abs_y + (abs_h - text_surf.get_height()) / 2.0
        screen.blit(text_surf, (int(tx), int(ty)))

    def draw_labels(self, screen: pygame.Surface, app: Any) -> None:
        """Renders pin text labels."""
        cw, ch = screen.get_size()
        ox, oy = getattr(app, "offset", (0.0, 0.0))
        zoom = getattr(app, "zoom_scale", 1.0)
        font_size = shared_style.get_size("font_size_subnode", 12)
        try:
            label_font = pygame.font.Font(None, font_size)
        except Exception:
            label_font = pygame.font.SysFont("arial", font_size)

        for inp in self.inputs:
            cx = (inp.center[0] * cw) * zoom + ox
            cy = (inp.center[1] * ch) * zoom + oy
            lbl = label_font.render(inp.label, True, (220, 220, 225))
            screen.blit(lbl, (int(cx + 8), int(cy - lbl.get_height() / 2)))

        for out in self.outputs:
            cx = (out.center[0] * cw) * zoom + ox
            cy = (out.center[1] * ch) * zoom + oy
            lbl = label_font.render(out.label, True, (220, 220, 225))
            screen.blit(lbl, (int(cx - lbl.get_width() - 8), int(cy - lbl.get_height() / 2)))

    @classmethod
    def from_template(cls, template: dict, pos: Tuple[float, float] = (0.1, 0.1)) -> "UILogicComponent":
        """Instantiates a UILogicComponent using a template dictionary and include.py classes."""
        name = template.get("name", "Gate")
        w = template.get("width", 100)
        h = template.get("height", 80)
        # Relative size normalized against 1000x800 default canvas
        size = (w / 1000.0, h / 800.0)
        inputs_def = template.get("inputs", [])
        outputs_def = template.get("outputs", [])
        raw_color = template.get("color")
        color = tuple(raw_color) if raw_color else None

        # Convert relative pixel pin offsets to relative unit fractions
        norm_inputs = []
        for inp in inputs_def:
            norm_inputs.append({
                "name": inp.get("name", "I"),
                "rel_x": float(inp.get("rel_x", 0)) / 1000.0,
                "rel_y": float(inp.get("rel_y", 0)) / 800.0,
                "color": inp.get("color")
            })

        norm_outputs = []
        for out in outputs_def:
            norm_outputs.append({
                "name": out.get("name", "O"),
                "rel_x": float(out.get("rel_x", 0)) / 1000.0,
                "rel_y": float(out.get("rel_y", 0)) / 800.0,
                "color": out.get("color")
            })

        n_in = len(inputs_def)
        n_out = len(outputs_def)

        # Build backend using include.COMPONENT_LIB or compile table
        backend = None
        comp_lib_item = COMPONENT_LIB.get(name)
        if comp_lib_item is not None:
            backend = comp_lib_item
        elif "logic_table" in template:
            # Convert dictionary truth table into include.Bits
            t_dict = template["logic_table"]
            table_bits_str = ""
            for i in range(2 ** n_in):
                # Format binary key
                key = bin(i)[2:].zfill(n_in)
                val = t_dict.get(key, "0" * n_out)
                if isinstance(val, (list, tuple)):
                    val_str = "".join("1" if b else "0" for b in val)
                else:
                    val_str = str(val)
                table_bits_str += val_str
            table_bits = Bits(table_bits_str)
            backend = LogicTable(create_node_constructor(), (n_in, n_out), table_bits)

        return cls(
            name=name,
            size=size,
            inputs_def=norm_inputs,
            outputs_def=norm_outputs,
            logic_backend=backend,
            pos=pos,
            color=color,
            inner_circuit=template.get("inner_circuit")
        )
