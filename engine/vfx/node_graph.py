"""CorridorKey 2.0 Desktop — Directed Acyclic Graph (DAG) Node Compositing Engine.

Implements graph topology, cycle detection, topological sorting, socket validation,
and node execution across 10 production compositing nodes:
1. Media Input
2. AI Foreground
3. Alpha Matte
4. Mask
5. Blur
6. Colour Correction
7. Transform
8. Background
9. Merge
10. Media Output
"""

from __future__ import annotations

import copy
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np


@dataclass
class NodeSocket:
    socket_id: str
    name: str
    data_type: str  # "rgba" | "alpha" | "vector" | "scalar"
    is_output: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NodeSocket":
        return cls(
            socket_id=d["socket_id"],
            name=d["name"],
            data_type=d["data_type"],
            is_output=bool(d.get("is_output", False)),
        )


@dataclass
class NodeConnection:
    connection_id: str
    from_node_id: str
    from_socket_id: str
    to_node_id: str
    to_socket_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NodeConnection":
        return cls(
            connection_id=d.get("connection_id", f"conn-{uuid.uuid4().hex[:8]}"),
            from_node_id=d["from_node_id"],
            from_socket_id=d["from_socket_id"],
            to_node_id=d["to_node_id"],
            to_socket_id=d["to_socket_id"],
        )


