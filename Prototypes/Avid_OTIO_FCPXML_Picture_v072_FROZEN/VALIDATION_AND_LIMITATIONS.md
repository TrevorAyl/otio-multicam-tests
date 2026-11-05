# Frozen v0.7.2 — test evidence and limits

## Version and provenance

- **Frozen implementation:** Avid → enriched experimental OTIO → FCPXML 1.14 picture-only adapter, v0.7.2.
- **User application tests:** DaVinci Resolve on Mac (reported 2026-11-05).
- **Code/doc authorship:** ChatGPT-generated; actual NLE test operations and observations supplied by the user.
- **State:** research proof of concept; no production certification, independent review or automated Resolve UI testing.

## Evidence matrix

| Property | Status | Evidence / caveat |
|---|---|---|
| Import picture FCPXML into Resolve | **PASS, reported by user** | Import succeeded; native editable multicam created |
| Picture source placement and gaps | **PASS, reported by user** | User confirmed v0.7.2 source sync and gaps match original Avid multicam |
| Nine logical picture angles, 12 recordings | **PASS, structural** | Inspected generated XML + local tests |
| 11 picture selections, one 46-frame filler | **PASS, structural** | Edited 1,406-frame sequence; user previously found edit boundaries appeared correct |
| Exactly matched media relinking / decoding | **Not fully established** | Original file locators may be offline; a video was reported offline in an earlier diagnostic |
| Audio channel mapping in Resolve FCPXML | **FAIL for tested case** | Resolve's *own* export and re-import of 16 discrete A01 mono audio streams loses channels |
| Source audio topology in native Resolve project | **Observed** | 16 mono tracks / audio media indices 0–15 in DRT of user's A01 multicam |
| Complex nested graphics composite mode | **Not preserved / excluded** | Resolve FCPXML roundtrip dropped original composite settings; picture adapter intentionally omits graphics |
| Source-track ordering | **Not guaranteed** | Resolve self-export/re-import changed track ordering and some audio configuration in an earlier test |
| Full original AAF audio edit | **Not implemented** | Two independent mono tracks (26 + 23 selectors) remain future work |
| Broad Resolve / FCPXML interoperability | **Not established** | One real project and particular application import behaviour |

### Picture placement evidence

- A01 at 0f; B01 125f; C01 0f; C02 2002f; D01 300f; E01 200f; F01 0f; F02 1540f; F03 3520f; G01 0f; H01 500f; P01 0f.
- Within C, the C01/C02 gap is 377f; within F, the F01/F02 gap is 40f, and the F02/F03 gap is 605f.
- Original 59-slot backing composition includes **11 picture slots** (graphics fill/key included) and **48 mono audio slots**. The frozen picture adapter exports **nine logical camera angles** and excludes graphics and audio.
- Native Avid backing placement is available in the enriched OTIO's `CompositionDefinition.attributes.backing_placement_model`; no external sync manifest is needed.

### Interpreting the legacy report

`adapter_v072/outputs/picture_report.json` was generated **before** the successful user import. Its `EXPERIMENTAL_UNTESTED_IN_RESOLVE` status and generic 'not tested' limitations are historical metadata, not the current outcome. We preserve it verbatim to maintain the frozen artifact. The application validation recorded in this document supersedes that historical test-state label, but **does not** remove the other relevant unknowns.

The report's machine-generated `sync_manifest` path is an output audit file, not an external input to the converter. It may contain the original author's absolute working directory; do not rely on that path outside its original environment.

## Separate Resolve audio round-trip finding

On the real A01.mov, FFprobe reported **16 separate PCM 24-bit mono audio streams**, and native Resolve displayed 16 mapped mono source tracks. The user created a Resolve multicam from A01, exported it as FCPXML, and reimported that same Resolve-generated FCPXML. On reimport, the extra mono audio channels were lost. Earlier XML component/role variants likewise failed to produce distinct channel mappings.

**Interpretation:** Resolve's tested FCPXML export/import workflow is lossy for this particular audio topology. The result does **not** establish that the FCPXML specification itself cannot represent multichannel mono streams, and does **not** mean the OTIO schema dropped the AAF mono backing data. Therefore this picture adapter release should *not* be advertised as audio-capable or a complete archive format.

## Freeze / scope decision

Do not modify the successful picture generator to work around Resolve audio import behaviour. Keep the v1.4 custom schema compatibility and its enriched AAF backing data as-is. Any audio adapter, alternative output (e.g. native DRT), or typed backing-output schema proposal should be developed separately and versioned independently.

## Useful next steps, not part of this frozen release

- Publish the frozen adapter and its test findings as a separate prototype with explicit AI provenance.
- If a target NLE requires picture-only transfer, test separately using its own source media and import version; preserve the sync and edit selection information while flagging dropped audio/graphics.
- Future full-fidelity interchange work should preserve mono stream identity, AAF source slot and SourceMob provenance, independent audio edits and precise placement without equating 'camera angle' with 'audio channel'.
