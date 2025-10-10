**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.5.x   | :white_check_mark: |
| 2.4.x   | :x:                |
| 2.3.x   | :x:                |
| < 2.3   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. **DO NOT** create a public GitHub issue
Security vulnerabilities should be reported privately to prevent exploitation.

### 2. Email Security Team
Send details to: security@orchintel.com

### 3. Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if any)

### 4. Response Timeline
- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Based on severity (Critical: 24h, High: 7 days, Medium: 30 days, Low: 90 days)

## Security Features

### Audit Logging
- All operations are logged with structured JSON
- Sensitive data (tokens, emails) are automatically redacted
- Audit logs rotate based on size (~10MB) with SHA-256 integrity
- Immutable JSONL audit rotation policy with configurable size/time limits
- Hash-based integrity verification for all audit entries

### Zero-Retention Controls
- Provider-level data retention flags
- Automatic cleanup of sensitive data
- Configurable retention policies

### PKI Integration
- Agent trust verification via digital signatures
- Tenant isolation enforcement
- Manifest validation against schemas
- AES-256 encryption at rest for cold storage (feature-flagged)
- Configurable encryption key management via environment variables

### Governance Hooks
- Pre/post-operation security checks
- Denial reasoning and audit trails
- Trust registry validation

## Security Best Practices

### Environment Variables
- Never commit API keys or secrets to version control
- Use `.env` files for local development (excluded from git)
- Rotate keys regularly

### Agent Onboarding
- Validate all agent manifests against schemas
- Verify trust signatures before registration
- Enforce tenant isolation

### Network Security
- Use HTTPS for all external API calls
- Implement rate limiting for provider APIs
- Monitor for unusual access patterns

## Known Security Considerations

### LLM Provider APIs
- API keys provide full access to provider services
- Monitor usage and implement spending limits
- Consider using provider-specific security features

### Audit Logs
- Audit logs may contain sensitive information
- Implement proper access controls for log files
- Consider encryption for audit log storage

### Multi-Tenant Isolation
- Verify tenant isolation in multi-tenant deployments
- Implement proper access controls between tenants
- Regular security audits of isolation mechanisms

## Security Updates

Security updates are released as patch versions (e.g., 2.5.1, 2.5.2) and should be applied promptly.

### Critical Updates
- Applied immediately upon release
- May require service restart
- Include security patches and urgent fixes

### Regular Updates
- Applied within 30 days of release
- Include security improvements and bug fixes
- Backward compatible when possible

## Compliance

IOA Core is designed to support various compliance requirements:

- **GDPR**: Data retention controls and audit logging
- **SOC 2**: Comprehensive audit trails and access controls
- **HIPAA**: Secure handling of sensitive data (with proper configuration)

## Security Contacts

- **Security Team**: security@orchintel.com
- **Maintainers**: maintainers@orchintel.com
- **Community**: security-issues@orchintel.com

## Acknowledgments

We thank security researchers and community members who responsibly report vulnerabilities. Contributors to security improvements are acknowledged in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file.
