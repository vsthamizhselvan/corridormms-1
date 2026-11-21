export interface ProjectMetadata {
  name: string;
  width: number;
  height: number;
  frameRate: number;
  colorSpace: string;
  createdAt: string;
  modifiedAt: string;
}

export interface MediaItem {
  id: string;
  name: string;
  path: string;
  relativePath?: string;
  width: number;
  height: number;
  frameRate: number;
  durationFrames: number;
  durationSeconds: number;
  codec: string;
  fileSizeBytes: number;
  thumbnailUrl?: string;
}

export interface Clip {
  id: string;
  mediaId: string;
  trackId: string;
  name: string;
  startFrame: number;
  endFrame: number;
  sourceIn: number;
  sourceOut: number;
  color?: string;
  speed?: number;
  volume?: number;
  isMuted?: boolean;
}

export interface Track {
  id: string;
  type: "video" | "audio";
  name: string;
  visible: boolean;
  locked: boolean;
  muted: boolean;
  solo?: boolean;
  clips: Clip[];
}

export interface KeyingSettings {
  hannChunk: number;
  hannStride: number;
  lowVram: boolean;
  despillStrength: number;
  hintMode: "none" | "first_frame" | "video";
  hintQuality: number;
}

export interface MatteSettings {
  contrast: number; // 0.0 - 2.0 (default 1.0)
  edgeRefinement: number; // 0.0 - 1.0 (default 0.0)
  invert: boolean;
  alphaThreshold: number; // 0.0 - 1.0 (default 0.0)
}

export interface TransformSettings {
  posX: number;
  posY: number;
  scale: number;
  rotation: number;
  opacity: number;
}

export interface AutosaveSnapshot {
  path: string;
  filename: string;
  modified_time: number;
  size_bytes: number;
}

export interface RecoveryStatus {
  recovery_available: boolean;
  newest_snapshot?: AutosaveSnapshot;
  snapshot_count: number;
}

export interface ProjectFile {
  format: "corridorkey-project";
  version?: number;
  schema_version?: string;
  generator?: string;
  project: ProjectMetadata;
  media?: MediaItem[];
  media_pool?: MediaItem[];
  timeline?: {
    durationFrames?: number;
    duration_frames?: number;
    currentFrame?: number;
    current_frame?: number;
    tracks: Track[];
  };
  keyingSettings?: KeyingSettings;
  matteSettings?: MatteSettings;
  transformSettings?: TransformSettings;
  settings?: {
    keying?: KeyingSettings;
    matte?: MatteSettings;
    viewer?: any;
    export?: any;
  };
  workspace?: {
    leftPanelWidth?: number;
    rightPanelWidth?: number;
    bottomPanelHeight?: number;
    left_panel_width?: number;
    right_panel_width?: number;
    bottom_panel_height?: number;
    show_media_browser?: boolean;
    show_inspector?: boolean;
    show_timeline?: boolean;
    zoom_ratio?: number;
  };
}

export type ViewerDisplayMode = "original" | "foreground" | "alpha" | "checkerboard" | "split";
