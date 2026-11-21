# Native Project Format Specification (`.ckproj`)

## 1. Document Format & Standards

CorridorKey 2.0 Desktop projects are stored with the extension `.ckproj`. The payload is a structured UTF-8 JSON document adhering to the `1.0.0` specification.

### Top-Level Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `format` | `string` | Always `"corridorkey-project"` |
| `schema_version` | `string` | Semantic schema version (current: `"1.0.0"`) |
| `generator` | `string` | Application generating the file (`"CorridorKey 2.0 Desktop"`) |
| `project` | `object` | Project metadata, resolution, framerate, rational timebase, color space |
| `media_pool` | `array` | List of imported media items, asset IDs, paths, codecs, and durations |
| `timeline` | `object` | Sequence duration, video and audio tracks, clips, and keyframes |
| `settings` | `object` | Keying, matte, viewer, and export configurations |
| `workspace` | `object` | User interface layout, panel widths, heights, visibility, and zoom |

---

## 2. Complete Schema Example

```json
{
  "format": "corridorkey-project",
  "schema_version": "1.0.0",
  "generator": "CorridorKey 2.0 Desktop",
  "project": {
    "project_id": "proj-a1b2c3d4",
    "name": "SciFi_Hero_Shot",
    "width": 1920,
    "height": 1080,
    "frame_rate": 24.0,
    "timebase_numerator": 24,
    "timebase_denominator": 1,
    "color_space": "Rec.709",
    "created_at": "2026-11-20T21:00:00Z",
    "modified_at": "2026-11-20T22:30:00Z"
  },
  "media_pool": [
    {
      "asset_id": "asset-f0e1d2c3",
      "name": "actor_take01.mov",
      "relative_path": "footage/actor_take01.mov",
      "absolute_path": "/Volumes/VFX_Drive/Projects/footage/actor_take01.mov",
      "width": 1920,
      "height": 1080,
      "frame_rate": 24.0,
      "duration_frames": 240,
      "duration_seconds": 10.0,
      "codec": "PRORES_4444",
      "file_size_bytes": 104857600
    }
  ],
  "timeline": {
    "sequence_id": "seq-main",
    "name": "Master Sequence",
    "timebase": { "numerator": 24, "denominator": 1 },
    "duration_frames": 240,
    "tracks": [
      {
        "track_id": "v1",
        "type": "video",
        "name": "Video 1",
        "visible": true,
        "locked": false,
        "muted": false,
        "solo": false,
        "order_index": 0,
        "clips": [
          {
            "clip_id": "clip-1234",
            "media_id": "asset-f0e1d2c3",
            "track_id": "v1",
            "name": "Actor Take 01",
            "source_path": "footage/actor_take01.mov",
            "source_in": 0,
            "source_out": 240,
            "timeline_start": 0,
            "timeline_end": 240,
            "speed": 1.0,
            "volume": 1.0,
            "is_muted": false,
            "color_tag": "#0d9488",
            "properties": {
              "posX": { "name": "posX", "default_value": 0.0, "keyframes": [] },
              "posY": { "name": "posY", "default_value": 0.0, "keyframes": [] },
              "scale": { "name": "scale", "default_value": 100.0, "keyframes": [] },
              "rotation": { "name": "rotation", "default_value": 0.0, "keyframes": [] },
              "opacity": {
                "name": "opacity",
                "default_value": 100.0,
                "keyframes": [
                  {
                    "frame": 0,
                    "value": 0.0,
                    "interpolation": "linear",
                    "in_handle": [-0.33, 0.0],
                    "out_handle": [0.33, 0.0]
                  },
                  {
                    "frame": 24,
                    "value": 100.0,
                    "interpolation": "bezier",
                    "in_handle": [-0.33, 0.0],
                    "out_handle": [0.33, 0.0]
                  }
                ]
              }
            }
          }
        ]
      }
    ]
  },
  "settings": {
    "keying": {
      "hann_chunk": 96,
      "hann_stride": 48,
      "low_vram": false,
      "despill_strength": 0.7,
      "hint_mode": "first_frame",
      "hint_quality": 3
    },
    "matte": {
      "contrast": 1.0,
      "edge_refinement": 0.0,
      "invert": false,
      "alpha_threshold": 0.0
    },
    "viewer": {
      "display_mode": "composite",
      "background_type": "checkerboard",
      "background_color": "#000000",
      "gradient_color_a": "#1e293b",
      "gradient_color_b": "#0f172a",
      "compare_mode": "off",
      "wipe_position": 0.5,
      "alpha_mode": "premultiplied",
      "exposure": 0.0,
      "saturation": 1.0
    },
    "export": {
      "format": "prores_4444",
      "colorSpace": "rec709"
    }
  },
  "workspace": {
    "left_panel_width": 300,
    "right_panel_width": 340,
    "bottom_panel_height": 260,
    "show_media_browser": true,
    "show_inspector": true,
    "show_timeline": true,
    "zoom_ratio": 1.5
  }
}
```

---

## 3. Schema Version Migration Framework

The migration module (`engine/project/schema.py`) inspects `schema_version` and executes migrations:
- **0.9.0 to 1.0.0:** Promotes `media` array to `media_pool`, initializes rational timebase `{"numerator": 24, "denominator": 1}` for sequences lacking exact framerate fractions.
- All migrations are non-destructive and retain existing configurations.
