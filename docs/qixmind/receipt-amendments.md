# QiXMind receipt amendments and role source (ioa-core 2.18.0)

## Why

A signed Session Evidence Receipt is a record of what happened. When something
recorded on it is wrong (for example a mistyped pseudonymous episode
reference), the record must be corrected without overwriting signed history.
An amendment is therefore a new signed receipt that names the receipt it
corrects. The original is never modified and still verifies on its own.

## The `amendment` block

`amend_session_receipt(original, ...)` builds the new receipt from the
original's signed metadata and adds an `amendment` block inside the signed
payload (schema `qixmind.receipt-amendment.v1`):

| Field | Meaning |
|---|---|
| `amends_receipt_id` | Id of the receipt being amended (`qixmind-ser-...`) |
| `amends_receipt_sha256` | SHA-256 of the original's exported bytes (`receipt_json_bytes`, the downloaded file). Check it with `receipt_sha256()` or any SHA-256 tool |
| `amends_issued_at` | When the original was issued |
| `reason_code` | One of `AMENDMENT_REASON_CODES`: `episode_reference_corrected`, `care_event_type_corrected`, `administrative_correction` |
| `reason_sha256` | Optional SHA-256 of a short reason the operator keeps. The text itself is never placed in a receipt |
| `corrected_fields` | The fields changed, from `AMENDABLE_FIELDS`: `episode.episode_id`, `care_event.type`. Each reason code requires exactly its field; `administrative_correction` changes no field |
| `amended_by` | `role` (a role token), `role_source` (see below) and `authority` (`original_signer` or `supervising_role`); never a name |
| `amended_at` | When the amendment was signed |
| `original_preserved` | Always `true` |

The receipt also carries `supersedes_receipt_id` equal to `amends_receipt_id`.

What is never amendable: gate results, the input and output hashes, the
acknowledgement, provenance and the session block. Those are evidence of what
happened at the time. The operator may pass the current follow-up state and
review state, so the newest receipt in a chain reflects the obligations as they
stand when it is signed.

## Linear chains

The operator amends only the latest receipt in a chain. Amending a receipt
that is already superseded is refused by the operator (the console enforces it
with a unique index on `supersedes_receipt_id`). Each receipt therefore has at
most one successor.

## Verification

- Each receipt verifies on its own with `verify_session_receipt` or
  `verify_session_receipt_from_registry`, exactly as before.
- `verify_amendment_link(amending, original)` is true only when the amending
  receipt names the original's id and the hash of its exported bytes, and
  supersedes it. It checks the link, not the signatures.
- `ioa verify amended.json qixmind-pubkey.pem` prints `AMENDS: <id> (<sha256>)`
  after the signature result. `ioa verify amended.json qixmind-pubkey.pem
  --amends original.json` also verifies the original's signature and the link.
- The original receipt cannot name its successor, because it was signed first.
  "Superseded by" is reported by the operator's server alongside verification.

## Role source (`acknowledgement.role_source`)

Optional, emitted only when supplied, one of `ROLE_SOURCES`:

| Value | Meaning |
|---|---|
| `claims` | A role claim in the verified session token |
| `clerk_org_role` | The sign-in provider's organisation role (`org:<role>`) |
| `self_declared` | Chosen in the request by a verified member of the organisation |
| `role_directory` | A verified staff role directory held by the operator |
| `unrecorded` | The operator did not record a source |

A receipt that says `self_declared` records honestly that the role was not
independently verified.

## Compatibility

- Receipts issued without these fields are byte-identical to 2.17.0 and 2.17.1 receipts.
- 2.16.0, 2.17.0 and 2.17.1 verifiers verify receipts that carry the new fields; they
  do not interpret them.
- Sandbox evaluation receipts are unchanged and cannot be amended with this
  function (it accepts production session receipts only).
