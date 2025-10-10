# Doctor Check Example

System health check to verify your IOA Core environment.

## Usage

```bash
python examples/30_doctor/doctor_check.py
```

## Output

Returns JSON with:
- `python_version_ok` - Whether Python 3.10+ is installed
- `python_version` - Exact Python version
- `env_provider_keys` - Which provider API keys are configured (masked)
- `local_cache_writeable` - Whether cache directory is accessible
- `ioa_core_version` - IOA Core version
- `overall_health` - "healthy" or "issues_detected"

## Health Checks

- ✅ Python 3.10+ required
- ✅ Cache directory writeable
- ℹ️ Provider keys (optional, shows which are configured)

## Notes

- Runs offline, no network calls
- Safe to run anytime
- Helps diagnose environment issues

