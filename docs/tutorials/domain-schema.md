**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Domain Schema Tutorial

This tutorial covers domain schema validation in IOA Core, including schema definition, validation, and integration with workflows.

## Quick Start

### 1. Define Schema
```yaml
# domain_schema.yaml
name: "Data Analysis Domain"
description: "Schema for data analysis workflows"

entities:
  - name: "Dataset"
    fields:
      - name: "id"
        type: "string"
        required: true
        pattern: "^[a-zA-Z0-9_-]+$"
      - name: "name"
        type: "string"
        required: true
        max_length: 100
      - name: "size_mb"
        type: "number"
        required: true
        min_value: 0.1
      - name: "format"
        type: "string"
        enum: ["csv", "json", "parquet", "excel"]
        required: true

  - name: "Analysis"
    fields:
      - name: "id"
        type: "string"
        required: true
      - name: "dataset_id"
        type: "string"
        required: true
        reference: "Dataset.id"
      - name: "type"
        type: "string"
        enum: ["statistical", "ml", "visualization"]
        required: true
      - name: "parameters"
        type: "object"
        required: false
```

### 2. Validate Schema
> **Note**: Some commands below are examples for future functionality.

```bash
# Validate schema file
# Example (not currently implemented): ioa governance schema validate --file domain_schema.yaml

# Validate against data
# Example (not currently implemented): ioa governance schema validate --file domain_schema.yaml --data sample_data.json
```

### 3. Use in Workflow
```yaml
# workflow.yaml
name: "Data Analysis"
schema: "domain_schema.yaml"

steps:
  - name: "validate_input"
    task: "Validate input data against schema"
    schema_validation: true
```

## Schema Definition

### Basic Structure
```yaml
name: "Domain Name"
description: "Domain description"

entities:
  - name: "EntityName"
    description: "Entity description"
    fields:
      - name: "field_name"
        type: "string|number|boolean|object|array"
        required: true|false
        # Additional constraints...
```

### Field Types

#### String Fields
```yaml
- name: "title"
  type: "string"
  required: true
  min_length: 1
  max_length: 200
  pattern: "^[A-Za-z0-9\\s]+$"
  default: "Untitled"
```

#### Number Fields
```yaml
- name: "price"
  type: "number"
  required: true
  min_value: 0.0
  max_value: 10000.0
  precision: 2
  unit: "USD"
```

#### Boolean Fields
```yaml
- name: "active"
  type: "boolean"
  required: false
  default: true
```

#### Object Fields
```yaml
- name: "metadata"
  type: "object"
  required: false
  properties:
    - name: "created_by"
      type: "string"
      required: true
    - name: "tags"
      type: "array"
      items:
        type: "string"
```

#### Array Fields
```yaml
- name: "tags"
  type: "array"
  required: false
  min_items: 0
  max_items: 10
  items:
    type: "string"
    max_length: 50
```

### Relationships
```yaml
entities:
  - name: "User"
    fields:
      - name: "id"
        type: "string"
        required: true
      - name: "name"
        type: "string"
        required: true

  - name: "Post"
    fields:
      - name: "id"
        type: "string"
        required: true
      - name: "user_id"
        type: "string"
        required: true
        reference: "User.id"
      - name: "title"
        type: "string"
        required: true
```

## Validation Rules

### Built-in Validators
```yaml
- name: "email"
  type: "string"
  required: true
  format: "email"

- name: "url"
  type: "string"
  required: false
  format: "url"

- name: "date"
  type: "string"
  required: true
  format: "date"

- name: "datetime"
  type: "string"
  required: true
  format: "datetime"
```

### Custom Validators
```yaml
- name: "product_code"
  type: "string"
  required: true
  custom_validator: "product_code_format"
  validator_params:
    prefix: "PROD"
    length: 10
```

### Conditional Validation
```yaml
- name: "shipping_address"
  type: "object"
  required: false
  conditional:
    field: "requires_shipping"
    value: true
    required: true
```

## Schema Integration

### Python Validation
```python
from src.governance.schema_validator import SchemaValidator

# Load schema
validator = SchemaValidator("domain_schema.yaml")

# Validate data
data = {
    "id": "dataset_001",
    "name": "Sales Data",
    "size_mb": 15.5,
    "format": "csv"
}

result = validator.validate("Dataset", data)

if result.is_valid:
    print("✅ Data is valid")
else:
    print("❌ Validation errors:")
    for error in result.errors:
        print(f"  - {error.field}: {error.message}")
```

### Workflow Integration
```python
class SchemaValidatedWorkflow:
    def __init__(self, schema_file: str):
        self.validator = SchemaValidator(schema_file)
    
    async def execute_step(self, step_name: str, data: dict) -> dict:
        # Validate input data
        validation_result = self.validator.validate(step_name, data)
        
        if not validation_result.is_valid:
            raise ValueError(f"Schema validation failed: {validation_result.errors}")
        
        # Execute step
        result = await self._execute_step_internal(step_name, data)
        
        # Validate output data
        output_validation = self.validator.validate(f"{step_name}_output", result)
        
        if not output_validation.is_valid:
            raise ValueError(f"Output validation failed: {output_validation.errors}")
        
        return result
```

### CLI Integration
> **Note**: Some commands below are examples for future functionality.

```bash
# Validate schema file
# Example (not currently implemented): ioa governance schema validate --file domain_schema.yaml

# Validate data against schema
# Example (not currently implemented): ioa governance schema validate \
#     --file domain_schema.yaml \
#     --entity Dataset \
#     --data '{"id": "test", "name": "Test Dataset", "size_mb": 10, "format": "csv"}'

# Generate schema documentation
# Example (not currently implemented): ioa governance schema docs --file domain_schema.yaml --output docs/schema/

# Export schema as JSON
# Example (not currently implemented): ioa governance schema export --file domain_schema.yaml --format json --output schema.json
```

