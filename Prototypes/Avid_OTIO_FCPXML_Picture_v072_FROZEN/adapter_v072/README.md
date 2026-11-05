# Avid → enriched OTIO → FCPXML v0.7.2 — controlled Resolve tests

**AI-generated experimental code and fixtures; not independently reviewed.** The user supplied real Avid sources and NLE validation results. Use a new disposable Resolve project. **Neither output has yet been tested in Resolve.** This is not a certified Avid interchange adapter.

## First test: synchronised picture

Import `outputs/avid_picture_enriched_sync.fcpxml`. It is generated from `avid_multicam_v14_enriched_backing.otio`, **not** a separate manually maintained sync manifest or Resolve FCPXML template. The enriched OTIO's `CompositionDefinition.attributes.backing_placement_model.slots[*].segments[*]` provides each source's `timeline_start_frame`, `duration_frames`, `source_in_frame`, `media_id` and backing slot identity. The converter resolves the original media locators through `RelinkableMedia` records.

Expected: 9 logical picture angles, 12 recordings, 11 selected picture edits and 46 frames of filler in a 1,406-frame (25 fps) edit. Specific placements: B01 125f, C02 2002f, D01 300f, E01 200f, F02 1540f, F03 3520f, H01 500f. Distinct C01/C02 and F01/F02/F03 gaps should be visible. Graphics and audio are intentionally omitted.

Source-range handling retains the previous v0.7.1 algorithm; **source-frame interpretation and import fidelity still require checking in Resolve**. The `outputs/picture_report.json` lists selection-coverage warnings, which are heuristics, not verified failures.

## Second test: minimum audio selection (diagnostic, NOT verified mono routing)

Only **after** the picture test, import `outputs/avid_A01_mono_audio_diagnostic.fcpxml` into a separate disposable project. It declares A01 as a 16-channel source (16 separately identified mono channels in Avid), places one audio-enabled multicam angle and selects it for a four-second timeline. The AAF backing record used is **slot 2 = A01's first discrete mono output** (the master/media slot ID is also 2). The XML itself does **not yet** encode a proven way to force Resolve to select exactly AAF channel 2; Resolve may interpret or expose all 16 channels. The `48000` audio sample rate is a provisional value for the import experiment and has NOT been validated against the actual file. The audio test exists to learn what Resolve recognises, not to claim accurate mono routing. No source track changes should be made on a valuable project.

Check whether the source media links, Resolve recognises an editable multicam, an audio angle is selectable, and what channel count/track format Resolve creates. Report any import error or crash and stop testing if unstable.

## Regenerate, inspect and test

```bash
source ~/otio-python/bin/activate
cd Avid_OTIO_FCPXML_v072
python generate_v072.py
python -m unittest discover -p 'test*.py' -v
export OTIO_PLUGIN_MANIFEST_PATH="$PWD/manifest.json"
```

An untouched copy of the compatible SchemaDef plugin is included for native OTIO read/write checks. The generator itself reads the JSON representation and does not require OpenTimelineIO installed. The `legacy_generate_v07.py` picture serializer is reused **only for FCPXML generation**; the sync placements are derived from the enriched OTIO in `generate_v072.py`. `outputs/embedded_sync_audit.json` is emitted solely for inspection, not used as a manually managed input.

## Unproven / future work

* Verify real picture sync/selected source frame in Resolve.
* Determine FCPXML/Resolve mapping of one mono channel of a multichannel Avid source. AAF mono backing slots and source slots are not the same as a single-channel audio file.
* Build native independent mono edit tracks (26 and 23 selections) after the channel-mapping experiment.
* Test samples vs frame edit accuracy and relink behaviour.
* Source track ordering and complex graphics composite mode are not guaranteed by Resolve FCPXML round-trip.
* If Resolve rejects or crashes on the diagnostic file, discard it; do not repeatedly import it.
