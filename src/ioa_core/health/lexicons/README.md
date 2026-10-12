# Content-gate lexicons

These JSON files are the pattern sets behind `ioa_core.health.content_gates`.
Each file has the shape:

```json
{
  "version": "2026.10.1",
  "category": "risk_to_self",
  "default_severity": "escalate",
  "words": ["..."],
  "patterns": ["..."],
  "notes": "..."
}
```

`words` are matched case-insensitively on word boundaries. `patterns` are
regular expressions compiled case-insensitively. A gate fires when any entry
matches. The evaluator records only the gate name, severity, `category` and
`version`; it never records the matched text.

## Provenance

Every entry was written by OrchIntel from clinical-register documentation
phrasing. No entry was derived from patient records, transcripts or any real
case material. The lists are deliberately conservative: a false positive costs
a clinician one acknowledgement, a false negative is silent, so phrasing that
plainly signals the category is preferred over broad single words.

## Changing a lexicon

1. Bump `version` (date-based, `YYYY.MM.N`). Receipts record the version of
   every lexicon used, so changes stay auditable.
2. Add or adjust entries. Keep single common words out unless they are
   unambiguous in clinical notes.
3. Run `python -m pytest tests/health/test_content_gates.py` and make sure the
   synthetic fixtures still behave as asserted.
4. Describe the change in `CHANGELOG.md`.

Files: `crisis_risk_to_self.json`, `risk_to_others.json`, `child_protection.json`,
`crisis_mandatory_reporting.json`.
