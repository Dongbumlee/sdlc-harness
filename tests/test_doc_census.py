"""Gate the numbers reader docs state against the tree's own census.

README, the guides, the quick reference, and the Pages site all restate
counts (agents, skills, templates, canaries, ...). When the tree grows
and the prose does not, the repo disagrees with itself in the first
place a new reader looks. tools/check_doc_census.py computes each count
from the tree and compares every stated number in the reader docs;
these tests pin the census values it must compute today and the
mismatch behaviour, and run the check itself against the live tree.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "check_doc_census", REPO_ROOT / "tools" / "check_doc_census.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_census_matches_the_shipped_tree():
    census = load_tool().compute_census(REPO_ROOT)
    assert census == {
        "agents": 22,
        "skills": 25,
        "templates": 30,
        "stacks": 6,
        "canaries": 60,
        "eval_specs": 25,
        "prompt_files": 6,
        "instruction_files": 14,
        "checklists": 7,
        "bug_corpus": 338,
    }


def test_reader_docs_agree_with_census():
    tool = load_tool()
    census = tool.compute_census(REPO_ROOT)
    assert tool.find_mismatches(REPO_ROOT, census) == []


def test_a_wrong_stated_number_is_flagged(tmp_path):
    tool = load_tool()
    (tmp_path / "README.md").write_text(
        "Install once — get all 99 agents and 25 skills.\n", encoding="utf-8"
    )
    census = dict.fromkeys(tool.NOUN_TO_KEY.values(), 0)
    census.update({"agents": 22, "skills": 25})
    mismatches = tool.find_mismatches(tmp_path, census)
    assert [(m[2], m[3], m[4]) for m in mismatches] == [("agents", 99, 22)]


def test_shipped_surface_is_the_sum_of_its_parts():
    surface = load_tool().shipped_surface(REPO_ROOT)
    assert surface["total"] == surface["agents"] + surface["skills"]
    assert surface["agents"] > 0 and surface["skills"] > 0


def test_group_count_spans_are_subtotals_not_totals(tmp_path):
    tool = load_tool()
    (tmp_path / "index.html").write_text(
        '<span class="group-count">02 AGENTS</span> of 22 agents total.\n',
        encoding="utf-8",
    )
    census = dict.fromkeys(tool.NOUN_TO_KEY.values(), 0)
    census.update({"agents": 22})
    assert tool.find_mismatches(tmp_path, census) == []
