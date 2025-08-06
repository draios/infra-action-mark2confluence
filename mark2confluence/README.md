# Mark2Confluence Main Script

The `main.py` script is the core component of the Mark2Confluence GitHub Action. It processes Markdown files and converts them to Confluence pages using the `mark` tool.

## Overview

This script:
- Processes Markdown files in a specified directory or specific files
- Injects Confluence-specific headers and metadata
- Handles parent page relationships
- Supports dry-run, publish, and verify modes
- Integrates with GitHub Actions environment

## Features

### 🔧 **Processing Modes**
- **Dry Run**: Test processing without publishing (`--dry-run`)
- **Publish**: Actually publish to Confluence
- **Verify**: Compile HTML only (`--compile-only`)

### 📁 **File Processing**
- Process specific files or entire directories
- Pattern-based file filtering with regex
- Modified time filtering
- Automatic header injection

### 🏷️ **Confluence Integration**
- Automatic header template injection
- Parent page relationship management
- Space and parent page configuration
- Source code link generation

## Configuration

### Environment Variables

The script reads configuration from environment variables with specific prefixes:

#### **Input Variables** (`INPUT_` prefix)
| Variable | Default | Description |
|----------|---------|-------------|
| `DOC_DIR` | `""` | Directory to search for Markdown files |
| `DOC_DIR_PATTERN` | `".*"` | Regex pattern to match files |
| `FILES` | `""` | Space-separated list of specific files |
| `ACTION` | `"dry-run"` | Processing mode: `dry-run`, `publish`, `verify` |
| `LOGURU_LEVEL` | `"INFO"` | Logging level for the script |
| `MARK_LOG_LEVEL` | `""` | Logging level for mark tool (TRACE, DEBUG, INFO, WARNING, ERROR, FATAL) |
| `HEADER_TEMPLATE` | See below | Jinja2 template for page headers |
| `MODIFIED_INTERVAL` | `"0"` | Only process files modified within N minutes |
| `CONFLUENCE_PASSWORD` | `""` | Confluence password |
| `CONFLUENCE_USERNAME` | `""` | Confluence username |
| `CONFLUENCE_BASE_URL` | `""` | Confluence base URL |
| `MERMAID_PROVIDER` | `""` | Mermaid diagram provider |
| `DEFAULT_PARENTS` | `""` | Default parent page configuration |

#### **GitHub Variables** (`GITHUB_` prefix)
| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_URL` | `"https://github.com"` | GitHub server URL |
| `REPOSITORY` | `"draios/infra-action-mark2confluence"` | Repository name |
| `REF_NAME` | `"main"` | Branch/tag name |
| `WORKSPACE` | `"."` | GitHub workspace path |

### Default Header Template

```jinja2
---

**WARNING**: This page is automatically generated from [this source code]({{ source_link }})

---
<!-- Include: ac:toc -->

```

## Usage

### Command Line

```bash
# Basic usage
python mark2confluence/main.py

# With environment variables
DOC_DIR="docs" ACTION="publish" python mark2confluence/main.py
```

### GitHub Action

```yaml
- name: Convert Markdown to Confluence
  uses: draios/infra-action-mark2confluence@v1
  with:
    action: "dry-run"
    doc_dir: "docs"
    doc_dir_pattern: ".*\\.md$"
    confluence_username: ${{ secrets.CONFLUENCE_USERNAME }}
    confluence_password: ${{ secrets.CONFLUENCE_PASSWORD }}
    confluence_base_url: "https://your-domain.atlassian.net"
```

## File Processing Logic

### 1. **File Discovery**
- If `FILES` is specified: Process only those files
- Otherwise: Search `DOC_DIR` using `DOC_DIR_PATTERN`
- Apply modified time filtering if `MODIFIED_INTERVAL > 0`

### 2. **File Validation**
- Only process `.md` files
- Files must have Confluence headers (Space, Parent, Title)
- Skip files without proper headers

### 3. **Header Processing**
- Inject default parent headers if configured
- Add source code link header
- Apply custom header template

### 4. **Publishing**
- Execute `mark` command with appropriate parameters
- Handle timeouts (120 seconds)
- Return success/failure status

## Examples

### **Process Specific Files**
```bash
export INPUT_FILES="README.md docs/guide.md"
export INPUT_ACTION="dry-run"
python mark2confluence/main.py
```

### **Process Directory with Pattern**
```bash
export INPUT_DOC_DIR="docs"
export INPUT_DOC_DIR_PATTERN=".*\\.md$"
export INPUT_MODIFIED_INTERVAL="60"
python mark2confluence/main.py
```

### **With Parent Configuration**
```bash
export INPUT_DEFAULT_PARENTS="docs/=Documentation->User Guide
api/=Documentation->API Reference"
export INPUT_ACTION="publish"
python mark2confluence/main.py
```

### **Custom Header Template**
```bash
export INPUT_HEADER_TEMPLATE="---
Generated from: {{ source_link }}
Last updated: $(date)
---"
python mark2confluence/main.py
```
