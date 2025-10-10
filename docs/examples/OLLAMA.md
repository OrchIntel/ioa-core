# Ollama Turbo Mode Guide

Optimize local model performance with turbo mode.

## Demo

```bash
# Turbo mode
python examples/50_ollama/turbo_mode_demo.py turbo_cloud

# Baseline
python examples/50_ollama/turbo_mode_demo.py local_preset
```

## Performance

- 20-40% latency improvement (hardware dependent)
- Reduced context window
- Lower temperature
- Optimized batch sizes

See [examples/50_ollama/README.md](../../examples/50_ollama/README.md) for details.
