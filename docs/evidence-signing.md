# Evidence Bundle Signing

IOA Core evidence bundles use operator-provided Ed25519 keys. The signing
implementation does not generate a private key when the process starts, does
not commit private key material, and does not place a private key in a bundle.

This document covers `EvidenceBundle` signatures. The older System Laws
manifest and agent trust-registry signing documentation is a separate surface.

## Key Configuration

Provide exactly one private-key source to the process that creates signed
bundles:

```bash
export IOA_EVIDENCE_PRIVATE_KEY_PATH=/run/secrets/ioa-evidence-private.pem
```

or provide the PEM bytes through a secret manager's base64 value:

```bash
export IOA_EVIDENCE_PRIVATE_KEY_B64="<secret-manager-value>"
```

The operator is responsible for protecting the private key, controlling its
rotation, and distributing the matching public key through an approved channel.
The public key is safe to distribute; the private key is not.

## Bundle Envelope

`EvidenceBundle.generate_signature()` adds an envelope like this:

```json
{
  "sig_version": "ed25519-v1",
  "algo": "Ed25519",
  "public_key_id": "<16-character-public-key-fingerprint>",
  "signature": "<base64-signature>",
  "canonical_hash": "<sha256-canonical-bundle-hash>",
  "signed_at": "<UTC-timestamp>"
}
```

The signature covers the canonical bundle with `signature` and
`signature_status` removed. Mutating a supported bundle field invalidates the
signature state.

## Local Verification

Verification is local. It does not require a gateway, a workspace service, a
private key, or network access.

```bash
ioa verify examples/evidence_bundle_signed.json \
  examples/evidence_bundle_public_key.pub
```

Expected result for the committed synthetic sample:

```text
PASS: Ed25519 evidence signature verified offline
```

To verify chain membership and continuity as well:

```bash
ioa verify --chain \
  --chain-path /path/to/evidence_chain.jsonl \
  examples/evidence_bundle_signed.json \
  examples/evidence_bundle_public_key.pub
```

The evidence sink appends a signed bundle membership event before storing the
bundle. Its keystone chain defaults to
`<EVIDENCE_STORAGE_PATH>/evidence_chain.jsonl` and has rotation disabled so
continuity does not depend on joining rotated files. An explicit persistent
path can be supplied with `EVIDENCE_CHAIN_PATH`.

## Legacy Records

Old `SIGv1:` values were checksum labels, not cryptographic signatures. IOA
Core preserves them for forensic reading and marks them
`signature_status: unsigned_legacy`. They do not pass `ioa verify`, cannot be
exported as a new signature, and must not be presented as signed in UI or API
surfaces.

## Synthetic Sample

The repository includes a synthetic signed bundle and public key:

- `examples/evidence_bundle_signed.json`
- `examples/evidence_bundle_public_key.pub`

No private key is included. The PyPI clean-install proof is run against the
published 2.9.0 package as part of the GATE0 release procedure.