class BaseNode(ABC):
    """Abstract base class for nodes in the compositing DAG."""

    node_type: str = "base"

    def __init__(
        self,
        node_id: Optional[str] = None,
        title: Optional[str] = None,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id or f"node-{uuid.uuid4().hex[:8]}"
        self.title = title or self.default_title()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.properties = self.default_properties()
        if properties:
            self.properties.update(properties)
        self.inputs = self.define_inputs()
        self.outputs = self.define_outputs()

    @abstractmethod
    def default_title(self) -> str:
        pass

    @abstractmethod
    def default_properties(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def define_inputs(self) -> List[NodeSocket]:
        pass

    @abstractmethod
    def define_outputs(self) -> List[NodeSocket]:
        pass

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Executes node logic given input socket data, returning output socket data."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "properties": copy.deepcopy(self.properties),
            "inputs": [s.to_dict() for s in self.inputs],
            "outputs": [s.to_dict() for s in self.outputs],
        }


# -------------------------------------------------------------
# Node Implementations
# -------------------------------------------------------------

class MediaInputNode(BaseNode):
    node_type = "media_input"

    def default_title(self) -> str:
        return "Media Input"

    def default_properties(self) -> Dict[str, Any]:
        return {"source_path": "", "media_id": ""}

    def define_inputs(self) -> List[NodeSocket]:
        return []

    def define_outputs(self) -> List[NodeSocket]:
        return [
            NodeSocket("out_rgba", "RGBA", "rgba", is_output=True),
            NodeSocket("out_alpha", "Alpha", "alpha", is_output=True),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        img = inputs.get("custom_image")
        if img is None:
            # Synthetic 100x100 black image as default
            img = np.zeros((100, 100, 4), dtype=np.float32)
            img[:, :, 3] = 1.0
        elif img.shape[2] == 3:
            img = np.dstack([img, np.ones((img.shape[0], img.shape[1], 1), dtype=np.float32)])

        return {
            "out_rgba": img,
            "out_alpha": img[:, :, 3],
        }


class AIForegroundNode(BaseNode):
    node_type = "ai_foreground"

    def default_title(self) -> str:
        return "AI Foreground"

    def default_properties(self) -> Dict[str, Any]:
        return {"despill_strength": 0.7, "edge_threshold": 0.1}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_rgba", "Source RGBA", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return [
            NodeSocket("out_fg", "Foreground", "rgba", is_output=True),
            NodeSocket("out_matte", "Matte", "alpha", is_output=True),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        img = inputs.get("in_rgba")
        if img is None:
            return {"out_fg": None, "out_matte": None}

        despill = float(self.properties.get("despill_strength", 0.7))
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        max_rb = np.maximum(r, b)
        spill = np.maximum(0.0, g - max_rb)
        alpha = np.clip(1.0 - spill * 2.5, 0.0, 1.0)

        fg_rgb = img[:, :, :3].copy()
        fg_rgb[:, :, 1] = np.clip(g - spill * despill, 0.0, 1.0)
        fg_rgba = np.dstack([fg_rgb, alpha])

        return {"out_fg": fg_rgba, "out_matte": alpha}


class AlphaMatteNode(BaseNode):
    node_type = "alpha_matte"

    def default_title(self) -> str:
        return "Alpha Matte Refine"

    def default_properties(self) -> Dict[str, Any]:
        return {"contrast": 1.0, "choke_expand": 0.0, "feather": 0.0, "invert": False}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_alpha", "Matte In", "alpha")]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_alpha", "Matte Out", "alpha", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        alpha = inputs.get("in_alpha")
        if alpha is None:
            return {"out_alpha": None}

        from engine.vfx.matte_refine import MatteRefineSettings, refine_alpha_matte
        settings = MatteRefineSettings(
            contrast=float(self.properties.get("contrast", 1.0)),
            choke_expand=float(self.properties.get("choke_expand", 0.0)),
            edge_feather=float(self.properties.get("feather", 0.0)),
            invert=bool(self.properties.get("invert", False)),
        )
        refined, _ = refine_alpha_matte(alpha, settings=settings)
        return {"out_alpha": refined}


class MaskNode(BaseNode):
    node_type = "mask"

    def default_title(self) -> str:
        return "Vector Mask"

    def default_properties(self) -> Dict[str, Any]:
        return {"mask_type": "rectangle", "feather": 0.0, "inverted": False, "opacity": 1.0}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_rgba", "Reference", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_mask", "Mask", "alpha", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ref = inputs.get("in_rgba")
        h, w = (ref.shape[:2]) if ref is not None else (100, 100)

        from engine.vfx.masking import MaskItem, MaskType, rasterize_mask
        mask_item = MaskItem(
            mask_id=self.node_id,
            name=self.title,
            mask_type=MaskType(self.properties.get("mask_type", "rectangle")),
            feather=float(self.properties.get("feather", 0.0)),
            inverted=bool(self.properties.get("inverted", False)),
            opacity=float(self.properties.get("opacity", 1.0)),
        )
        mask_matte = rasterize_mask(mask_item, w, h)
        return {"out_mask": mask_matte}


class BlurNode(BaseNode):
    node_type = "blur"

    def default_title(self) -> str:
        return "Blur"

    def default_properties(self) -> Dict[str, Any]:
        return {"radius": 10.0}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_rgba", "RGBA", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_rgba", "Blurred", "rgba", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        img = inputs.get("in_rgba")
        if img is None:
            return {"out_rgba": None}
        radius = float(self.properties.get("radius", 10.0))
        if radius < 0.5:
            return {"out_rgba": img}
        ksize = int(round(radius * 2.5)) * 2 + 1
        blurred = cv2.GaussianBlur(img, (ksize, ksize), sigmaX=radius / 2.0)
        return {"out_rgba": blurred}


class ColorCorrectionNode(BaseNode):
    node_type = "color_correction"

    def default_title(self) -> str:
        return "Color Grade"

    def default_properties(self) -> Dict[str, Any]:
        return {"exposure": 0.0, "contrast": 1.0, "saturation": 1.0, "temperature": 0.0}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_rgba", "RGBA", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_rgba", "Graded", "rgba", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        img = inputs.get("in_rgba")
        if img is None:
            return {"out_rgba": None}
        from engine.vfx.color_grade import ColorGradeSettings, apply_color_grade
        settings = ColorGradeSettings(
            exposure=float(self.properties.get("exposure", 0.0)),
            contrast=float(self.properties.get("contrast", 1.0)),
            saturation=float(self.properties.get("saturation", 1.0)),
            temperature=float(self.properties.get("temperature", 0.0)),
        )
        return {"out_rgba": apply_color_grade(img, settings)}


class TransformNode(BaseNode):
    node_type = "transform"

    def default_title(self) -> str:
        return "Transform"

    def default_properties(self) -> Dict[str, Any]:
        return {"pos_x": 0.0, "pos_y": 0.0, "scale": 1.0, "rotation": 0.0}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_rgba", "RGBA", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_rgba", "Transformed", "rgba", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        img = inputs.get("in_rgba")
        if img is None:
            return {"out_rgba": None}
        from engine.vfx.layer_compositor import LayerItem, transform_layer_image
        h, w = img.shape[:2]
        layer = LayerItem(
            layer_id=self.node_id,
            name=self.title,
            pos_x=float(self.properties.get("pos_x", 0.0)),
            pos_y=float(self.properties.get("pos_y", 0.0)),
            scale_x=float(self.properties.get("scale", 1.0)),
            scale_y=float(self.properties.get("scale", 1.0)),
            rotation=float(self.properties.get("rotation", 0.0)),
        )
        return {"out_rgba": transform_layer_image(img, w, h, layer)}


class BackgroundNode(BaseNode):
    node_type = "background"

    def default_title(self) -> str:
        return "Background Plate"

    def default_properties(self) -> Dict[str, Any]:
        return {"color": [0.1, 0.1, 0.15]}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_ref", "Size Ref", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_bg", "Background", "rgba", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ref = inputs.get("in_ref")
        h, w = (ref.shape[:2]) if ref is not None else (100, 100)
        col = self.properties.get("color", [0.1, 0.1, 0.15])
        bg = np.zeros((h, w, 4), dtype=np.float32)
        bg[:, :, :3] = col
        bg[:, :, 3] = 1.0
        return {"out_bg": bg}


class MergeNode(BaseNode):
    node_type = "merge"

    def default_title(self) -> str:
        return "Merge"

    def default_properties(self) -> Dict[str, Any]:
        return {"blend_mode": "normal", "fg_opacity": 1.0}

    def define_inputs(self) -> List[NodeSocket]:
        return [
            NodeSocket("in_bg", "Background", "rgba"),
            NodeSocket("in_fg", "Foreground", "rgba"),
            NodeSocket("in_mask", "Mask (Opt)", "alpha"),
        ]

    def define_outputs(self) -> List[NodeSocket]:
        return [NodeSocket("out_comp", "Composite", "rgba", is_output=True)]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        bg = inputs.get("in_bg")
        fg = inputs.get("in_fg")
        mask = inputs.get("in_mask")

        if bg is None and fg is None:
            return {"out_comp": None}
        if bg is None:
            return {"out_comp": fg}
        if fg is None:
            return {"out_comp": bg}

        from engine.vfx.layer_compositor import BlendMode, composite_two_layers

        fg_work = fg.copy()
        if mask is not None:
            fg_work[:, :, 3] *= mask

        mode = BlendMode(self.properties.get("blend_mode", "normal"))
        op = float(self.properties.get("fg_opacity", 1.0))

        comp = composite_two_layers(bg, fg_work, blend_mode=mode, fg_opacity=op)
        return {"out_comp": comp}


class MediaOutputNode(BaseNode):
    node_type = "media_output"

    def default_title(self) -> str:
        return "Media Output"

    def default_properties(self) -> Dict[str, Any]:
        return {"export_format": "prores_4444"}

    def define_inputs(self) -> List[NodeSocket]:
        return [NodeSocket("in_composite", "Final Composite", "rgba")]

    def define_outputs(self) -> List[NodeSocket]:
        return []

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {"final_image": inputs.get("in_composite")}


# -------------------------------------------------------------
# Node Graph DAG and Evaluator
# -------------------------------------------------------------

NODE_REGISTRY: Dict[str, Type[BaseNode]] = {
    "media_input": MediaInputNode,
    "ai_foreground": AIForegroundNode,
    "alpha_matte": AlphaMatteNode,
    "mask": MaskNode,
    "blur": BlurNode,
    "color_correction": ColorCorrectionNode,
    "transform": TransformNode,
    "background": BackgroundNode,
    "merge": MergeNode,
    "media_output": MediaOutputNode,
}


class NodeGraph:
    """Directed Acyclic Graph (DAG) for node-based compositing."""

    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}
        self.connections: List[NodeConnection] = []

    def add_node(self, node: BaseNode) -> BaseNode:
        self.nodes[node.node_id] = node
        return node

    def remove_node(self, node_id: str) -> Optional[BaseNode]:
        if node_id in self.nodes:
            # Remove all connections linked to this node
            self.connections = [
                c for c in self.connections if c.from_node_id != node_id and c.to_node_id != node_id
            ]
            return self.nodes.pop(node_id)
        return None

    def connect(self, from_node_id: str, from_socket_id: str, to_node_id: str, to_socket_id: str) -> NodeConnection:
        # Check that nodes exist
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            raise ValueError("Both nodes must exist in the graph.")

        # Disallow connecting to self
        if from_node_id == to_node_id:
            raise ValueError("Cannot connect a node to itself.")

        # Replace existing incoming connection to to_socket_id
        self.connections = [
            c for c in self.connections if not (c.to_node_id == to_node_id and c.to_socket_id == to_socket_id)
        ]

        conn = NodeConnection(
            connection_id=f"conn-{uuid.uuid4().hex[:8]}",
            from_node_id=from_node_id,
            from_socket_id=from_socket_id,
            to_node_id=to_node_id,
            to_socket_id=to_socket_id,
        )
        self.connections.append(conn)

        # Validate that graph remains acyclic
        if self.detect_cycle():
            self.connections.remove(conn)
            raise ValueError("Connecting these nodes would create a circular dependency (cycle).")

        return conn

    def disconnect(self, connection_id: str) -> bool:
        for i, c in enumerate(self.connections):
            if c.connection_id == connection_id:
                self.connections.pop(i)
                return True
        return False

    def detect_cycle(self) -> bool:
        """Returns True if the graph contains any circular dependency."""
        adj = defaultdict(list)
        in_degree = defaultdict(int)

        for n_id in self.nodes:
            in_degree[n_id] = 0

        for c in self.connections:
            adj[c.from_node_id].append(c.to_node_id)
            in_degree[c.to_node_id] += 1

        queue = deque([n for n, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited_count < len(self.nodes)

    def get_evaluation_order(self) -> List[str]:
        """Returns topologically sorted list of node IDs for deterministic execution."""
        if self.detect_cycle():
            raise ValueError("Cannot evaluate graph with cycles.")

        adj = defaultdict(list)
        in_degree = defaultdict(int)

        for n_id in self.nodes:
            in_degree[n_id] = 0

        for c in self.connections:
            adj[c.from_node_id].append(c.to_node_id)
            in_degree[c.to_node_id] += 1

        queue = deque([n for n, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            curr = queue.popleft()
            order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    def execute_graph(self, initial_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes the complete DAG in topological order."""
        eval_order = self.get_evaluation_order()
        node_outputs: Dict[str, Dict[str, Any]] = {}

        for n_id in eval_order:
            node = self.nodes[n_id]
            # Gather inputs for this node from incoming connections
            in_data: Dict[str, Any] = {}
            if initial_inputs and n_id in initial_inputs:
                in_data.update(initial_inputs[n_id])

            for conn in self.connections:
                if conn.to_node_id == n_id:
                    from_out = node_outputs.get(conn.from_node_id, {})
                    val = from_out.get(conn.from_socket_id)
                    in_data[conn.to_socket_id] = val

            out_data = node.execute(in_data)
            node_outputs[n_id] = out_data

        return node_outputs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "connections": [c.to_dict() for c in self.connections],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NodeGraph":
        graph = cls()
        for nd in d.get("nodes", []):
            ntype = nd.get("node_type")
            ncls = NODE_REGISTRY.get(ntype)
            if ncls:
                node = ncls(
                    node_id=nd.get("node_id"),
                    title=nd.get("title"),
                    pos_x=float(nd.get("pos_x", 0.0)),
                    pos_y=float(nd.get("pos_y", 0.0)),
                    properties=nd.get("properties", {}),
                )
                graph.add_node(node)

        for cd in d.get("connections", []):
            try:
                graph.connect(
                    from_node_id=cd["from_node_id"],
                    from_socket_id=cd["from_socket_id"],
                    to_node_id=cd["to_node_id"],
                    to_socket_id=cd["to_socket_id"],
                )
            except ValueError:
                pass
        return graph
