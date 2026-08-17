import math
import pygame
from typing import Any, Tuple
from pyinteractive_objects.nodes import (
    InteractiveNode,
    GlobalInputNode,
    GlobalOutputNode,
    ConnectorNode,
    Connection,
    LogicComponent,
    ComponentSubNode
)

def to_canvas(screen_pos: Tuple[float, float], offset: Tuple[float, float]) -> Tuple[float, float]:
    """Converts screen coordinates to canvas coordinates based on the viewport offset."""
    return (screen_pos[0] - offset[0], screen_pos[1] - offset[1])

def to_screen(canvas_pos: Tuple[float, float], offset: Tuple[float, float]) -> Tuple[float, float]:
    """Converts canvas coordinates to screen coordinates based on the viewport offset."""
    return (canvas_pos[0] + offset[0], canvas_pos[1] + offset[1])

def get_or_create_connector(conn: Connection, node: InteractiveNode) -> ConnectorNode:
    """Helper to retrieve or create a connector node linked to a node inside a connection."""
    for c in conn.connector_nodes:
        if c.linked_node is node:
            return c
    c_id = f"c_{node.label}_{pygame.time.get_ticks()}_{id(node)}"
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

def connect_nodes(app: Any, node_a: InteractiveNode, node_b: InteractiveNode):
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
        c_b = ConnectorNode(identifier=f"c_{node_b.label}_{pygame.time.get_ticks()}_{id(node_b)}", linked_node=node_b)
        conn_a.add_connector_node(c_b)
        node_b.connection = conn_a
        conn_a.add_line(c_a.id, c_b.id)
    elif conn_a is None and conn_b is not None:
        c_b = get_or_create_connector(conn_b, node_b)
        c_a = ConnectorNode(identifier=f"c_{node_a.label}_{pygame.time.get_ticks()}_{id(node_a)}", linked_node=node_a)
        conn_b.add_connector_node(c_a)
        node_a.connection = conn_b
        conn_b.add_line(c_a.id, c_b.id)
    else:
        new_conn = Connection()
        c_a = ConnectorNode(identifier=f"c_{node_a.label}_{pygame.time.get_ticks()}_{id(node_a)}", linked_node=node_a)
        c_b = ConnectorNode(identifier=f"c_{node_b.label}_{pygame.time.get_ticks()}_{id(node_b)}", linked_node=node_b)
        new_conn.add_connector_node(c_a)
        new_conn.add_connector_node(c_b)
        new_conn.add_line(c_a.id, c_b.id)
        node_a.connection = new_conn
        node_b.connection = new_conn
        # Add to app connections
        app.connections.add(new_conn)

    # Re-verify and update all app connections list
    app.connections = {obj.connection for obj in app.objects if isinstance(obj, InteractiveNode) and obj.connection is not None}

def delete_selected_node(app: Any, node: InteractiveNode):
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
        conn.split_if_disconnected()
    node.connection = None
    
    # Update app connections
    app.connections = {obj.connection for obj in app.objects if isinstance(obj, InteractiveNode) and obj.connection is not None}

def delete_selected_line(app: Any, conn: Connection, line: tuple):
    """Deletes a line segment, and dissolves the connection if empty."""
    if line in conn.lines:
        conn.lines.remove(line)
    elif (line[1], line[0]) in conn.lines:
        conn.lines.remove((line[1], line[0]))
        
    conn.validate_lines()
    conn.split_if_disconnected()
    
    # Update app connections
    app.connections = {obj.connection for obj in app.objects if isinstance(obj, InteractiveNode) and obj.connection is not None}

def delete_connector_node(app: Any, conn: Connection, connector: ConnectorNode):
    """Deletes a connector node from the connection, removing all lines that use it."""
    if connector in conn.connector_nodes:
        conn.connector_nodes.remove(connector)
    if connector.linked_node is not None:
        connector.linked_node.connection = None
        
    conn.validate_lines()
    conn.split_if_disconnected()
    
    # Update app connections
    app.connections = {obj.connection for obj in app.objects if isinstance(obj, InteractiveNode) and obj.connection is not None}

