import os
import shlex
import sys
import re
import subprocess
from datetime import datetime,timedelta
from fnmatch import fnmatch
from typing import List, Tuple
import jinja2
from loguru import logger
from supermutes import dot
from pprint import pformat
from dataclasses import dataclass

ACTION_PUBLISH = "publish"
ACTION_DRY_RUN = "dry-run"
ACTION_VERIFY = "verify"

ENV_PREFIXES = {
  "inputs": "INPUT_",
  "github": "GITHUB_",
  "actions": "ACTIONS_",
  "runner": "RUNNER_",
}

# SANE DEFAULTS
DEFAULT_INPUTS = {
  "DOC_DIR": "",
  "DOC_DIR_PATTERN": ".*",
  "FILES": "",
  "ACTION": ACTION_DRY_RUN,
  "LOGURU_LEVEL": "INFO",
  "MARK_LOG_LEVEL": "",
  "HEADER_TEMPLATE": "---\n\n**WARNING**: This page is automatically generated from [this source code]({{ source_link }})\n\n---\n<!-- Include: ac:toc -->\n\n",
  "MODIFIED_INTERVAL": "0",
  "CONFLUENCE_PASSWORD": "",
  "CONFLUENCE_USERNAME": "",
  "CONFLUENCE_BASE_URL": "",
  "MERMAID_PROVIDER": "",
  "DEFAULT_PARENTS": "",
}

DEFAULT_GITHUB = {
  "SERVER_URL": "https://github.com",
  "REPOSITORY": "draios/infra-action-mark2confluence",
  "REF_NAME": "main",
  "WORKSPACE": ".",
}

cfg =dot.dotify({
  "inputs": DEFAULT_INPUTS,
  "github": DEFAULT_GITHUB,
  "actions": {},
  "runner": {},
})


def load_vars():
  global cfg
  cfg = dot.dotify(cfg)

  for k, _ in cfg.items():
    logger.info(f"Loading {k} vars from ENV")
    candidate = { key.replace(ENV_PREFIXES[k],""): value for key,value in os.environ.items() if key.startswith(ENV_PREFIXES[k]) }
    for key, value in candidate.items():
      cfg[k][key] = value

  logger.debug(pformat(cfg))

  if os.getenv("LOGURU_LEVEL"):
    logger.remove()
    logger.add(sys.stderr, level=os.getenv['LOGURU_LEVEL'])


def publish(path: str)-> tuple:
  global cfg

  other_args = ""
  if cfg.inputs.ACTION == ACTION_DRY_RUN:
    other_args = "--dry-run"
  elif cfg.inputs.ACTION == ACTION_VERIFY:
    other_args = "--compile-only"

  mermaid_provider = ""
  if cfg.inputs.MERMAID_PROVIDER:
    mermaid_provider = f"--mermaid-provider {cfg.inputs.MERMAID_PROVIDER}"

  # Build command line with proper flag handling
  cmd_parts = ['mark']

  # Add required flags only if values are provided
  if cfg.inputs.CONFLUENCE_PASSWORD:
    cmd_parts.extend(['-p', cfg.inputs.CONFLUENCE_PASSWORD])
  if cfg.inputs.CONFLUENCE_USERNAME:
    cmd_parts.extend(['-u', cfg.inputs.CONFLUENCE_USERNAME])
  if cfg.inputs.CONFLUENCE_BASE_URL:
    cmd_parts.extend(['-b', cfg.inputs.CONFLUENCE_BASE_URL])

  # Add optional flags
  if mermaid_provider:
    cmd_parts.extend(mermaid_provider.split())
  if other_args:
    cmd_parts.extend(other_args.split())

  # Add log level if specified
  if cfg.inputs.MARK_LOG_LEVEL and cfg.inputs.MARK_LOG_LEVEL.upper() in ['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL']:
    cmd_parts.extend(['--log-level', cfg.inputs.MARK_LOG_LEVEL.upper()])
  elif os.getenv('MARK_LOG_LEVEL'):
    cmd_parts.extend(['--log-level', os.getenv('MARK_LOG_LEVEL')])
  elif cfg.inputs.LOGURU_LEVEL and cfg.inputs.LOGURU_LEVEL.upper() in ['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL']:
    cmd_parts.extend(['--log-level', cfg.inputs.LOGURU_LEVEL.upper()])

  # Add file path
  cmd_parts.extend(['-f', path])

  cmd_line = ' '.join(cmd_parts)
  args = shlex.split(cmd_line)
  proc = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = os.path.dirname(path))

  try:
    out, errs = proc.communicate(timeout=120)
    if cfg.inputs.ACTION == ACTION_VERIFY:
      logger.info(f"Verify: mark compiled html: {out}")
  except subprocess.TimeoutExpired:
    proc.kill()
    _, errs = proc.communicate()
    logger.error(f"Exec timeout: {errs}")
    return False, errs
  if proc.returncode != 0:
    return False, errs
  return True, None


