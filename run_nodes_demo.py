import sys
import math
import pygame
from pyinteractive import PygameApp
from pyinteractive_objects.nodes import (
    InteractiveNode,
    GlobalInputNode,
    GlobalOutputNode,
    ConnectorNode,
    Connection,
    LogicComponent,
    ComponentSubNode
)

def get_or_create_connector(conn: Connection, node: InteractiveNode) -> ConnectorNode:
    """Helper to retrieve or create a connector node linked to a node inside a connection."""
    for c in conn.connector_nodes:
        if c.linked_node is node:
            return c
    c_id = f"c_{node.label}_{pygame.time.get_ticks()}"
    new_connector = ConnectorNode(identifier=c_id, linked_node=node)
    conn.add_connector_node(new_connector)
    return new_connector

def merge_connections_with_map(conn_dest: Connection, conn_src: Connection) -> dict:
    """Merges all connector nodes and lines from src into dest, remapping IDs and returning the mapping."""
    if conn_dest is conn_src:
        return {}
        
    id_map = {}
    for c in conn_src.connector_nodes:
        if c.linked_node is not None:
            existing = next((d for d in conn_dest.connector_nodes if d.linked_node is c.linked_node), None)
            if existing:
                id_map[c.id] = existing.id
                continue
        conn_dest.add_connector_node(c)
        id_map[c.id] = c.id
        
    for id1, id2 in conn_src.lines:
        new_id1 = id_map.get(id1, id1)
        new_id2 = id_map.get(id2, id2)
        if new_id1 != new_id2:
            conn_dest.add_line(new_id1, new_id2)
            
    for c in conn_src.connector_nodes:
        if c.linked_node is not None:
            c.linked_node.connection = conn_dest
            
    return id_map

def merge_connections(conn_dest: Connection, conn_src: Connection):
    merge_connections_with_map(conn_dest, conn_src)

def connect_nodes(app: PygameApp, node_a: InteractiveNode, node_b: InteractiveNode):
    """Helper to connect node_a and node_b, merging connections if necessary."""
    conn_a = node_a.connection
    conn_b = node_b.connection

    if conn_a is not None and conn_b is not None:
        if conn_a is conn_b:
            c_a = get_or_create_connector(conn_a, node_a)
            c_b = get_or_create_connector(conn_a, node_b)
            conn_a.add_line(c_a.id, c_b.id)
        else:
            merge_connections(conn_a, conn_b)
            c_a = get_or_create_connector(conn_a, node_a)
            c_b = get_or_create_connector(conn_a, node_b)
            conn_a.add_line(c_a.id, c_b.id)
    elif conn_a is not None and conn_b is None:
        c_a = get_or_create_connector(conn_a, node_a)
        c_b = ConnectorNode(identifier=f"c_{node_b.label}_{pygame.time.get_ticks()}", linked_node=node_b)
        conn_a.add_connector_node(c_b)
        node_b.connection = conn_a
        conn_a.add_line(c_a.id, c_b.id)
    elif conn_a is None and conn_b is not None:
        c_b = get_or_create_connector(conn_b, node_b)
        c_a = ConnectorNode(identifier=f"c_{node_a.label}_{pygame.time.get_ticks()}", linked_node=node_a)
        conn_b.add_connector_node(c_a)
        node_a.connection = conn_b
        conn_b.add_line(c_a.id, c_b.id)
    else:
        new_conn = Connection()
        c_a = ConnectorNode(identifier=f"c_{node_a.label}_{pygame.time.get_ticks()}", linked_node=node_a)
        c_b = ConnectorNode(identifier=f"c_{node_b.label}_{pygame.time.get_ticks()}", linked_node=node_b)
        new_conn.add_connector_node(c_a)
        new_conn.add_connector_node(c_b)
        new_conn.add_line(c_a.id, c_b.id)
        node_a.connection = new_conn
        node_b.connection = new_conn

def delete_selected_node(app: PygameApp, node: InteractiveNode):
    """Deletes a node from the app, cleans up its connection references and dissolves it if empty."""
    if node not in app.objects:
        return
        
    if isinstance(node, LogicComponent):
        app.remove_object(node)
        for inp in list(node.inputs):
            delete_selected_node(app, inp)
        for out in list(node.outputs):
            delete_selected_node(app, out)
        return
    elif isinstance(node, ComponentSubNode):
        parent = node.parent
        if parent in app.objects:
            delete_selected_node(app, parent)

    app.remove_object(node)
    conn = node.connection
    if conn is not None:
        # Remove connector nodes linked to this node
        conn.connector_nodes = [c for c in conn.connector_nodes if c.linked_node is not node]
        conn.validate_lines()
        
        # If no lines remain, dissolve connection
        if not conn.lines:
            for c in conn.connector_nodes:
                if c.linked_node is not None:
                    c.linked_node.connection = None
    node.connection = None

