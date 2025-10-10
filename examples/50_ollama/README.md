# Ollama Turbo Mode Example

Demonstration of Ollama turbo mode optimization for faster local inference.

## Usage

```bash
# Run turbo mode
python examples/50_ollama/turbo_mode_demo.py turbo_cloud

# Run baseline mode
python examples/50_ollama/turbo_mode_demo.py local_preset
```

## Output

Returns JSON with:
- `mode` - Mode being tested
- `p50_ms` - Median latency in milliseconds
- `expected_improvement` - Expected performance gain
- `optimizations` - Which optimizations are enabled
- `note` - Hardware dependency disclaimer

## Turbo Mode Optimizations

- **Reduced Context Window**: Faster processing
- **Lower Temperature**: More deterministic output
- **Optimized Batch Sizes**: Better throughput

## Expected Performance

- **Latency**: 20-40% faster on capable hardware
- **Throughput**: Up to 2x for batch operations
- **Trade-off**: Slightly reduced output creativity

## Notes

- Mock demonstration (sleeps 20ms vs 40ms)
- Real performance varies by hardware (CPU, GPU, RAM, model size)
- For production, benchmark on your specific setup