def begins_with_mark_headers(path: str, headers: List[str] = ["Space", "Parent", "Title"]) -> bool:
  with open(path, 'r+') as f:
    first_row = f.readline()
    for header in headers:
      regex = re.compile(f"^<!--.?{header}:.*-->", re.IGNORECASE)
      if regex.match(first_row):
        return True
  return False

def begins_with_mark_space_header(path: str):
  return begins_with_mark_headers(path, ["Space"])

class MultilineCommentIsOpenException(Exception):
    pass

def inject_header_before_first_line_of_content(path: str, header: str) -> Tuple[List[str], int]:
  def is_comment_line(line: str) -> bool:
    return re.compile("^<!--.*-->$").match(line.strip())
  def is_opening_comment_line(line: str) -> bool:
    return re.compile("^<!--").match(line.strip()) and not is_comment_line(line)
  def is_closing_comment_line(line: str) -> bool:
    return re.compile("-->$").match(line.strip()) and not is_comment_line(line)

  file_lines = list()
  with open(path, 'r') as f:
    file_lines = f.readlines()

  beginning_of_content_index = 0
  is_inside_multiline_comment = False
  for line in file_lines:
      if is_opening_comment_line(line):
        is_inside_multiline_comment = True
      elif is_closing_comment_line(line):
        is_inside_multiline_comment = False
      elif line.strip() != "" and not is_inside_multiline_comment and not is_comment_line(line):
        break
      beginning_of_content_index += 1

  if is_inside_multiline_comment:
    raise MultilineCommentIsOpenException(f"The file {path} has multiline comments in it that are not closed.")

  file_lines.insert(beginning_of_content_index, header)
  with open(path, "w") as f:
    f.writelines(file_lines)
  return (file_lines, beginning_of_content_index)


def get_files_by_doc_dir_pattern() -> list():
  global cfg

  try:
    pattern = re.compile(cfg.inputs.DOC_DIR_PATTERN)
  except re.error as e:
    logger.error(f"Setup error, DOC_DIR_PATTERN: {e}")
    exit(1)

  topdir = os.path.join(cfg.github.WORKSPACE, cfg.inputs.DOC_DIR)
  logger.info(f"Searching into {topdir}")

  filtered_files = []
  for root, dirs, files in os.walk( topdir ,topdown=True, followlinks=False):

    for file in files:
      # validate regexp on filepath
      path = os.path.join(root,file)
      if pattern.match(path) is None:
        logger.info(f"Doesn't match DOC_DIR_PATTERN, skipping {path}")

      ## validate modified time
      elif int(cfg.inputs.MODIFIED_INTERVAL) > 0:
        mtime: datetime = datetime.fromtimestamp(os.stat(path).st_mtime)
        diff = (datetime.now() -
                timedelta(minutes=int(cfg.inputs.MODIFIED_INTERVAL)))
        if mtime < diff:
          logger.info(f"Is too old, skipping ({mtime}) {path}")
      else:
        filtered_files.append(path)

  return filtered_files

def check_header_template(header_template: str):
  try:
    return jinja2.Template(header_template)
  except jinja2.exceptions.TemplateError as e:
    logger.error(f"Setup error, HEADER_TEMPLATE: {e}")
    exit(1)

