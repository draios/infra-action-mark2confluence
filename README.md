# mark2confluence

GitHub Action for converting markdown files into Confluence pages

This Action uses [mark](https://github.com/kovetskiy/mark) to accomplish this task

## Inputs

### Required

`action` - `[publish, dry-run, verify]`

- `verify`  - Verify only the conversion from markdown to html
- `dry-run` - Verify in dry-run the conversion will success (connecting to confluence)
- `publish` - Use the given confluence account and push the generated pages

## Required Environment variables

```yaml
BASE_URL: https://your.confluence.url # Confluence base url of your instance
DOC_DIR: docs # Docs directory based on the git repo root
DOC_DIR_PATTERN: ".*" # Regexp to filter markdown files
MODIFIED_INTERVAL: "0" # Last modified files in minutes
CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }} # CONFLUENCE_USERNAME (Confluence username) must be set in GitHub Repo secrets
CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }} # CONFLUENCE_PASSWORD (Confluence api key) must be set in GitHub Repo secrets
HEADER_TEMPLATE: "---\n\n**WARNING**: This page is automatically generated from [this source code]({{source_link}})\n\n---\n" # This is a jinja template used as header, source_link is automatically resolved as github source url of the current file
```

## Optional environment variables

```yaml
FILES: "" # space separated list of file to upload (relative to the repo root directory).
          # if FILES is defined; DOC_DIR, DOC_DIR_PATTERN and MODIFIED_INTERVAL are ignored
```

## Example workflow


```yaml
name: Docs Test and Publish

on: pull_request

jobs:
  helm-suite:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    # - name: myOtherJob1
    #   run:

    - name: Test docs generation
      uses: draios/infra-action-mark2confluence@main
      with:
        action: "dry-run"
        DOC_DIR_PATTERN: ".*"
        DOC_DIR: docs
        CONFLUENCE_BASE_URL: https://your.atlassian.net/wiki
        CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
        CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }}



    - name: Test docs generation
      uses: draios/infra-action-mark2confluence@main
      with:
        action: "publish"
        DOC_DIR_PATTERN: ".*"
        DOC_DIR: docs
        CONFLUENCE_BASE_URL: https://your.atlassian.net/wiki
        CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
        CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }}


```

## Upload only changed files

```yaml
name: Docs Publish

on:
  push:
    branches:
      - main

jobs:
  pull_request:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - uses: tj-actions/changed-files@v14.3
      id: changed-files
      with:
        since_last_remote_commit: "true"

    - name: Test docs generation
      uses: draios/infra-action-mark2confluence@main
      with:
        action: "publish"
        FILES: ${{ steps.changed-filed.outputs.all_changed_files }}
        CONFLUENCE_BASE_URL: https://sysdig.atlassian.net/wiki
        CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
        CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }}

```
