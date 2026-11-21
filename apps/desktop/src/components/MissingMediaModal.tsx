import React from "react";
import { AlertTriangle, FolderSearch, FileQuestion, Check, X } from "lucide-react";
import { MediaItem } from "../types/project";

interface MissingMediaModalProps {
  isOpen: boolean;
  missingMedia: MediaItem[];
  onRelinkSingle: (mediaId: string, newPath: string) => void;
  onRelinkFolder: (folderPath: string) => void;
  onClose: () => void;
}

export const MissingMediaModal: React.FC<MissingMediaModalProps> = ({
  isOpen,
  missingMedia,
  onRelinkSingle,
  onRelinkFolder,
  onClose,
}) => {
  if (!isOpen || missingMedia.length === 0) return null;

  const handlePickFolder = async () => {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({
        directory: true,
        multiple: false,
        title: "Select Folder Containing Missing Media",
      });
      if (selected && typeof selected === "string") {
        onRelinkFolder(selected);
      }
    } catch (e) {
      console.warn("Folder picker failed:", e);
    }
  };

  const handlePickFile = async (mediaId: string) => {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({
        multiple: false,
        title: "Locate Replacement Media File",
      });
      if (selected && typeof selected === "string") {
        onRelinkSingle(mediaId, selected);
      }
    } catch (e) {
      console.warn("File picker failed:", e);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-[620px] max-h-[85vh] bg-[#1a1a22] border border-amber-500/40 rounded-xl shadow-2xl flex flex-col overflow-hidden text-slate-200">
        {/* Header */}
        <div className="px-5 py-4 bg-amber-950/30 border-b border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Missing Media Detected</h2>
              <p className="text-xs text-amber-300/80">
                {missingMedia.length} media reference{missingMedia.length === 1 ? "" : "s"} could not be found at their saved location.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Missing File List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {missingMedia.map((m) => (
            <div
              key={m.id}
              className="p-3 bg-[#14141a] border border-[#2a2a36] rounded-lg flex items-center justify-between gap-3 text-xs"
            >
              <div className="flex items-center gap-2.5 truncate">
                <FileQuestion className="w-4 h-4 text-amber-400 shrink-0" />
                <div className="truncate">
                  <div className="font-medium text-white truncate">{m.name}</div>
                  <div className="text-[11px] font-mono text-[#808090] truncate">{m.path}</div>
                </div>
              </div>

              <button
                onClick={() => handlePickFile(m.id)}
                className="px-2.5 py-1 rounded bg-[#2a2a36] hover:bg-[#343444] text-white shrink-0 font-medium transition-colors"
              >
                Locate File...
              </button>
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3.5 bg-[#14141a] border-t border-[#262632] flex items-center justify-between">
          <button
            onClick={handlePickFolder}
            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-2 transition-colors shadow-sm"
          >
            <FolderSearch className="w-3.5 h-3.5" />
            <span>Search Folder to Relink All...</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-[#282834] hover:bg-[#323242] text-slate-300 hover:text-white font-medium text-xs transition-colors"
          >
            Skip For Now
          </button>
        </div>
      </div>
    </div>
  );
};
