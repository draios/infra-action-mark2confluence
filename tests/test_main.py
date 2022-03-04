from nis import match
import os
import pytest

import mark2confluence.main as main

RESOURCE_DIR = "tests/resources"

def clean_github_environment_variables():
    if(os.getenv("CI", False)):
        for env_var in os.environ.keys():
            if env_var.startswith("GITHUB"):
                os.environ.pop(env_var)

def test_load_vars_without_env():
    clean_github_environment_variables()
    main.load_vars()
    assert main.cfg.inputs == main.DEFAULT_INPUTS
    assert main.cfg.github == main.DEFAULT_GITHUB

def test_load_env_prefixes():
    prefixes = main.ENV_PREFIXES
    os.environ[f"{prefixes['inputs']}DOC_DIR_PATTERN"] = "foo"
    os.environ[f"{prefixes['github']}REPOSITORY"] = "foo"
    os.environ[f"{prefixes['actions']}FOO"] = "foo"
    os.environ[f"{prefixes['runner']}FOO"] = "foo"
    main.load_vars()
    assert main.cfg.inputs["DOC_DIR_PATTERN"] == "foo"
    assert main.cfg.github["REPOSITORY"] == "foo"
    assert main.cfg.actions["FOO"] == "foo"
    assert main.cfg.runner["FOO"] == "foo"

def test_has_mark_headers():
    assert main.has_mark_headers(f"{RESOURCE_DIR}/markdown/with_mark_headers.md")
    assert not main.has_mark_headers(f"{RESOURCE_DIR}/markdown/without_mark_headers.md")


def test_check_header_template():
    assert main.check_header_template("Valid Jinja2 {{ var }}")
    with pytest.raises(SystemExit, match="1"):
        main.check_header_template("{{")


def test_default_header_template():
    assert main.check_header_template(main.DEFAULT_INPUTS["HEADER_TEMPLATE"])
