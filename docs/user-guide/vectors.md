**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Vector Search with IOA Core

IOA Core provides a powerful vector search capability through the CLI, allowing you to search through pattern collections using semantic similarity.

## Quick Start

Search through patterns using the `ioa vectors` command:

> **Note**: Some commands below are examples for future functionality.

```bash
# Basic search
# Example (not currently implemented): ioa vectors --index patterns.json --query "machine learning"

# Search with custom parameters
# Example (not currently implemented): ioa vectors --index patterns.json --query "data processing" --k 5 --backend tfidf --verbose
```

## Command Options

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--index` | `-i` | Yes | - | Path to patterns JSON file |
| `--query` | `-q` | Yes | - | Search query string |
| `--k` | - | No | 3 | Number of results to return |
| `--backend` | `-b` | No | faiss | Search backend (faiss or tfidf) |
| `--verbose` | `-v` | No | false | Enable verbose output |
| `--help` | - | No | - | Show help information |

## Search Backends

### FAISS (Default)
- Fast approximate nearest neighbor search
- Optimized for large-scale vector operations
- Best performance for production use

### TF-IDF
- Traditional text-based search
- Good for smaller datasets
- More interpretable scoring

## Pattern File Format

Your patterns file should be a JSON file with the following structure:

```json
{
  "patterns": [
    {
      "id": "unique-id",
      "name": "Pattern Name",
      "description": "Brief description",
      "content": "Full content text for search",
      "tags": ["tag1", "tag2"],
      "category": "category_name"
    }
  ],
  "metadata": {
    "version": "1.0.0",
    "description": "Collection description"
  }
}
```

## Search Algorithm

The search algorithm uses a multi-field scoring approach:

1. **Content Match**: +3 points for query found in content
2. **Name Match**: +2 points for query found in name
3. **Tag Match**: +1 point for query found in tags

Results are ranked by total score and returned in descending order.

## Examples

### Basic Search
> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa vectors --index examples/patterns.json --query "hello world"
```

### Advanced Search
> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa vectors \
#   --index examples/patterns.json \
#   --query "security encryption" \
#   --k 5 \
#   --backend tfidf \
#   --verbose
```

### Search for Specific Content
> **Note**: Some commands below are examples for future functionality.

```bash
# Find patterns related to APIs
# Example (not currently implemented): ioa vectors --index patterns.json --query "api integration"

# Find security-related patterns
# Example (not currently implemented): ioa vectors --index patterns.json --query "authentication"
```

## Output Format

The command provides structured output with:

- **Result count**: Number of matching patterns found
- **Pattern details**: Name, description, tags, and category
- **Scoring**: Relevance score for each result
- **Verbose mode**: Additional content preview and search metadata

## Troubleshooting

### Common Issues

1. **File not found**: Ensure the patterns file path is correct
2. **No results**: Try different query terms or check file content
3. **Invalid JSON**: Verify your patterns file has valid JSON syntax

### Debug Mode

Use the `--verbose` flag to see detailed search information:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa vectors --index patterns.json --query "test" --verbose
```

This will show:
- Number of patterns loaded
- Search parameters used
- Content previews
- Backend information

## Performance Tips

- Use FAISS backend for large pattern collections
- Keep pattern content concise but descriptive
- Use meaningful tags for better search results
- Consider indexing frequently searched terms

## Integration

The vectors command can be integrated into:

- CI/CD pipelines for pattern validation
- Documentation generation workflows
- Content discovery systems
- Pattern recommendation engines

## Next Steps

- Explore the [Governance System](../governance/GOVERNANCE.md)
- Learn about [Memory Management](../MEMORY_ENGINE.md)
- Check out [Workflows](../WORKFLOWS.md)
