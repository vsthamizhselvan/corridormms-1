import { create } from "zustand";
import { Track, Clip } from "../types/project";

export type TimelineTool = "select" | "razor";

interface TimelineSnapshot {
  tracks: Track[];
  durationFrames: number;
  selectedClipId: string | null;
}

interface TimelineState {
  tracks: Track[];
  selectedClipId: string | null;
  durationFrames: number;
  zoomRatio: number; // pixels per frame (e.g. 1.0 = 1 frame is 1px)
  activeTool: TimelineTool;
  snappingEnabled: boolean;

  // History
  undoStack: TimelineSnapshot[];
  redoStack: TimelineSnapshot[];
  canUndo: boolean;
  canRedo: boolean;

  // Track operations
  setTracks: (tracks: Track[]) => void;
  addTrack: (type: "video" | "audio", name?: string) => void;
  deleteTrack: (trackId: string) => void;
  reorderTrack: (trackId: string, direction: "up" | "down") => void;
  toggleTrackVisibility: (trackId: string) => void;
  toggleTrackLock: (trackId: string) => void;
  toggleTrackMute: (trackId: string) => void;
  toggleTrackSolo: (trackId: string) => void;

  // Clip operations
  addClip: (clip: Clip) => void;
  selectClip: (clipId: string | null) => void;
  moveClip: (clipId: string, targetTrackId: string, newStartFrame: number) => boolean;
  trimClipIn: (clipId: string, newStartFrame: number) => boolean;
  trimClipOut: (clipId: string, newEndFrame: number) => boolean;
  splitClip: (clipId: string, splitFrame: number) => boolean;
  splitClipAtPlayhead: (currentFrame: number) => boolean;
  deleteClip: (clipId: string) => void;
  rippleDeleteClip: (clipId: string) => void;
  duplicateClip: (clipId: string) => void;

  // Tool & view operations
  setActiveTool: (tool: TimelineTool) => void;
  toggleSnapping: () => void;
  setZoomRatio: (zoom: number) => void;
  setDurationFrames: (duration: number) => void;
  findSnapTarget: (frame: number, tolerance?: number) => number | null;

  // Undo / Redo
  undo: () => void;
  redo: () => void;
}

const defaultTracks: Track[] = [
  {
    id: "track_v2",
    type: "video",
    name: "Video 2",
    visible: true,
    locked: false,
    muted: false,
    solo: false,
    clips: [],
  },
  {
    id: "track_v1",
    type: "video",
    name: "Video 1",
    visible: true,
    locked: false,
    muted: false,
    solo: false,
    clips: [],
  },
  {
    id: "track_a1",
    type: "audio",
    name: "Audio 1",
    visible: true,
    locked: false,
    muted: false,
    solo: false,
    clips: [],
  },
];

const MAX_HISTORY = 50;

function createSnapshot(state: { tracks: Track[]; durationFrames: number; selectedClipId: string | null }): TimelineSnapshot {
  return {
    tracks: JSON.parse(JSON.stringify(state.tracks)),
    durationFrames: state.durationFrames,
    selectedClipId: state.selectedClipId,
  };
}

