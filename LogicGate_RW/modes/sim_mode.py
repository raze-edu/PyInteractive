import math
from typing import Any, Tuple, Optional, List
import pygame

from LogicGate_RW.core.ui_node import (
    UINode,
    UIGlobalInputNode,
    UIGlobalOutputNode,
    UIComponentPin,
    UIConnectorPoint
)
from LogicGate_RW.core.ui_connection import UIConnection
from LogicGate_RW.core.ui_component import UILogicComponent
from LogicGate_RW.core.ui_arrays import UIArrayNode, UINodeArray
from LogicGate_RW.ui.style import shared_style

def to_canvas(screen_pos: Tuple[float, float], offset: Tuple[float, float], zoom_scale: float = 1.0) -> Tuple[float, float]:
    """Converts screen coordinates to canvas coordinates based on viewport offset and zoom scale."""
    return ((screen_pos[0] - offset[0]) / zoom_scale, (screen_pos[1] - offset[1]) / zoom_scale)

def to_screen(canvas_pos: Tuple[float, float], offset: Tuple[float, float], zoom_scale: float = 1.0) -> Tuple[float, float]:
    """Converts canvas coordinates to screen coordinates based on viewport offset and zoom scale."""
    return (canvas_pos[0] * zoom_scale + offset[0], canvas_pos[1] * zoom_scale + offset[1])

def get_or_create_connector(conn: UIConnection, node: UINode) -> UIConnectorPoint:
    """Retrieves existing or creates new connector linked to the node inside the connection."""
    for c in conn.connector_nodes:
        if c.linked_node is node:
            return c
    c_id = f"c_{node.label}_{pygame.time.get_ticks()}_{id(node)}"
    new_connector = UIConnectorPoint(identifier=c_id, linked_node=node)
    conn.add_connector_node(new_connector)
    return new_connector

def merge_connections_with_map(conn_dest: UIConnection, conn_src: UIConnection) -> dict:
    """Merges all connector nodes and lines from src into dest, remapping IDs."""
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
        nid1 = id_map.get(id1, id1)
        nid2 = id_map.get(id2, id2)
        if nid1 != nid2:
            conn_dest.add_line(nid1, nid2)

    for c in conn_src.connector_nodes:
        if c.linked_node is not None:
            c.linked_node.connection = conn_dest

    return id_map

def merge_connections(conn_dest: UIConnection, conn_src: UIConnection):
    merge_connections_with_map(conn_dest, conn_src)

def connect_nodes(app: Any, node_a: UINode, node_b: UINode):
    """Connects node_a and node_b, merging connections if necessary."""
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
            if conn_b in app.connections:
                app.connections.remove(conn_b)
    elif conn_a is not None and conn_b is None:
        c_a = get_or_create_connector(conn_a, node_a)
        c_b = UIConnectorPoint(identifier=f"c_{node_b.label}_{pygame.time.get_ticks()}_{id(node_b)}", linked_node=node_b)
        conn_a.add_connector_node(c_b)
        node_b.connection = conn_a
        conn_a.add_line(c_a.id, c_b.id)
    elif conn_a is None and conn_b is not None:
        c_b = get_or_create_connector(conn_b, node_b)
        c_a = UIConnectorPoint(identifier=f"c_{node_a.label}_{pygame.time.get_ticks()}_{id(node_a)}", linked_node=node_a)
        conn_b.add_connector_node(c_a)
        node_a.connection = conn_b
        conn_b.add_line(c_a.id, c_b.id)
    else:
        new_conn = UIConnection()
        c_a = UIConnectorPoint(identifier=f"c_{node_a.label}_{pygame.time.get_ticks()}_{id(node_a)}", linked_node=node_a)
        c_b = UIConnectorPoint(identifier=f"c_{node_b.label}_{pygame.time.get_ticks()}_{id(node_b)}", linked_node=node_b)
        new_conn.add_connector_node(c_a)
        new_conn.add_connector_node(c_b)
        new_conn.add_line(c_a.id, c_b.id)
        node_a.connection = new_conn
        node_b.connection = new_conn
        app.connections.add(new_conn)

