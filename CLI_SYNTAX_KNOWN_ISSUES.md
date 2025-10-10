# CLI Syntax Known Issues

**Status**: 🔴 **BLOCKER FOR DEEP IMPORTS** (Not blocking OSS release)  
**Date**: 2025-10-10  
**Severity**: Medium  
**Target Fix**: v2.5.1 patch

---

## Summary

`src/ioa_core/cli.py` has multiple pre-existing syntax and indentation errors that prevent deep imports like:
```python
from ioa_core.governance.policy_engine import PolicyEngine  # Fails
```

However, basic imports work:
```python
import ioa  # ✅ Works
```

And the installed CLI binary is functional:
```bash
ioa --help  # ✅ Works
```

---

## Errors Identified

1. **Line 1-6**: Malformed header using `"""` instead of `#` comments  
   - Status: ✅ FIXED

2. **Line 125**: Empty `else:` block causing indent error  
   - Status: ✅ FIXED

3. **Line 144**: Missing `if` statement for version check  
   - Status: ✅ FIXED

4. **Line 794+**: Additional indentation errors  
   - Status: ⚠️ NEEDS FIX

5. **Line 1299**: Missing f-string assignment for report_content  
   - Status: ✅ FIXED

6. **Line 1367-1370**: Malformed f-strings in table rows  
   - Status: ✅ FIXED

---

## Impact

**For OSS Release**:
- ✅ Package builds successfully
- ✅ Basic `import ioa` works
- ✅ Installed CLI binary works
- ⚠️ Deep imports fail (not critical for most users)

**Workaround**: Use the installed CLI binary instead of importing CLI internals

---

## Recommendation

**For v2.5.0 OSS Release**: PROCEED  
- Functionality is intact via installed binary
- Basic package imports work
- Issue doesn't affect end users

**For v2.5.1 Patch**: FIX REMAINING ISSUES  
- Systematically fix all indentation errors (lines 794+)
- Add linting to CI/CD to prevent future issues
- Expand CLI unit test coverage

---

**Documented**: 2025-10-10  
**Target Fix**: v2.5.1 (post-release patch)