def delete_selected_line(app: PygameApp, conn: Connection, line: tuple):
    """Deletes a line segment, and dissolves the connection if empty."""
    if line in conn.lines:
        conn.lines.remove(line)
    elif (line[1], line[0]) in conn.lines:
        conn.lines.remove((line[1], line[0]))
        
    conn.validate_lines()
    if not conn.lines:
        # Dissolve connection
        for c in conn.connector_nodes:
            if c.linked_node is not None:
                c.linked_node.connection = None

def delete_connector_node(app: PygameApp, conn: Connection, connector: ConnectorNode):
    """Deletes a connector node from the connection, removing all lines that use it."""
    if connector in conn.connector_nodes:
        conn.connector_nodes.remove(connector)
    if connector.linked_node is not None:
        connector.linked_node.connection = None
        
    conn.validate_lines()
    if not conn.lines:
        # Dissolve connection
        for c in conn.connector_nodes:
            if c.linked_node is not None:
                c.linked_node.connection = None

def split_line_on_connection(app: PygameApp, start_pt, conn_target: Connection, line_seg: tuple, click_pos: tuple, select_connector_fn):
    """Splits an existing connection wire line, connecting the split node to both endpoints and the start point."""
    mx, my = click_pos
    
    # 1. Resolve connection of starting point
    conn_start = None
    if isinstance(start_pt, InteractiveNode):
        conn_start = start_pt.connection
    else: # ConnectorNode
        connections = set()
        for obj in app.objects:
            if isinstance(obj, InteractiveNode) and obj.connection is not None:
                connections.add(obj.connection)
        for c in connections:
            if start_pt in c.connector_nodes:
                conn_start = c
                break
                
    # 2. Merge if they are different
    id1, id2 = line_seg
    active_conn = conn_target
    if conn_start is not None and conn_start is not conn_target:
        id_map = merge_connections_with_map(conn_start, conn_target)
        id1 = id_map.get(id1, id1)
        id2 = id_map.get(id2, id2)
        active_conn = conn_start
    elif conn_start is None:
        active_conn = conn_target
        if isinstance(start_pt, InteractiveNode):
            c_start = get_or_create_connector(conn_target, start_pt)
            start_pt.connection = conn_target
            
    # Resolve connector of start_pt in active_conn
    if isinstance(start_pt, InteractiveNode):
        c_start = get_or_create_connector(active_conn, start_pt)
    else:
        c_start = start_pt
        
    # Create split connector node
    split_id = f"split_{pygame.time.get_ticks()}"
    c_split = ConnectorNode(identifier=split_id, x=mx, y=my)
    active_conn.add_connector_node(c_split)
    
    # Remove original line
    if (id1, id2) in active_conn.lines:
        active_conn.lines.remove((id1, id2))
    elif (id2, id1) in active_conn.lines:
        active_conn.lines.remove((id2, id1))
        
    # Add three new lines
    active_conn.add_line(id1, split_id)
    active_conn.add_line(id2, split_id)
    active_conn.add_line(c_start.id, split_id)
    
    active_conn.validate_lines()
    select_connector_fn(c_split)


