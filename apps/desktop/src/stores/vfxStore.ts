import { create } from "zustand";

export interface MaskPoint {
  x: number;
  y: number;
  handleIn?: [number, number];
  handleOut?: [number, number];
}

export interface MaskItem {
  id: string;
  name: string;
  type: "rectangle" | "ellipse" | "polygon" | "bezier" | "freehand";
  mode: "add" | "subtract";
  inverted: boolean;
  feather: number; // pixels
  expansion: number; // pixels
  opacity: number; // 0.0 to 1.0
  visible: boolean;
  posX: number;
  posY: number;
  scale: number;
  points: MaskPoint[];
}

export interface MatteRefineSettings {
  contrast: number;
  brightness: number;
  edgeSoftness: number;
  edgeFeather: number;
  chokeExpand: number;
  alphaBlur: number;
  alphaThreshold: number;
  invert: boolean;
  edgeDecontamination: number;
  foregroundRestoration: number;
  spillSuppression: number;
}

export interface ColorGradeSettings {
  exposure: number;
  contrast: number;
  brightness: number;
  highlights: number;
  shadows: number;
  whites: number;
  blacks: number;
  temperature: number;
  tint: number;
  saturation: number;
  vibrance: number;
  lift: number;
  gamma: number;
  gain: number;
  channelR: number;
  channelG: number;
  channelB: number;
}

export interface EffectItem {
  id: string;
  type: string;
  name: string;
  enabled: boolean;
  parameters: Record<string, any>;
}

export interface LayerItem {
  id: string;
  name: string;
  type: "video" | "image" | "solid" | "ai_foreground";
  visible: boolean;
  locked: boolean;
  opacity: number;
  blendMode: "normal" | "multiply" | "screen" | "add" | "overlay" | "difference";
  posX: number;
  posY: number;
  scaleX: number;
  scaleY: number;
  rotation: number;
  anchorX: number;
  anchorY: number;
}

export interface NodeSocket {
  id: string;
  name: string;
  dataType: "rgba" | "alpha" | "vector" | "scalar";
  isOutput: boolean;
}

export interface NodeItem {
  id: string;
  type: string;
  title: string;
  posX: number;
  posY: number;
  properties: Record<string, any>;
  inputs: NodeSocket[];
  outputs: NodeSocket[];
}

export interface NodeConnection {
  id: string;
  fromNodeId: string;
  fromSocketId: string;
  toNodeId: string;
  toSocketId: string;
}

interface VFXState {
  // Masking
  masks: MaskItem[];
  selectedMaskId: string | null;
  addMask: (type: MaskItem["type"]) => void;
  removeMask: (id: string) => void;
  updateMask: (id: string, partial: Partial<MaskItem>) => void;
  reorderMask: (id: string, newIndex: number) => void;
  selectMask: (id: string | null) => void;

  // Matte Refine
  matteRefine: MatteRefineSettings;
  updateMatteRefine: (partial: Partial<MatteRefineSettings>) => void;
  resetMatteRefine: () => void;

  // Color Grade
  colorGrade: ColorGradeSettings;
  updateColorGrade: (partial: Partial<ColorGradeSettings>) => void;
  resetColorGrade: () => void;

  // Effect Stack
  effects: EffectItem[];
  selectedEffectId: string | null;
  addEffect: (type: string) => void;
  removeEffect: (id: string) => void;
  duplicateEffect: (id: string) => void;
  toggleEffect: (id: string) => void;
  reorderEffect: (id: string, newIndex: number) => void;
  updateEffectParams: (id: string, params: Record<string, any>) => void;
  selectEffect: (id: string | null) => void;

  // Layer Compositing
  layers: LayerItem[];
  selectedLayerId: string | null;
  addLayer: (type: LayerItem["type"], name: string) => void;
  removeLayer: (id: string) => void;
  updateLayer: (id: string, partial: Partial<LayerItem>) => void;
  reorderLayer: (id: string, newIndex: number) => void;
  selectLayer: (id: string | null) => void;

  // Node Compositing
  nodes: NodeItem[];
  connections: NodeConnection[];
  selectedNodeId: string | null;
  addNode: (type: string, posX: number, posY: number) => void;
  removeNode: (id: string) => void;
  updateNodeProps: (id: string, props: Record<string, any>) => void;
  connectNodes: (fromNodeId: string, fromSocketId: string, toNodeId: string, toSocketId: string) => void;
  disconnectNodes: (connectionId: string) => void;
  selectNode: (id: string | null) => void;

  // Project serialization & reset
  loadVFXData: (data: {
    masks?: MaskItem[];
    matte_refine?: Partial<MatteRefineSettings>;
    color_grade?: Partial<ColorGradeSettings>;
    effects?: EffectItem[];
    layers?: LayerItem[];
    node_graph?: {
      nodes?: NodeItem[];
      connections?: NodeConnection[];
    };
  }) => void;
  resetVFX: () => void;
}

