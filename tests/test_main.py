import os
import pytest
import shutil

import mark2confluence.main as main

RESOURCE_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/resources"

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
    resource_directory = f"{RESOURCE_DIR}/markdown/test_has_mark_headers"
    assert main.has_mark_headers(f"{resource_directory}/with_mark_headers.md")
    assert not main.has_mark_headers(f"{resource_directory}/without_mark_headers.md")

def test_check_header_template():
    assert main.check_header_template("Valid Jinja2 {{ var }}")
    with pytest.raises(SystemExit, match="1"):
        main.check_header_template("{{")


def test_default_header_template():
    assert main.check_header_template(main.DEFAULT_INPUTS["HEADER_TEMPLATE"])

@pytest.mark.parametrize(
    "file,expected_index,raises",
    [
        ("with_standard_mark_headers", 4, False),
        ("with_macros", 15, False),
        ("with_broken_open_multiline_comments", -1, True),
    ]
)
def test_inject_header(file, expected_index, raises):
    resource_directory = f"{RESOURCE_DIR}/markdown/test_inject_header"
    test_file = f"{file}.md"
    test_path = f"{resource_directory}/{test_file}"
    temp_path = f"/tmp/{test_file}"
    shutil.copyfile(test_path, temp_path)
    header = main.DEFAULT_INPUTS["HEADER_TEMPLATE"]
    if raises:
        with pytest.raises(main.MultilineCommentIsOpenException):
            main.inject_header_before_first_line_of_content(temp_path, header)
    else:
        lines, injected_at_index = main.inject_header_before_first_line_of_content(temp_path, header)
        assert injected_at_index == expected_index
        assert lines[injected_at_index] == header
@pytest.mark.parametrize(
    "string,expected_dir,expected_space,expected_parents,raises",
    [
        ("tools/=foo->bar->baz", "tools/", "foo", ["bar", "baz"], False),
        ("tools/=foo->bar", "tools/", "foo", ["bar"], False),
        ("tools/=foo", "tools/", "foo", [], False),
        ("tools/=", "tools/", "", [], True),
        ("tools/", "", "", [], True),
        ("tools/=foo->", "tools/", "foo", [], True),
        ("=foo", "tools/", "foo", [], True),
    ]
)
def test__parse_parents_string(string, expected_dir, expected_space, expected_parents, raises):
    if raises:
        with pytest.raises(ValueError, match=r"^default_parents.+"):
            main._parse_parents_string(string)
    else:
        directory, space, parents = main._parse_parents_string(string)
        assert directory == expected_dir
        assert space == expected_space
        assert parents == expected_parents
