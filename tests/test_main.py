import os
import pytest
import shutil
from supermutes import dot

import mark2confluence.main as main

RESOURCE_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/resources"
WORKSPACE = os.path.realpath(f"{os.path.dirname(os.path.abspath(__file__))}/..")

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
    assert main.has_mark_headers(f"{resource_directory}/with_mark_space_header.md")
    assert main.has_mark_headers(f"{resource_directory}/with_mark_parent_header.md")
    assert main.has_mark_headers(f"{resource_directory}/with_mark_title_header.md")
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
            main._parse_parent_string(string)
    else:
        directory, space, parents = main._parse_parent_string(string)
        assert directory == expected_dir
        assert space == expected_space
        assert parents == expected_parents

@pytest.mark.parametrize(
    "string,expected_parents_count",
    [
        ("tools/=foo", 1),
        ("tools/=foo\n", 1),
        ("tools/=foo\ntools/=foo", 2),
        ("", 0),
        (None, 0)
    ]
)
def test_get_default_parents(string, expected_parents_count):
    parents = main.get_default_parents(string)
    assert len(parents) == expected_parents_count

@pytest.mark.parametrize(
    "cfg,expected_header",
    [
        (
            main.ParentCfg(directory="test",space="FOO",parents=["BAR", "BAZ"]),
            "<!-- Space: FOO -->\n<!-- Parent: BAR -->\n<!-- Parent: BAZ -->\n",
        ),
        (
            main.ParentCfg(directory="test",space="BAR",parents=["FOO"]),
            "<!-- Space: BAR -->\n<!-- Parent: FOO -->\n",
        ),
        (
            main.ParentCfg(directory="test",space="FOO",parents=[]),
            "<!-- Space: FOO -->\n",
        ),
    ]
)
def test_ParentCfg_get_header(cfg: main.ParentCfg, expected_header):
    assert cfg.get_header() == expected_header

def test_inject_default_parents(monkeypatch):
    monkeypatch.setattr('mark2confluence.main.cfg', dot.dotify({"github": {"WORKSPACE": WORKSPACE}}))

    base_dir = f"{RESOURCE_DIR}/markdown/test_inject_default_parents"
    source_file_path = f"{base_dir}/0-input.md"
    expected_file_path = f"{base_dir}/0-output.md"
    parsed_file_dir = f"{WORKSPACE}/tests/foo"
    parsed_file_path = f"{parsed_file_dir}/parsed_file.md"
    cfgs = [
        main.ParentCfg(directory="tests/foo/bar", space="FOO", parents=["BAZ"]),
        main.ParentCfg(directory="tests/foo/*", space="FOO", parents=["BAR"]),
        main.ParentCfg(directory="tests/*", space="FOO", parents=["BAZ"]),
        main.ParentCfg(directory="mark2confluence/", space="BOZ", parents=["BIZ"]),
    ]

    os.makedirs(parsed_file_dir, exist_ok=True)
    shutil.copy(source_file_path, parsed_file_path)

    main.inject_default_parents(parsed_file_path, cfgs)

    with open(parsed_file_path, "r") as f:
        parsed_file_content =  f.read()
    with open(expected_file_path, "r") as f:
        expected_file_content =  f.read()

    try:
        assert parsed_file_content == expected_file_content
    finally:
        shutil.rmtree(parsed_file_dir)
