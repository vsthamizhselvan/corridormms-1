import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Folder,
  FolderOpen,
  Save,
  Download,
  Film,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  HelpCircle,
  Settings,
  Sparkles,
  Layout,
  Sliders,
  Check,
  History,
  AlertTriangle,
  Clock,
  RotateCcw,
} from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { useProjectStore } from "../project/projectStore";
import { useMediaStore } from "../project/mediaStore";
import { usePlaybackStore } from "../project/playbackStore";
import { useWorkspaceStore } from "../project/workspaceStore";
import { useInspectorStore } from "../project/inspectorStore";
import { useTimelineStore } from "../project/timelineStore";
import { useViewerStore } from "../stores/viewerStore";
import { useExportStore } from "../stores/exportStore";
import { useVFXStore } from "../stores/vfxStore";
import { NewProjectModal } from "./NewProjectModal";
import { AboutModal } from "./AboutModal";
import { MissingMediaModal } from "./MissingMediaModal";
import { RecoveryModal } from "./RecoveryModal";
import { FirstRunWizard } from "./setup/FirstRunWizard";
import { DiagnosticsModal } from "./DiagnosticsModal";
import { MediaItem, AutosaveSnapshot, RecoveryStatus } from "../types/project";

export const TopMenu: React.FC = () => {
  const {
    project,
    projectFilePath,
    setProject,
    setFilePath,
    isDirty,
    markDirty,
    recentProjects,
    resetProject,
    autosaveEnabled,
    autosaveIntervalMinutes,
    maxAutosaves,
  } = useProjectStore();

  const { media, addMedia, setAllMedia, updateMediaPath } = useMediaStore();
  const { isPlaying, togglePlay, stepFrame, setCurrentFrame, totalFrames } =
    usePlaybackStore();
  const {
    showMediaBrowser,
    showInspector,
    showTimeline,
    leftPanelWidth,
    rightPanelWidth,
    bottomPanelHeight,
    toggleMediaBrowser,
    toggleInspector,
    toggleTimeline,
    resetWorkspace,
  } = useWorkspaceStore();
  const { tracks, setTracks, zoomRatio, setZoomRatio } = useTimelineStore();
  const { keying, matte, transform } = useInspectorStore();
  const viewerStore = useViewerStore();
  const exportStore = useExportStore();
  const vfxStore = useVFXStore();

  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [isSetupWizardOpen, setIsSetupWizardOpen] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);

  // Check if first-run setup wizard has completed
  useEffect(() => {
    invoke<boolean>("check_first_run_completed")
      .then((completed) => {
        if (!completed) {
          setIsSetupWizardOpen(true);
        }
      })
      .catch(() => {
        // In browser mock mode, keep closed by default
      });
  }, []);

  // Missing media & recovery dialog states
  const [missingMediaList, setMissingMediaList] = useState<MediaItem[]>([]);
  const [isMissingMediaOpen, setIsMissingMediaOpen] = useState(false);

  const [recoverySnapshots, setRecoverySnapshots] = useState<AutosaveSnapshot[]>([]);
  const [isRecoveryOpen, setIsRecoveryOpen] = useState(false);
  const [pendingOpenPath, setPendingOpenPath] = useState<string | null>(null);

  // Helper to serialize current state to .ckproj format
  const serializeCurrentProject = useCallback(() => {
    return JSON.stringify(
      {
        format: "corridorkey-project",
        schema_version: "1.1.0",
        generator: "CorridorKey 2.0 Desktop",
        project: {
          ...project,
          modified_at: new Date().toISOString(),
        },
        media_pool: media,
        timeline: {
          duration_frames: totalFrames,
          current_frame: 0,
          tracks,
        },
        settings: {
          keying,
          matte,
          viewer: {
            display_mode: viewerStore.displayMode,
            background_type: viewerStore.backgroundType,
            background_color: viewerStore.backgroundColor,
            gradient_color_a: viewerStore.gradientColorA,
            gradient_color_b: viewerStore.gradientColorB,
            alpha_mode: viewerStore.alphaMode,
            exposure: viewerStore.exposure,
            saturation: viewerStore.saturation,
          },
          export: {
            format: exportStore.settings.format,
            colorSpace: exportStore.settings.colorSpace,
          },
        },
        vfx: {
          masks: vfxStore.masks,
          matte_refine: vfxStore.matteRefine,
          color_grade: vfxStore.colorGrade,
          effects: vfxStore.effects,
          layers: vfxStore.layers,
          node_graph: {
            nodes: vfxStore.nodes,
            connections: vfxStore.connections,
          },
        },
        workspace: {
          left_panel_width: leftPanelWidth,
          right_panel_width: rightPanelWidth,
          bottom_panel_height: bottomPanelHeight,
          show_media_browser: showMediaBrowser,
          show_inspector: showInspector,
          show_timeline: showTimeline,
          zoom_ratio: zoomRatio,
        },
      },
      null,
      2
    );
  }, [
    bottomPanelHeight,
    exportStore.settings.colorSpace,
    exportStore.settings.format,
    keying,
    leftPanelWidth,
    matte,
    media,
    project,
    rightPanelWidth,
    showInspector,
    showMediaBrowser,
    showTimeline,
    totalFrames,
    tracks,
    viewerStore.alphaMode,
    viewerStore.backgroundColor,
    viewerStore.backgroundType,
    viewerStore.displayMode,
    viewerStore.exposure,
    viewerStore.gradientColorA,
    viewerStore.gradientColorB,
    viewerStore.saturation,
    vfxStore.colorGrade,
    vfxStore.connections,
    vfxStore.effects,
    vfxStore.layers,
    vfxStore.masks,
    vfxStore.matteRefine,
    vfxStore.nodes,
    zoomRatio,
  ]);

  // Check missing media on loaded project data
  const checkMediaPresence = async (loadedMedia: MediaItem[]) => {
    const missing: MediaItem[] = [];
    for (const m of loadedMedia) {
      if (!m.path) continue;
      // In web fallback, skip path check
      try {
        const exists = await invoke<boolean>("check_file_exists", { path: m.path });
        if (!exists) {
          missing.push(m);
        }
      } catch {
        // If Tauri not available, ignore
      }
    }
    if (missing.length > 0) {
      setMissingMediaList(missing);
      setIsMissingMediaOpen(true);
    }
  };

  // Load project content into Zustand stores
  const loadProjectData = (data: any, filePath: string | null) => {
    if (data.project) {
      setProject(data.project, filePath);
    }
    const mediaPool = data.media_pool || data.media || [];
    setAllMedia(mediaPool);

    if (data.timeline?.tracks) {
      setTracks(data.timeline.tracks);
    }

    if (data.workspace?.zoom_ratio) {
      setZoomRatio(data.workspace.zoom_ratio);
    }

    if (data.vfx) {
      vfxStore.loadVFXData(data.vfx);
    }

    // Check if media is missing
    checkMediaPresence(mediaPool);
  };

  // Open Project File from disk
  const openProjectFile = async (filePath: string) => {
    try {
      // First check if recovery snapshot exists that is newer
      try {
        const recStatus = await invoke<RecoveryStatus>("check_project_recovery", {
          projectPath: filePath,
        });
        if (recStatus.recovery_available && recStatus.snapshot_count > 0) {
          const snapshots = await invoke<AutosaveSnapshot[]>("list_project_autosaves", {
            projectPath: filePath,
          });
          setRecoverySnapshots(snapshots);
          setPendingOpenPath(filePath);
          setIsRecoveryOpen(true);
          return;
        }
      } catch (err) {
        console.warn("Could not check recovery status:", err);
      }

      // Read directly
      const content = await invoke<string>("read_project_file", { path: filePath });
      const data = JSON.parse(content);
      loadProjectData(data, filePath);
    } catch (e) {
      console.error("Failed to open project file:", e);
    }
  };

  // Native Picker for Open Project
  const handleOpenProject = async () => {
    setActiveMenu(null);
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({
        filters: [{ name: "CorridorKey Project", extensions: ["ckproj", "json"] }],
        multiple: false,
      });

      if (selected && typeof selected === "string") {
        await openProjectFile(selected);
      }
    } catch {
      // Fallback for browser
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".ckproj,.json";
      input.onchange = (e: any) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
          try {
            const data = JSON.parse(ev.target?.result as string);
            loadProjectData(data, file.name);
          } catch (err) {
            console.error("Failed to parse project file:", err);
          }
        };
        reader.readAsText(file);
      };
      input.click();
    }
  };

  // Save Project (Atomic)
  const handleSaveProject = async () => {
    setActiveMenu(null);
    const jsonString = serializeCurrentProject();

    try {
      let targetPath = projectFilePath;
      if (!targetPath) {
        const { save } = await import("@tauri-apps/plugin-dialog");
        targetPath = (await save({
          defaultPath: `${project.name.toLowerCase().replace(/\s+/g, "_")}.ckproj`,
          filters: [{ name: "CorridorKey Project", extensions: ["ckproj"] }],
        })) as string | null;
      }

      if (targetPath) {
        // Atomic save via native Tauri command
        await invoke("save_project_atomic", { path: targetPath, content: jsonString });
        setFilePath(targetPath);
        markDirty(false);
      }
    } catch {
      // Browser fallback download
      const blob = new Blob([jsonString], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${project.name.toLowerCase().replace(/\s+/g, "_")}.ckproj`;
      a.click();
      URL.revokeObjectURL(url);
      markDirty(false);
    }
  };

  // Save Project As
  const handleSaveProjectAs = async () => {
    setActiveMenu(null);
    const jsonString = serializeCurrentProject();

    try {
      const { save } = await import("@tauri-apps/plugin-dialog");
      const targetPath = (await save({
        defaultPath: `${project.name.toLowerCase().replace(/\s+/g, "_")}_copy.ckproj`,
        filters: [{ name: "CorridorKey Project", extensions: ["ckproj"] }],
      })) as string | null;

      if (targetPath) {
        await invoke("save_project_atomic", { path: targetPath, content: jsonString });
        setFilePath(targetPath);
        markDirty(false);
      }
    } catch {
      // Browser fallback
      const blob = new Blob([jsonString], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${project.name.toLowerCase().replace(/\s+/g, "_")}_copy.ckproj`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  // Manual Backup Snapshot
  const handleBackupProject = async () => {
    setActiveMenu(null);
    if (!projectFilePath) {
      await handleSaveProject();
      return;
    }

    try {
      const jsonString = serializeCurrentProject();
      const backupPath = await invoke<string>("create_project_backup", {
        projectPath: projectFilePath,
        content: jsonString,
      });
      console.log("Created backup snapshot at:", backupPath);
    } catch (e) {
      console.error("Backup failed:", e);
    }
  };

  // Close Project
  const handleCloseProject = () => {
    setActiveMenu(null);
    if (isDirty) {
      const confirmClose = window.confirm("You have unsaved changes. Discard and close?");
      if (!confirmClose) return;
    }
    resetProject();
    setAllMedia([]);
    setTracks([]);
    vfxStore.resetVFX();
  };

  // Background Periodic Autosave
  useEffect(() => {
    if (!autosaveEnabled || !projectFilePath) return;

    const intervalMs = Math.max(1, autosaveIntervalMinutes) * 60 * 1000;
    const timer = setInterval(async () => {
      if (!isDirty || !projectFilePath) return;

      try {
        const jsonString = serializeCurrentProject();
        // Determine autosave directory next to project file
        const p = projectFilePath;
        const lastSlash = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\"));
        const parentDir = lastSlash > 0 ? p.substring(0, lastSlash) : ".";
        const fileStem = p.substring(lastSlash + 1).replace(/\.ckproj$/i, "");
        const timestamp = new Date().toISOString().replace(/[-:T.]/g, "_").slice(0, 19);
        const autosavePath = `${parentDir}/.ck_autosaves/${fileStem}_autosave_${timestamp}.ckproj`;

        await invoke("save_project_atomic", { path: autosavePath, content: jsonString });
        console.log("Autosave completed at:", autosavePath);
      } catch (err) {
        console.warn("Autosave failed:", err);
      }
    }, intervalMs);

    return () => clearInterval(timer);
  }, [autosaveEnabled, autosaveIntervalMinutes, isDirty, projectFilePath, serializeCurrentProject]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        if (e.shiftKey) {
          handleSaveProjectAs();
        } else {
          handleSaveProject();
        }
      } else if ((e.metaKey || e.ctrlKey) && e.key === "o") {
        e.preventDefault();
        handleOpenProject();
      } else if ((e.metaKey || e.ctrlKey) && e.key === "n") {
        e.preventDefault();
        setIsNewProjectOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSaveProject, handleSaveProjectAs, handleOpenProject]);

  // Import Media
  const handleImportMedia = async () => {
    setActiveMenu(null);
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({
        multiple: true,
        filters: [{ name: "Video Files", extensions: ["mp4", "mov", "avi", "mkv", "webm", "png", "exr"] }],
      });

      if (selected) {
        const paths = Array.isArray(selected) ? selected : [selected];
        for (const filePath of paths) {
          try {
            const meta = await invoke<any>("probe_media_file", { path: filePath });
            const fileName = filePath.split(/[/\\]/).pop() || "Video";
            addMedia({
              id: `med_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
              name: fileName,
              path: filePath,
              width: meta.width,
              height: meta.height,
              frameRate: meta.frame_rate,
              durationFrames: meta.duration_frames,
              durationSeconds: meta.duration_seconds,
              codec: meta.codec,
              fileSizeBytes: meta.file_size_bytes,
            });
          } catch {
            const fileName = filePath.split(/[/\\]/).pop() || "Video";
            addMedia({
              id: `med_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
              name: fileName,
              path: filePath,
              width: project.width,
              height: project.height,
              frameRate: project.frameRate,
              durationFrames: 240,
              durationSeconds: 10,
              codec: "H.264",
              fileSizeBytes: 0,
            });
          }
        }
      }
    } catch {
      // Browser fallback
      const input = document.createElement("input");
      input.type = "file";
      input.multiple = true;
      input.accept = "video/*,image/*";
      input.onchange = (e: any) => {
        const files: File[] = Array.from(e.target.files || []);
        files.forEach((file) => {
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

  return (
    <>
      <div className="h-9 bg-[#1a1a1e] border-b border-[#2c2c32] flex items-center justify-between px-3 text-xs select-none z-40">
        {/* Left: App Logo & Menu Items */}
        <div className="flex items-center gap-1">
          {/* Logo */}
          <div className="flex items-center gap-1.5 pr-3 border-r border-[#2c2c32] mr-1">
            <div className="w-5 h-5 rounded bg-blue-600 flex items-center justify-center font-black text-[10px] text-white">
              CK
            </div>
            <span className="font-semibold text-white tracking-wide">CorridorKey</span>
            <span className="text-[10px] text-blue-400 font-mono">2.0</span>
          </div>

          {/* Menus */}
          <div className="flex items-center">
            {/* FILE */}
            <div className="relative">
              <button
                onClick={() => setActiveMenu(activeMenu === "file" ? null : "file")}
                className={`px-2.5 py-1 rounded hover:bg-[#2c2c32] ${
                  activeMenu === "file" ? "bg-[#2c2c32] text-white" : "text-[#d4d4d8]"
                }`}
              >
                File
              </button>
              {activeMenu === "file" && (
                <div className="absolute left-0 top-full mt-0.5 w-52 bg-[#1e1e22] border border-[#2c2c32] rounded shadow-xl py-1 z-50">
                  <button
                    onClick={() => {
                      setActiveMenu(null);
                      setIsNewProjectOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>New Project</span>
                    <span className="text-[10px] text-[#71717a]">⌘N</span>
                  </button>
                  <button
                    onClick={handleOpenProject}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Open Project...</span>
                    <span className="text-[10px] text-[#71717a]">⌘O</span>
                  </button>

                  {/* Recent Projects Submenu */}
                  {recentProjects.length > 0 && (
                    <div className="py-0.5">
                      <div className="px-3 py-1 text-[10px] uppercase font-semibold text-[#606070]">
                        Recent Projects
                      </div>
                      {recentProjects.slice(0, 5).map((p) => (
                        <button
                          key={p}
                          onClick={() => {
                            setActiveMenu(null);
                            openProjectFile(p);
                          }}
                          className="w-full text-left px-3 py-1 hover:bg-[#2c2c36] hover:text-white text-[11px] truncate text-slate-300 block"
                          title={p}
                        >
                          {p.split(/[/\\]/).pop()}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="h-px bg-[#2c2c32] my-1" />
                  <button
                    onClick={handleSaveProject}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Save Project</span>
                    <span className="text-[10px] text-[#71717a]">⌘S</span>
                  </button>
                  <button
                    onClick={handleSaveProjectAs}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Save As...</span>
                    <span className="text-[10px] text-[#71717a]">⇧⌘S</span>
                  </button>
                  <button
                    onClick={handleBackupProject}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Backup Snapshot</span>
                    <span className="text-[10px] text-[#71717a]">Backup</span>
                  </button>

                  <div className="h-px bg-[#2c2c32] my-1" />
                  <button
                    onClick={handleImportMedia}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Import Media...</span>
                    <span className="text-[10px] text-[#71717a]">⌘I</span>
                  </button>

                  <div className="h-px bg-[#2c2c32] my-1" />
                  <button
                    onClick={handleCloseProject}
                    className="w-full text-left px-3 py-1.5 hover:bg-red-600 hover:text-white flex items-center justify-between text-red-400"
                  >
                    <span>Close Project</span>
                  </button>
                </div>
              )}
            </div>

            {/* EDIT */}
            <div className="relative">
              <button
                onClick={() => setActiveMenu(activeMenu === "edit" ? null : "edit")}
                className={`px-2.5 py-1 rounded hover:bg-[#2c2c32] ${
                  activeMenu === "edit" ? "bg-[#2c2c32] text-white" : "text-[#d4d4d8]"
                }`}
              >
                Edit
              </button>
              {activeMenu === "edit" && (
                <div className="absolute left-0 top-full mt-0.5 w-44 bg-[#1e1e22] border border-[#2c2c32] rounded shadow-xl py-1 z-50">
                  <button
                    onClick={() => setActiveMenu(null)}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Undo</span>
                    <span className="text-[10px] text-[#71717a]">⌘Z</span>
                  </button>
                  <button
                    onClick={() => setActiveMenu(null)}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Redo</span>
                    <span className="text-[10px] text-[#71717a]">⇧⌘Z</span>
                  </button>
                  <div className="h-px bg-[#2c2c32] my-1" />
                  <button
                    onClick={() => setActiveMenu(null)}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Preferences...</span>
                    <span className="text-[10px] text-[#71717a]">⌘,</span>
                  </button>
                </div>
              )}
            </div>

            {/* VIEW */}
            <div className="relative">
              <button
                onClick={() => setActiveMenu(activeMenu === "view" ? null : "view")}
                className={`px-2.5 py-1 rounded hover:bg-[#2c2c32] ${
                  activeMenu === "view" ? "bg-[#2c2c32] text-white" : "text-[#d4d4d8]"
                }`}
              >
                View
              </button>
              {activeMenu === "view" && (
                <div className="absolute left-0 top-full mt-0.5 w-48 bg-[#1e1e22] border border-[#2c2c32] rounded shadow-xl py-1 z-50">
                  <button
                    onClick={() => {
                      toggleMediaBrowser();
                      setActiveMenu(null);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Media Browser</span>
                    {showMediaBrowser && <Check className="w-3.5 h-3.5 text-blue-400" />}
                  </button>
                  <button
                    onClick={() => {
                      toggleInspector();
                      setActiveMenu(null);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Inspector Panel</span>
                    {showInspector && <Check className="w-3.5 h-3.5 text-blue-400" />}
                  </button>
                  <button
                    onClick={() => {
                      toggleTimeline();
                      setActiveMenu(null);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Timeline Panel</span>
                    {showTimeline && <Check className="w-3.5 h-3.5 text-blue-400" />}
                  </button>
                  <div className="h-px bg-[#2c2c32] my-1" />
                  <button
                    onClick={() => {
                      resetWorkspace();
                      setActiveMenu(null);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white"
                  >
                    Reset Layout
                  </button>
                </div>
              )}
            </div>

            {/* HELP */}
            <div className="relative">
              <button
                onClick={() => setActiveMenu(activeMenu === "help" ? null : "help")}
                className={`px-2.5 py-1 rounded hover:bg-[#2c2c32] ${
                  activeMenu === "help" ? "bg-[#2c2c32] text-white" : "text-[#d4d4d8]"
                }`}
              >
                Help
              </button>
              {activeMenu === "help" && (
                <div className="absolute left-0 top-full mt-0.5 w-56 bg-[#1e1e22] border border-[#2c2c32] rounded shadow-xl py-1 z-50">
                  <button
                    onClick={() => {
                      setActiveMenu(null);
                      setIsSetupWizardOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>Initial Setup Wizard...</span>
                  </button>
                  <button
                    onClick={() => {
                      setActiveMenu(null);
                      setIsDiagnosticsOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between"
                  >
                    <span>System Diagnostics & Logs...</span>
                  </button>
                  <div className="h-px bg-[#2c2c32] my-1" />
                  <button
                    onClick={() => {
                      setActiveMenu(null);
                      setIsAboutOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white"
                  >
                    About CorridorKey
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Center: Current Project & Status */}
        <div className="flex items-center gap-2">
          <span className="font-medium text-white">{project.name}</span>
          {isDirty && (
            <span
              title="Unsaved changes"
              className="w-2 h-2 rounded-full bg-amber-400 inline-block shadow-sm"
            />
          )}
          <span className="text-[10px] text-[#71717a] border-l border-[#2c2c32] pl-2 font-mono">
            {project.width}x{project.height} @ {project.frameRate}fps ({project.colorSpace})
          </span>
        </div>

        {/* Right: Autosave Status & Project Path */}
        <div className="flex items-center gap-3 text-[11px] text-[#71717a]">
          {autosaveEnabled && (
            <span
              className="flex items-center gap-1 text-[10px] text-teal-400/80 bg-teal-950/30 px-2 py-0.5 rounded border border-teal-500/20"
              title={`Autosave every ${autosaveIntervalMinutes} mins`}
            >
              <Clock className="w-3 h-3" />
              <span>Autosave On</span>
            </span>
          )}
          <span className="truncate max-w-[200px]" title={projectFilePath || "Unsaved project"}>
            {projectFilePath ? projectFilePath.split(/[/\\]/).pop() : "Unsaved Project"}
          </span>
        </div>
      </div>

      {/* Modals */}
      <NewProjectModal
        isOpen={isNewProjectOpen}
        onClose={() => setIsNewProjectOpen(false)}
      />

      <AboutModal
        isOpen={isAboutOpen}
        onClose={() => setIsAboutOpen(false)}
      />

      <MissingMediaModal
        isOpen={isMissingMediaOpen}
        missingMedia={missingMediaList}
        onRelinkSingle={(mediaId, newPath) => {
          updateMediaPath(mediaId, newPath);
          setMissingMediaList((prev) => prev.filter((m) => m.id !== mediaId));
          if (missingMediaList.length <= 1) {
            setIsMissingMediaOpen(false);
          }
        }}
        onRelinkFolder={async (folderPath) => {
          // Relink matching filenames in folder
          let relinked = 0;
          for (const m of missingMediaList) {
            const fileName = m.name || m.path.split(/[/\\]/).pop() || "";
            const candidate = `${folderPath}/${fileName}`;
            try {
              const exists = await invoke<boolean>("check_file_exists", { path: candidate });
              if (exists) {
                updateMediaPath(m.id, candidate);
                relinked++;
              }
            } catch {}
          }
          if (relinked > 0) {
            setIsMissingMediaOpen(false);
          }
        }}
        onClose={() => setIsMissingMediaOpen(false)}
      />

      <RecoveryModal
        isOpen={isRecoveryOpen}
        projectName={project.name}
        projectFilePath={pendingOpenPath || projectFilePath || ""}
        snapshots={recoverySnapshots}
        onRecoverSnapshot={async (snapshotPath) => {
          setIsRecoveryOpen(false);
          try {
            const content = await invoke<string>("read_project_file", { path: snapshotPath });
            const data = JSON.parse(content);
            loadProjectData(data, pendingOpenPath);
            markDirty(true);
          } catch (e) {
            console.error("Failed to recover snapshot:", e);
          }
        }}
        onOpenSavedVersion={async () => {
          setIsRecoveryOpen(false);
          if (pendingOpenPath) {
            try {
              const content = await invoke<string>("read_project_file", { path: pendingOpenPath });
              const data = JSON.parse(content);
              loadProjectData(data, pendingOpenPath);
            } catch (e) {
              console.error("Failed to open saved project:", e);
            }
          }
        }}
        onDismiss={() => setIsRecoveryOpen(false)}
      />

      <FirstRunWizard
        isOpen={isSetupWizardOpen}
        onComplete={() => setIsSetupWizardOpen(false)}
        onDismiss={() => setIsSetupWizardOpen(false)}
      />

      <DiagnosticsModal
        isOpen={isDiagnosticsOpen}
        onClose={() => setIsDiagnosticsOpen(false)}
      />
    </>
  );
};