def split_line_on_connection(app: Any, start_pt, conn_target: Connection, line_seg: tuple, click_pos: tuple, select_connector_fn):
    """Splits an existing connection wire line, connecting the split node to both endpoints and the start point."""
    mx, my = click_pos
    
    # 1. Resolve connection of starting point
    conn_start = None
    if isinstance(start_pt, InteractiveNode):
        conn_start = start_pt.connection
    else: # ConnectorNode
        connections = app.connections
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
    split_id = f"split_{pygame.time.get_ticks()}_{id(start_pt)}"
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
    
    # Update app connections
    app.connections = {obj.connection for obj in app.objects if isinstance(obj, InteractiveNode) and obj.connection is not None}

def draw_grid(screen: pygame.Surface, offset: Tuple[float, float], width: int, height: int, grid_size: int = 50):
    """Draws an infinite pan-aware background grid."""
    start_x = int(offset[0] % grid_size)
    start_y = int(offset[1] % grid_size)
    grid_color = (40, 40, 45)
    for x in range(start_x, width, grid_size):
        pygame.draw.line(screen, grid_color, (x, 0), (x, height), 1)
    for y in range(start_y, height, grid_size):
        pygame.draw.line(screen, grid_color, (0, y), (width, y), 1)

def draw_sim(screen: pygame.Surface, app: Any):
    """Draws the viewport-panned simulation canvas."""
    width, height = screen.get_size()
    draw_grid(screen, app.offset, width, height)

    ox, oy = app.offset
    
    # Temporarily offset all non-subnode coordinates
    shifted_objects = []
    for obj in app.objects:
        if not isinstance(obj, ComponentSubNode):
            obj.x += ox
            obj.y += oy
            shifted_objects.append(obj)

    shifted_connectors = []
    for conn in app.connections:
        for c in conn.connector_nodes:
            if c.linked_node is None:
                c.x += ox
                c.y += oy
                shifted_connectors.append(c)

    # Draw connection lines (bottom layer)
    for conn in app.connections:
        conn.draw(screen, app)

    # Draw connector handles
    for conn in app.connections:
        active_handle_color = app.get_color("connection_active", (0, 255, 240, 255))
        inactive_handle_color = app.get_color("connection_inactive", (80, 80, 95, 255))
        h_color = active_handle_color if conn.state else inactive_handle_color
        for c in conn.connector_nodes:
            if app.selected_start_point is c:
                pygame.draw.circle(screen, (255, 220, 0), (int(c.pos[0]), int(c.pos[1])), 9, 2)
                pygame.draw.circle(screen, (255, 220, 0), (int(c.pos[0]), int(c.pos[1])), 3)
            else:
                pygame.draw.circle(screen, h_color[:3], (int(c.pos[0]), int(c.pos[1])), 6)
                pygame.draw.circle(screen, (220, 220, 225), (int(c.pos[0]), int(c.pos[1])), 6, 1)

    # Draw nodes/components
    for obj in app.objects:
        obj.skip_connection_draw = True
        obj.draw(screen, app)
        obj.skip_connection_draw = False

    # Restore coordinate values
    for obj in shifted_objects:
        obj.x -= ox
        obj.y -= oy
    for c in shifted_connectors:
        c.x -= ox
        c.y -= oy

