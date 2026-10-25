# OTIO multicam experimental SchemaDef — v1.4 specification/conformance

> **AI provenance:** All code, design, generated examples, tests, documentation and this package were authored by **ChatGPT (OpenAI)** with the user supplying the real NLE project examples, framing requirements, correcting model assumptions, and running/reporting Mac-based tests. No independent maintainer review, NLE import validation or upstream acceptance is implied.

v1.4 retains **v1.3's tested plugin and fixtures unchanged**. It adds an exploratory interoperability specification and explicit disclosure, adapter capability declarations, a no-silent-loss report, a validation script and regression tests. The full descriptions are in `SPECIFICATION_DRAFT.md` and `GITHUB_DISCUSSION_DRAFT.md`.

## Run

```bash
python -m unittest discover -p 'test*.py' -v
python conformance_report.py
export OTIO_PLUGIN_MANIFEST_PATH="$PWD/manifest.json"
python check_v13_runtime.py
```

A conformance report is an **audit of the proposed semantics**, not a certification of native NLE interchange. Explicitly unsupported features are never re-labelled as supported.
