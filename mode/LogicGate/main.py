import sys
import os
import json

# Add the project root directory to sys.path to allow running this script directly
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
from pyinteractive import PygameApp
from mode.LogicGate.Nodes import (
    InteractiveNode,
    GlobalInputNode,
    GlobalOutputNode,
    ConnectorNode,
    Connection,
    LogicComponent,
    ComponentSubNode,
    ArrayNode,
    NodeArray
)

# Import module functions from absolute package paths
from mode.LogicGate.sim import draw_sim, handle_sim_event, to_canvas
from mode.LogicGate.gui import draw_gui, handle_gui_event, update_gui, load_gui_library
from mode.LogicGate.builder import draw_builder, handle_builder_event, init_builder_mode
from mode.LogicGate.manager import draw_manager, handle_manager_event

class LogicGateApp(PygameApp):
    """The main Logic Gate Simulation and Builder Application."""
    
    def __init__(self):
        # Configure app title
        super().__init__(config_path="config.json", title="Logic Gate Playground & Builder")
        
        # Selection states
        self.selected_node = None
        self.selected_connection = None  # Tuple: (connection, line)
        self.selected_start_point = None # InteractiveNode or ConnectorNode
        self.is_dragging_connector = False
        self.dragged_connector = None

        # Mode setup
        self.mode = "sim" # "sim" or "builder"
        
        # Viewport offsets
        self.offset = [0.0, 0.0]
        self.is_panning = False
        self.pan_start_pos = (0.0, 0.0)

        # Bottom hover-bar variables
        self.bar_slide_ratio = 0.0
        self.bar_scroll_x = 0.0
        self.selected_placement_item = None
        self.active_picker_group = None
        self.editing_array_value_node = None
        self.editing_array_value_str = ""
        
        # Left panel variables
        self.left_panel_open = False
        self.left_panel_slide_ratio = 0.0
        self.left_panel_scroll_y = 0.0
        self.editing_node = None
        self.editing_name = ""

        # Groups overlay variables
        self.groups = []
        self.load_groups()

        # Load logic component template library
        self.gui_library = load_gui_library()

        # Set up custom theme colors for selections
        self._ensure_theme_colors()
        
        # Create initial nodes
        self._init_demo_nodes()

    def _ensure_theme_colors(self):
        """Pre-populates application colortheme with default colors if not already defined."""
        theme = self.config.colortheme
        defaults = {
            "connection_active": (0, 255, 240, 255),
            "connection_inactive": (80, 80, 95, 255),
            "connection_selected": (255, 220, 0, 255),
            "node_active_fill": (46, 204, 113, 255),
            "node_inactive_fill": (60, 60, 65, 255),
            "node_active_border": (50, 255, 120, 255),
            "node_inactive_border": (140, 140, 150, 255),
            "node_selected_border": (255, 220, 0, 255),
            "node_active_glow": (46, 204, 113, 40),
            "node_text": (240, 240, 245, 255),
            "logic_component_fill": (142, 68, 173, 255),
            "background": (15, 15, 20, 255),
            "primary": (142, 68, 173, 255),
            "secondary": (155, 89, 182, 255)
        }
        for k, v in defaults.items():
            if k not in theme:
                theme[k] = v

    def _init_demo_nodes(self):
        """Spawns initial inputs, outputs, and connections in the playground."""
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()

        inp1 = GlobalInputNode(pos=(0.15, 0.3))
        inp2 = GlobalInputNode(pos=(0.15, 0.5))
        out1 = GlobalOutputNode(pos=(0.75, 0.4))

        # Load standard gate from library if present
        gate = None
        for item in self.gui_library:
            if item["type"] == "gate" and item["name"] == "!=":
                try:
                    gate = LogicComponent.from_json("!=", pos=(0.4, 0.38))
                except Exception as e:
                    print(f"Error auto-loading NOT gate: {e}")
                break

        self.add_object(inp1)
        self.add_object(inp2)
        self.add_object(out1)

        if gate:
            self.add_object(gate)
            for inp in gate.inputs:
                self.add_object(inp)
            for out in gate.outputs:
                self.add_object(out)

            # Establish initial connections: inp1 -> gate.input, gate.output -> out1
            c1 = ConnectorNode(identifier="c_inp1", linked_node=inp1)
            c2 = ConnectorNode(identifier="c_gate_in", linked_node=gate.inputs[0])
            conn1 = Connection(connector_nodes=[c1, c2])
            conn1.add_line("c_inp1", "c_gate_in")
            inp1.connection = conn1
            gate.inputs[0].connection = conn1

            c3 = ConnectorNode(identifier="c_gate_out", linked_node=gate.outputs[0])
            c4 = ConnectorNode(identifier="c_out1", linked_node=out1)
            conn2 = Connection(connector_nodes=[c3, c4])
            conn2.add_line("c_gate_out", "c_out1")
            gate.outputs[0].connection = conn2
            out1.connection = conn2

        # Cache active connections
        self.connections = {obj.connection for obj in self.objects if isinstance(obj, InteractiveNode) and obj.connection is not None}

    def select_node(self, node: InteractiveNode):
        if self.selected_node:
            self.selected_node.selected = False
        if self.selected_connection and self.selected_connection[0] is not None:
            conn, line = self.selected_connection
            conn.selected_line = None
            
        self.selected_connection = None
        self.selected_node = node
        self.selected_start_point = node
        if node:
            node.selected = True

    def select_connection(self, conn: Connection, line: tuple):
        if self.selected_node:
            self.selected_node.selected = False
            self.selected_node = None
        if self.selected_connection and self.selected_connection[0] is not None:
            prev_conn, prev_line = self.selected_connection
            prev_conn.selected_line = None
            
        self.selected_connection = (conn, line) if conn is not None else None
        self.selected_start_point = None
        if conn:
            conn.selected_line = line

    def select_connector(self, connector: ConnectorNode):
        if self.selected_node:
            self.selected_node.selected = False
            self.selected_node = None
        if self.selected_connection and self.selected_connection[0] is not None:
            prev_conn, prev_line = self.selected_connection
            prev_conn.selected_line = None
            self.selected_connection = None
            
        self.selected_start_point = connector

    def clear_selection(self):
        self.select_node(None)
        self.select_connection(None, None)
        self.selected_start_point = None

    def switch_to_builder(self):
        """Handles switching from Simulation mode to Builder mode."""
        self.clear_selection()
        init_builder_mode(self)
        self.mode = "builder"
        self.active_picker_group = None

    def load_groups(self):
        """Loads logic component groups from the overlay JSON file."""
        lib_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(lib_dir, 'LogicComponentGroups.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    self.groups = json.load(f)
            except Exception as e:
                print(f"Error loading group overlay: {e}")
                self.groups = []
        else:
            self.groups = []

        # Ensure default "Inputs" and "Outputs" groups exist
        has_inputs = any(g["name"] == "Inputs" for g in self.groups)
        has_outputs = any(g["name"] == "Outputs" for g in self.groups)
        
        default_inputs = [
            "Input Array 2H", "Input Array 2V",
            "Input Array 4H", "Input Array 4V",
            "Input Array 8H", "Input Array 8V"
        ]
        default_outputs = [
            "Output Array 2H", "Output Array 2V",
            "Output Array 4H", "Output Array 4V",
            "Output Array 8H", "Output Array 8V"
        ]
        
        changed = False
        if not has_inputs:
            self.groups.append({
                "name": "Inputs",
                "color": [142, 68, 173],
                "components": default_inputs
            })
            changed = True
        if not has_outputs:
            self.groups.append({
                "name": "Outputs",
                "color": [46, 204, 113],
                "components": default_outputs
            })
            changed = True
            
        if changed:
            self.save_groups()

    def save_groups(self):
        """Saves logic component groups to the overlay JSON file and syncs it to the root."""
        lib_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(lib_dir, 'LogicComponentGroups.json')
        try:
            with open(path, 'w') as f:
                json.dump(self.groups, f, indent=2)
        except Exception as e:
            print(f"Error saving group overlay: {e}")

        # Sync to root LogicComponentGroups.json
        root_path = os.path.join(os.path.dirname(os.path.dirname(lib_dir)), 'LogicComponentGroups.json')
        try:
            with open(root_path, 'w') as f:
                json.dump(self.groups, f, indent=2)
        except Exception as e:
            print(f"Error syncing group overlay to root: {e}")

    def get_component_group_color(self, component_name: str) -> Optional[Tuple[int, int, int, int]]:
        """Returns the assigned group color for a component if its group has a color assigned."""
        for g in self.groups:
            if component_name in g.get("components", []):
                color = g.get("color")
                if color:
                    if len(color) == 3:
                        return (color[0], color[1], color[2], 255)
                    elif len(color) == 4:
                        return (color[0], color[1], color[2], color[3])
        return None

    def switch_to_manager(self):
        """Handles switching to Components Manager mode."""
        self.clear_selection()
        self.mode = "manager"
        self.load_groups()
        self.gui_library = load_gui_library()
        self.manager_selected_group_idx = 0 if self.groups else -1
        self.manager_editing_group_name = ""
        self.manager_focus = None
        self.active_picker_group = None

    def switch_to_sim(self):
        """Handles switching from other modes back to Simulation mode."""
        self.selected_placement_item = None
        self.active_picker_group = None
        self.mode = "sim"
        # Reload library templates and groups
        self.gui_library = load_gui_library()
        self.load_groups()

    def handle_event(self, event: pygame.event.Event):
        """Delegates event routing based on the current active mode."""
        if event.type == pygame.QUIT:
            self.is_running = False
            return
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.is_running = False
            return
            
        # Toggle left panel on F2 key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.left_panel_open = not self.left_panel_open
            if not self.left_panel_open:
                # If closed, commit or cancel editing
                if getattr(self, "editing_node", None) is not None:
                    name_to_commit = self.editing_name.strip()
                    from mode.LogicGate.gui import is_name_valid_and_unique
                    if is_name_valid_and_unique(self, self.editing_node, name_to_commit):
                        self.editing_node.custom_name = name_to_commit
                        if self.mode == "builder":
                            from mode.LogicGate.builder import init_builder_mode
                            init_builder_mode(self)
                    self.editing_node = None
            return

        # Intercept event for left panel if slide ratio > 0
        if getattr(self, "left_panel_slide_ratio", 0.0) > 0.0:
            from mode.LogicGate.gui import handle_left_panel_event
            if handle_left_panel_event(self, event):
                return

        if self.mode == "builder":
            handle_builder_event(self, event)
        elif self.mode == "manager":
            handle_manager_event(self, event)
        else:
            # 1. First offer event to GUI (bottom picker/plus button)
            if handle_gui_event(self, event):
                return

            # 2. Handle stamp-placement click when placing an item on canvas
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.selected_placement_item is not None:
                    # Ignore placement Y inside bottom hover Y area
                    screen_w = self.screen.get_width()
                    screen_h = self.screen.get_height()
                    if event.pos[1] < screen_h - 110:
                        canvas_pos = to_canvas(event.pos, self.offset)
                        rel_pos = (canvas_pos[0] / screen_w, canvas_pos[1] / screen_h)
                        item = self.selected_placement_item
                        if item["type"] == "input":
                            inp = GlobalInputNode(pos=rel_pos)
                            self.add_object(inp)
                        elif item["type"] == "output":
                            out = GlobalOutputNode(pos=rel_pos)
                            self.add_object(out)
                        elif item["type"] == "array":
                            try:
                                name_parts = item["name"].split()
                                array_type = name_parts[0].lower() # "input" or "output"
                                size_align = name_parts[-1] # e.g. "4V"
                                size = int(size_align[:-1])
                                alignment = size_align[-1]
                                
                                arr = NodeArray(array_type, size, alignment, pos=rel_pos)
                                self.add_object(arr)
                                for node in arr.nodes:
                                    self.add_object(node)
                            except Exception as e:
                                print(f"Error placing array: {e}")
                        elif item["type"] == "gate":
                            try:
                                gate = LogicComponent.from_json(item["name"], pos=rel_pos)
                                self.add_object(gate)
                                for inp in gate.inputs:
                                    self.add_object(inp)
                                for out in gate.outputs:
                                    self.add_object(out)
                            except Exception as e:
                                print(f"Error placing component from JSON: {e}")
                        # Auto-deselect after placement to make stamping quick but clean unless Shift is held
                        keys = pygame.key.get_pressed()
                        if not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                            self.selected_placement_item = None
                        return

            # 3. Fallback to normal canvas simulation events
            handle_sim_event(self, event)

    def update(self, dt: float):
        """Updates physics/drawing offsets (only updates GUI slide animations in sim mode)."""
        # Update left panel slide animation
        left_panel_open = getattr(self, "left_panel_open", False)
        panel_speed = 8.0
        if left_panel_open:
            self.left_panel_slide_ratio = min(1.0, self.left_panel_slide_ratio + panel_speed * dt)
        else:
            self.left_panel_slide_ratio = max(0.0, self.left_panel_slide_ratio - panel_speed * dt)

        if self.mode == "sim":
            update_gui(self, dt)
        
        # Dynamically tick states of all components and inputs (reactively synced)
        super().update(dt)

    def draw(self):
        """Routes draw rendering calls to respective modes."""
        bg_color = self.get_color("background", (15, 15, 20, 255))
        self.screen.fill(bg_color[:3])
        
        if self.mode == "sim":
            # Render grid and canvas
            draw_sim(self.screen, self)
            
            # Render HUD text instructions
            self._draw_hud_instructions()
            
            # Render hover bar UI on top
            draw_gui(self.screen, self)
        elif self.mode == "builder":
            # Render builder UI
            draw_builder(self.screen, self)
        elif self.mode == "manager":
            # Render manager UI
            draw_manager(self.screen, self)

        # Draw left panel on top of all modes if slide ratio is greater than zero
        if getattr(self, "left_panel_slide_ratio", 0.0) > 0.0:
            from mode.LogicGate.gui import draw_left_panel
            draw_left_panel(self.screen, self)

    def _draw_hud_instructions(self):
        """Renders simulation guide overlays."""
        screen_w = self.screen.get_width()
        try:
            font = pygame.font.Font(None, 22)
            title_font = pygame.font.Font(None, 28)
        except Exception:
            font = pygame.font.SysFont("arial", 22)
            title_font = pygame.font.SysFont("arial", 28)
            
        title_surf = title_font.render("Logic Gate Simulator & Builder", True, self.get_color("primary"))
        self.screen.blit(title_surf, ((screen_w - title_surf.get_width()) // 2, 15))

        instructions = [
            "SPACE + DRAG: Pan the simulation viewport canvas",
            "LEFT CLICK: Select Node / Toggle Input Node state / Click Connector node",
            "DRAG NODE: Click and drag any node, sub-node, or connector to reposition",
            "CTRL + CLICK: Draw wire connection from selected point to empty space/node/connector",
            "CTRL + CLICK on wire line: Splits the wire segment",
            "DELETE KEY: Remove the selected node, wire segment, or connector",
            "F2 KEY: Toggle Left Nodes panel (scrollable, click to center/edit name)",
            "Hover mouse at bottom edge to pick components | Click '+' in top-right to build new gate",
            "ESC to Exit"
        ]
        
        y_offset = 45
        for inst in instructions:
            inst_surf = font.render(inst, True, self.get_color("node_text", (240, 240, 245)))
            self.screen.blit(inst_surf, ((screen_w - inst_surf.get_width()) // 2, y_offset))
            y_offset += 20

def main():
    print("Launching Integrated Logic Gate Simulator & Builder...")
    app = LogicGateApp()
    app.run()
    print("Application closed.")

if __name__ == "__main__":
    main()
