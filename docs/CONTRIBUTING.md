# Contributing to IOA Core

**IOA Module:** docs/CONTRIBUTING.md  
**Version:** v2.5.0  
Last-Updated: 2025-10-09
**Agents:** Cursor assist  
**Summary:** Guidelines for contributing to IOA Core

## How to Contribute

### Development Setup

1. Fork the repository
2. Clone your fork locally
3. Install development dependencies:
   ```bash
   pip install -e .[dev]
```

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write docstrings for all public APIs
- Include tests for new functionality

### Testing

Run the test suite before submitting:

```bash
pytest tests/ -v
```

### Pull Request Process

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Update documentation
5. Submit a pull request

## Questions?

For questions about contributing, please open an issue or contact the maintainers.