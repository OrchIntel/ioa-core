**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# KMS Circuit Breaker Open - Critical Alert

**Alert**: `IOACircuitBreakerOpen` (KMS)  
**Severity**: Critical  
**Impact**: KMS operations are failing, signing operations may be affected

## Immediate Actions

### 1. Acknowledge Alert
- [ ] Acknowledge in AlertManager
- [ ] Notify on-call engineer
- [ ] Check Slack #ioa-critical channel

### 2. Assess Impact
- [ ] Check if signing operations are working
- [ ] Verify if KMS is accessible
- [ ] Check for signature failures

### 3. Investigate Root Cause

#### Check KMS Connectivity
> **Note**: Some commands below are examples for future functionality.

```bash
# Test KMS connectivity
# aws kms list-keys --region us-east-1

# Check KMS key access
# aws kms describe-key --key-id alias/ioa-staging
```

#### Check IOA Logs
```bash
# Check for KMS errors
grep -i "kms" /var/log/ioa/ioa.log | tail -20

# Check circuit breaker logs
grep -i "circuit breaker" /var/log/ioa/ioa.log | tail -20
```

#### Check Network
> **Note**: Some commands below are examples for future functionality.

```bash
# Test network connectivity
# ping kms.us-east-1.amazonaws.com
# telnet kms.us-east-1.amazonaws.com 443
```

### 4. Common Causes

#### AWS Credentials Issues
- **Symptom**: 403 Forbidden errors
- **Check**: `aws sts get-caller-identity`
- **Fix**: Update credentials or IAM permissions

#### KMS Key Access
- **Symptom**: Access denied errors
- **Check**: KMS key permissions
- **Fix**: Update IAM policy for KMS access

#### Network Connectivity
- **Symptom**: Connection timeout errors
- **Check**: Network connectivity to KMS
- **Fix**: Check firewall, proxy, or network configuration

#### KMS Service Issues
- **Symptom**: 5xx errors from AWS
- **Check**: AWS Status Page
- **Fix**: Wait for AWS to resolve or use different region

#### Rate Limiting
- **Symptom**: 429 Too Many Requests
- **Check**: Request rate to KMS
- **Fix**: Implement backoff or reduce request rate

### 5. Resolution Steps

#### Option 1: Reset Circuit Breaker
> **Note**: Some commands below are examples for future functionality.

```bash
# Restart IOA services to reset circuit breaker
# systemctl restart ioa-audit-chain
# systemctl restart ioa-signing

# Check circuit breaker state
# curl http://localhost:8080/metrics | grep ioa_circuit_breaker_state
```

#### Option 2: Fix Underlying Issue
1. **Credentials**: Update AWS credentials
2. **Permissions**: Update IAM policy for KMS
3. **Network**: Fix network connectivity
4. **Rate Limiting**: Implement backoff

#### Option 3: Use Fallback Signing
> **Note**: Some commands below are examples for future functionality.

```bash
# Switch to dev RSA signing temporarily
export IOA_SIGNING_BACKEND=dev
# systemctl restart ioa-signing
```

### 6. Verification

#### Check Circuit Breaker State
> **Note**: Some commands below are examples for future functionality.

```bash
# Should show state=0 (CLOSED)
# curl http://localhost:8080/metrics | grep ioa_circuit_breaker_state
```

#### Test KMS Operations
> **Note**: Some commands below are examples for future functionality.

```bash
# Test signing with KMS
# curl -X POST http://localhost:8080/sign \
#   -H "Content-Type: application/json" \
#   -d '{"data": "test data"}'
```

#### Check Metrics
> **Note**: Some commands below are examples for future functionality.

```bash
# Verify KMS operations are working
# curl http://localhost:8080/metrics | grep ioa_kms_operations_total
```

### 7. Prevention

#### Monitoring
- Set up KMS health checks
- Monitor KMS error rates
- Track circuit breaker state changes

#### Configuration
- Tune circuit breaker thresholds
- Implement proper retry logic
- Use connection pooling

#### Testing
- Regular KMS connectivity tests
- Circuit breaker testing
- Disaster recovery drills

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
- [ ] Review monitoring thresholds
- [ ] Update alerting rules
- [ ] Schedule post-mortem if needed

## Related Alerts

- `IOAKMSFailuresHigh` - High KMS failure rate
- `IOAServiceDown` - IOA service down
- `IOAEncryptionErrors` - Encryption issues

## Contact Information

- **On-call**: ioa-oncall@company.com
- **Slack**: #ioa-critical
- **Phone**: +1-555-IOA-HELP
