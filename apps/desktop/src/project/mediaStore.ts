import { create } from "zustand";
import { MediaItem } from "../types/project";

interface MediaState {
  media: MediaItem[];
  selectedMediaId: string | null;
  searchQuery: string;
  addMedia: (item: MediaItem) => void;
  removeMedia: (id: string) => void;
  selectMedia: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setAllMedia: (items: MediaItem[]) => void;
  clearMedia: () => void;
  updateMediaPath: (id: string, newPath: string) => void;
}

export const useMediaStore = create<MediaState>((set) => ({
  media: [],
  selectedMediaId: null,
  searchQuery: "",

  addMedia: (item) =>
    set((state) => {
      // Avoid duplicate path import
      if (state.media.some((m) => m.path === item.path)) {
        return state;
      }
      return {
        media: [...state.media, item],
        selectedMediaId: state.selectedMediaId ?? item.id,
      };
    }),

  removeMedia: (id) =>
    set((state) => ({
      media: state.media.filter((m) => m.id !== id),
      selectedMediaId: state.selectedMediaId === id ? null : state.selectedMediaId,
    })),

  selectMedia: (id) => set({ selectedMediaId: id }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  setAllMedia: (items) =>
    set({
      media: items,
      selectedMediaId: items.length > 0 ? items[0].id : null,
    }),

  clearMedia: () => set({ media: [], selectedMediaId: null }),

  updateMediaPath: (id, newPath) =>
    set((state) => ({
      media: state.media.map((m) =>
        m.id === id
          ? {
              ...m,
              path: newPath,
              name: newPath.split(/[/\\]/).pop() || m.name,
            }
          : m
      ),
    })),
}));
