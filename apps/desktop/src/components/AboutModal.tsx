import React from "react";
import { X, Sparkles, Cpu, HardDrive } from "lucide-react";

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-[#1a1a1e] border border-[#2e2e34] rounded shadow-2xl w-full max-w-md text-sm text-[#f4f4f6]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#2e2e34] bg-[#222226]">
          <div className="flex items-center gap-2 font-medium">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <span>About CorridorKey 2.0 Desktop</span>
          </div>
          <button onClick={onClose} className="text-[#a1a1aa] hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded bg-gradient-to-br from-blue-600 to-indigo-800 flex items-center justify-center font-bold text-xl text-white shadow-lg">
              CK
            </div>
            <div>
              <h2 className="text-base font-bold text-white">CorridorKey 2.0 Desktop</h2>
              <p className="text-xs text-[#a1a1aa]">Professional AI Rotoscoping & VFX Keying Suite</p>
              <p className="text-[11px] text-blue-400 font-mono mt-0.5">Version 2.0.0 (Phase 2 Build)</p>
            </div>
          </div>

          <div className="text-xs text-[#a1a1aa] leading-relaxed border-t border-[#2e2e34] pt-3">
            CorridorKey 2.0 was designed and trained by Zachary Harris in collaboration with Niko Pueringer and Corridor Digital LLC. 
            This standalone cross-platform desktop application provides hardware-accelerated matte generation, despill suppression, and alpha extraction.
          </div>

          <div className="bg-[#121214] border border-[#2e2e34] rounded p-3 text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-[#a1a1aa]">Architecture:</span>
              <span className="text-white font-mono">Tauri 2 + Rust + React</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#a1a1aa]">Neural Foundations:</span>
              <span className="text-white">C-RADIO (NVIDIA), MoGe-2, RVM (DeepMind)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#a1a1aa]">Target Platforms:</span>
              <span className="text-white">Windows RTX 5060 (CUDA) & macOS (Apple Silicon)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#a1a1aa]">License:</span>
              <span className="text-white">Corridor Key Licence v2.0 (CC BY-NC-SA 4.0)</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end px-4 py-3 border-t border-[#2e2e34] bg-[#222226]">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
