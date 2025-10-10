# Service Down Runbook

## Alert: Service Unavailable

**Severity**: Critical  
**Response Time**: Immediate

## Symptoms

- Service returns 503/504 errors
- Health check endpoints failing
- No response from service

## Diagnostic Steps

1. Check service status
2. Review recent deployments
3. Check resource availability
4. Review logs for errors

## Resolution

1. Restart service if crashed
2. Roll back recent changes if needed
3. Scale up resources if capacity issue
4. Contact on-call engineer if persists

## Prevention

- Implement health checks
- Set up automated restarts
- Monitor resource usage
- Regular capacity planning

## See Also

- [Monitoring Guide](../docs/architecture.md)
- [Deployment Guide](../docs/deployment.md)

