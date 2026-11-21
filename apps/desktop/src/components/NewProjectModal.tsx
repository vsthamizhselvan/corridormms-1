import React, { useState } from "react";
import { useProjectStore } from "../project/projectStore";
import { useTimelineStore } from "../project/timelineStore";
import { useMediaStore } from "../project/mediaStore";
import { useVFXStore } from "../stores/vfxStore";
import { X, FolderPlus } from "lucide-react";

interface NewProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NewProjectModal: React.FC<NewProjectModalProps> = ({ isOpen, onClose }) => {
  const { setProject } = useProjectStore();
  const { setTracks, setDurationFrames } = useTimelineStore();
  const { clearMedia } = useMediaStore();

  const [name, setName] = useState("VFX_Shot_01");
  const [resolution, setResolution] = useState("1920x1080");
  const [frameRate, setFrameRate] = useState("24");
  const [colorSpace, setColorSpace] = useState("sRGB / Rec.709");

  if (!isOpen) return null;

  const handleCreate = () => {
    const [width, height] = resolution.split("x").map(Number);
    const fps = parseFloat(frameRate);

    setProject({
      name,
      width,
      height,
      frameRate: fps,
      colorSpace,
      createdAt: new Date().toISOString(),
      modifiedAt: new Date().toISOString(),
    });

    clearMedia();
    setTracks([
      {
        id: "track_v1",
        type: "video",
        name: "Video 1",
        visible: true,
        locked: false,
        muted: false,
        clips: [],
      },
      {
        id: "track_a1",
        type: "audio",
        name: "Audio 1",
        visible: true,
        locked: false,
        muted: false,
        clips: [],
      },
    ]);
    setDurationFrames(240);
    useVFXStore.getState().resetVFX();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-[#1a1a1e] border border-[#2e2e34] rounded shadow-2xl w-full max-w-md text-sm text-[#f4f4f6]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#2e2e34] bg-[#222226]">
          <div className="flex items-center gap-2 font-medium">
            <FolderPlus className="w-4 h-4 text-blue-500" />
            <span>New CorridorKey Project</span>
          </div>
          <button onClick={onClose} className="text-[#a1a1aa] hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-xs text-[#a1a1aa] mb-1">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#121214] border border-[#2e2e34] px-2.5 py-1.5 rounded text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-[#a1a1aa] mb-1">Resolution</label>
              <select
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                className="w-full bg-[#121214] border border-[#2e2e34] px-2.5 py-1.5 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="1920x1080">1080p FHD (1920×1080)</option>
                <option value="3840x2160">4K UHD (3840×2160)</option>
                <option value="2560x1440">1440p QHD (2560×1440)</option>
                <option value="1280x720">720p HD (1280×720)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-[#a1a1aa] mb-1">Frame Rate</label>
              <select
                value={frameRate}
                onChange={(e) => setFrameRate(e.target.value)}
                className="w-full bg-[#121214] border border-[#2e2e34] px-2.5 py-1.5 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="23.976">23.976 fps</option>
                <option value="24">24.0 fps (Film)</option>
                <option value="25">25.0 fps (PAL)</option>
                <option value="29.97">29.97 fps (NTSC)</option>
                <option value="30">30.0 fps</option>
                <option value="60">60.0 fps</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs text-[#a1a1aa] mb-1">Working Color Space</label>
            <select
              value={colorSpace}
              onChange={(e) => setColorSpace(e.target.value)}
              className="w-full bg-[#121214] border border-[#2e2e34] px-2.5 py-1.5 rounded text-white focus:outline-none focus:border-blue-500"
            >
              <option value="sRGB / Rec.709">sRGB / Rec.709 (Standard Video)</option>
              <option value="Scene Linear / ACEScg">Scene-Linear / ACEScg (VFX HDR)</option>
            </select>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t border-[#2e2e34] bg-[#222226]">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded bg-[#2e2e34] hover:bg-[#383840] text-xs text-[#f4f4f6]"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white"
          >
            Create Project
          </button>
        </div>
      </div>
    </div>
  );
};
