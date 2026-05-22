#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019-2026 Pynguin Contributors
#
#  SPDX-License-Identifier: MIT
#
"""Tests for specific-line targeting via ToCoverConfiguration.only_cover_lines.

The SUT fixture (line_targeting_sut.py) has two clearly separated zones:

    ZONE A  lines 25-28:  def zone_a  +  its branch predicate + bodies
    ZONE B  lines 37-40:  def zone_b  +  its branch predicate + bodies

Each test instruments the SUT and then inspects SubjectProperties directly
(existing_lines, existing_predicates) to check which lines/branches Pynguin
registered as coverage goals.  No GA is run.

Pass criteria are stated as plain inequalities so a failure message shows
exactly which lines appeared or were missing.
"""
from __future__ import annotations

import importlib

import pytest

from pynguin.configuration import CoverageMetric, ToCoverConfiguration
from pynguin.instrumentation.machinery import install_import_hook
from pynguin.instrumentation.tracer import SubjectProperties

# ---------------------------------------------------------------------------
# Constants matching line_targeting_sut.py
# ---------------------------------------------------------------------------
MODULE = "tests.fixtures.instrumentation.line_targeting_sut"

# ZONE A  (the target)
ZONE_A_LINES: frozenset[int] = frozenset({25, 26, 27, 28})
ZONE_A_PREDICATE_LINE = 26      # the "if x > 0" branch

# ZONE B  (must stay out of goals when only zone A is targeted)
ZONE_B_LINES: frozenset[int] = frozenset({37, 38, 39, 40})
ZONE_B_PREDICATE_LINE = 38      # the "if x % 2 == 0" branch

ALL_ZONE_LINES = ZONE_A_LINES | ZONE_B_LINES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _registered_line_numbers(sp: SubjectProperties) -> frozenset[int]:
    """Return the set of line numbers registered as LINE coverage goals."""
    return frozenset(meta.line_number for meta in sp.existing_lines.values())


def _registered_predicate_lines(sp: SubjectProperties) -> frozenset[int]:
    """Return the set of line numbers for registered BRANCH predicates."""
    return frozenset(meta.line_no for meta in sp.existing_predicates.values())


def _instrument(
    module_name: str,
    subject_properties: SubjectProperties,
    to_cover_config: ToCoverConfiguration | None = None,
) -> None:
    """Install the import hook, import/reload the module, then uninstall."""
    if to_cover_config is None:
        to_cover_config = ToCoverConfiguration()

    with install_import_hook(
        module_name,
        subject_properties,
        coverage_metrics={CoverageMetric.LINE, CoverageMetric.BRANCH},
        to_cover_config=to_cover_config,
    ):
        with subject_properties.instrumentation_tracer:
            mod = importlib.import_module(module_name)
            importlib.reload(mod)


# ---------------------------------------------------------------------------
# Baseline: no targeting  ->  BOTH zones must be registered
# ---------------------------------------------------------------------------

def test_baseline_no_targeting_registers_both_zones(subject_properties: SubjectProperties):
    """Without any targeting both zone A and zone B lines/predicates are goals."""
    _instrument(MODULE, subject_properties)

    lines = _registered_line_numbers(subject_properties)
    predicates = _registered_predicate_lines(subject_properties)

    # ---- All zone A lines must be present ----
    missing_a = ZONE_A_LINES - lines
    assert not missing_a, (
        f"FAIL (baseline): zone A lines missing from goals: {sorted(missing_a)}\n"
        f"Registered lines: {sorted(lines)}"
    )

    # ---- All zone B lines must be present ----
    missing_b = ZONE_B_LINES - lines
    assert not missing_b, (
        f"FAIL (baseline): zone B lines missing from goals: {sorted(missing_b)}\n"
        f"Registered lines: {sorted(lines)}"
    )

    # ---- Both predicates must be present ----
    assert ZONE_A_PREDICATE_LINE in predicates, (
        f"FAIL (baseline): zone A predicate (line {ZONE_A_PREDICATE_LINE}) not in predicates.\n"
        f"Registered predicate lines: {sorted(predicates)}"
    )
    assert ZONE_B_PREDICATE_LINE in predicates, (
        f"FAIL (baseline): zone B predicate (line {ZONE_B_PREDICATE_LINE}) not in predicates.\n"
        f"Registered predicate lines: {sorted(predicates)}"
    )


# ---------------------------------------------------------------------------
# Targeting ZONE A only  ->  zone A in, zone B completely absent
# ---------------------------------------------------------------------------