const defaultMatteRefine: MatteRefineSettings = {
  contrast: 1.0,
  brightness: 0.0,
  edgeSoftness: 0.0,
  edgeFeather: 0.0,
  chokeExpand: 0.0,
  alphaBlur: 0.0,
  alphaThreshold: 0.0,
  invert: false,
  edgeDecontamination: 0.0,
  foregroundRestoration: 0.0,
  spillSuppression: 0.7,
};

const defaultColorGrade: ColorGradeSettings = {
  exposure: 0.0,
  contrast: 1.0,
  brightness: 0.0,
  highlights: 0.0,
  shadows: 0.0,
  whites: 0.0,
  blacks: 0.0,
  temperature: 0.0,
  tint: 0.0,
  saturation: 1.0,
  vibrance: 0.0,
  lift: 0.0,
  gamma: 1.0,
  gain: 1.0,
  channelR: 1.0,
  channelG: 1.0,
  channelB: 1.0,
};

const defaultLayers: LayerItem[] = [
  {
    id: "layer_fg",
    name: "Foreground Plate",
    type: "ai_foreground",
    visible: true,
    locked: false,
    opacity: 1.0,
    blendMode: "normal",
    posX: 0,
    posY: 0,
    scaleX: 1.0,
    scaleY: 1.0,
    rotation: 0,
    anchorX: 0.5,
    anchorY: 0.5,
  },
  {
    id: "layer_bg",
    name: "Background Plate",
    type: "video",
    visible: true,
    locked: false,
    opacity: 1.0,
    blendMode: "normal",
    posX: 0,
    posY: 0,
    scaleX: 1.0,
    scaleY: 1.0,
    rotation: 0,
    anchorX: 0.5,
    anchorY: 0.5,
  },
];

const defaultNodes: NodeItem[] = [
  {
    id: "node_input",
    type: "media_input",
    title: "Media Input",
    posX: 60,
    posY: 80,
    properties: {},
    inputs: [],
    outputs: [{ id: "out_rgba", name: "RGBA", dataType: "rgba", isOutput: true }],
  },
  {
    id: "node_ai",
    type: "ai_foreground",
    title: "AI Foreground",
    posX: 300,
    posY: 80,
    properties: { despill_strength: 0.7 },
    inputs: [{ id: "in_rgba", name: "RGBA", dataType: "rgba", isOutput: false }],
    outputs: [
      { id: "out_fg", name: "FG", dataType: "rgba", isOutput: true },
      { id: "out_matte", name: "Matte", dataType: "alpha", isOutput: true },
    ],
  },
  {
    id: "node_merge",
    type: "merge",
    title: "Merge Composite",
    posX: 560,
    posY: 100,
    properties: { blend_mode: "normal", fg_opacity: 1.0 },
    inputs: [
      { id: "in_bg", name: "BG", dataType: "rgba", isOutput: false },
      { id: "in_fg", name: "FG", dataType: "rgba", isOutput: false },
    ],
    outputs: [{ id: "out_comp", name: "Comp", dataType: "rgba", isOutput: true }],
  },
  {
    id: "node_output",
    type: "media_output",
    title: "Media Output",
    posX: 800,
    posY: 100,
    properties: {},
    inputs: [{ id: "in_composite", name: "Composite", dataType: "rgba", isOutput: false }],
    outputs: [],
  },
];

const defaultConnections: NodeConnection[] = [
  {
    id: "conn_1",
    fromNodeId: "node_input",
    fromSocketId: "out_rgba",
    toNodeId: "node_ai",
    toSocketId: "in_rgba",
  },
  {
    id: "conn_2",
    fromNodeId: "node_ai",
    fromSocketId: "out_fg",
    toNodeId: "node_merge",
    toSocketId: "in_fg",
  },
  {
    id: "conn_3",
    fromNodeId: "node_merge",
    fromSocketId: "out_comp",
    toNodeId: "node_output",
    toSocketId: "in_composite",
  },
];