def split_line_on_connection(app: Any, start_pt: Any, conn_target: UIConnection, line_seg: tuple, click_pos: tuple, select_connector_fn):
    """Splits an existing wire segment, inserting a joint waypoint and connecting start_pt."""
    mx, my = click_pos
    screen_w, screen_h = app.screen.get_size()

    # 1. Resolve connection of starting point
    conn_start = None
    if isinstance(start_pt, UINode):
        conn_start = start_pt.connection
    elif isinstance(start_pt, UIConnectorPoint):
        for c in app.connections:
            if start_pt in c.connector_nodes:
                conn_start = c
                break

    # 2. Merge if different connections
    id1, id2 = line_seg
    active_conn = conn_target
    if conn_start is not None and conn_start is not conn_target:
        id_map = merge_connections_with_map(conn_start, conn_target)
        id1 = id_map.get(id1, id1)
        id2 = id_map.get(id2, id2)
        if conn_target in app.connections:
            app.connections.remove(conn_target)
        active_conn = conn_start
    elif conn_start is None:
        active_conn = conn_target
        if isinstance(start_pt, UINode):
            c_start = get_or_create_connector(conn_target, start_pt)
            start_pt.connection = conn_target

    if isinstance(start_pt, UINode):
        c_start = get_or_create_connector(active_conn, start_pt)
    else:
        c_start = start_pt

    split_id = f"split_{pygame.time.get_ticks()}_{id(start_pt)}"
    c_split = UIConnectorPoint(identifier=split_id, x=mx / screen_w, y=my / screen_h)
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

def draw_grid(screen: pygame.Surface, app: Any):
    screen_w, screen_h = screen.get_size()
    ox, oy = app.offset
    zoom = app.zoom_scale
    grid_size = 40.0 * zoom

    start_x = ox % grid_size
    start_y = oy % grid_size
    grid_color = (30, 30, 38)

    x = start_x
    while x < screen_w:
        pygame.draw.line(screen, grid_color, (x, 0), (x, screen_h), 1)
        x += grid_size

    y = start_y
    while y < screen_h:
        pygame.draw.line(screen, grid_color, (0, y), (screen_w, y), 1)
        y += grid_size

def draw_sim(screen: pygame.Surface, app: Any):
    draw_grid(screen, app)

    # Draw wires
    for conn in list(app.connections):
        conn.draw(screen, app)

    # Draw nodes, components, arrays
    for obj in app.objects:
        obj.draw(screen, app)

    # Draw component pin labels on top
    for obj in app.objects:
        if isinstance(obj, UILogicComponent):
            obj.draw_labels(screen, app)

    # In-progress wire dragging preview
    if app.selected_start_point is not None:
        mouse_pos = pygame.mouse.get_pos()
        screen_w, screen_h = screen.get_size()
        ox, oy = app.offset
        zoom = app.zoom_scale

        if isinstance(app.selected_start_point, UINode):
            sp = app.selected_start_point.center
        else:
            sp = app.selected_start_point.pos

        sx = sp[0] * screen_w * zoom + ox
        sy = sp[1] * screen_h * zoom + oy
        pygame.draw.line(screen, (255, 220, 0), (sx, sy), mouse_pos, 2)

def handle_sim_event(app: Any, event: pygame.event.Event):
    screen_w, screen_h = app.screen.get_size()
    canvas_size = (screen_w, screen_h)
    zoom = getattr(app, "zoom_scale", 1.0)
    keys = pygame.key.get_pressed()

