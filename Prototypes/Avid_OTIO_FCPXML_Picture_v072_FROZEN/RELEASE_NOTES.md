# Release notes — picture-only v0.7.2 (frozen)

**Freeze date:** 2026-11-05.

**Reason for freezing:** User confirmed successful editable multicam import and correct camera recording sync/recording gaps in Resolve. Later direct Resolve FCPXML export/reimport proved lossy for A01's 16 mono audio streams. Audio investigations are outside this picture-only release.

**Implementation changes made during this freeze:** None to the copied generator, custom SchemaDef plugin, enriched OTIO, generated FCPXML, regression tests, or reports. Documentation and hash manifest are added at the package root.

**Reproducibility:** four local Python structural tests pass. The Resolve application behaviour is user-reported and cannot be automatically rerun by this package.

**Recommended repository naming:** `Prototypes/Avid-OTIO-FCPXML-Picture-v0.7.2-Frozen/`.