@dataclass
class ParentCfg():
  directory: str
  space: str
  parents: List[str]

  def get_header(self) -> str:
    header = f"<!-- Space: {self.space} -->\n"
    for parent in self.parents:
      header += f"<!-- Parent: {parent} -->\n"
    return header

  def is_directory_included(self, directory: str) -> bool:
    global cfg
    sanitized_dir = directory.replace(f"{cfg.github.WORKSPACE}/", "")
    if not sanitized_dir.endswith("/"):
      sanitized_dir += "/"
    return fnmatch(sanitized_dir, self.directory)

def _parse_parent_string(parent_string: str) -> Tuple[str, str, List[str]]:
  dir_separator = "="
  spaces_separator = "->"
  try:
    parent_string_regex = re.compile(rf".+=.+({spaces_separator}.+)*")
    if not parent_string_regex.match(parent_string) or parent_string.endswith(spaces_separator):
      raise ValueError
    directory, space_and_parents = parent_string.split(dir_separator)
    space_and_parents_splitted = space_and_parents.split(spaces_separator)
    space = space_and_parents_splitted[0]
    parents = space_and_parents_splitted[1::]

    if not directory or not space:
      raise ValueError


    return directory, space, parents
  except ValueError:
    msg = f"default_parents must follow the format DIR=SPACE[->PARENT1->PARENT2], provided: {parent_string}"
    logger.error(msg)
    raise ValueError(msg)

def get_default_parents(parents_string: str) -> List[ParentCfg]:
  if not parents_string:
    return []
  default_parents = list()
  parents_string_array = parents_string.split("\n")
  parents_string_array = list(filter(lambda x: x, parents_string_array))
  for parent_string in parents_string_array:
    directory, space, parents = _parse_parent_string(parent_string)
    default_parents.append(ParentCfg(directory, space, parents))
  default_parents.sort(key=lambda cfg: len(cfg.directory), reverse=True)
  return default_parents

def inject_default_parents(path: str, default_parents_cfg: List[ParentCfg]):
  file_dir = f"{os.path.dirname(os.path.abspath(path))}"
  for parent_cfg in default_parents_cfg:
    if parent_cfg.is_directory_included(file_dir) and not begins_with_mark_space_header(path):
      header = parent_cfg.get_header()
      with open(path, 'r') as f:
        file_content = f.read()
      file_content = f"{header}{file_content}"
      with open(path, "w") as f:
        f.write(file_content)
      return


def main()->int:
  global cfg
  load_vars()

  tpl = check_header_template(cfg.inputs.HEADER_TEMPLATE)

  files = []
  if cfg.inputs.FILES:
    files = list(map(
      lambda file: f"{cfg.github.WORKSPACE}/{file}",
      cfg.inputs.FILES.split(" ")
    ))
  else:
    files = get_files_by_doc_dir_pattern()

  logger.info(f"Files to be processed: {', '.join(files)}")

  default_parents = get_default_parents(cfg.inputs.DEFAULT_PARENTS)
  status = {}
  for path in files:
    if path[-3:] == '.md' and begins_with_mark_headers(path):
      logger.info(f"Processing file {path}")
      inject_default_parents(path, default_parents)

      source_link = f"{ cfg.github.SERVER_URL }/{ cfg.github.REPOSITORY }/blob/{ cfg.github.REF_NAME }/{ path.replace(cfg.github.WORKSPACE, '') }"
      header = tpl.render(source_link=source_link)
      inject_header_before_first_line_of_content(path, header)

      status[path] = publish(path)
    else:
      logger.info(f"Skipping headerless or non md file {path}")

  # Calculate counters and exit code
  rc = 0
  for k, v in status.items():
    if not v[0]:
      rc += 1
      logger.error(f"{k} {v[1]}")
  logger.info(f"Success: {len(status)-rc} | Failures: {rc} | Total: {len(status)}")
  return rc

if __name__ == "__main__":
  exit(main())
