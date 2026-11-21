import { create } from "zustand";
import { ProjectMetadata } from "../types/project";

interface ProjectState {
  project: ProjectMetadata;
  projectFilePath: string | null;
  isDirty: boolean;
  recentProjects: string[];
  autosaveEnabled: boolean;
  autosaveIntervalMinutes: number;
  maxAutosaves: number;

  setProject: (metadata: ProjectMetadata, filePath?: string | null) => void;
  updateMetadata: (partial: Partial<ProjectMetadata>) => void;
  setFilePath: (path: string | null) => void;
  markDirty: (dirty?: boolean) => void;
  addRecentProject: (path: string) => void;
  setAutosaveSettings: (enabled: boolean, intervalMinutes?: number, maxAutosaves?: number) => void;
  resetProject: () => void;
}

const defaultProjectMetadata: ProjectMetadata = {
  name: "Untitled Project",
  width: 1920,
  height: 1080,
  frameRate: 24.0,
  colorSpace: "Rec.709",
  createdAt: new Date().toISOString(),
  modifiedAt: new Date().toISOString(),
};

// Load recent projects from localStorage if available
function loadRecentProjects(): string[] {
  try {
    const raw = localStorage.getItem("ck_recent_projects");
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRecentProjects(paths: string[]) {
  try {
    localStorage.setItem("ck_recent_projects", JSON.stringify(paths));
  } catch {
    // Ignore storage errors
  }
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  project: { ...defaultProjectMetadata },
  projectFilePath: null,
  isDirty: false,
  recentProjects: loadRecentProjects(),
  autosaveEnabled: true,
  autosaveIntervalMinutes: 3,
  maxAutosaves: 5,

  setProject: (metadata, filePath = null) => {
    set({
      project: metadata,
      projectFilePath: filePath,
      isDirty: false,
    });
    if (filePath) {
      get().addRecentProject(filePath);
    }
  },

  updateMetadata: (partial) =>
    set((state) => ({
      project: {
        ...state.project,
        ...partial,
        modifiedAt: new Date().toISOString(),
      },
      isDirty: true,
    })),

  setFilePath: (path) => {
    set({ projectFilePath: path });
    if (path) {
      get().addRecentProject(path);
    }
  },

  markDirty: (dirty = true) => set({ isDirty: dirty }),

  addRecentProject: (path) => {
    const filtered = get().recentProjects.filter((p) => p !== path);
    const updated = [path, ...filtered].slice(0, 10);
    saveRecentProjects(updated);
    set({ recentProjects: updated });
  },

  setAutosaveSettings: (enabled, intervalMinutes, maxAutosaves) =>
    set((state) => ({
      autosaveEnabled: enabled,
      autosaveIntervalMinutes: intervalMinutes ?? state.autosaveIntervalMinutes,
      maxAutosaves: maxAutosaves ?? state.maxAutosaves,
    })),

  resetProject: () =>
    set({
      project: { ...defaultProjectMetadata, createdAt: new Date().toISOString() },
      projectFilePath: null,
      isDirty: false,
    }),
}));
