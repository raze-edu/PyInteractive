import json
from typing import Any, Dict, List, Tuple

from include import Bits
from LogicGate_RW.core.ui_node import UIGlobalInputNode, UIGlobalOutputNode, normalize_label
from LogicGate_RW.core.ui_arrays import UIArrayNode, UINodeArray
from LogicGate_RW.core.ui_component import UILogicComponent
from LogicGate_RW.core.ui_connection import UIConnection, UIConnectorPoint

def serialize_canvas(app: Any) -> Dict[str, Any]:
    """Serializes canvas nodes, components, arrays, and wire connections."""
    canvas_w = app.screen.get_width()
    canvas_h = app.screen.get_height()

    serialized_nodes = []
    node_id_map = {}

    for obj in app.objects:
        if isinstance(obj, UIGlobalInputNode):
            nid = f"in_{obj.label}"
            node_id_map[obj] = nid
            serialized_nodes.append({
                "id": nid,
                "type": "input",
                "label": obj.label,
                "x": obj.x,
                "y": obj.y
            })
        elif isinstance(obj, UIGlobalOutputNode):
            nid = f"out_{obj.label}"
            node_id_map[obj] = nid
            serialized_nodes.append({
                "id": nid,
                "type": "output",
                "label": obj.label,
                "x": obj.x,
                "y": obj.y
            })
        elif isinstance(obj, UINodeArray):
            nid = f"array_{obj.label}"
            node_id_map[obj] = nid
            for i, sub in enumerate(obj.nodes):
                sub_nid = f"{nid}_{i}"
                node_id_map[sub] = sub_nid
            serialized_nodes.append({
                "id": nid,
                "type": "array",
                "array_type": obj.array_type,
                "size": obj.array_size,
                "alignment": obj.alignment,
                "label": obj.label,
                "x": obj.x,
                "y": obj.y
            })
        elif isinstance(obj, UILogicComponent):
            nid = f"comp_{obj.label}_{id(obj)}"
            node_id_map[obj] = nid
            for i, inp in enumerate(obj.inputs):
                node_id_map[inp] = f"{nid}_in_{i}_{inp.label}"
            for i, out in enumerate(obj.outputs):
                node_id_map[out] = f"{nid}_out_{i}_{out.label}"
            serialized_nodes.append({
                "id": nid,
                "type": "gate",
                "gate_name": obj.label_prefix,
                "label": obj.label,
                "x": obj.x,
                "y": obj.y
            })

    serialized_conns = []
    for conn in getattr(app, "connections", []):
        c_nodes = []
        for c in conn.connector_nodes:
            c_data = {
                "id": str(c.id),
                "x": c.x,
                "y": c.y,
                "linked_node_id": node_id_map.get(c.linked_node) if c.linked_node else None
            }
            c_nodes.append(c_data)
        serialized_conns.append({
            "connector_nodes": c_nodes,
            "lines": [list(line) for line in conn.lines]
        })

    return {
        "canvas_size": [canvas_w, canvas_h],
        "nodes": serialized_nodes,
        "connections": serialized_conns
    }

def deserialize_inner_circuit(circuit_data: Dict[str, Any], library: List[dict] = None) -> Tuple[List[Any], List[UIConnection]]:
    """Reconstructs internal circuit elements from serialized data."""
    if not circuit_data:
        return [], []

    nodes_data = circuit_data.get("nodes", [])
    conns_data = circuit_data.get("connections", [])

    id_to_obj = {}
    objects = []

    for nd in nodes_data:
        ntype = nd.get("type")
        pos = (nd.get("x", 0.1), nd.get("y", 0.1))
        if ntype == "input":
            inp = UIGlobalInputNode(pos=pos, custom_label=nd.get("label"))
            id_to_obj[nd["id"]] = inp
            objects.append(inp)
        elif ntype == "output":
            out = UIGlobalOutputNode(pos=pos, custom_label=nd.get("label"))
            id_to_obj[nd["id"]] = out
            objects.append(out)
        elif ntype == "array":
            arr = UINodeArray(
                array_type=nd.get("array_type", "input"),
                size=nd.get("size", 4),
                alignment=nd.get("alignment", "V"),
                pos=pos
            )
            arr.label = nd.get("label", arr.label)
            id_to_obj[nd["id"]] = arr
            objects.append(arr)
            for i, sub in enumerate(arr.nodes):
                sub_nid = f"{nd['id']}_{i}"
                id_to_obj[sub_nid] = sub
                objects.append(sub)
        elif ntype == "gate":
            gate_name = nd.get("gate_name")
            template = None
            if library:
                for item in library:
                    if item.get("type") == "gate" and item.get("name") == gate_name:
                        template = item.get("template")
                        break
            if template:
                gate = UILogicComponent.from_template(template, pos=pos)
                id_to_obj[nd["id"]] = gate
                objects.append(gate)
                for i, in_pin in enumerate(gate.inputs):
                    id_to_obj[f"{nd['id']}_in_{i}_{in_pin.label}"] = in_pin
                    objects.append(in_pin)
                for i, out_pin in enumerate(gate.outputs):
                    id_to_obj[f"{nd['id']}_out_{i}_{out_pin.label}"] = out_pin
                    objects.append(out_pin)

    connections = []
    for cd in conns_data:
        c_nodes = []
        for c_data in cd.get("connector_nodes", []):
            linked = id_to_obj.get(c_data.get("linked_node_id"))
            c = UIConnectorPoint(
                identifier=c_data.get("id"),
                x=c_data.get("x", 0.0),
                y=c_data.get("y", 0.0),
                linked_node=linked
            )
            c_nodes.append(c)

        lines = [tuple(line) for line in cd.get("lines", [])]
        conn = UIConnection(connector_nodes=c_nodes, lines=lines)
        connections.append(conn)

        for c in c_nodes:
            if c.linked_node:
                c.linked_node.connection = conn

    return objects, connections

def compile_canvas_to_table(app: Any) -> Tuple[Bits, Dict[str, str]]:
    """Compiles the canvas circuit into an include.Bits truth table and string dict."""
    inputs = [obj for obj in app.objects if isinstance(obj, UIGlobalInputNode) or (isinstance(obj, UIArrayNode) and obj.is_transmitter)]
    outputs = [obj for obj in app.objects if isinstance(obj, UIGlobalOutputNode) or (isinstance(obj, UIArrayNode) and not obj.is_transmitter)]

    inputs.sort(key=lambda n: n.label)
    outputs.sort(key=lambda n: n.label)

    # Save original states
    orig_states = [inp.state for inp in inputs]

    truth_table_dict = {}
    table_bits = Bits('')

    for b in Bits.range(len(inputs)):
        # Apply inputs
        for inp, val in zip(inputs, b.bool_array):
            inp.state = val

        # Run simulation propagation tick
        if hasattr(app, "tick_simulation"):
            app.tick_simulation()

        # Capture outputs
        out_states = [out.state for out in outputs]
        out_bits = Bits(out_states)
        table_bits += out_bits

        key_str = "".join("1" if x else "0" for x in b.bool_array)
        val_str = "".join("1" if x else "0" for x in out_states)
        truth_table_dict[key_str] = val_str

    # Restore original input states
    for inp, val in zip(inputs, orig_states):
        inp.state = val
    if hasattr(app, "tick_simulation"):
        app.tick_simulation()

    return table_bits, truth_table_dict
