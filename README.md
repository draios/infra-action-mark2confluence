# mark2confluence

GitHub Action for converting markdown files into Confluence pages

This Action uses [mark](https://github.com/kovetskiy/mark) to accomplish this task

## Installation

This project uses `requirements.txt` as the single source of truth for dependencies. Both Poetry and Pipenv can natively read from requirements.txt.

### Quick Setup (Recommended)

```bash
# Using Poetry
make install-poetry

# Or using Pipenv
make install-pipenv
```

### Manual Installation

#### Using Poetry

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies from requirements.txt
poetry add -r requirements.txt

# Run the application
poetry run mark2confluence
```

#### Using Pipenv

```bash
# Install Pipenv if you haven't already
pip install pipenv

# Install dependencies from requirements.txt
pipenv install -r requirements.txt

# Run the application
pipenv run mark2confluence
```

#### Using pip

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install in development mode
pip install -e .

# Run the application
python mark2confluence/main.py
```

### Managing Dependencies

When you update `requirements.txt`, update your preferred package manager:

```bash
# For Poetry
poetry add -r requirements.txt

# For Pipenv
pipenv install -r requirements.txt

# Or use make commands
make sync-poetry
make sync-pipenv
```

## Inputs

### Required

`action` - `[publish, dry-run, verify]`

- `verify`  - Verify only the conversion from markdown to html
- `dry-run` - Verify in dry-run the conversion will success (connecting to confluence)
- `publish` - Use the given confluence account and push the generated pages

## Required Environment variables

```yaml
CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }} # CONFLUENCE_USERNAME (Confluence username) must be set in GitHub Repo secrets
CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }} # CONFLUENCE_PASSWORD (Confluence api key) must be set in GitHub Repo secrets
CONFLUENCE_BASE_URL: https://sysdig.atlassian.net/wiki # Confluence base url
```

## Optional environment variables

```yaml
DOC_DIR: docs # Docs directory based on the git repo root
DOC_DIR_PATTERN: ".*" # Regexp to filter markdown files
MODIFIED_INTERVAL: "0" # Last modified files in minutes
FILES: "" # space separated list of file to upload (relative to the repo root directory).
          # if FILES is defined; DOC_DIR, DOC_DIR_PATTERN and MODIFIED_INTERVAL are ignored
HEADER_TEMPLATE: "---\n\n**WARNING**: This page is automatically generated from [this source code]({{source_link}})\n\n---\n<!-- Include: ac:toc -->\n\n" # This is a jinja template used as header, source_link is automatically resolved as github source url of the current file
MERMAID_PROVIDER: "" # Defines the mermaid provider to use. Supported options are: cloudscript, mermaid-go
default_parents: "" # Automatically inject space and parents headers for the files under the specified directory, format: DIR=SPACE->PARENT1->PARENT2, each definition is separated by a newline
```

### Automatically creating space and parent headers

If you want to avoid to copy and paste the same space and parents for every MD file, you can use the `default_parents` input.
Based on the content of the file it will automatically prepend headers before pushing the file onto confluence.
Only the file with `mark` headers will be modified.

Let's take this example:

```yaml
default_headers: |
  tests/=FOO->Tests
  mark2confluence/=FOO->Code
```

Every `markdawn` file under the `tests` directory that already contains mark headers will be prepended the following headers:
```markdown
<!-- Space: FOO -->
<!-- Parent: Tests -->

<your-content>
```

The directive supports glob matching and prioritize the longest directory first, for example:

```yaml
default_headers: |
  tests/**=FOO->Tests
  tests/resources/**=FOO->Tests->Resources
```

Files under `tests/resources/` will have `FOO->Tests->Resources` as headers, while files under `tests/other-dir` will have `FOO->Tests`.

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

## Verify and publish only changed files

```yaml
name: Docs verification and publish
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
  push:
    branches: main
jobs:
  documentation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
      with:
        # For pushes getting the diff from the previous commit might be tricky:
        # if you squash and merge you will create only one new commit, so you
        # can set 2 as fetch-depth. But if you are rebasing and merging or
        # creating a merge commit you might end up with a long history of
        # new commits, to fetch the previous working commit you should set
        # the fetch-depth to 0 (full history) or an arbitrary value to
        # cover the commit history.
        fetch-depth: ${{ github.event_name == 'pull_request' && 1 || 0 }}

    - uses: tj-actions/changed-files@v14.3
      id: changed-files

    - uses: draios/infra-action-mark2confluence@main
      with:
        action: "${{ github.event_name == 'push' && 'publish' || 'dry-run' }}"
        FILES: ${{ steps.changed-files.outputs.all_changed_files }}
        CONFLUENCE_BASE_URL: https://your.atlassian.net/wiki
        CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
        CONFLUENCE_PASSWORD: ${{ secrets.CONFLUENCE_PASSWORD }}

```
