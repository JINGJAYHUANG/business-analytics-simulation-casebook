# Release verification

## v0.1.0 local qualification

The public fixture was qualified before GitHub publication with:

- CPython 3.13 local execution;
- exactly 207 automated tests;
- deterministic reconstruction of the complete synthetic company example;
- 108 public text files scanned for private paths, credentials, personal identifiers, and prohibited proprietary-course language;
- 15 internal Markdown links checked;
- six deliberate evidence-bundle tampering attacks detected;
- two byte-identical wheel builds under a fixed `SOURCE_DATE_EPOCH`;
- installation and CLI execution in a clean virtual environment.

The permanent GitHub CI matrix re-runs the test and evidence gates on Python 3.11, 3.12, and 3.13. A green workflow is evidence for the exact commit that it names; this document does not treat a local pass as a future cloud pass.

## Fixed fixture identity

- Run ID: `BASC-0f9a48a9a5b1d578`
- Declared artifacts: `46`
- Input manifest SHA-256: `183f46aa01439ca3908790806c34e02d004f67a02aca7368e8206dc0103d6882`
- Artifact manifest SHA-256: `0c5d9120d478b5b503a93b6cec197cbf2873b2c0eea0a6caa43074dbbae04b68`
- SQLite semantic SHA-256: `528a569b46ac4d2ff9cc8da1ebba7b96e627f6496a4173c1a625232bcadbd86c`

## Non-claims

Verification does not mean that the fictional business decisions are correct for a real company, that the experiment proves a causal effect beyond its stated design, or that the project reproduces a commercial simulation platform.
