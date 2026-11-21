# Timeline Render Graph & Layer Composition — CorridorKey 2.0 Desktop

## 1. Composition Hierarchy

The `TimelineRenderGraph` produces an immutable `TimelineFrameCompositePlan` for any integer frame tick $F$.

```
                    +---------------------------+
                    | Current Sequence Frame F  |
                    +-------------+-------------+
                                  |
               +------------------v------------------+
               | Video Tracks (Bottom V1 to Top Vn)  |
               +------------------+------------------+
                                  |
              +-------------------v-------------------+
              | Filter: track.visible == True         |
              +-------------------+-------------------+
                                  |
          +-----------------------v-----------------------+
          | Active Clip Resolution:                       |
          |   clip.start <= F < clip.end                  |
          | Calculate Source Frame:                       |
          |   src = clip.source_in + (F - start) * speed  |
          | Evaluate Keyframed Parameters:                |
          |   (posX, posY, scale, rotation, opacity)      |
          +-----------------------+-----------------------+
                                  |
         +------------------------v------------------------+
         | Layer Stack: [ Layer 0 (V1), Layer 1 (V2), ... ]|
         | Audio Mix:   [ Voice 0 (A1), Voice 1 (A2), ... ]|
         +------------------------+------------------------+
                                  |
                WebGL2 GPU Compositor / Video Export
```

---

## 2. Plan Structure

The emitted composite plan contains:
- `frame`: Target integer frame tick.
- `timecode`: SMPTE string `HH:MM:SS:FF`.
- `layers`: Ordered list of `RenderLayerPlan` records containing:
  - `track_id`, `track_name`, `order_index`
  - `clip_id`, `clip_name`, `source_path`, `source_frame`
  - `opacity`, `pos_x`, `pos_y`, `scale`, `rotation`
- `audio_voices`: Ordered list of `AudioMixVoice` records containing:
  - `clip_id`, `track_id`, `source_path`, `source_frame`, `volume`, `is_audible`