def handle_sim_event(app: Any, event: pygame.event.Event) -> bool:
    """Processes canvas logic events, including dragging, connecting, and panning."""
    keys = pygame.key.get_pressed()
    
    # 1. Viewport panning when Space bar is held down
    if keys[pygame.K_SPACE]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            app.is_panning = True
            app.pan_start_pos = (event.pos[0] - app.offset[0], event.pos[1] - app.offset[1])
            return True
        elif event.type == pygame.MOUSEMOTION and getattr(app, "is_panning", False):
            app.offset[0] = event.pos[0] - app.pan_start_pos[0]
            app.offset[1] = event.pos[1] - app.pan_start_pos[1]
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            app.is_panning = False
            return True
    else:
        app.is_panning = False

    # Ignore all other canvas interactions if panning is active
    if getattr(app, "is_panning", False):
        return True

    # Forward event to objects (with canvas mouse position mapped) first, so objects process drag/click states
    for obj in app.objects:
        if hasattr(obj, "handle_event") and callable(obj.handle_event):
            has_pos = hasattr(event, "pos")
            if has_pos:
                old_pos = event.pos
                event.pos = to_canvas(old_pos, app.offset)
            try:
                obj.handle_event(event)
            finally:
                if has_pos:
                    event.pos = old_pos

    # 2. Deletions
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_DELETE:
            if app.selected_node:
                delete_selected_node(app, app.selected_node)
                app.clear_selection()
            elif app.selected_connection:
                conn, line = app.selected_connection
                delete_selected_line(app, conn, line)
                app.clear_selection()
            elif app.selected_start_point and isinstance(app.selected_start_point, ConnectorNode):
                connector = app.selected_start_point
                for conn in list(app.connections):
                    if connector in conn.connector_nodes:
                        delete_connector_node(app, conn, connector)
                        break
                app.clear_selection()
            return True

    # 3. Canvas Clicks and Drags
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            # Map click coordinates to canvas offset coordinates
            mouse_pos = to_canvas(event.pos, app.offset)
            ctrl_held = (pygame.key.get_mods() & pygame.KMOD_CTRL)

            # Check connector node collisions
            clicked_connector = None
            for conn in app.connections:
                for c in conn.connector_nodes:
                    if math.hypot(mouse_pos[0] - c.pos[0], mouse_pos[1] - c.pos[1]) <= 10:
                        clicked_connector = c
                        break
                if clicked_connector:
                    break

            # Check node collisions (check reversed to prioritize top-drawn elements)
            clicked_node = None
            for obj in reversed(app.objects):
                if isinstance(obj, InteractiveNode) and obj.collidepoint(mouse_pos):
                    clicked_node = obj
                    break

            # Ctrl + Click connection workflow
            if ctrl_held and app.selected_start_point is not None:
                start_pt = app.selected_start_point

                # Check wire collision to split segment
                clicked_line_conn = None
                clicked_line_seg = None
                for conn in app.connections:
                    line = conn.get_colliding_line(mouse_pos, threshold=8.0)
                    if line is not None:
                        clicked_line_conn = conn
                        clicked_line_seg = line
                        break

                if clicked_line_conn is not None:
                    # Translate canvas pos to absolute coordinates
                    split_line_on_connection(app, start_pt, clicked_line_conn, clicked_line_seg, mouse_pos, app.select_connector)
                    return True

                if clicked_node is not None:
                    # Connect to node
                    if clicked_node is not start_pt:
                        if isinstance(start_pt, InteractiveNode):
                            connect_nodes(app, start_pt, clicked_node)
                            app.select_node(clicked_node)
                        elif isinstance(start_pt, ConnectorNode):
                            conn_a = None
                            for c in app.connections:
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
                                    c_b = ConnectorNode(identifier=f"c_{clicked_node.label}_{pygame.time.get_ticks()}_{id(clicked_node)}", linked_node=clicked_node)
                                    conn_a.add_connector_node(c_b)
                                    clicked_node.connection = conn_a
                                    conn_a.add_line(start_pt.id, c_b.id)
                                app.select_node(clicked_node)
                else:
                    # Connect to space or connector
                    if clicked_connector is not None:
                        if isinstance(start_pt, InteractiveNode):
                            if start_pt.connection is not None:
                                if start_pt.connection is not clicked_connector.linked_node:
                                    found_conn = None
                                    for conn in app.connections:
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
                                for conn in app.connections:
                                    if clicked_connector in conn.connector_nodes:
                                        found_conn = conn
                                        break
                                if found_conn:
                                    c_a = ConnectorNode(identifier=f"c_{start_pt.label}_{pygame.time.get_ticks()}_{id(start_pt)}", linked_node=start_pt)
                                    found_conn.add_connector_node(c_a)
                                    start_pt.connection = found_conn
                                    found_conn.add_line(c_a.id, clicked_connector.id)
                            app.select_node(None)
                            app.select_connector(clicked_connector)
                        elif isinstance(start_pt, ConnectorNode):
                            conn_a = None
                            for c in app.connections:
                                if start_pt in c.connector_nodes:
                                    conn_a = c
                                    break
                            if conn_a is not None:
                                found_conn = None
                                for conn in app.connections:
                                    if clicked_connector in conn.connector_nodes:
                                        found_conn = conn
                                        break
                                if found_conn:
                                    if conn_a is found_conn:
                                        conn_a.add_line(start_pt.id, clicked_connector.id)
                                    else:
                                        merge_connections(conn_a, found_conn)
                                        conn_a.add_line(start_pt.id, clicked_connector.id)
                            app.select_node(None)
                            app.select_connector(clicked_connector)
                    else:
                        # Draw wire to free space
                        free_id = f"free_{pygame.time.get_ticks()}_{id(start_pt)}"
                        c_free = ConnectorNode(identifier=free_id, x=mouse_pos[0], y=mouse_pos[1])
                        
                        if isinstance(start_pt, InteractiveNode):
                            if start_pt.connection is not None:
                                start_pt.connection.add_connector_node(c_free)
                                c_a = get_or_create_connector(start_pt.connection, start_pt)
                                start_pt.connection.add_line(c_a.id, free_id)
                                app.select_node(None)
                                app.select_connector(c_free)
                            else:
                                new_conn = Connection()
                                c_a = ConnectorNode(identifier=f"c_{start_pt.label}_{pygame.time.get_ticks()}_{id(start_pt)}", linked_node=start_pt)
                                new_conn.add_connector_node(c_a)
                                new_conn.add_connector_node(c_free)
                                new_conn.add_line(c_a.id, free_id)
                                start_pt.connection = new_conn
                                app.connections.add(new_conn)
                                app.select_node(None)
                                app.select_connector(c_free)
                        elif isinstance(start_pt, ConnectorNode):
                            conn_a = None
                            for c in app.connections:
                                if start_pt in c.connector_nodes:
                                    conn_a = c
                                    break
                            if conn_a is not None:
                                conn_a.add_connector_node(c_free)
                                conn_a.add_line(start_pt.id, free_id)
                                app.select_node(None)
                                app.select_connector(c_free)
                return True

            else:
                # Regular click selection
                if clicked_connector is not None:
                    if clicked_connector.linked_node is not None:
                        # Drag the linked node instead of moving connector independently
                        app.select_node(clicked_connector.linked_node)
                        clicked_connector.linked_node.is_dragging = True
                        clicked_connector.linked_node.drag_start_pos = mouse_pos
                        clicked_connector.linked_node.dragged_far = False
                        clicked_connector.linked_node.drag_offset_x = mouse_pos[0] - clicked_connector.linked_node.x
                        clicked_connector.linked_node.drag_offset_y = mouse_pos[1] - clicked_connector.linked_node.y
                    else:
                        app.select_connector(clicked_connector)
                        app.is_dragging_connector = True
                        app.dragged_connector = clicked_connector
                        app.drag_offset_x = mouse_pos[0] - clicked_connector.x
                        app.drag_offset_y = mouse_pos[1] - clicked_connector.y
                elif clicked_node is not None:
                    app.select_node(clicked_node)
                else:
                    # Check wire segment selection
                    clicked_conn = None
                    clicked_line = None
                    for conn in app.connections:
                        line = conn.get_colliding_line(mouse_pos, threshold=8.0)
                        if line is not None:
                            clicked_conn = conn
                            clicked_line = line
                            break
                            
                    if clicked_conn is not None:
                        app.select_connection(clicked_conn, clicked_line)
                    else:
                        app.clear_selection()
                return True

    elif event.type == pygame.MOUSEMOTION:
        if app.is_dragging_connector and app.dragged_connector:
            mouse_pos = to_canvas(event.pos, app.offset)
            c = app.dragged_connector
            # Drag free connector node (linked nodes are handled by InteractiveNode itself)
            c.x = mouse_pos[0] - app.drag_offset_x
            c.y = mouse_pos[1] - app.drag_offset_y
            return True

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            app.is_dragging_connector = False
            app.dragged_connector = None

    return False
