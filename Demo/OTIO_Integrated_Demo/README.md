# OTIO multicam: integrated known-AAf demonstration (November 2026)

This package joins two **previously Mac-validated** operations into one new command:

- Fresh `Avid MCAM EDIT.aaf` backing parsing: previously observed 59/59 slots, 107 component segments and exact archived comparison.
- Fresh AAF editorial selectors: previously observed 79/79 readable and exact matches, with AAF `Selected` prepended to `Alternates` when compared with the fixture.
- Refresh **only those AAF-derived fields** in a copy of the enriched v1.4 fixture, run the unchanged frozen v0.7.2 exporter, compare FCPXML bytes with the known-good baseline.

## Run on your Mac

```bash
source ~/otio-python/bin/activate
bash run_demo.command
```

Requires Python 3 and `pyaaf2` in the activated environment. No source media is needed for structural tests.

Output in `demo_output/`: `VALIDATION_REPORT.md`, `structural_report.json`, `selector_evidence.json`, `refreshed_from_AAF_verified_template.otio`, `avid_picture_enriched_sync.fcpxml`, `picture_report.json`, `generator.log`. On failure the command exits nonzero and writes `failure_traceback.txt`.

## Evidence and limits

Two **separate** Mac runs previously passed. The *new combined launcher* has been syntax checked and the frozen release's own checksum/XML verification succeeded here, but the combined launcher has **not** yet been run against the AAF in this environment because `pyaaf2` is unavailable. Its first Mac test remains pending.

Not a general-purpose AAF reader/writer or complete independent OTIO conversion: `definitions`, media registry, portable IDs, timeline topology, and other editorial metadata are retained from the previously validated reference v1.4 fixture. No complete mono-audio interchange is claimed. Native Resolve import/editability must be demonstrated in Resolve by the operator; byte identity establishes equivalence to the previously successful import file, not a new application import.

The frozen files are not modified: the launcher checks hashes, generates into temporary adapter directories, and checks hashes again. This demo is AI-generated and must be reviewed before public distribution. Preserve the original project owner's NLE validation provenance.

## Eight-minute demonstration cues

0:00–1:00 — Show editorially equivalent sequences in Avid, Premiere and Resolve. Pose the question: *Does matching output imply the original multicam remains editable?*

1:00–2:00 — Show Avid source group: 9 logical picture angles, 12 recordings, 48 mono backing outputs, staggered starts/gaps. Explain 59 slots != 59 angles.

2:00–3:00 — Explain OTIO: `CompositionDefinition` holds shared synchronised sources; `MulticamSelector` models individual editorial choices. Distinguish AAF source slots, logical angles, source channels, Resolve UUIDs.

3:00–4:15 — Terminal: run `bash run_demo.command`; open `demo_output/VALIDATION_REPORT.md`. Explain this is an AAF-backed **reference-fixture refresh** with strict exact-match guards, not a general converter.

4:15–6:00 — Resolve: import `demo_output/avid_picture_enriched_sync.fcpxml` into disposable project; relink source media; compare cuts, 46f filler and staggered angle gaps; switch a camera in native multicam mode. Keep a pre-imported Resolve project and screen capture ready.

6:00–7:00 — Audio: source channel identities can be represented; v0.7.7 selected one mono channel, but full independent mono edit reconstruction and switching have not been demonstrated. Resolve's own FCPXML 1.14 round trip also omitted separate mono edits in an independent test.

7:00–8:00 — Conclusion: structure and editing semantics matter beyond visible cuts. Experimental v1.4 not accepted upstream; v0.7.2 picture-specific; code and docs AI generated, user supplied source material and NLE validation.
