import os
import shlex
import sys
import re
import subprocess
from datetime import datetime,timedelta
import jinja2
from loguru import logger
from supermutes import dot
from pprint import pformat

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
  "ACTION": ACTION_DRY_RUN,
  "LOGURU_LEVEL": "INFO",
  "HEADER_TEMPLATE": "---\n\n**WARNING**: This page is automatically generated from [this source code]({{ source_link }})\n\n---\n",
  "MODIFIED_INTERVAL": "0",
  "CONFLUENCE_PASSWORD": "",
  "CONFLUENCE_USERNAME": "",
  "CONFLUENCE_BASE_URL": "",
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

space_re = re.compile("\<\!\-\-.?[Ss]pace\:.*\-\-\>", re.MULTILINE)
is_comment_re = re.compile("^\<\!\-\-", re.MULTILINE)
is_empty_line_re = re.compile("^[ \n]*$")

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

  cmd_line = f'mark -p "{cfg.inputs.CONFLUENCE_PASSWORD}" -u "{cfg.inputs.CONFLUENCE_USERNAME}" -b "{cfg.inputs.CONFLUENCE_BASE_URL}" {other_args} --color never --debug -f {path}'
  args = shlex.split(cmd_line)
  proc = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = os.path.dirname(path))

  try:
    _, errs = proc.communicate(timeout=120)
  except subprocess.TimeoutExpired:
    proc.kill()
    _, errs = proc.communicate()
    logger.error(f"Exec timeout: {errs}")
    return False, errs
  if proc.returncode != 0:
    return False, errs
  return True, None


def has_mark_headers(path: str) -> bool:
  global space_re
  with open(path, 'r+') as f:
    data = f.read().split("\n")
    for line in data:
      if space_re.match(line):
        return True
  return False

def inject_header(path: str, header: str) -> bool:
  global is_comment_re, is_empty_line_re
  injected = valid = False

  with open(path, 'r+') as f:
    data = f.read().split("\n")
    i = 0
    for line in data:
      if not is_comment_re.match(line) and not is_empty_line_re.match(line) and not injected:
        injected = True
        data.insert(i, header)
        f.seek(0)
        f.truncate()
        f.write("\n".join(data))
        f.flush()
      i += 1
  return valid

def main()->int:
  global cfg
  load_vars()

  try:
    # Compile regex pattern
    pattern: re.Pattern = re.compile(cfg.inputs.DOC_DIR_PATTERN)
    # Compile header template
    tpl = jinja2.Template(cfg.inputs.HEADER_TEMPLATE)

    # Search into the right directory (this runs into a docker container)
    topdir = os.path.join(cfg.github.WORKSPACE, cfg.inputs.DOC_DIR)
  except Exception as e:
    logger.error(f"Setup error: {e}")

  logger.info(f"Searching into {topdir}")

  status = {}

  for root, dirs, files in os.walk( topdir ,topdown=True, followlinks=False):

    for file in files:
      # Skip files that without .md extension
      if file[-3:] != '.md': continue

      # validate regexp on filepath
      path = os.path.join(root,file)
      if pattern.match(path) is None:
        logger.info(f"Doesn't match DOC_DIR_PATTERN, skipping {path}")
        continue

      ## validate modified time
      if int(cfg.inputs.MODIFIED_INTERVAL) > 0:
        mtime: datetime = datetime.fromtimestamp(os.stat(path).st_mtime)
        diff = (datetime.now() -
                timedelta(minutes=int(cfg.inputs.MODIFIED_INTERVAL)))
        if mtime < diff:
          logger.info(f"Is too old, skipping ({mtime}) {path}")
          continue

      # render header template
      source_link = f"{ cfg.github.SERVER_URL }/{ cfg.github.REPOSITORY }/blob/{ cfg.github.REF_NAME }/{ path.replace(cfg.github.WORKSPACE) }"
      header = tpl.render(source_link=source_link)
      # logger.info(f"Rendering template for {source_link}")

      if not has_mark_headers(path):
        logger.info(f"Skipping headerless file {path}")
        continue

      inject_header(path, header)

      # publish file
      status[path] = publish(path)

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
