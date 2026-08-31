# Contributing

Contributions are welcome when they preserve the project's analytical and public-safety boundaries.

## A valid new case must include

- an explicit decision and audience;
- a unit of analysis and source-grain map;
- metric contracts with numerator and denominator;
- deterministic synthetic data;
- at least one realistic analytical trap;
- a corrected method and a decision-oriented report;
- positive and negative tests;
- an interpretation boundary.

Do not submit proprietary classroom data, employer data, personal records, or screenshots whose rights are unclear.

Run before opening a pull request:

```bash
python -m unittest discover -s tests -v
python scripts/public_audit.py .
python scripts/check_markdown_links.py .
python scripts/rebuild_examples.py --check
```