def main():
    print("Initializing Pygame App for Nodes & Connections Demo...")
    
    try:
        app = PygameApp(config_path="config.json", title="Interactive Nodes & State Propagation Demo")
    except Exception as e:
        print(f"Error loading configuration or initializing app: {e}")
        sys.exit(1)

    # Initialize app selection and dragging attributes
    app.selected_node = None
    app.selected_connection = None  # Tuple: (connection, line)
    app.selected_start_point = None # InteractiveNode or ConnectorNode
    
    app.is_dragging_connector = False
    app.dragged_connector = None

    def select_node(node: InteractiveNode):
        if app.selected_node:
            app.selected_node.selected = False
        if app.selected_connection and app.selected_connection[0] is not None:
            conn, line = app.selected_connection
            conn.selected_line = None
            
        app.selected_connection = None
        app.selected_node = node
        app.selected_start_point = node
        if node:
            node.selected = True

    def select_connection(conn: Connection, line: tuple):
        if app.selected_node:
            app.selected_node.selected = False
            app.selected_node = None
        if app.selected_connection and app.selected_connection[0] is not None:
            prev_conn, prev_line = app.selected_connection
            prev_conn.selected_line = None
            
        app.selected_connection = (conn, line) if conn is not None else None
        app.selected_start_point = None
        if conn:
            conn.selected_line = line

    def select_connector(connector: ConnectorNode):
        if app.selected_node:
            app.selected_node.selected = False
            app.selected_node = None
        if app.selected_connection and app.selected_connection[0] is not None:
            prev_conn, prev_line = app.selected_connection
            prev_conn.selected_line = None
            app.selected_connection = None
            
        app.selected_start_point = connector

    def clear_selection():
        select_node(None)
        select_connection(None, None)
        app.selected_start_point = None

    # Set up custom theme colors for selections
    if "connection_active" not in app.config.colortheme:
        app.config.colortheme["connection_active"] = (0, 255, 240, 255)
    if "connection_inactive" not in app.config.colortheme:
        app.config.colortheme["connection_inactive"] = (80, 80, 95, 255)
    if "connection_selected" not in app.config.colortheme:
        app.config.colortheme["connection_selected"] = (255, 220, 0, 255)
    if "node_active_fill" not in app.config.colortheme:
        app.config.colortheme["node_active_fill"] = (46, 204, 113, 255)
    if "node_inactive_fill" not in app.config.colortheme:
        app.config.colortheme["node_inactive_fill"] = (60, 60, 65, 255)
    if "node_active_border" not in app.config.colortheme:
        app.config.colortheme["node_active_border"] = (50, 255, 120, 255)
    if "node_inactive_border" not in app.config.colortheme:
        app.config.colortheme["node_inactive_border"] = (140, 140, 150, 255)
    if "node_selected_border" not in app.config.colortheme:
        app.config.colortheme["node_selected_border"] = (255, 220, 0, 255)
    if "node_active_glow" not in app.config.colortheme:
        app.config.colortheme["node_active_glow"] = (46, 204, 113, 40)
    if "node_text" not in app.config.colortheme:
        app.config.colortheme["node_text"] = (240, 240, 245, 255)
    if "logic_component_fill" not in app.config.colortheme:
        app.config.colortheme["logic_component_fill"] = (142, 68, 173, 255)

    screen_w = app.screen.get_width()
    screen_h = app.screen.get_height()

    # Create Initial Nodes (Inputs round circles, Outputs square rectangles)
    inp1 = GlobalInputNode(pos=(screen_w * 0.2, screen_h * 0.3), size=25.0)
    inp2 = GlobalInputNode(pos=(screen_w * 0.2, screen_h * 0.5), size=25.0)
    inp3 = GlobalInputNode(pos=(screen_w * 0.2, screen_h * 0.7), size=25.0)

    out1 = GlobalOutputNode(pos=(screen_w * 0.7, screen_h * 0.35), size=50.0)
    out2 = GlobalOutputNode(pos=(screen_w * 0.7, screen_h * 0.65), size=50.0)

    # Standard Standalone Node
    node_center = InteractiveNode(pos=(screen_w * 0.45, screen_h * 0.8), shape="circle", size=25.0, label_prefix="N", state=False)

    # Load NOT gate logic component from not_gate.json
    try:
        not_gate = LogicComponent.from_json("not_gate.json", pos=(screen_w * 0.45, screen_h * 0.45))
    except Exception as e:
        print(f"Error loading not_gate.json: {e}")
        not_gate = LogicComponent(
            name="NOT Gate",
            size=(80, 50),
            inputs_def=[{"name": "I", "rel_x": 0, "rel_y": 25, "color": [231, 76, 60, 255]}],
            outputs_def=[{"name": "O", "rel_x": 80, "rel_y": 25, "color": [46, 204, 113, 255]}],
            logic_table={"0": "1", "1": "0"},
            pos=(screen_w * 0.45, screen_h * 0.45),
            color=(142, 68, 173, 255)
        )

    # Initial Connection 1 (from inp1 & inp2 to out1)
    c1_1 = ConnectorNode(identifier="c1_inp1", linked_node=inp1)
    c1_2 = ConnectorNode(identifier="c1_inp2", linked_node=inp2)
    c1_3 = ConnectorNode(identifier="c1_out1", linked_node=out1)
    
    conn1 = Connection(connector_nodes=[c1_1, c1_2, c1_3])
    conn1.add_line("c1_inp1", "c1_out1")
    conn1.add_line("c1_inp2", "c1_out1")
    out1.connection = conn1
    inp1.connection = conn1
    inp2.connection = conn1

    # Initial Connection 2 (from inp3 to out2)
    c2_2 = ConnectorNode(identifier="c2_inp3", linked_node=inp3)
    c2_3 = ConnectorNode(identifier="c2_out2", linked_node=out2)
    
    conn2 = Connection(connector_nodes=[c2_2, c2_3])
    conn2.add_line("c2_inp3", "c2_out2")
    out2.connection = conn2
    inp3.connection = conn2

    # Add nodes to app
    app.add_object(inp1)
    app.add_object(inp2)
    app.add_object(inp3)
    app.add_object(out1)
    app.add_object(out2)
    app.add_object(node_center)
    app.add_object(not_gate)
    for inp in not_gate.inputs:
        app.add_object(inp)
    for out in not_gate.outputs:
        app.add_object(out)

    # Event Handler
    original_handle_event = app.handle_event
    def custom_handle_event(event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                app.is_running = False
            elif event.key == pygame.K_DELETE:
                if app.selected_node:
                    delete_selected_node(app, app.selected_node)
                    clear_selection()
                elif app.selected_connection:
                    conn, line = app.selected_connection
                    delete_selected_line(app, conn, line)
                    clear_selection()
                elif app.selected_start_point and isinstance(app.selected_start_point, ConnectorNode):
                    # Delete connector node and clean up
                    connector = app.selected_start_point
                    # Find connection
                    connections = set()
                    for obj in app.objects:
                        if isinstance(obj, InteractiveNode) and obj.connection is not None:
                            connections.add(obj.connection)
                    for conn in connections:
                        if connector in conn.connector_nodes:
                            delete_connector_node(app, conn, connector)
                            break
                    clear_selection()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                ctrl_held = (pygame.key.get_mods() & pygame.KMOD_CTRL)

                # Collect all connections
                connections = set()
                for obj in app.objects:
                    if isinstance(obj, InteractiveNode) and obj.connection is not None:
                        connections.add(obj.connection)

                # Check if click is on any connector node (within 10 pixels)
                clicked_connector = None
                for conn in connections:
                    for c in conn.connector_nodes:
                        if math.hypot(mouse_pos[0] - c.pos[0], mouse_pos[1] - c.pos[1]) <= 10:
                            clicked_connector = c
                            break
                    if clicked_connector:
                        break

                # Check if click is on any node (check in reverse to prioritize sub-nodes drawn on top)
                clicked_node = None
                for obj in reversed(app.objects):
                    if isinstance(obj, InteractiveNode) and obj.collidepoint(mouse_pos):
                        clicked_node = obj
                        break

                if ctrl_held and app.selected_start_point is not None:
                    start_pt = app.selected_start_point

                    # First check if click is on an existing connection line segment to split it
                    clicked_line_conn = None
                    clicked_line_seg = None
                    for conn in connections:
                        line = conn.get_colliding_line(mouse_pos, threshold=8.0)
                        if line is not None:
                            clicked_line_conn = conn
                            clicked_line_seg = line
                            break

                    if clicked_line_conn is not None:
                        # Splitting wire connection!
                        split_line_on_connection(app, start_pt, clicked_line_conn, clicked_line_seg, mouse_pos, select_connector)
                        return

                    if clicked_node is not None:
                        # Case A: Connect to another node
                        if clicked_node is not start_pt:
                            if isinstance(start_pt, InteractiveNode):
                                connect_nodes(app, start_pt, clicked_node)
                                select_node(clicked_node)
                            elif isinstance(start_pt, ConnectorNode):
                                # Find connection of start_pt
                                conn_a = None
                                for c in connections:
                                    if start_pt in c.connector_nodes:
                                        conn_a = c
                                        break
                                if conn_a is not None:
                                    conn_b = clicked_node.connection
                                    if conn_b is not None:
                                        if conn_b is conn_a:
                                            c_b = get_or_create_connector(conn_a, clicked_node)
                                            conn_a.add_line(start_pt.id, c_b.id)
                                        else:
                                            merge_connections(conn_a, conn_b)
                                            c_b = get_or_create_connector(conn_a, clicked_node)
                                            conn_a.add_line(start_pt.id, c_b.id)
                                    else:
                                        c_b = ConnectorNode(identifier=f"c_{clicked_node.label}_{pygame.time.get_ticks()}", linked_node=clicked_node)
                                        conn_a.add_connector_node(c_b)
                                        clicked_node.connection = conn_a
                                        conn_a.add_line(start_pt.id, c_b.id)
                                    select_node(clicked_node)
                    else:
                        # Case B: Connect to empty space or existing connector
                        if clicked_connector is not None:
                            # Connect start_pt to existing connector
                            if isinstance(start_pt, InteractiveNode):
                                if start_pt.connection is not None:
                                    if start_pt.connection is clicked_connector:
                                        pass # self-connection not allowed
                                    elif start_pt.connection is clicked_connector.linked_node:
                                        pass
                                    else:
                                        # Find which connection clicked_connector belongs to
                                        found_conn = None
                                        for conn in connections:
                                            if clicked_connector in conn.connector_nodes:
                                                found_conn = conn
                                                break
                                        if found_conn:
                                            if start_pt.connection is found_conn:
                                                c_a = get_or_create_connector(start_pt.connection, start_pt)
                                                start_pt.connection.add_line(c_a.id, clicked_connector.id)
                                            else:
                                                merge_connections(start_pt.connection, found_conn)
                                                c_a = get_or_create_connector(start_pt.connection, start_pt)
                                                start_pt.connection.add_line(c_a.id, clicked_connector.id)
                                else:
                                    found_conn = None
                                    for conn in connections:
                                        if clicked_connector in conn.connector_nodes:
                                            found_conn = conn
                                            break
                                    if found_conn:
                                        c_a = ConnectorNode(identifier=f"c_{start_pt.label}_{pygame.time.get_ticks()}", linked_node=start_pt)
                                        found_conn.add_connector_node(c_a)
                                        start_pt.connection = found_conn
                                        found_conn.add_line(c_a.id, clicked_connector.id)
                                select_node(None)
                                select_connector(clicked_connector)
                            elif isinstance(start_pt, ConnectorNode):
                                conn_a = None
                                for c in connections:
                                    if start_pt in c.connector_nodes:
                                        conn_a = c
                                        break
                                if conn_a is not None:
                                    found_conn = None
                                    for conn in connections:
                                        if clicked_connector in conn.connector_nodes:
                                            found_conn = conn
                                            break
                                    if found_conn:
                                        if conn_a is found_conn:
                                            conn_a.add_line(start_pt.id, clicked_connector.id)
                                        else:
                                            merge_connections(conn_a, found_conn)
                                            conn_a.add_line(start_pt.id, clicked_connector.id)
                                select_node(None)
                                select_connector(clicked_connector)
                        else:
                            # Create new free connector node
                            free_id = f"free_{pygame.time.get_ticks()}"
                            c_free = ConnectorNode(identifier=free_id, x=mouse_pos[0], y=mouse_pos[1])
                            
                            if isinstance(start_pt, InteractiveNode):
                                if start_pt.connection is not None:
                                    start_pt.connection.add_connector_node(c_free)
                                    c_a = get_or_create_connector(start_pt.connection, start_pt)
                                    start_pt.connection.add_line(c_a.id, free_id)
                                    select_node(None)
                                    select_connector(c_free)
                                else:
                                    new_conn = Connection()
                                    c_a = ConnectorNode(identifier=f"c_{start_pt.label}_{pygame.time.get_ticks()}", linked_node=start_pt)
                                    new_conn.add_connector_node(c_a)
                                    new_conn.add_connector_node(c_free)
                                    new_conn.add_line(c_a.id, free_id)
                                    start_pt.connection = new_conn
                                    select_node(None)
                                    select_connector(c_free)
                            elif isinstance(start_pt, ConnectorNode):
                                conn_a = None
                                for c in connections:
                                    if start_pt in c.connector_nodes:
                                        conn_a = c
                                        break
                                if conn_a is not None:
                                    conn_a.add_connector_node(c_free)
                                    conn_a.add_line(start_pt.id, free_id)
                                    select_node(None)
                                    select_connector(c_free)
                    return

                else:
                    # Regular Left Click: Prioritize connector node selection
                    if clicked_connector is not None:
                        select_connector(clicked_connector)
                        app.is_dragging_connector = True
                        app.dragged_connector = clicked_connector
                    elif clicked_node is not None:
                        select_node(clicked_node)
                    else:
                        clicked_conn = None
                        clicked_line = None
                        for conn in connections:
                            line = conn.get_colliding_line(mouse_pos, threshold=8.0)
                            if line is not None:
                                clicked_conn = conn
                                clicked_line = line
                                break
                                
                        if clicked_conn is not None:
                            select_connection(clicked_conn, clicked_line)
                        else:
                            clear_selection()

        elif event.type == pygame.MOUSEMOTION:
            if app.is_dragging_connector and app.dragged_connector:
                mouse_pos = event.pos
                c = app.dragged_connector
                if c.linked_node is not None:
                    node = c.linked_node
                    node.x = mouse_pos[0] - node.width / 2
                    node.y = mouse_pos[1] - node.height / 2
                else:
                    c.x = mouse_pos[0]
                    c.y = mouse_pos[1]

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                app.is_dragging_connector = False
                app.dragged_connector = None

        # Forward events to all game objects
        for obj in app.objects:
            if hasattr(obj, "handle_event") and callable(obj.handle_event):
                obj.handle_event(event)
                
        original_handle_event(event)
    app.handle_event = custom_handle_event

    # Draw Loop
    original_draw = app.draw
    def custom_draw():
        # Get all unique active connections
        connections = set()
        for obj in app.objects:
            if isinstance(obj, InteractiveNode) and obj.connection is not None:
                connections.add(obj.connection)

        # 1. Draw connection lines first (bottom layer)
        for conn in connections:
            conn.draw(app.screen, app)
                
        # 2. Draw HUD Overlay
        try:
            title_font = pygame.font.Font(None, 40)
            text_font = pygame.font.Font(None, 24)
        except Exception:
            title_font = pygame.font.SysFont("arial", 40)
            text_font = pygame.font.SysFont("arial", 24)
            
        title_surf = title_font.render("Interactive Nodes & Connections Playground", True, app.get_color("primary"))
        app.screen.blit(title_surf, ((screen_w - title_surf.get_width()) // 2, 25))
        
        instructions = [
            "LEFT CLICK: Select Node / Select Wire / Click Connector Node / Toggle Input State",
            "DRAG: Drag any selected node or connector node freely",
            "CTRL + CLICK: Draw wire from selected point to empty space, node, or connector",
            "CTRL + CLICK on wire line: Splits the wire, connecting both endpoints and start point",
            "DELETE KEY: Remove the selected node, wire segment, or connector node",
            "Inputs are consistent ROUND circles; Outputs are consistent SQUARE rectangles",
            "Press ESC to exit"
        ]
        
        y_offset = 70
        for inst in instructions:
            inst_surf = text_font.render(inst, True, app.get_color("secondary"))
            app.screen.blit(inst_surf, ((screen_w - inst_surf.get_width()) // 2, y_offset))
            y_offset += 22

        # 3. Draw connector node handles
        for conn in connections:
            active_handle_color = app.get_color("connection_active", (0, 255, 240, 255))
            inactive_handle_color = app.get_color("connection_inactive", (80, 80, 95, 255))
            h_color = active_handle_color if conn.state else inactive_handle_color
            for c in conn.connector_nodes:
                if app.selected_start_point is c:
                    pygame.draw.circle(app.screen, (255, 220, 0), (int(c.pos[0]), int(c.pos[1])), 9, 2)
                    pygame.draw.circle(app.screen, (255, 220, 0), (int(c.pos[0]), int(c.pos[1])), 3)
                else:
                    pygame.draw.circle(app.screen, h_color[:3], (int(c.pos[0]), int(c.pos[1])), 6)
                    pygame.draw.circle(app.screen, (220, 220, 225), (int(c.pos[0]), int(c.pos[1])), 6, 1)

        # 4. Temporarily clear node connections so they don't draw connection wires again on top of themselves
        saved_conns = {}
        for obj in app.objects:
            if isinstance(obj, InteractiveNode) and obj.connection is not None:
                saved_conns[obj] = obj.connection
                obj.connection = None
                
        # 5. Render node bodies (including selection outlines)
        original_draw()
        
        # 6. Restore connection references
        for node, conn in saved_conns.items():
            node.connection = conn

    app.draw = custom_draw

    # Run
    app.run()
    print("App closed successfully.")

if __name__ == "__main__":
    main()
