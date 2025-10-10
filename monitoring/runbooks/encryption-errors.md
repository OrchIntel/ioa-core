**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Encryption Errors - Critical Alert

**Alert**: `IOAEncryptionErrors`  
**Severity**: Critical  
**Impact**: Audit manifests may be unencrypted, security risk

## Immediate Actions

### 1. Acknowledge Alert
- [ ] Acknowledge in AlertManager
- [ ] Notify on-call engineer
- [ ] Check Slack #ioa-critical channel

### 2. Assess Impact
- [ ] Check if audit manifests are encrypted
- [ ] Verify encryption key is working
- [ ] Check for data exposure

### 3. Investigate Root Cause

#### Check Encryption Configuration
```bash
# Check encryption environment variables
echo $IOA_AUDIT_ENCRYPT_MANIFEST
echo $IOA_AUDIT_ENC_KEY_B64

# Verify encryption key
echo $IOA_AUDIT_ENC_KEY_B64 | base64 -d | wc -c
```

#### Check IOA Logs
```bash
# Check for encryption errors
grep -i "encryption" /var/log/ioa/ioa.log | tail -20

# Check for AES-GCM errors
grep -i "aes" /var/log/ioa/ioa.log | tail -20
```

#### Check Audit Manifests
> **Note**: Some commands below are examples for future functionality.

```bash
# Check if manifests are encrypted
# file /var/lib/ioa/audit_manifest.json
# head -c 100 /var/lib/ioa/audit_manifest.json
```

### 4. Common Causes

#### Invalid Encryption Key
- **Symptom**: "AESGCM key must be 128, 192, or 256 bits"
- **Check**: Key length and format
- **Fix**: Generate proper encryption key

#### Missing Environment Variables
- **Symptom**: "Encryption key not found"
- **Check**: Environment variables
- **Fix**: Set proper environment variables

#### Key Format Issues
- **Symptom**: "Invalid base64 encoding"
- **Check**: Base64 encoding
- **Fix**: Regenerate properly encoded key

#### Crypto Library Issues
- **Symptom**: "Crypto library error"
- **Check**: Python cryptography library
- **Fix**: Update or reinstall cryptography

### 5. Resolution Steps

#### Option 1: Fix Encryption Key
> **Note**: Some commands below are examples for future functionality.

```bash
# Generate new encryption key
python3 -c "
# import base64
# import os
# key = os.urandom(32)  # 256-bit key
# print(base64.b64encode(key).decode())
# "

# Set environment variable
export IOA_AUDIT_ENC_KEY_B64="<generated_key>"
# systemctl restart ioa-audit-chain
```

#### Option 2: Disable Encryption Temporarily
> **Note**: Some commands below are examples for future functionality.

```bash
# Disable encryption temporarily
export IOA_AUDIT_ENCRYPT_MANIFEST=0
# systemctl restart ioa-audit-chain
```

#### Option 3: Fix Environment Variables
> **Note**: Some commands below are examples for future functionality.

```bash
# Set all required encryption variables
export IOA_AUDIT_ENCRYPT_MANIFEST=1
export IOA_AUDIT_ENC_KEY_B64="<valid_key>"
# systemctl restart ioa-audit-chain
```

### 6. Verification

#### Check Encryption Status
> **Note**: Some commands below are examples for future functionality.

```bash
# Check if encryption is working
# curl http://localhost:8080/metrics | grep ioa_encryption_errors_total
```

#### Test Audit Chain
> **Note**: Some commands below are examples for future functionality.

```bash
# Test audit chain with encryption
# curl -X POST http://localhost:8080/audit \
#   -H "Content-Type: application/json" \
#   -d '{"event": "test", "data": {"test": "data"}}'
```

#### Check Manifest Files
> **Note**: Some commands below are examples for future functionality.

```bash
# Verify manifests are encrypted
# file /var/lib/ioa/audit_manifest.json
# Should show "data" or "encrypted" not "ASCII text"
```

### 7. Prevention

#### Monitoring
- Monitor encryption error rates
- Check encryption key validity
- Track encryption success rates

#### Configuration
- Use proper encryption keys
- Set environment variables correctly
- Test encryption on deployment

#### Testing
- Regular encryption tests
- Key rotation testing
- Security audits

## Escalation

If unable to resolve within 15 minutes:
1. **Escalate** to team lead
2. **Notify** manager
3. **Consider** emergency procedures
4. **Document** incident details

## Post-Incident

### Documentation
- [ ] Document root cause
- [ ] Update runbook if needed
- [ ] Share lessons learned

### Follow-up
- [ ] Review encryption configuration
- [ ] Update alerting rules
- [ ] Schedule post-mortem if needed

## Related Alerts

- `IOAServiceDown` - IOA service down
- `IOACircuitBreakerOpen` - Circuit breaker issues
- `IOAAuthFailuresHigh` - Authentication issues

## Contact Information

- **On-call**: ioa-oncall@company.com
- **Slack**: #ioa-critical
- **Phone**: +1-555-IOA-HELP
