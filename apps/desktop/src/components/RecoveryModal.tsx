import React, { useState } from "react";
import { History, ShieldAlert, FileClock, Check, X, ChevronRight } from "lucide-react";
import { AutosaveSnapshot } from "../types/project";

interface RecoveryModalProps {
  isOpen: boolean;
  projectName: string;
  projectFilePath: string;
  snapshots: AutosaveSnapshot[];
  onRecoverSnapshot: (snapshotPath: string) => void;
  onOpenSavedVersion: () => void;
  onDismiss: () => void;
}

export const RecoveryModal: React.FC<RecoveryModalProps> = ({
  isOpen,
  projectName,
  projectFilePath,
  snapshots,
  onRecoverSnapshot,
  onOpenSavedVersion,
  onDismiss,
}) => {
  const [selectedSnapshot, setSelectedSnapshot] = useState<string | null>(
    snapshots.length > 0 ? snapshots[0].path : null
  );

  if (!isOpen || snapshots.length === 0) return null;

  const newest = snapshots[0];
  const newestDate = new Date(newest.modified_time * 1000).toLocaleString();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-[640px] max-h-[85vh] bg-[#1a1a22] border border-blue-500/40 rounded-xl shadow-2xl flex flex-col overflow-hidden text-slate-200">
        {/* Header */}
        <div className="px-5 py-4 bg-blue-950/30 border-b border-blue-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Project Recovery Available</h2>
              <p className="text-xs text-blue-300/80">
                A newer autosave snapshot was detected for &quot;{projectName}&quot;.
              </p>
            </div>
          </div>
          <button
            onClick={onDismiss}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Snapshot list & information */}
        <div className="p-5 space-y-4 flex-1 overflow-y-auto">
          <div className="p-3.5 bg-blue-950/20 border border-blue-500/20 rounded-lg text-xs leading-relaxed text-blue-200">
            The application detected an unexpected termination or autosave recorded more recently than the manually saved project file. You can restore your project state from any of the recovery snapshots below without overwriting your original saved file.
          </div>

          <div>
            <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
              Available Recovery Snapshots ({snapshots.length})
            </div>

            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {snapshots.map((snap, idx) => {
                const isSelected = selectedSnapshot === snap.path;
                const formattedTime = new Date(snap.modified_time * 1000).toLocaleString();
                const sizeKb = (snap.size_bytes / 1024).toFixed(1);

                return (
                  <div
                    key={snap.path}
                    onClick={() => setSelectedSnapshot(snap.path)}
                    className={`p-3 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
                      isSelected
                        ? "bg-blue-600/20 border-blue-500 text-white"
                        : "bg-[#14141a] border-[#2a2a36] hover:bg-[#20202a] text-slate-300"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <FileClock className={`w-4 h-4 ${isSelected ? "text-blue-400" : "text-[#707080]"}`} />
                      <div>
                        <div className="font-medium flex items-center gap-2">
                          <span>{snap.filename}</span>
                          {idx === 0 && (
                            <span className="px-1.5 py-0.2 rounded text-[10px] bg-blue-500/30 text-blue-300 border border-blue-400/40">
                              Latest
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-[#808090] font-mono mt-0.5">
                          {formattedTime} • {sizeKb} KB
                        </div>
                      </div>
                    </div>

                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                      isSelected ? "border-blue-400 bg-blue-500" : "border-[#404050]"
                    }`}>
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3.5 bg-[#14141a] border-t border-[#262632] flex items-center justify-between">
          <button
            onClick={onOpenSavedVersion}
            className="px-3.5 py-1.5 rounded-lg bg-[#282834] hover:bg-[#323242] text-slate-300 hover:text-white font-medium text-xs transition-colors"
          >
            Open Last Saved File
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onDismiss}
              className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white text-xs font-medium"
            >
              Cancel
            </button>
            <button
              onClick={() => selectedSnapshot && onRecoverSnapshot(selectedSnapshot)}
              disabled={!selectedSnapshot}
              className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <History className="w-3.5 h-3.5" />
              <span>Recover Selected Snapshot</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
