# Node-Based Compositing Subsystem

## Overview
The Node-Based Compositing Subsystem introduces a visual Directed Acyclic Graph (DAG) architecture inspired by industry standards such as Foundry Nuke and Blackmagic Fusion. It enables arbitrary routing, branching, multi-matte combining, and complex VFX graph execution.

## Directed Acyclic Graph (DAG) Engine

### 1. Kahn's Algorithm for Topological Sorting
To guarantee deterministic execution and verify causality, graph evaluation order is determined via Kahn's algorithm:
1. Identify all nodes with in-degree 0 (no incoming connection dependencies).
2. Push nodes into the evaluation queue.
3. For each visited node, decrement the in-degree of downstream dependent nodes.
4. If all nodes are visited, a valid execution order is returned.
5. If unvisited nodes remain with non-zero in-degree, a cyclic dependency loop exists, and a `ValueError` is raised before any GPU/CPU resources are allocated.

### 2. Socket Data Types
Nodes communicate via typed sockets:
- `RGBA`: 4-channel image buffer (Color plate + Alpha).
- `Alpha`: 1-channel scalar grayscale mask buffer.
- `Vector`: 2D/3D coordinate vector (motion, normals, spatial offsets).
- `Scalar`: Single floating-point value (densities, thresholds, strengths).

### 3. Core Node Types
1. **MediaInput**: Loads image or video plate from disk or memory.
2. **AIForeground**: Connects to the CorridorKey inference engine, outputting RGBA FG and Alpha Matte.
3. **AlphaMatte**: Extracts or injects a custom alpha channel.
4. **Mask**: Vector shape generator (Rectangle, Ellipse, Polygon, Bezier).
5. **Blur**: Gaussian spatial filter.
6. **ColorCorrection**: ASC-CDL Lift/Gamma/Gain and tone adjustment.
7. **Transform**: 2D Affine transformation.
8. **Background**: Generative background plate.
9. **Merge**: Multi-input layer composite with blend modes and mask input.
10. **MediaOutput**: Terminal sink node feeding the interactive viewer and export engine.

## Interactive Node Editor UI
The React frontend features an interactive node canvas (`NodeEditorModal.tsx`):
- Zoomable and pannable infinite canvas.
- Draggable node cards with status indicators and parameter controls.
- Socket ports color-coded by data type.
- Cubic Bezier connection wires drawn dynamically via SVG.
- Context-menu adding, deleting, and wiring of nodes.