export const useTimelineStore = create<TimelineState>((set, get) => ({
  tracks: defaultTracks,
  selectedClipId: null,
  durationFrames: 240,
  zoomRatio: 1.5,
  activeTool: "select",
  snappingEnabled: true,
  undoStack: [],
  redoStack: [],
  canUndo: false,
  canRedo: false,

  setTracks: (tracks) => set({ tracks }),

  addTrack: (type, customName) => {
    const state = get();
    const snap = createSnapshot(state);
    const existingTypeTracks = state.tracks.filter((t) => t.type === type);
    const count = existingTypeTracks.length + 1;
    const name = customName || (type === "video" ? `Video ${count}` : `Audio ${count}`);
    const newTrack: Track = {
      id: `track_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      type,
      name,
      visible: true,
      locked: false,
      muted: false,
      solo: false,
      clips: [],
    };

    set({
      tracks: type === "video" ? [newTrack, ...state.tracks] : [...state.tracks, newTrack],
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  deleteTrack: (trackId) => {
    const state = get();
    if (state.tracks.length <= 1) return;
    const snap = createSnapshot(state);

    set({
      tracks: state.tracks.filter((t) => t.id !== trackId),
      selectedClipId: null,
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  reorderTrack: (trackId, direction) => {
    const state = get();
    const index = state.tracks.findIndex((t) => t.id === trackId);
    if (index === -1) return;
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= state.tracks.length) return;

    const snap = createSnapshot(state);
    const newTracks = [...state.tracks];
    const [moved] = newTracks.splice(index, 1);
    newTracks.splice(targetIndex, 0, moved);

    set({
      tracks: newTracks,
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  toggleTrackVisibility: (trackId) =>
    set((state) => ({
      tracks: state.tracks.map((t) =>
        t.id === trackId ? { ...t, visible: !t.visible } : t
      ),
    })),

  toggleTrackLock: (trackId) =>
    set((state) => ({
      tracks: state.tracks.map((t) =>
        t.id === trackId ? { ...t, locked: !t.locked } : t
      ),
    })),

  toggleTrackMute: (trackId) =>
    set((state) => ({
      tracks: state.tracks.map((t) =>
        t.id === trackId ? { ...t, muted: !t.muted } : t
      ),
    })),

  toggleTrackSolo: (trackId) =>
    set((state) => ({
      tracks: state.tracks.map((t) =>
        t.id === trackId ? { ...t, solo: !t.solo } : t
      ),
    })),

  addClip: (clip) => {
    const state = get();
    const snap = createSnapshot(state);

    set({
      tracks: state.tracks.map((t) =>
        t.id === clip.trackId ? { ...t, clips: [...t.clips, clip] } : t
      ),
      selectedClipId: clip.id,
      durationFrames: Math.max(state.durationFrames, clip.endFrame),
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  selectClip: (clipId) => set({ selectedClipId: clipId }),

  moveClip: (clipId, targetTrackId, newStartFrame) => {
    const state = get();
    if (newStartFrame < 0) return false;

    // Find the clip
    let sourceTrack: Track | null = null;
    let clip: Clip | null = null;
    for (const t of state.tracks) {
      const found = t.clips.find((c) => c.id === clipId);
      if (found) {
        sourceTrack = t;
        clip = found;
        break;
      }
    }
    if (!sourceTrack || !clip) return false;

    const targetTrack = state.tracks.find((t) => t.id === targetTrackId);
    if (!targetTrack || targetTrack.locked) return false;

    // Type compatibility: video only on video track, audio only on audio track
    if (sourceTrack.type !== targetTrack.type) return false;

    const duration = clip.endFrame - clip.startFrame;
    const newEndFrame = newStartFrame + duration;

    // Collision check
    for (const other of targetTrack.clips) {
      if (other.id === clipId) continue;
      if (Math.max(newStartFrame, other.startFrame) < Math.min(newEndFrame, other.endFrame)) {
        return false; // Collision detected
      }
    }

    const snap = createSnapshot(state);

    const updatedClip: Clip = {
      ...clip,
      trackId: targetTrackId,
      startFrame: newStartFrame,
      endFrame: newEndFrame,
    };

    const newTracks = state.tracks.map((t) => {
      if (t.id === sourceTrack!.id && t.id === targetTrackId) {
        // Move within same track
        return {
          ...t,
          clips: t.clips.map((c) => (c.id === clipId ? updatedClip : c)),
        };
      } else if (t.id === sourceTrack!.id) {
        // Remove from source track
        return {
          ...t,
          clips: t.clips.filter((c) => c.id !== clipId),
        };
      } else if (t.id === targetTrackId) {
        // Add to dest track
        return {
          ...t,
          clips: [...t.clips, updatedClip],
        };
      }
      return t;
    });

    set({
      tracks: newTracks,
      durationFrames: Math.max(state.durationFrames, newEndFrame),
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
    return true;
  },

  trimClipIn: (clipId, newStartFrame) => {
    const state = get();
    let foundTrack: Track | null = null;
    let foundClip: Clip | null = null;

    for (const t of state.tracks) {
      const c = t.clips.find((x) => x.id === clipId);
      if (c) {
        foundTrack = t;
        foundClip = c;
        break;
      }
    }

    if (!foundTrack || !foundClip || foundTrack.locked) return false;
    if (newStartFrame >= foundClip.endFrame || newStartFrame < 0) return false;

    // Collision check with previous clip
    for (const other of foundTrack.clips) {
      if (other.id === clipId) continue;
      if (newStartFrame < other.endFrame && foundClip.endFrame > other.startFrame) {
        return false;
      }
    }

    const frameDelta = newStartFrame - foundClip.startFrame;
    const newSourceIn = foundClip.sourceIn + frameDelta;
    if (newSourceIn >= foundClip.sourceOut) return false;

    const snap = createSnapshot(state);

    const updatedClips = foundTrack.clips.map((c) =>
      c.id === clipId
        ? { ...c, startFrame: newStartFrame, sourceIn: newSourceIn }
        : c
    );

    set({
      tracks: state.tracks.map((t) => (t.id === foundTrack!.id ? { ...t, clips: updatedClips } : t)),
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
    return true;
  },

  trimClipOut: (clipId, newEndFrame) => {
    const state = get();
    let foundTrack: Track | null = null;
    let foundClip: Clip | null = null;

    for (const t of state.tracks) {
      const c = t.clips.find((x) => x.id === clipId);
      if (c) {
        foundTrack = t;
        foundClip = c;
        break;
      }
    }

    if (!foundTrack || !foundClip || foundTrack.locked) return false;
    if (newEndFrame <= foundClip.startFrame) return false;

    // Collision check with following clip
    for (const other of foundTrack.clips) {
      if (other.id === clipId) continue;
      if (foundClip.startFrame < other.endFrame && newEndFrame > other.startFrame) {
        return false;
      }
    }

    const frameDelta = newEndFrame - foundClip.startFrame;
    const newSourceOut = foundClip.sourceIn + frameDelta;
    if (newSourceOut <= foundClip.sourceIn) return false;

    const snap = createSnapshot(state);

    const updatedClips = foundTrack.clips.map((c) =>
      c.id === clipId
        ? { ...c, endFrame: newEndFrame, sourceOut: newSourceOut }
        : c
    );

    set({
      tracks: state.tracks.map((t) => (t.id === foundTrack!.id ? { ...t, clips: updatedClips } : t)),
      durationFrames: Math.max(state.durationFrames, newEndFrame),
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
    return true;
  },

  splitClip: (clipId, splitFrame) => {
    const state = get();
    let foundTrack: Track | null = null;
    let foundClip: Clip | null = null;

    for (const t of state.tracks) {
      const c = t.clips.find((x) => x.id === clipId);
      if (c) {
        foundTrack = t;
        foundClip = c;
        break;
      }
    }

    if (!foundTrack || !foundClip || foundTrack.locked) return false;
    if (splitFrame <= foundClip.startFrame || splitFrame >= foundClip.endFrame) return false;

    const snap = createSnapshot(state);

    const delta = splitFrame - foundClip.startFrame;
    const sourceCut = foundClip.sourceIn + delta;

    const firstHalf: Clip = {
      ...foundClip,
      endFrame: splitFrame,
      sourceOut: sourceCut,
    };

    const secondHalf: Clip = {
      ...foundClip,
      id: `clip_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: `${foundClip.name} (Split)`,
      startFrame: splitFrame,
      endFrame: foundClip.endFrame,
      sourceIn: sourceCut,
      sourceOut: foundClip.sourceOut,
    };

    const newClips: Clip[] = [];
    for (const c of foundTrack.clips) {
      if (c.id === clipId) {
        newClips.push(firstHalf, secondHalf);
      } else {
        newClips.push(c);
      }
    }

    set({
      tracks: state.tracks.map((t) => (t.id === foundTrack!.id ? { ...t, clips: newClips } : t)),
      selectedClipId: secondHalf.id,
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
    return true;
  },

  splitClipAtPlayhead: (currentFrame) => {
    const state = get();
    // Split active selected clip or first clip under playhead
    if (state.selectedClipId) {
      return get().splitClip(state.selectedClipId, currentFrame);
    }

    // Look for any clip under playhead
    for (const t of state.tracks) {
      if (t.locked) continue;
      const c = t.clips.find((x) => x.startFrame < currentFrame && x.endFrame > currentFrame);
      if (c) {
        return get().splitClip(c.id, currentFrame);
      }
    }
    return false;
  },

  deleteClip: (clipId) => {
    const state = get();
    const snap = createSnapshot(state);

    set({
      tracks: state.tracks.map((t) => ({
        ...t,
        clips: t.clips.filter((c) => c.id !== clipId),
      })),
      selectedClipId: state.selectedClipId === clipId ? null : state.selectedClipId,
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  rippleDeleteClip: (clipId) => {
    const state = get();
    let foundTrack: Track | null = null;
    let targetClip: Clip | null = null;

    for (const t of state.tracks) {
      const c = t.clips.find((x) => x.id === clipId);
      if (c) {
        foundTrack = t;
        targetClip = c;
        break;
      }
    }

    if (!foundTrack || !targetClip || foundTrack.locked) return;

    const snap = createSnapshot(state);
    const duration = targetClip.endFrame - targetClip.startFrame;

    const newClips = foundTrack.clips
      .filter((c) => c.id !== clipId)
      .map((c) => {
        if (c.startFrame >= targetClip!.endFrame) {
          return {
            ...c,
            startFrame: c.startFrame - duration,
            endFrame: c.endFrame - duration,
          };
        }
        return c;
      });

    set({
      tracks: state.tracks.map((t) => (t.id === foundTrack!.id ? { ...t, clips: newClips } : t)),
      selectedClipId: null,
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  duplicateClip: (clipId) => {
    const state = get();
    let foundTrack: Track | null = null;
    let targetClip: Clip | null = null;

    for (const t of state.tracks) {
      const c = t.clips.find((x) => x.id === clipId);
      if (c) {
        foundTrack = t;
        targetClip = c;
        break;
      }
    }

    if (!foundTrack || !targetClip || foundTrack.locked) return;

    const snap = createSnapshot(state);
    const duration = targetClip.endFrame - targetClip.startFrame;
    const maxEnd = Math.max(...foundTrack.clips.map((c) => c.endFrame), 0);

    const dupClip: Clip = {
      ...targetClip,
      id: `clip_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: `${targetClip.name} (Copy)`,
      startFrame: maxEnd,
      endFrame: maxEnd + duration,
    };

    set({
      tracks: state.tracks.map((t) =>
        t.id === foundTrack!.id ? { ...t, clips: [...t.clips, dupClip] } : t
      ),
      selectedClipId: dupClip.id,
      durationFrames: Math.max(state.durationFrames, dupClip.endFrame),
      undoStack: [...state.undoStack.slice(-MAX_HISTORY + 1), snap],
      redoStack: [],
      canUndo: true,
      canRedo: false,
    });
  },

  setActiveTool: (tool) => set({ activeTool: tool }),
  toggleSnapping: () => set((s) => ({ snappingEnabled: !s.snappingEnabled })),
  setZoomRatio: (zoom) => set({ zoomRatio: Math.max(0.1, Math.min(10, zoom)) }),
  setDurationFrames: (duration) => set({ durationFrames: Math.max(24, duration) }),

  findSnapTarget: (frame, tolerance = 5) => {
    const state = get();
    if (!state.snappingEnabled) return null;

    const candidates = new Set<number>([0]);
    for (const t of state.tracks) {
      for (const c of t.clips) {
        candidates.add(c.startFrame);
        candidates.add(c.endFrame);
      }
    }

    let bestTarget: number | null = null;
    let minDist = tolerance + 1;

    for (const target of candidates) {
      const dist = Math.abs(frame - target);
      if (dist <= tolerance && dist < minDist) {
        minDist = dist;
        bestTarget = target;
      }
    }
    return bestTarget;
  },

  undo: () => {
    const state = get();
    if (state.undoStack.length === 0) return;

    const snap = createSnapshot(state);
    const prevSnap = state.undoStack[state.undoStack.length - 1];
    const newUndoStack = state.undoStack.slice(0, -1);

    set({
      tracks: prevSnap.tracks,
      durationFrames: prevSnap.durationFrames,
      selectedClipId: prevSnap.selectedClipId,
      undoStack: newUndoStack,
      redoStack: [...state.redoStack, snap],
      canUndo: newUndoStack.length > 0,
      canRedo: true,
    });
  },

  redo: () => {
    const state = get();
    if (state.redoStack.length === 0) return;

    const snap = createSnapshot(state);
    const nextSnap = state.redoStack[state.redoStack.length - 1];
    const newRedoStack = state.redoStack.slice(0, -1);

    set({
      tracks: nextSnap.tracks,
      durationFrames: nextSnap.durationFrames,
      selectedClipId: nextSnap.selectedClipId,
      undoStack: [...state.undoStack, snap],
      redoStack: newRedoStack,
      canUndo: true,
      canRedo: newRedoStack.length > 0,
    });
  },
}));
