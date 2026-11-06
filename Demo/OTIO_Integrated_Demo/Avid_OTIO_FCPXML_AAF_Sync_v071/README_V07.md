# Avid multicam FCPXML sync bridge v0.7 — experimental

**ChatGPT-generated code and documentation.** The user supplied Avid/Resolve examples, observations and Mac testing. This is not a validated interchange converter.

v0.7 keeps the 1,406-frame Avid picture edit from v0.6 but adds a **per-recording multicam synchronisation manifest**. Unlike v0.6, it does not blindly concatenate all media inside each angle. `offset` is the recording's placement in multicam time; `start` remains the source-media time. This can preserve gaps, e.g. C01 → C02.

## Why no authoritative import candidate yet?

Source timecode establishes provisional placements for A01/B01/C01/C02/D01/H01/P01 and the G01 two-frame marker comes from the screenshot. The original group placement of **E01/F01/F02/F03 remains unresolved** (zero-based source TC). Forcing their placement would invent sync. Use the original Avid group or original Resolve multicam source timeline to confirm their **start frames relative to A01 at multicam frame zero**, then edit `sync_manifest.json`.

Run from the extracted directory with Python 3:

```bash
python generate_v07.py avid_multicam_v12_native_roundtrip.otio \
  --sync sync_manifest.json \
  --out outputs/avid_picture_sync_v07.fcpxml \
  --report outputs/sync_report_v07.json
```

The exporter **refuses** incomplete placements by default. You may use `--allow-provisional` for diagnostics, but **do not treat its FCPXML as correctly synchronised**. Import into a disposable Resolve project only.

## Audio scope for v0.8

**No stereo grouping assumption.** The Avid source group has 0–16 independent mono channels per camera/angle; timeline audio tracks are mono. Future conversion should preserve channel identity, independently selectable source channels, per-track cuts and native mono topology. Some source files may physically contain many PCM channels. Do not infer audio mapping from the picture source slot alone.

## Fidelity limits

- Source sync unverified for zero-based TC recordings; +2 frame G01 marker not yet verified against AAF.
- Video editing decisions retained, audio and graphics explicitly omitted.
- Inferred source TC placements are hypotheses until visually checked against the original synced group.
- Resolve import of v0.7 has not been tested.
