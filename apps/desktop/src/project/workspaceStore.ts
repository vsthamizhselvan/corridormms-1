import { create } from "zustand";

interface WorkspaceState {
  leftPanelWidth: number;
  rightPanelWidth: number;
  bottomPanelHeight: number;
  showMediaBrowser: boolean;
  showInspector: boolean;
  showTimeline: boolean;
  setLeftPanelWidth: (width: number) => void;
  setRightPanelWidth: (width: number) => void;
  setBottomPanelHeight: (height: number) => void;
  toggleMediaBrowser: () => void;
  toggleInspector: () => void;
  toggleTimeline: () => void;
  resetWorkspace: () => void;
}

const defaultLayout = {
  leftPanelWidth: 300,
  rightPanelWidth: 340,
  bottomPanelHeight: 260,
  showMediaBrowser: true,
  showInspector: true,
  showTimeline: true,
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  ...defaultLayout,

  setLeftPanelWidth: (width) =>
    set({ leftPanelWidth: Math.max(200, Math.min(600, width)) }),

  setRightPanelWidth: (width) =>
    set({ rightPanelWidth: Math.max(240, Math.min(600, width)) }),

  setBottomPanelHeight: (height) =>
    set({ bottomPanelHeight: Math.max(160, Math.min(500, height)) }),

  toggleMediaBrowser: () =>
    set((state) => ({ showMediaBrowser: !state.showMediaBrowser })),

  toggleInspector: () =>
    set((state) => ({ showInspector: !state.showInspector })),

  toggleTimeline: () =>
    set((state) => ({ showTimeline: !state.showTimeline })),

  resetWorkspace: () => set({ ...defaultLayout }),
}));