<<<<<<< HEAD
    # 0. Handle text typing when editing a node name
    if getattr(app, "editing_node", None) is not None and event.type == pygame.KEYDOWN:
        from LogicGate_RW.ui.left_panel import is_name_valid_and_unique
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            val_to_commit = getattr(app, "editing_name", "").strip()
            if is_name_valid_and_unique(app, app.editing_node, val_to_commit):
                app.editing_node.custom_name = val_to_commit
                app.editing_node = None
            return True
        elif event.key == pygame.K_ESCAPE:
            app.editing_node = None
            return True
        elif event.key == pygame.K_BACKSPACE:
            app.editing_name = getattr(app, "editing_name", "")[:-1]
            return True
        elif event.unicode and event.unicode.isprintable() and len(getattr(app, "editing_name", "")) < 18:
            if event.unicode.isalnum() or event.unicode == "_":
                app.editing_name = getattr(app, "editing_name", "") + event.unicode
            return True
        return True

=======
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d
    # 1. Right Click deselects everything
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        app.clear_selection()
        app.selected_placement_item = None
        app.selected_start_point = None
        app.is_dragging_connector = False
        app.dragged_connector = None
        if hasattr(app, "editing_array_value_node"):
            app.editing_array_value_node = None
<<<<<<< HEAD
        if hasattr(app, "editing_node"):
            app.editing_node = None
