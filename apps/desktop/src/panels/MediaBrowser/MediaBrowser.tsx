import React, { useState } from "react";
import {
  Film,
  Plus,
  Search,
  Folder,
  FolderOpen,
  FileVideo,
  Layers,
  Trash2,
  Play,
  ArrowRight,
} from "lucide-react";
import { useMediaStore } from "../../project/mediaStore";
import { useTimelineStore } from "../../project/timelineStore";
import { usePlaybackStore } from "../../project/playbackStore";
import { useProjectStore } from "../../project/projectStore";
import { MediaItem } from "../../types/project";

export const MediaBrowser: React.FC = () => {
  const { media, selectedMediaId, selectMedia, addMedia, removeMedia, searchQuery, setSearchQuery } =
    useMediaStore();
  const { tracks, addClip } = useTimelineStore();
  const { setCurrentFrame, setTotalFrames } = usePlaybackStore();
  const { project } = useProjectStore();

  const [activeTab, setActiveTab] = useState<"project" | "explorer">("project");
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  // Filtered media
  const filteredMedia = media.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Native import dialog or fallback
  const handleImportClick = async () => {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({
        filters: [
          {
            name: "Video & Image Sequences",
            extensions: ["mp4", "mov", "mkv", "avi", "png", "jpg", "jpeg", "exr"],
          },
        ],
        multiple: true,
      });

      if (selected && Array.isArray(selected)) {
        selected.forEach((filePath) => {
          const filename = filePath.split(/[/\\]/).pop() || "media";
          addMedia({
            id: `med_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
            name: filename,
            path: filePath,
            width: project.width,
            height: project.height,
            frameRate: project.frameRate,
            durationFrames: 240,
            durationSeconds: 10,
            codec: filename.endsWith(".mov") ? "Apple ProRes 4444" : "H.264 / AVC",
            fileSizeBytes: 24500000,
          });
        });
      }
    } catch {
      // Browser input fallback
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "video/mp4,video/quicktime,image/png,image/jpeg";
      input.multiple = true;
      input.onchange = (e: any) => {
        const files: FileList = e.target.files;
        if (!files) return;
        Array.from(files).forEach((file) => {
          const objectUrl = URL.createObjectURL(file);
          addMedia({
            id: `med_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
            name: file.name,
            path: objectUrl,
            width: project.width,
            height: project.height,
            frameRate: project.frameRate,
            durationFrames: 240,
            durationSeconds: 10,
            codec: file.type || "video/mp4",
            fileSizeBytes: file.size,
          });
        });
      };
      input.click();
    }
  };

  // Drag and Drop Handler
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      Array.from(e.dataTransfer.files).forEach((file) => {
        const objectUrl = URL.createObjectURL(file);
        addMedia({
          id: `med_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          name: file.name,
          path: objectUrl,
          width: project.width,
          height: project.height,
          frameRate: project.frameRate,
          durationFrames: 240,
          durationSeconds: 10,
          codec: file.type || "video/mp4",
          fileSizeBytes: file.size,
        });
      });
    }
  };

  // Add selected media to Timeline Track V1
  const handleAddToTimeline = (item: MediaItem, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const videoTrack = tracks.find((t) => t.type === "video") || tracks[0];
    if (!videoTrack) return;

    // Find the end frame of existing clips on this track
    const lastEndFrame = videoTrack.clips.reduce(
      (max, c) => Math.max(max, c.endFrame),
      0
    );

    addClip({
      id: `clip_${Date.now()}`,
      mediaId: item.id,
      trackId: videoTrack.id,
      name: item.name,
      startFrame: lastEndFrame,
      endFrame: lastEndFrame + item.durationFrames,
      sourceIn: 0,
      sourceOut: item.durationFrames,
      color: "#0d9488",
    });

    setTotalFrames(Math.max(240, lastEndFrame + item.durationFrames));
  };

  return (
    <div
      className={`h-full flex flex-col bg-[#16161a] border-r border-[#282830] select-none text-xs ${
        isDraggingOver ? "ring-2 ring-blue-500 ring-inset" : ""
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDraggingOver(true);
      }}
      onDragLeave={() => setIsDraggingOver(false)}
      onDrop={handleDrop}
    >
      {/* Panel Tab Header */}
      <div className="h-8 bg-[#1e1e24] border-b border-[#282830] flex items-center justify-between px-2">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab("project")}
            className={`px-3 py-1 font-medium rounded-t text-xs flex items-center gap-1.5 transition-colors ${
              activeTab === "project"
                ? "bg-[#16161a] text-white border-t-2 border-blue-500"
                : "text-[#8a8a96] hover:text-[#d4d4dc]"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Project Media</span>
          </button>
          <button
            onClick={() => setActiveTab("explorer")}
            className={`px-3 py-1 font-medium rounded-t text-xs flex items-center gap-1.5 transition-colors ${
              activeTab === "explorer"
                ? "bg-[#16161a] text-white border-t-2 border-blue-500"
                : "text-[#8a8a96] hover:text-[#d4d4dc]"
            }`}
          >
            <Folder className="w-3.5 h-3.5" />
            <span>Media Browser</span>
          </button>
        </div>

        <button
          onClick={handleImportClick}
          className="p-1 rounded bg-blue-600/80 hover:bg-blue-600 text-white flex items-center gap-1 px-2 text-[11px] font-medium"
          title="Import Media (Cmd+I)"
        >
          <Plus className="w-3 h-3" />
          <span>Import</span>
        </button>
      </div>

      {/* Search & Stats Bar */}
      <div className="p-2 border-b border-[#24242c] bg-[#141418] flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 absolute left-2 top-2 text-[#70707c]" />
          <input
            type="text"
            placeholder="Search clips..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#1c1c22] border border-[#282832] rounded pl-7 pr-2 py-1 text-white placeholder-[#70707c] text-xs focus:outline-none focus:border-blue-500"
          />
        </div>
        <span className="text-[10px] text-[#70707c] whitespace-nowrap">
          {filteredMedia.length} item{filteredMedia.length === 1 ? "" : "s"}
        </span>
      </div>

      {/* Media List / Drop Zone */}
      <div className="flex-1 overflow-y-auto p-1.5 space-y-1">
        {filteredMedia.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#70707c]">
            <Film className="w-10 h-10 mb-2 stroke-[1.2] opacity-40" />
            <p className="font-medium text-[#90909c] text-xs">No media imported</p>
            <p className="text-[11px] mt-1 text-[#60606c]">
              Drag and drop MP4, MOV, PNG or EXR plates here, or click Import.
            </p>
            <button
              onClick={handleImportClick}
              className="mt-3 px-3 py-1.5 rounded bg-[#202028] hover:bg-[#282834] border border-[#30303c] text-white text-xs font-medium flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5 text-blue-400" />
              <span>Import Footage</span>
            </button>
          </div>
        ) : (
          filteredMedia.map((item) => {
            const isSelected = selectedMediaId === item.id;
            return (
              <div
                key={item.id}
                onClick={() => {
                  selectMedia(item.id);
                  setTotalFrames(item.durationFrames);
                }}
                onDoubleClick={() => handleAddToTimeline(item)}
                className={`group p-2 rounded border cursor-pointer transition-all flex items-center gap-2.5 ${
                  isSelected
                    ? "bg-[#22222c] border-blue-500 text-white shadow-sm"
                    : "bg-[#18181e] border-[#22222a] text-[#c4c4cc] hover:bg-[#1e1e26] hover:border-[#30303c]"
                }`}
              >
                {/* Thumbnail Icon */}
                <div className="w-10 h-7 rounded bg-[#101014] border border-[#282832] flex items-center justify-center shrink-0 text-[#606070] group-hover:text-blue-400">
                  <FileVideo className="w-4 h-4" />
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate text-xs text-white" title={item.name}>
                    {item.name}
                  </div>
                  <div className="text-[10px] text-[#787886] flex items-center gap-2 mt-0.5">
                    <span>{item.width}×{item.height}</span>
                    <span>•</span>
                    <span>{item.frameRate} fps</span>
                    <span>•</span>
                    <span>{item.durationFrames}f</span>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleAddToTimeline(item, e)}
                    title="Insert to Timeline"
                    className="p-1 rounded bg-[#2a2a36] hover:bg-blue-600 text-white"
                  >
                    <ArrowRight className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeMedia(item.id);
                    }}
                    title="Remove from Project"
                    className="p-1 rounded bg-[#2a2a36] hover:bg-red-600 text-white"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="h-6 px-3 bg-[#141418] border-t border-[#24242c] flex items-center justify-between text-[10px] text-[#70707c]">
        <span>CorridorKey Media Pool</span>
        <span>Drag clip to timeline</span>
      </div>
    </div>
  );
};
