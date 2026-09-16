import sys
import os
from typing import Optional, Tuple, Any, Set
import pygame

# Add project root to sys.path to ensure imports work cleanly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pyinteractive import PygameApp
from include import (
    Bits,
    Color,
    Relative,
    RelPoint,
    Area,
    Polygon,
    Direction,
    LogicTable,
    SimComponent,
    COMPONENT_LIB
)
from LogicGate_RW.core import (
    UINode,
    UIGlobalInputNode,
    UIGlobalOutputNode,
    UIComponentPin,
    UIConnectorPoint,
    UIConnection,
    UILogicComponent,
    UIArrayNode,
    UINodeArray
)
from LogicGate_RW.storage import (
    load_gui_library,
    load_groups,
    save_groups,
    get_component_group_color
)
from LogicGate_RW.modes import (
    draw_sim,
    handle_sim_event,
    to_canvas,
    draw_builder,
    handle_builder_event,
    init_builder_mode,
    draw_manager,
    handle_manager_event
)
from LogicGate_RW.ui.bottom_bar import draw_bottom_bar, handle_bottom_bar_event, update_bottom_bar
from LogicGate_RW.ui.left_panel import draw_left_panel, handle_left_panel_event
from LogicGate_RW.ui.style import shared_style

class LogicGateAppRW(PygameApp):
    """Rebuilt Logic Gate Simulation & Builder Playground driven by include.py logic classes."""

    def __init__(self):
        super().__init__(config_path="config.json", title="Logic Gate Playground (Rebuilt with include.py)")

        # Selection state
        self.selected_node: Optional[UINode] = None
        self.selected_connection: Optional[Tuple[UIConnection, Any]] = None
        self.selected_start_point: Optional[Any] = None

        # Mode: "sim", "builder", "manager"
        self.mode = "sim"

        # Viewport offsets & zoom
        self.offset = [0.0, 0.0]
        self.zoom_scale = 1.0
        self.is_panning = False
        self.pan_start_pos = (0.0, 0.0)

        # UI Animation and state
        self.bar_slide_ratio = 0.0
        self.bar_scroll_x = 0.0
        self.selected_placement_item = None
        self.active_picker_group = None
        self.show_help = False

        self.left_panel_open = False
        self.left_panel_slide_ratio = 0.0
        self.left_panel_scroll_y = 0.0

        # Groups and library loading
        self.groups = load_groups()
        self.gui_library = load_gui_library()

        # Canvas objects and connections
        self.connections: Set[UIConnection] = set()

        self._init_demo_nodes()

    def _init_demo_nodes(self):
        """Spawns an initial NOT gate demonstration circuit."""
        inp1 = UIGlobalInputNode(pos=(0.15, 0.38), state=True)
        out1 = UIGlobalOutputNode(pos=(0.65, 0.38))

        gate = None
        for item in self.gui_library:
            if item.get("name") in ("NOT", "!=") and item.get("template"):
                gate = UILogicComponent.from_template(item["template"], pos=(0.35, 0.34))
                break

        self.add_object(inp1)
        self.add_object(out1)

        if gate is not None:
            self.add_object(gate)
            for p in gate.inputs + gate.outputs:
                self.add_object(p)

            # Connect inp1 -> gate.inputs[0]
            c1 = UIConnectorPoint("c_in1", linked_node=inp1)
            c2 = UIConnectorPoint("c_gin", linked_node=gate.inputs[0])
            conn1 = UIConnection(connector_nodes=[c1, c2], lines=[("c_in1", "c_gin")])
            inp1.connection = conn1
            gate.inputs[0].connection = conn1
            self.connections.add(conn1)

            # Connect gate.outputs[0] -> out1
            c3 = UIConnectorPoint("c_gout", linked_node=gate.outputs[0])
            c4 = UIConnectorPoint("c_out1", linked_node=out1)
            conn2 = UIConnection(connector_nodes=[c3, c4], lines=[("c_gout", "c_out1")])
            gate.outputs[0].connection = conn2
            out1.connection = conn2
            self.connections.add(conn2)

    def select_node(self, node: Optional[UINode]):
        if self.selected_node:
            self.selected_node.selected = False
        if self.selected_connection and self.selected_connection[0]:
            self.selected_connection[0].selected_line = None

        self.selected_connection = None
        self.selected_node = node
        self.selected_start_point = node
        if node:
            node.selected = True

    def select_connection(self, conn: Optional[UIConnection], line: Optional[Tuple[Any, Any]]):
        if self.selected_node:
            self.selected_node.selected = False
            self.selected_node = None
        if self.selected_connection and self.selected_connection[0]:
            self.selected_connection[0].selected_line = None

        self.selected_connection = (conn, line) if conn is not None else None
        self.selected_start_point = None
        if conn:
            conn.selected_line = line

    def select_connector(self, connector: UIConnectorPoint):
        if self.selected_node:
            self.selected_node.selected = False
            self.selected_node = None
        if self.selected_connection and self.selected_connection[0]:
            self.selected_connection[0].selected_line = None
            self.selected_connection = None
        self.selected_start_point = connector

    def clear_selection(self):
        self.select_node(None)
        self.select_connection(None, None)
        self.selected_start_point = None

    def switch_to_sim(self):
        self.mode = "sim"
        self.gui_library = load_gui_library()
        self.groups = load_groups()
        self.selected_placement_item = None
        self.active_picker_group = None

    def switch_to_builder(self):
        self.clear_selection()
        init_builder_mode(self)
        self.mode = "builder"

    def switch_to_manager(self):
        self.clear_selection()
        self.mode = "manager"
        self.groups = load_groups()
        self.gui_library = load_gui_library()
        self.manager_selected_group_idx = 0 if self.groups else -1
        self.manager_editing_group_name = self.groups[0]["name"] if self.groups else ""
        self.manager_focus = None

    def get_component_group_color(self, name: str) -> Optional[Tuple[int, int, int, int]]:
        return get_component_group_color(self.groups, name)

    def save_groups(self):
        save_groups(self.groups)

    def tick_simulation(self):
        """Simulation tick driving signals through include.Connection and include.LogicTable/SimComponent."""
        # 1. Propagate input arrays
        for obj in self.objects:
            if isinstance(obj, UINodeArray):
                obj.run()

        # 2. Run connections from transmitters to receivers
        for conn in self.connections:
            conn.run()

        # 3. Run all logic components
        for obj in self.objects:
            if isinstance(obj, UILogicComponent):
                obj.run()

        # 4. Secondary propagation pass for downstream signals
        for conn in self.connections:
            conn.run()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.is_running = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.show_help = not self.show_help
            return

        # Toggle Left Panel on F2
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.left_panel_open = not self.left_panel_open
            return

        # Zoom on Space + Scroll
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                mx, my = event.pos
                z_old = self.zoom_scale
                if event.button == 4:
                    self.zoom_scale = min(4.0, z_old * 1.15)
                else:
                    self.zoom_scale = max(0.25, z_old / 1.15)
                z_ratio = self.zoom_scale / z_old
                self.offset[0] = mx - (mx - self.offset[0]) * z_ratio
                self.offset[1] = my - (my - self.offset[1]) * z_ratio
                return

        # Left panel event interception
        if self.left_panel_slide_ratio > 0.0:
            if handle_left_panel_event(self, event):
                return

        if self.mode == "builder":
            handle_builder_event(self, event)
        elif self.mode == "manager":
            handle_manager_event(self, event)
        else:
            # Right click deselects everything
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.selected_placement_item = None
                self.clear_selection()
                self.selected_start_point = None
                return

            # Offer event to bottom bar
            if handle_bottom_bar_event(self, event):
                return

            # Placement stamp click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.selected_placement_item is not None:
                screen_w, screen_h = self.screen.get_size()
                if event.pos[1] < screen_h - 110:
                    cpos = to_canvas(event.pos, self.offset, self.zoom_scale)
                    rel_pos = (cpos[0] / screen_w, cpos[1] / screen_h)
                    item = self.selected_placement_item

                    if item["type"] == "input":
                        inp = UIGlobalInputNode(pos=rel_pos)
                        self.add_object(inp)
                    elif item["type"] == "output":
                        out = UIGlobalOutputNode(pos=rel_pos)
                        self.add_object(out)
                    elif item["type"] == "array":
                        parts = item["name"].split()
                        atype = parts[0].lower()
                        size_align = parts[-1]
                        size = int(size_align[:-1])
                        align = size_align[-1]
                        arr = UINodeArray(array_type=atype, size=size, alignment=align, pos=rel_pos)
                        self.add_object(arr)
                        for sub in arr.nodes:
                            self.add_object(sub)
                    elif item["type"] == "gate" and item.get("template"):
                        gate = UILogicComponent.from_template(item["template"], pos=rel_pos)
                        self.add_object(gate)
                        for p in gate.inputs + gate.outputs:
                            self.add_object(p)

                    keys = pygame.key.get_pressed()
                    if not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                        self.selected_placement_item = None
                    return

            handle_sim_event(self, event)

    def update(self, dt: float):
        # Update left panel animation
        spd = 8.0
        if self.left_panel_open:
            self.left_panel_slide_ratio = min(1.0, self.left_panel_slide_ratio + spd * dt)
        else:
            self.left_panel_slide_ratio = max(0.0, self.left_panel_slide_ratio - spd * dt)

        if self.mode == "sim":
            update_bottom_bar(self, dt)
            self.tick_simulation()

        super().update(dt)

    def draw(self):
        bg = shared_style.get_color("background", (15, 15, 20, 255))
        self.screen.fill(bg[:3])

        if self.mode == "sim":
            draw_sim(self.screen, self)
            self._draw_hud()
            draw_bottom_bar(self.screen, self)
        elif self.mode == "builder":
            draw_builder(self.screen, self)
        elif self.mode == "manager":
            draw_manager(self.screen, self)

        if self.left_panel_slide_ratio > 0.0:
            draw_left_panel(self.screen, self)

    def _draw_hud(self):
        screen_w = self.screen.get_width()
        try:
            title_font = pygame.font.Font(None, 24)
            font = pygame.font.Font(None, 18)
        except Exception:
            title_font = pygame.font.SysFont("arial", 24)
            font = pygame.font.SysFont("arial", 18)

        t_str = "Logic Gate Playground (Rebuilt) - F1: Help" if not self.show_help else "Logic Gate Playground (Rebuilt) - Press F1 to Hide"
        t_surf = title_font.render(t_str, True, shared_style.get_color("primary")[:3])
        self.screen.blit(t_surf, ((screen_w - t_surf.get_width()) // 2, 15))

        if self.show_help:
            guides = [
                "SPACE + DRAG: Pan canvas  |  SPACE + SCROLL: Zoom",
                "LEFT CLICK: Select / Toggle input / Drag node",
                "CTRL + CLICK: Draw wire connection to node or free space",
                "DELETE: Delete selected node or wire segment",
                "F2: Toggle Left Node Inspector Panel",
                "Hover at bottom edge to pick gates  |  '+' top-right to build new gate",
                "ESC: Exit"
            ]
            y = 45
            for g in guides:
                s = font.render(g, True, (220, 220, 230))
                self.screen.blit(s, ((screen_w - s.get_width()) // 2, y))
                y += 18

def main():
    print("Launching Rebuilt Logic Gate Playground (LogicGate_RW)...")
    app = LogicGateAppRW()
    app.run()
    print("Application closed.")

if __name__ == "__main__":
    main()
