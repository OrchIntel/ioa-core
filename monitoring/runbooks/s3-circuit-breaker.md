**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# S3 Circuit Breaker Open - Critical Alert

**Alert**: `IOACircuitBreakerOpen` (S3)  
**Severity**: Critical  
**Impact**: S3 operations are failing, audit chain storage may be affected

## Immediate Actions

### 1. Acknowledge Alert
- [ ] Acknowledge in AlertManager
- [ ] Notify on-call engineer
- [ ] Check Slack #ioa-critical channel

### 2. Assess Impact
- [ ] Check if audit chain is still functioning
- [ ] Verify if S3 storage is accessible
- [ ] Check for data loss or corruption

### 3. Investigate Root Cause

#### Check S3 Connectivity
> **Note**: Some commands below are examples for future functionality.

```bash
# Test S3 connectivity
# aws s3 ls s3://your-ioa-bucket/ --profile ioa-staging

# Check S3 endpoint
# curl -I https://s3.amazonaws.com/
```

#### Check IOA Logs
```bash
# Check for S3 errors
grep -i "s3" /var/log/ioa/ioa.log | tail -20

# Check circuit breaker logs
grep -i "circuit breaker" /var/log/ioa/ioa.log | tail -20
```

#### Check Network
> **Note**: Some commands below are examples for future functionality.

```bash
# Test network connectivity
# ping s3.amazonaws.com
# telnet s3.amazonaws.com 443
```

### 4. Common Causes

#### AWS Credentials Issues
- **Symptom**: 403 Forbidden errors
- **Check**: `aws sts get-caller-identity`
- **Fix**: Update credentials or IAM permissions

#### Network Connectivity
- **Symptom**: Connection timeout errors
- **Check**: Network connectivity to S3
- **Fix**: Check firewall, proxy, or network configuration

#### S3 Service Issues
- **Symptom**: 5xx errors from AWS
- **Check**: AWS Status Page
- **Fix**: Wait for AWS to resolve or use different region

#### Rate Limiting
- **Symptom**: 429 Too Many Requests
- **Check**: Request rate to S3
- **Fix**: Implement backoff or reduce request rate

### 5. Resolution Steps

#### Option 1: Reset Circuit Breaker
> **Note**: Some commands below are examples for future functionality.

```bash
# Restart IOA services to reset circuit breaker
# systemctl restart ioa-audit-chain
# systemctl restart ioa-storage

# Check circuit breaker state
# curl http://localhost:8080/metrics | grep ioa_circuit_breaker_state
```

#### Option 2: Fix Underlying Issue
1. **Credentials**: Update AWS credentials
2. **Network**: Fix network connectivity
3. **Permissions**: Update IAM permissions
4. **Rate Limiting**: Implement backoff

#### Option 3: Use Fallback Storage
> **Note**: Some commands below are examples for future functionality.

```bash
# Switch to local storage temporarily
export IOA_STORAGE_BACKEND=local
# systemctl restart ioa-storage
```

### 6. Verification

#### Check Circuit Breaker State
> **Note**: Some commands below are examples for future functionality.

```bash
# Should show state=0 (CLOSED)
# curl http://localhost:8080/metrics | grep ioa_circuit_breaker_state
```

#### Test S3 Operations
> **Note**: Some commands below are examples for future functionality.

```bash
# Test audit chain with S3
# curl -X POST http://localhost:8080/audit \
#   -H "Content-Type: application/json" \
#   -d '{"event": "test", "data": {"test": "data"}}'
```

#### Check Metrics
> **Note**: Some commands below are examples for future functionality.

```bash
# Verify S3 operations are working
# curl http://localhost:8080/metrics | grep ioa_s3_operations_total
```

### 7. Prevention

#### Monitoring
- Set up S3 health checks
- Monitor S3 error rates
- Track circuit breaker state changes

#### Configuration
- Tune circuit breaker thresholds
- Implement proper retry logic
- Use connection pooling

#### Testing
- Regular S3 connectivity tests
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

- `IOAS3FailuresHigh` - High S3 failure rate
- `IOAServiceDown` - IOA service down
- `IOAEncryptionErrors` - Encryption issues

## Contact Information

- **On-call**: ioa-oncall@company.com
- **Slack**: #ioa-critical
- **Phone**: +1-555-IOA-HELP