def test_targeting_zone_a_registers_only_zone_a_lines(subject_properties: SubjectProperties):
    """only_cover_lines targeting zone A must not register any zone B lines."""
    _instrument(
        MODULE,
        subject_properties,
        ToCoverConfiguration(only_cover_lines=["25-28"]),
    )

    lines = _registered_line_numbers(subject_properties)

    # ---- Zone A lines must be present ----
    missing_a = ZONE_A_LINES - lines
    assert not missing_a, (
        f"FAIL: zone A lines were not registered as goals: {sorted(missing_a)}\n"
        f"Registered lines: {sorted(lines)}"
    )

    # ---- Zone B lines must be completely absent ----
    leaked_b = ZONE_B_LINES & lines
    assert not leaked_b, (
        f"FAIL: zone B lines leaked into goals despite targeting only zone A: {sorted(leaked_b)}\n"
        f"Registered lines: {sorted(lines)}"
    )

    # ---- No extra lines outside zone A ----
    extra = lines - ZONE_A_LINES
    assert not extra, (
        f"FAIL: extra lines outside zone A were registered as goals: {sorted(extra)}\n"
        f"Registered lines: {sorted(lines)}"
    )


def test_targeting_zone_a_registers_only_zone_a_predicate(subject_properties: SubjectProperties):
    """only_cover_lines targeting zone A must not register the zone B predicate."""
    _instrument(
        MODULE,
        subject_properties,
        ToCoverConfiguration(only_cover_lines=["25-28"]),
    )

    predicates = _registered_predicate_lines(subject_properties)

    # ---- Zone A predicate must be present ----
    assert ZONE_A_PREDICATE_LINE in predicates, (
        f"FAIL: zone A predicate (line {ZONE_A_PREDICATE_LINE}) not registered.\n"
        f"Registered predicate lines: {sorted(predicates)}"
    )

    # ---- Zone B predicate must be absent ----
    assert ZONE_B_PREDICATE_LINE not in predicates, (
        f"FAIL: zone B predicate (line {ZONE_B_PREDICATE_LINE}) leaked into goals.\n"
        f"Registered predicate lines: {sorted(predicates)}"
    )


# ---------------------------------------------------------------------------
# Targeting ZONE B only  ->  zone B in, zone A completely absent
# ---------------------------------------------------------------------------

def test_targeting_zone_b_registers_only_zone_b_lines(subject_properties: SubjectProperties):
    """only_cover_lines targeting zone B must not register any zone A lines."""
    _instrument(
        MODULE,
        subject_properties,
        ToCoverConfiguration(only_cover_lines=["37-40"]),
    )

    lines = _registered_line_numbers(subject_properties)

    missing_b = ZONE_B_LINES - lines
    assert not missing_b, (
        f"FAIL: zone B lines were not registered as goals: {sorted(missing_b)}\n"
        f"Registered lines: {sorted(lines)}"
    )

    leaked_a = ZONE_A_LINES & lines
    assert not leaked_a, (
        f"FAIL: zone A lines leaked into goals despite targeting only zone B: {sorted(leaked_a)}\n"
        f"Registered lines: {sorted(lines)}"
    )


# ---------------------------------------------------------------------------
# Targeting a single line  ->  exactly that line, nothing else
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("target_line", sorted(ZONE_A_LINES))
def test_targeting_single_zone_a_line(target_line: int, subject_properties: SubjectProperties):
    """Targeting a single line from zone A registers only that line."""
    _instrument(
        MODULE,
        subject_properties,
        ToCoverConfiguration(only_cover_lines=[str(target_line)]),
    )

    lines = _registered_line_numbers(subject_properties)

    assert target_line in lines, (
        f"FAIL: targeted line {target_line} was not registered.\n"
        f"Registered lines: {sorted(lines)}"
    )

    extra = lines - {target_line}
    assert not extra, (
        f"FAIL: extra lines registered when only targeting line {target_line}: {sorted(extra)}\n"
        f"Registered lines: {sorted(lines)}"
    )


# ---------------------------------------------------------------------------
# Targeting by function name (only_cover)  ->  whole function, zone B absent
# ---------------------------------------------------------------------------

def test_only_cover_function_name_registers_whole_zone_a(subject_properties: SubjectProperties):
    """only_cover targeting zone_a by name covers all zone A lines, not zone B."""
    _instrument(
        MODULE,
        subject_properties,
        ToCoverConfiguration(only_cover=["zone_a"]),
    )

    lines = _registered_line_numbers(subject_properties)

    missing_a = ZONE_A_LINES - lines
    assert not missing_a, (
        f"FAIL: zone A lines missing when targeting by function name: {sorted(missing_a)}\n"
        f"Registered lines: {sorted(lines)}"
    )

    leaked_b = ZONE_B_LINES & lines
    assert not leaked_b, (
        f"FAIL: zone B lines leaked when targeting zone_a by name: {sorted(leaked_b)}\n"
        f"Registered lines: {sorted(lines)}"
    )
