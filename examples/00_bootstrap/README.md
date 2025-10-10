# Bootstrap Example

Create a new IOA project with minimal scaffolding.

## Usage

```bash
# Create project with default name
python examples/00_bootstrap/boot_project.py

# Create project with custom name
python examples/00_bootstrap/boot_project.py my-custom-project
```

## Output

Creates a new directory with:
- `ioa.yaml` - Project configuration
- `README.md` - Project documentation

## Notes

- Runs offline, no network calls
- Creates files in current directory
- Safe to run multiple times (won't overwrite existing projects)

