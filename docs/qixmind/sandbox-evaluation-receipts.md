# QiXMind sandbox evaluation receipts (ioa-core 2.17.0)

Sandbox evaluation receipt: synthetic data, not a clinical record.

## What it is

A signed record of one evaluation in the QiXMind partner sandbox. The
sandbox runs only on server-held synthetic fixtures chosen by id; it never
takes free text. A sandbox receipt is designed so it can never pass for a
production Session Evidence Receipt (`qixmind.session-evidence-receipt.v1`).

| | Production session receipt | Sandbox evaluation receipt |
|---|---|---|
| Framework | `QIXMIND_SESSION_EVIDENCE_RECEIPT` | `QIXMIND_SANDBOX_EVALUATION_RECEIPT` |
| Schema | `qixmind.session-evidence-receipt.v1` | `qixmind.sandbox-evaluation-receipt.v1` |
| Id prefix | `qixmind-ser-` | `qixmind-sbx-` |
| Key registry schema | `qixmind.session-evidence-key-registry.v1` | `qixmind.sandbox-evaluation-key-registry.v1` |
| Key environment | `QIXMIND_EVIDENCE_*` | `QIXMIND_SANDBOX_*` |
| Verifier | `verify_session_receipt*` | `verify_sandbox_receipt*`, `check_sandbox_receipt` |

## Signed designation

Inside the signed metadata:

- `environment: "sandbox_evaluation"` and `not_for_clinical_use: true`
  (required by the sandbox verifier; a correctly signed bundle without them
  is refused);
- `synthetic_data_only: true`;
- `notice`: "Sandbox evaluation receipt: synthetic data, not a clinical record";
- disclaimers: no diagnosis, no efficacy claim, not a clinical record, no
  follow-up obligation created, no content included.

## Labels

Every field records who produced it.

`metadata.computed` (each block `computed_by: "qixmind"`):

| Field | Meaning |
|---|---|
| `fixtures` | Fixture set version, input and output fixture ids, profile, jurisdiction, label `SYNTHETIC` |
| `model_input`, `model_output` | SHA-256 and length of the fixture texts; `held` for the output |
| `content_gates` | Live content gate results (`ContentGateEvaluator`, review-output check on) |
| `review_output` | Produced, empty or refused |
| `findings` | Findings detector report, `status: evaluation_only` |
| `required_actions` | Required actions under the named policy; `label` is the policy status (`draft`) |
| `provenance` | `capture_session_provenance` with the policy and findings detector |
| `sign_off_checks` | QiXMind's own checks: every fired gate acknowledged, every required action dispositioned, no dismissal of a required escalation, output not held |

`metadata.assertions` (each `{"asserted_by": "partner", "value": ...}`):
`model`, `provider`, `clinician_role`, `partner_timestamps`
(`generated_at`, `reviewed_at`, `signed_off_at`), `acknowledged_gates` and
`dispositions` (codes only).

Rules enforced at creation and checked again at verification:

- A partner-asserted field placed in `computed`, or marked `computed_by`, is refused.
- A computed field placed in `assertions` is refused.
- Assertions are identifiers, roles, ISO 8601 timestamps or codes; values with
  spaces or unknown keys are refused, so prose cannot be carried.
- `metadata.labels` lists both sets and must match them.

## Keys

- The sandbox key is its own Ed25519 key, loaded from
  `QIXMIND_SANDBOX_PRIVATE_KEY_B64` or `_PATH` only.
  `configured_sandbox_private_key_pem()` refuses a key equal to the
  configured production key.
- `create_sandbox_receipt(..., production_registry=...)` refuses to sign with
  a key listed in the production registry.
- `check_sandbox_receipt(..., production_registry=...)` refuses a receipt
  whose key id is listed in the production registry
  (`production_key_not_accepted`), and `assert_registries_disjoint()` refuses
  registries that share a key.
- The production verifiers refuse the sandbox framework, schema, id prefix
  and any `environment` field, and the production registry normaliser refuses
  the sandbox registry schema.

## Verifying

```bash
ioa verify qixmind-sbx-receipt.json qixmind-sandbox-pubkey.pem
```

The first line printed for a sandbox receipt is the notice. In Python:

```python
from ioa_core.evidence import check_sandbox_receipt
result = check_sandbox_receipt(receipt, sandbox_registry, production_registry=production_registry)
# {"notice": "Sandbox evaluation receipt: ...", "valid": True, "reason": None, ...}
```

Reason codes: `not_a_sandbox_receipt`, `environment_missing`,
`labels_invalid`, `content_not_allowed`, `production_key_not_accepted`,
`key_not_in_sandbox_registry`, `signature_invalid`.

A valid signature shows the receipt was issued by the QiXMind sandbox and has
not changed. It says nothing about clinical correctness, and the partner's
assertions are recorded as stated, not independently validated.