export const useVFXStore = create<VFXState>((set) => ({
  // Masking
  masks: [],
  selectedMaskId: null,

  addMask: (type) =>
    set((state) => {
      const id = `mask_${Date.now()}`;
      const newMask: MaskItem = {
        id,
        name: `${type.charAt(0).toUpperCase() + type.slice(1)} Mask`,
        type,
        mode: "add",
        inverted: false,
        feather: 5.0,
        expansion: 0.0,
        opacity: 1.0,
        visible: true,
        posX: 0,
        posY: 0,
        scale: 1.0,
        points:
          type === "rectangle"
            ? [
                { x: 0.25, y: 0.25 },
                { x: 0.75, y: 0.75 },
              ]
            : [
                { x: 0.5, y: 0.2 },
                { x: 0.8, y: 0.5 },
                { x: 0.5, y: 0.8 },
                { x: 0.2, y: 0.5 },
              ],
      };
      return {
        masks: [...state.masks, newMask],
        selectedMaskId: id,
      };
    }),

  removeMask: (id) =>
    set((state) => ({
      masks: state.masks.filter((m) => m.id !== id),
      selectedMaskId: state.selectedMaskId === id ? null : state.selectedMaskId,
    })),

  updateMask: (id, partial) =>
    set((state) => ({
      masks: state.masks.map((m) => (m.id === id ? { ...m, ...partial } : m)),
    })),

  reorderMask: (id, newIndex) =>
    set((state) => {
      const idx = state.masks.findIndex((m) => m.id === id);
      if (idx === -1) return state;
      const list = [...state.masks];
      const [item] = list.splice(idx, 1);
      list.splice(newIndex, 0, item);
      return { masks: list };
    }),

  selectMask: (id) => set({ selectedMaskId: id }),

  // Matte Refine
  matteRefine: { ...defaultMatteRefine },
  updateMatteRefine: (partial) =>
    set((state) => ({ matteRefine: { ...state.matteRefine, ...partial } })),
  resetMatteRefine: () => set({ matteRefine: { ...defaultMatteRefine } }),

  // Color Grade
  colorGrade: { ...defaultColorGrade },
  updateColorGrade: (partial) =>
    set((state) => ({ colorGrade: { ...state.colorGrade, ...partial } })),
  resetColorGrade: () => set({ colorGrade: { ...defaultColorGrade } }),

  // Effect Stack
  effects: [],
  selectedEffectId: null,

  addEffect: (type) =>
    set((state) => {
      const id = `eff_${Date.now()}`;
      const defaultParamMap: Record<string, Record<string, any>> = {
        gaussian_blur: { radius: 10.0 },
        sharpen: { strength: 1.0, radius: 1.5 },
        glow: { threshold: 0.6, radius: 20.0, intensity: 1.0 },
        drop_shadow: { distance: 15.0, angle: 45.0, blur: 10.0, opacity: 0.75 },
        gaussian_noise: { amount: 0.05, monochromatic: true },
        film_grain: { intensity: 0.08, size: 1.5 },
        vignette: { amount: 0.5, radius: 0.75, softness: 0.4 },
        hue_saturation: { hueShift: 0.0, saturation: 1.0, lightness: 0.0 },
        color_correction: { exposure: 0.0, contrast: 1.0, saturation: 1.0 },
        spill_suppression: { spillType: "green", strength: 0.8 },
      };

      const titleMap: Record<string, string> = {
        gaussian_blur: "Gaussian Blur",
        sharpen: "Sharpen",
        glow: "Glow",
        drop_shadow: "Drop Shadow",
        gaussian_noise: "Gaussian Noise",
        film_grain: "Film Grain",
        vignette: "Vignette",
        hue_saturation: "Hue / Saturation",
        color_correction: "Color Correction",
        spill_suppression: "Spill Suppression",
      };

      const newEffect: EffectItem = {
        id,
        type,
        name: titleMap[type] || type,
        enabled: true,
        parameters: defaultParamMap[type] || {},
      };

      return {
        effects: [...state.effects, newEffect],
        selectedEffectId: id,
      };
    }),

  removeEffect: (id) =>
    set((state) => ({
      effects: state.effects.filter((e) => e.id !== id),
      selectedEffectId: state.selectedEffectId === id ? null : state.selectedEffectId,
    })),

  duplicateEffect: (id) =>
    set((state) => {
      const eff = state.effects.find((e) => e.id === id);
      if (!eff) return state;
      const dup: EffectItem = {
        ...eff,
        id: `eff_${Date.now()}`,
        name: `${eff.name} (Copy)`,
        parameters: JSON.parse(JSON.stringify(eff.parameters)),
      };
      return {
        effects: [...state.effects, dup],
        selectedEffectId: dup.id,
      };
    }),

  toggleEffect: (id) =>
    set((state) => ({
      effects: state.effects.map((e) =>
        e.id === id ? { ...e, enabled: !e.enabled } : e
      ),
    })),

  reorderEffect: (id, newIndex) =>
    set((state) => {
      const idx = state.effects.findIndex((e) => e.id === id);
      if (idx === -1) return state;
      const list = [...state.effects];
      const [item] = list.splice(idx, 1);
      list.splice(newIndex, 0, item);
      return { effects: list };
    }),

  updateEffectParams: (id, params) =>
    set((state) => ({
      effects: state.effects.map((e) =>
        e.id === id ? { ...e, parameters: { ...e.parameters, ...params } } : e
      ),
    })),

  selectEffect: (id) => set({ selectedEffectId: id }),

  // Layer Compositing
  layers: defaultLayers,
  selectedLayerId: "layer_fg",

  addLayer: (type, name) =>
    set((state) => {
      const id = `layer_${Date.now()}`;
      const newLayer: LayerItem = {
        id,
        name,
        type,
        visible: true,
        locked: false,
        opacity: 1.0,
        blendMode: "normal",
        posX: 0,
        posY: 0,
        scaleX: 1.0,
        scaleY: 1.0,
        rotation: 0,
        anchorX: 0.5,
        anchorY: 0.5,
      };
      return {
        layers: [newLayer, ...state.layers],
        selectedLayerId: id,
      };
    }),

  removeLayer: (id) =>
    set((state) => ({
      layers: state.layers.filter((l) => l.id !== id),
      selectedLayerId: state.selectedLayerId === id ? null : state.selectedLayerId,
    })),

  updateLayer: (id, partial) =>
    set((state) => ({
      layers: state.layers.map((l) => (l.id === id ? { ...l, ...partial } : l)),
    })),

  reorderLayer: (id, newIndex) =>
    set((state) => {
      const idx = state.layers.findIndex((l) => l.id === id);
      if (idx === -1) return state;
      const list = [...state.layers];
      const [item] = list.splice(idx, 1);
      list.splice(newIndex, 0, item);
      return { layers: list };
    }),

  selectLayer: (id) => set({ selectedLayerId: id }),

  // Node Compositing
  nodes: defaultNodes,
  connections: defaultConnections,
  selectedNodeId: "node_ai",

  addNode: (type, posX, posY) =>
    set((state) => {
      const id = `node_${Date.now()}`;
      const titleMap: Record<string, string> = {
        media_input: "Media Input",
        ai_foreground: "AI Foreground",
        alpha_matte: "Alpha Matte",
        mask: "Mask",
        blur: "Blur",
        color_correction: "Color Grade",
        transform: "Transform",
        background: "Background Plate",
        merge: "Merge",
        media_output: "Media Output",
      };

      const newNode: NodeItem = {
        id,
        type,
        title: titleMap[type] || type,
        posX,
        posY,
        properties: {},
        inputs: type === "media_input" ? [] : [{ id: "in_rgba", name: "In", dataType: "rgba", isOutput: false }],
        outputs: type === "media_output" ? [] : [{ id: "out_rgba", name: "Out", dataType: "rgba", isOutput: true }],
      };

      return {
        nodes: [...state.nodes, newNode],
        selectedNodeId: id,
      };
    }),

  removeNode: (id) =>
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== id),
      connections: state.connections.filter((c) => c.fromNodeId !== id && c.toNodeId !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),

  updateNodeProps: (id, props) =>
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === id ? { ...n, properties: { ...n.properties, ...props } } : n
      ),
    })),

  connectNodes: (fromNodeId, fromSocketId, toNodeId, toSocketId) =>
    set((state) => {
      if (fromNodeId === toNodeId) return state;
      const filtered = state.connections.filter(
        (c) => !(c.toNodeId === toNodeId && c.toSocketId === toSocketId)
      );
      const newConn: NodeConnection = {
        id: `conn_${Date.now()}`,
        fromNodeId,
        fromSocketId,
        toNodeId,
        toSocketId,
      };
      return { connections: [...filtered, newConn] };
    }),

  disconnectNodes: (connectionId) =>
    set((state) => ({
      connections: state.connections.filter((c) => c.id !== connectionId),
    })),

  selectNode: (id) => set({ selectedNodeId: id }),

  loadVFXData: (data) =>
    set((state) => ({
      masks: data.masks ?? state.masks,
      matteRefine: data.matte_refine ? { ...state.matteRefine, ...data.matte_refine } : state.matteRefine,
      colorGrade: data.color_grade ? { ...state.colorGrade, ...data.color_grade } : state.colorGrade,
      effects: data.effects ?? state.effects,
      layers: data.layers ?? state.layers,
      nodes: data.node_graph?.nodes ?? state.nodes,
      connections: data.node_graph?.connections ?? state.connections,
    })),

  resetVFX: () =>
    set(() => ({
      masks: [],
      selectedMaskId: null,
      matteRefine: defaultMatteRefine,
      colorGrade: defaultColorGrade,
      effects: [],
      selectedEffectId: null,
      layers: defaultLayers,
      selectedLayerId: "layer_fg",
      nodes: defaultNodes,
      connections: defaultConnections,
      selectedNodeId: "node_ai",
    })),
}));