## Advanced Features

### Schema Inheritance
```yaml
entities:
  - name: "BaseEntity"
    fields:
      - name: "id"
        type: "string"
        required: true
      - name: "created_at"
        type: "string"
        format: "datetime"
        required: true

  - name: "User"
    extends: "BaseEntity"
    fields:
      - name: "name"
        type: "string"
        required: true
      - name: "email"
        type: "string"
        format: "email"
        required: true
```

### Schema Composition
```yaml
entities:
  - name: "Address"
    fields:
      - name: "street"
        type: "string"
        required: true
      - name: "city"
        type: "string"
        required: true
      - name: "country"
        type: "string"
        required: true

  - name: "Customer"
    fields:
      - name: "id"
        type: "string"
        required: true
      - name: "name"
        type: "string"
        required: true
      - name: "addresses"
        type: "array"
        items:
          $ref: "Address"
        required: false
```

### Dynamic Schemas
```yaml
entities:
  - name: "ConfigurableEntity"
    fields:
      - name: "type"
        type: "string"
        required: true
        enum: ["type_a", "type_b", "type_c"]
      - name: "config"
        type: "object"
        required: true
        dynamic_schema:
          field: "type"
          schemas:
            type_a: "type_a_config.yaml"
            type_b: "type_b_config.yaml"
            type_c: "type_c_config.yaml"
```

## Error Handling

### Validation Errors
```python
class ValidationError:
    def __init__(self, field: str, message: str, code: str = None):
        self.field = field
        self.message = message
        self.code = code

# Handle validation errors
try:
    result = validator.validate("Dataset", data)
except ValidationError as e:
    print(f"Validation failed for {e.field}: {e.message}")
    
    # Handle specific error codes
    if e.code == "REQUIRED_FIELD":
        print("Missing required field")
    elif e.code == "INVALID_FORMAT":
        print("Invalid data format")
```

### Custom Error Messages
```yaml
- name: "email"
  type: "string"
  required: true
  format: "email"
  error_messages:
    required: "Email address is required"
    format: "Please provide a valid email address"
    pattern: "Email must match expected format"
```

## Performance Optimization

### Schema Caching
```python
class CachedSchemaValidator:
    def __init__(self):
        self._cache = {}
        self._schema_cache = {}
    
    def validate(self, schema_file: str, entity: str, data: dict) -> ValidationResult:
        # Cache schema file
        if schema_file not in self._schema_cache:
            self._schema_cache[schema_file] = self._load_schema(schema_file)
        
        schema = self._schema_cache[schema_file]
        
        # Cache validation results for common patterns
        cache_key = f"{schema_file}:{entity}:{hash(str(data))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Perform validation
        result = self._validate_data(schema, entity, data)
        
        # Cache result
        self._cache[cache_key] = result
        return result
```

### Batch Validation
```python
def validate_batch(validator: SchemaValidator, entity: str, data_list: list) -> list:
    """Validate multiple data items efficiently"""
    results = []
    
    for data in data_list:
        try:
            result = validator.validate(entity, data)
            results.append(result)
        except ValidationError as e:
            results.append(ValidationResult(is_valid=False, errors=[e]))
    
    return results
```

## Testing

### Schema Testing
```python
import pytest
from src.governance.schema_validator import SchemaValidator

class TestDomainSchema:
    @pytest.fixture
    def validator(self):
        return SchemaValidator("domain_schema.yaml")
    
    def test_valid_dataset(self, validator):
        data = {
            "id": "test_001",
            "name": "Test Dataset",
            "size_mb": 10.5,
            "format": "csv"
        }
        
        result = validator.validate("Dataset", data)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_dataset(self, validator):
        data = {
            "id": "",  # Empty ID
            "name": "A" * 200,  # Too long name
            "size_mb": -5,  # Negative size
            "format": "invalid_format"  # Invalid format
        }
        
        result = validator.validate("Dataset", data)
        assert not result.is_valid
        assert len(result.errors) == 4
        
        # Check specific errors
        error_fields = [e.field for e in result.errors]
        assert "id" in error_fields
        assert "name" in error_fields
        assert "size_mb" in error_fields
        assert "format" in error_fields
```

### Integration Testing
```python
class TestSchemaWorkflow:
    async def test_workflow_with_schema_validation(self):
        workflow = SchemaValidatedWorkflow("domain_schema.yaml")
        
        # Test valid data
        valid_data = {"id": "test", "name": "Test", "size_mb": 10, "format": "csv"}
        result = await workflow.execute_step("Dataset", valid_data)
        assert result is not None
        
        # Test invalid data
        invalid_data = {"id": "", "name": "Test", "size_mb": -5, "format": "invalid"}
        
        with pytest.raises(ValueError) as exc_info:
            await workflow.execute_step("Dataset", invalid_data)
        
        assert "Schema validation failed" in str(exc_info.value)
```

## Best Practices

1. **Schema Design**
   - Use descriptive names
   - Provide clear documentation
   - Keep schemas focused and modular

2. **Validation**
   - Validate early and often
   - Provide clear error messages
   - Use appropriate constraints

3. **Performance**
   - Cache schemas and results
   - Use batch validation when possible
   - Monitor validation performance

4. **Maintenance**
   - Version schemas properly
   - Maintain backward compatibility
   - Regular schema reviews

## Next Steps

1. Define your domain schemas
2. Integrate validation into workflows
3. Test schema validation
4. Monitor validation performance
5. Iterate and improve schemas

## Related Docs

- [Governance Tutorial](governance-audit.md)
- [Workflow Tutorial](hello-world.md)
- [API Reference](../api/governance.md)
