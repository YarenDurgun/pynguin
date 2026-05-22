#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019-2026 Pynguin Contributors
#
#  SPDX-License-Identifier: MIT
#
# Fixture for testing specific-line (only_cover_lines) targeting.
#
# It has two completely separate zones:
#   ZONE A  - the coverage TARGET in the test
#   ZONE B  - must be INVISIBLE to Pynguin when only zone A is targeted
#
# Each zone has:
#   - a function-entry line
#   - one branch predicate (if-condition)
#   - two branch-body lines (return statements)
#
# The zones are separated by blank lines so that a line-range targeting
# zone A cannot accidentally include zone B lines.


# ===========================================================================
# ZONE A  -  lines 25-28  -  TARGET THESE IN THE TEST
# ===========================================================================
def zone_a(x: int) -> str:             # line 25 - function entry
    if x > 0:                          # line 26 - branch predicate
        return "positive"              # line 27 - true  branch
    return "non-positive"              # line 28 - false branch
# ===========================================================================




# ===========================================================================
# ZONE B  -  lines 37-40  -  MUST NOT APPEAR IN GOALS WHEN TARGETING ZONE A
# ===========================================================================
def zone_b(x: int) -> str:             # line 37 - function entry
    if x % 2 == 0:                     # line 38 - branch predicate
        return "even"                  # line 39 - true  branch
    return "odd"                       # line 40 - false branch
# ===========================================================================
