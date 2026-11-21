import React, { useState, useRef } from "react";
import { X, Plus, Trash2, Cpu, ArrowRight, CheckCircle2, Play } from "lucide-react";
import { useVFXStore, NodeItem, NodeConnection } from "../../stores/vfxStore";

interface NodeEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NodeEditorModal: React.FC<NodeEditorModalProps> = ({ isOpen, onClose }) => {
  const {
    nodes,
    connections,
    selectedNodeId,
    addNode,
    removeNode,
    connectNodes,
    disconnectNodes,
    selectNode,
  } = useVFXStore();

  const [connectingFrom, setConnectingFrom] = useState<{ nodeId: string; socketId: string } | null>(null);

  if (!isOpen) return null;

  const availableNodeTypes = [
    { type: "media_input", label: "Media Input" },
    { type: "ai_foreground", label: "AI Foreground" },
    { type: "alpha_matte", label: "Alpha Matte" },
    { type: "mask", label: "Vector Mask" },
    { type: "blur", label: "Blur" },
    { type: "color_correction", label: "Color Grade" },
    { type: "transform", label: "Transform" },
    { type: "background", label: "Background Plate" },
    { type: "merge", label: "Merge Composite" },
    { type: "media_output", label: "Media Output" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md animate-in fade-in duration-150 select-none">
      <div className="w-[90vw] h-[85vh] bg-[#14141a] border border-[#2c2c38] rounded-xl shadow-2xl flex flex-col overflow-hidden text-slate-200">
        {/* Header */}
        <div className="px-5 py-3 bg-[#1a1a22] border-b border-[#2c2c36] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded bg-blue-600/20 text-blue-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Node-Based Compositing Graph</h2>
              <p className="text-[11px] text-[#808090]">
                Interactive Directed Acyclic Graph (DAG) with dependency evaluation
              </p>
            </div>
          </div>

          {/* Quick Node Adders */}
          <div className="flex items-center gap-2">
            <select
              onChange={(e) => {
                if (e.target.value) {
                  addNode(e.target.value, 150 + Math.random() * 300, 100 + Math.random() * 200);
                  e.target.value = "";
                }
              }}
              className="bg-[#242430] border border-[#343444] rounded px-2.5 py-1 text-xs text-white"
              defaultValue=""
            >
              <option value="" disabled>
                + Add Node...
              </option>
              {availableNodeTypes.map((nt) => (
                <option key={nt.type} value={nt.type}>
                  {nt.label}
                </option>
              ))}
            </select>

            <button
              onClick={onClose}
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-white/10"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Node Graph Canvas Area */}
        <div className="flex-1 relative bg-[#0e0e12] overflow-auto">
          {/* Subtle grid background */}
          <div
            className="absolute inset-0 opacity-20 pointer-events-none"
            style={{
              backgroundImage:
                "radial-gradient(circle, #404050 1px, transparent 1px)",
              backgroundSize: "24px 24px",
            }}
          />

          {/* SVG Connection Lines */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
            {connections.map((conn) => {
              const fromNode = nodes.find((n) => n.id === conn.fromNodeId);
              const toNode = nodes.find((n) => n.id === conn.toNodeId);
              if (!fromNode || !toNode) return null;

              const x1 = fromNode.posX + 180;
              const y1 = fromNode.posY + 45;
              const x2 = toNode.posX;
              const y2 = toNode.posY + 45;
              const dx = Math.abs(x2 - x1) * 0.5;

              return (
                <g key={conn.id}>
                  <path
                    d={`M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`}
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    className="opacity-80"
                  />
                  {/* Wire Flow Arrow Indicator */}
                  <circle cx={(x1 + x2) / 2} cy={(y1 + y2) / 2} r="3" fill="#60a5fa" />
                </g>
              );
            })}
          </svg>

          {/* Draggable Node Cards */}
          {nodes.map((node) => {
            const isSelected = node.id === selectedNodeId;
            return (
              <div
                key={node.id}
                onClick={() => selectNode(node.id)}
                className={`absolute w-44 rounded-lg border text-xs shadow-xl transition-shadow z-20 ${
                  isSelected
                    ? "bg-[#1e1e28] border-blue-500 ring-1 ring-blue-500/50"
                    : "bg-[#181820] border-[#2c2c38] hover:border-[#404054]"
                }`}
                style={{
                  left: `${node.posX}px`,
                  top: `${node.posY}px`,
                }}
              >
                {/* Node Title Header */}
                <div className="px-2.5 py-1.5 bg-[#20202c] border-b border-[#2c2c38] rounded-t-lg flex items-center justify-between">
                  <span className="font-semibold text-white truncate">{node.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeNode(node.id);
                    }}
                    className="text-[#707080] hover:text-red-400 p-0.5"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>

                {/* Sockets */}
                <div className="p-2 space-y-2">
                  {/* Inputs */}
                  <div className="space-y-1">
                    {node.inputs.map((inp) => (
                      <div
                        key={inp.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (connectingFrom) {
                            connectNodes(
                              connectingFrom.nodeId,
                              connectingFrom.socketId,
                              node.id,
                              inp.id
                            );
                            setConnectingFrom(null);
                          }
                        }}
                        className={`flex items-center gap-1.5 cursor-pointer hover:text-blue-300 ${
                          connectingFrom ? "animate-pulse font-bold text-amber-400" : "text-[#9090a0]"
                        }`}
                      >
                        <div className="w-2.5 h-2.5 rounded-full border border-blue-400 bg-blue-500/30" />
                        <span className="text-[10px]">{inp.name}</span>
                      </div>
                    ))}
                  </div>

                  {/* Outputs */}
                  <div className="space-y-1 pt-1 border-t border-[#262632]">
                    {node.outputs.map((out) => (
                      <div
                        key={out.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          setConnectingFrom({ nodeId: node.id, socketId: out.id });
                        }}
                        className="flex items-center justify-end gap-1.5 cursor-pointer text-blue-400 hover:text-blue-200"
                      >
                        <span className="text-[10px]">{out.name}</span>
                        <div className="w-2.5 h-2.5 rounded-full border border-teal-400 bg-teal-500/50" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-5 py-2.5 bg-[#16161e] border-t border-[#262632] flex items-center justify-between text-xs text-[#808090]">
          <div>
            <span>{nodes.length} Nodes</span> • <span>{connections.length} Connections</span>
            {connectingFrom && (
              <span className="ml-3 text-amber-400 font-medium">
                Click an input socket on another node to complete connection...
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1 rounded bg-[#2a2a36] hover:bg-[#343444] text-white font-medium"
          >
            Close Graph
          </button>
        </div>
      </div>
    </div>
  );
};
