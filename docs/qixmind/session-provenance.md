# QiXMind session provenance (receipt schema addition, ioa-core 2.16.0)

## What it is

An optional `metadata.provenance` block in a QiXMind Session Evidence Receipt
(`qixmind.session-evidence-receipt.v1`). It names what governed the session:

| Field | Meaning |
|---|---|
| `schema` | `qixmind.session-provenance.v1` |
| `source` | Always `runtime`: captured by the runtime when it evaluated the session |
| `ioa_core_version` | ioa-core version the runtime ran |
| `profile.profile_id`, `profile.fingerprint` | Care profile and the SHA-256 of its packaged definition |
| `content_gates.detector`, `detector_version`, `review_output_version`, `ruleset_sha256` | Live gate detector and a fingerprint of its rules and lexicons |
| `action_policy` | `{"applied": false, "basis": "profile_gate_severities"}` when no action policy was applied; otherwise `policy_id`, `version`, `status` (`draft`, `approved` or `retired`) and the definition `fingerprint` |
| `findings` (optional) | Findings detector name, version, context-rules version, status and ruleset fingerprint, when that detector ran |

## Rules

- The runtime captures the block with `ioa_core.health.capture_session_provenance`
  and passes it through unchanged. The console must not rebuild it from its own
  ioa-core, and a receipt issued without it is never back-filled.
- A policy fingerprint covers the definition only, not its status or approval,
  so approval cannot change what a fingerprint refers to. The status recorded
  is the status at the time of the session. A `draft` status means the policy
  was not approved.
- Fingerprints are canonical-JSON or byte-level SHA-256 values. With the
  ioa-core version they identify the exact definitions in that tagged release.

## Compatibility

- The block is optional. Receipts without it are byte-identical to earlier v1
  receipts.
- Verification is unchanged. A receipt with the block verifies with earlier
  verifiers (checked with ioa-core 2.13.0), because the signature covers the
  whole canonical bundle and the block uses no reserved content keys.
- Changing any field breaks the signature, like any other field.
