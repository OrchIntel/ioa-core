# IOA Core Makefile
# Add inventory targets to existing Makefile

.PHONY: inventory inventory-fast clean-inventory repo-map-internal repo-map-public

# Run full inventory scan
inventory:
	@echo "Running full file inventory scan..."
	python3 tools/inventory/inventory.py .
	python3 tools/inventory/render_markdown.py ops/reports/$(shell date +%Y-%m-%d)-file-inventory/
	@echo "Inventory complete. Reports generated in ops/reports/$(shell date +%Y-%m-%d)-file-inventory/"

# Run fast inventory scan (skip git blame for speed)
inventory-fast:
	@echo "Running fast file inventory scan..."
	python3 tools/inventory/inventory.py . --fast
	python3 tools/inventory/render_markdown.py ops/reports/$(shell date +%Y-%m-%d)-file-inventory/
	@echo "Fast inventory complete. Reports generated in ops/reports/$(shell date +%Y-%m-%d)-file-inventory/"

# Clean inventory reports
clean-inventory:
	@echo "Cleaning inventory reports..."
	rm -rf ops/reports/*-file-inventory/
	@echo "Inventory reports cleaned."

# Repository mapping targets
repo-map-internal:
	IOA_REPO_MODE=internal python3 tools/inventory/select_repo_map.py

repo-map-public:
	IOA_REPO_MODE=public python3 tools/inventory/select_repo_map.py

# Existing targets (if any) would go here
# Add your existing Makefile content below this line