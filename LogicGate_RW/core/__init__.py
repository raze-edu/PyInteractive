"""Core node and simulation primitives for LogicGate_RW."""

from .ui_node import (
    UINode,
    UIGlobalInputNode,
    UIGlobalOutputNode,
    UIComponentPin,
    UIConnectorPoint,
    NodeRegistry
)
from .ui_connection import UIConnection
from .ui_component import UILogicComponent
from .ui_arrays import UIArrayNode, UINodeArray
from .circuit_bridge import serialize_canvas, deserialize_inner_circuit, compile_canvas_to_table

__all__ = [
    "UINode",
    "UIGlobalInputNode",
    "UIGlobalOutputNode",
    "UIComponentPin",
    "UIConnectorPoint",
    "NodeRegistry",
    "UIConnection",
    "UILogicComponent",
    "UIArrayNode",
    "UINodeArray",
    "serialize_canvas",
    "deserialize_inner_circuit",
    "compile_canvas_to_table"
]