=======
>>>>>>> 6971f0f705df3300d6dac6510d05749867e5d60d
        return True

    # 2. Viewport panning with Space + Mouse Drag
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and keys[pygame.K_SPACE]:
        app.is_panning = True
        app.pan_start_pos = event.pos
        return True

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        if app.is_panning:
            app.is_panning = False
            return True
        if getattr(app, "is_dragging_connector", False):
            app.is_dragging_connector = False
            app.dragged_connector = None

    elif event.type == pygame.MOUSEMOTION:
        if app.is_panning:
            dx = event.pos[0] - app.pan_start_pos[0]
            dy = event.pos[1] - app.pan_start_pos[1]
            app.offset[0] += dx
            app.offset[1] += dy
            app.pan_start_pos = event.pos
            return True

        if getattr(app, "is_dragging_connector", False) and getattr(app, "dragged_connector", None):
            mouse_pos = to_canvas(event.pos, app.offset, zoom)
            c = app.dragged_connector
            c.x = (mouse_pos[0] - app.drag_offset_x) / screen_w
            c.y = (mouse_pos[1] - app.drag_offset_y) / screen_h
            return True

    # 3. Forward event to all canvas objects with event.pos mapped to canvas coordinates
    has_pos = hasattr(event, "pos")
    if has_pos:
        orig_pos = event.pos
        event.pos = to_canvas(orig_pos, app.offset, zoom)
    try:
        for obj in app.objects:
            if hasattr(obj, "handle_event") and callable(obj.handle_event):
                obj.handle_event(event, canvas_size)
    finally:
        if has_pos:
            event.pos = orig_pos

    # 4. Deletions on Delete / Backspace
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
        if app.selected_node:
            obj = app.selected_node
            if isinstance(obj, UILogicComponent):
                app.objects.remove(obj)
                for p in list(obj.inputs + obj.outputs):
                    if p.connection:
                        p.connection.remove_connector_node(p.id)
                        p.connection.split_if_disconnected()
                    if p in app.objects:
                        app.objects.remove(p)
            elif isinstance(obj, UINodeArray):
                app.objects.remove(obj)
                for sub in list(obj.nodes):
                    if sub.connection:
                        sub.connection.remove_connector_node(sub.id)
                        sub.connection.split_if_disconnected()
                    if sub in app.objects:
                        app.objects.remove(sub)
            else:
                if obj in app.objects:
                    app.objects.remove(obj)
                if hasattr(obj, "connection") and obj.connection:
                    obj.connection.remove_connector_node(obj.id)
                    obj.connection.split_if_disconnected()

            # Clean empty connections
            app.connections = {c for c in app.connections if c.lines}
            app.clear_selection()
            return True

        elif app.selected_connection and app.selected_connection[0]:
            conn, line = app.selected_connection
            if line in conn.lines:
                conn.lines.remove(line)
            elif (line[1], line[0]) in conn.lines:
                conn.lines.remove((line[1], line[0]))
            conn.validate_lines()
            conn.split_if_disconnected()
            app.connections = {c for c in app.connections if c.lines}
            app.clear_selection()
            return True

    # 5. Canvas Clicks and Ctrl-Connecting
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mouse_canvas_pos = to_canvas(event.pos, app.offset, zoom)
        ctrl_held = (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])

        # A. Check connector node collisions (waypoints & pin connectors)
        clicked_connector = None
        for conn in app.connections:
            for c in conn.connector_nodes:
                abs_cx = c.pos[0] * screen_w
                abs_cy = c.pos[1] * screen_h
                if math.hypot(mouse_canvas_pos[0] - abs_cx, mouse_canvas_pos[1] - abs_cy) <= 12.0 / zoom:
                    clicked_connector = c
                    break
            if clicked_connector:
                break

        # B. Check node collisions (subnodes/pins first, then components)
        clicked_node = None
        for obj in reversed(app.objects):
            if isinstance(obj, (UIComponentPin, UIArrayNode)):
                if obj.collidepoint(mouse_canvas_pos, canvas_size):
                    clicked_node = obj
                    break
        if not clicked_node:
            for obj in reversed(app.objects):
                if isinstance(obj, UINode) and not isinstance(obj, (UIComponentPin, UIArrayNode)):
                    if obj.collidepoint(mouse_canvas_pos, canvas_size):
                        clicked_node = obj
                        break

        # C. Check wire segment collision
        clicked_line_conn = None
        clicked_line_seg = None
        for conn in app.connections:
            line = conn.get_colliding_line(mouse_canvas_pos, canvas_size, threshold=8.0)
            if line is not None:
                clicked_line_conn = conn
                clicked_line_seg = line
                break

        # --- Ctrl + Click Connection Workflow ---
        if ctrl_held:
            start_pt = app.selected_start_point

            if start_pt is None:
                # Pick start point
                if clicked_node is not None:
                    app.select_node(clicked_node)
                elif clicked_connector is not None:
                    app.select_connector(clicked_connector)
                return True

            # Split wire segment if clicking an existing wire
            if clicked_line_conn is not None:
                split_line_on_connection(app, start_pt, clicked_line_conn, clicked_line_seg, mouse_canvas_pos, app.select_connector)
                return True

            # Connect to a node
            if clicked_node is not None and clicked_node is not start_pt:
                if isinstance(start_pt, UINode):
                    connect_nodes(app, start_pt, clicked_node)
                    app.select_node(clicked_node)
                elif isinstance(start_pt, UIConnectorPoint):
                    conn_a = next((c for c in app.connections if start_pt in c.connector_nodes), None)
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
                                if conn_b in app.connections:
                                    app.connections.remove(conn_b)
                        else:
                            c_b = UIConnectorPoint(identifier=f"c_{clicked_node.label}_{pygame.time.get_ticks()}_{id(clicked_node)}", linked_node=clicked_node)
                            conn_a.add_connector_node(c_b)
                            clicked_node.connection = conn_a
                            conn_a.add_line(start_pt.id, c_b.id)
                    app.select_node(clicked_node)
                return True

            # Connect to an existing connector
            if clicked_connector is not None and clicked_connector is not start_pt:
                if isinstance(start_pt, UINode):
                    if start_pt.connection is not None:
                        conn_a = start_pt.connection
                        conn_b = next((c for c in app.connections if clicked_connector in c.connector_nodes), None)
                        if conn_b:
                            if conn_a is conn_b:
                                c_a = get_or_create_connector(conn_a, start_pt)
                                conn_a.add_line(c_a.id, clicked_connector.id)
                            else:
                                merge_connections(conn_a, conn_b)
                                c_a = get_or_create_connector(conn_a, start_pt)
                                conn_a.add_line(c_a.id, clicked_connector.id)
                                if conn_b in app.connections:
                                    app.connections.remove(conn_b)
                    else:
                        conn_b = next((c for c in app.connections if clicked_connector in c.connector_nodes), None)
                        if conn_b:
                            c_a = UIConnectorPoint(identifier=f"c_{start_pt.label}_{pygame.time.get_ticks()}_{id(start_pt)}", linked_node=start_pt)
                            conn_b.add_connector_node(c_a)
                            start_pt.connection = conn_b
                            conn_b.add_line(c_a.id, clicked_connector.id)
                    app.select_connector(clicked_connector)

                elif isinstance(start_pt, UIConnectorPoint):
                    conn_a = next((c for c in app.connections if start_pt in c.connector_nodes), None)
                    conn_b = next((c for c in app.connections if clicked_connector in c.connector_nodes), None)
                    if conn_a and conn_b:
                        if conn_a is conn_b:
                            conn_a.add_line(start_pt.id, clicked_connector.id)
                        else:
                            merge_connections(conn_a, conn_b)
                            conn_a.add_line(start_pt.id, clicked_connector.id)
                            if conn_b in app.connections:
                                app.connections.remove(conn_b)
                    app.select_connector(clicked_connector)
                return True

            # Draw wire into free space (waypoint)
            free_id = f"free_{pygame.time.get_ticks()}_{id(start_pt)}"
            c_free = UIConnectorPoint(identifier=free_id, x=mouse_canvas_pos[0] / screen_w, y=mouse_canvas_pos[1] / screen_h)

            if isinstance(start_pt, UINode):
                if start_pt.connection is not None:
                    start_pt.connection.add_connector_node(c_free)
                    c_a = get_or_create_connector(start_pt.connection, start_pt)
                    start_pt.connection.add_line(c_a.id, free_id)
                else:
                    new_conn = UIConnection()
                    c_a = UIConnectorPoint(identifier=f"c_{start_pt.label}_{pygame.time.get_ticks()}", linked_node=start_pt)
                    new_conn.add_connector_node(c_a)
                    new_conn.add_connector_node(c_free)
                    new_conn.add_line(c_a.id, free_id)
                    start_pt.connection = new_conn
                    app.connections.add(new_conn)
                app.select_connector(c_free)

            elif isinstance(start_pt, UIConnectorPoint):
                conn_a = next((c for c in app.connections if start_pt in c.connector_nodes), None)
                if conn_a is not None:
                    conn_a.add_connector_node(c_free)
                    conn_a.add_line(start_pt.id, free_id)
                    app.select_connector(c_free)
            return True

        # --- Regular Left Click Workflow ---
        else:
            if clicked_connector is not None:
                if clicked_connector.linked_node is not None:
                    # Select and drag the linked node
                    app.select_node(clicked_connector.linked_node)
                    clicked_connector.linked_node.is_dragging = True
                    clicked_connector.linked_node.drag_start_pos = mouse_canvas_pos
                    clicked_connector.linked_node.dragged_far = False
                    clicked_connector.linked_node.drag_offset_x = (mouse_canvas_pos[0] / screen_w) - clicked_connector.linked_node.x
                    clicked_connector.linked_node.drag_offset_y = (mouse_canvas_pos[1] / screen_h) - clicked_connector.linked_node.y
                else:
                    # Select and drag free waypoint
                    app.select_connector(clicked_connector)
                    app.is_dragging_connector = True
                    app.dragged_connector = clicked_connector
                    app.drag_offset_x = mouse_canvas_pos[0] - (clicked_connector.x * screen_w)
                    app.drag_offset_y = mouse_canvas_pos[1] - (clicked_connector.y * screen_h)
                return True

            elif clicked_node is not None:
                app.select_node(clicked_node)
                return True

            elif clicked_line_conn is not None:
                app.select_connection(clicked_line_conn, clicked_line_seg)
                return True

            else:
                app.clear_selection()
                return True

    return False
