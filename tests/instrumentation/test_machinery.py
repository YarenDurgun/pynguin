#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2026 Pynguin Contributors
#
#  SPDX-License-Identifier: MIT
#
import asyncio
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys

from pynguin.instrumentation.machinery import InstrumentationLoader, install_import_hook
from pynguin.instrumentation.tracer import SubjectProperties


def test_hook(subject_properties: SubjectProperties):
    with install_import_hook("tests.fixtures.instrumentation.mixed", subject_properties):
        with subject_properties.instrumentation_tracer:
            module = importlib.import_module("tests.fixtures.instrumentation.mixed")
            importlib.reload(module)

        assert len(subject_properties.existing_code_objects) > 0

        with subject_properties.instrumentation_tracer:
            assert module.function(6) == 0


def test_module_instrumentation_integration(subject_properties: SubjectProperties):
    """Tests the instrumentation for various function types."""
    with install_import_hook("tests.fixtures.instrumentation.mixed", subject_properties):
        with subject_properties.instrumentation_tracer:
            mixed = importlib.import_module("tests.fixtures.instrumentation.mixed")
            mixed = importlib.reload(mixed)

        with subject_properties.instrumentation_tracer:
            inst = mixed.TestClass(5)
            inst.method(5)
            inst.method_with_nested(5)
            mixed.function(5)
            sum(mixed.generator())
            asyncio.run(mixed.coroutine(5))
            asyncio.run(run_async_generator(mixed.async_generator()))

        assert (
            len(subject_properties.instrumentation_tracer.get_trace().executed_code_objects) == 10
        )


async def run_async_generator(gen):
    """Small helper to execute async generator."""
    the_sum = 0
    async for i in gen:
        the_sum += i
    return the_sum


def test_pynguin_no_cover_functions(subject_properties: SubjectProperties):
    with install_import_hook(
        "tests.fixtures.instrumentation.covered_functions",
        subject_properties,
    ):
        with subject_properties.instrumentation_tracer:
            covered = importlib.import_module("tests.fixtures.instrumentation.covered_functions")
            covered = importlib.reload(covered)

        assert set(subject_properties.existing_code_objects) == {
            0,  # module code object
            1,  # `covered` function
        }
        assert not subject_properties.existing_predicates

        with subject_properties.instrumentation_tracer:
            covered.not_covered1(1, 2)
            covered.not_covered2(1, 2)
            covered.not_covered3(1, 2, 3)

        assert set(subject_properties.instrumentation_tracer.get_trace().executed_code_objects) == {
            0,
        }

        with subject_properties.instrumentation_tracer:
            covered.covered(4)

        assert set(subject_properties.instrumentation_tracer.get_trace().executed_code_objects) == {
            0,
            1,
        }


def test_pynguin_no_cover_classes(subject_properties: SubjectProperties):
    with install_import_hook(
        "tests.fixtures.instrumentation.covered_classes",
        subject_properties,
    ):
        with subject_properties.instrumentation_tracer:
            covered = importlib.import_module("tests.fixtures.instrumentation.covered_classes")
            covered = importlib.reload(covered)

        assert set(subject_properties.existing_code_objects) == {
            0,  # module code object
            1,  # `Bar` class
            2,  # `Baz` class
            3,  # `baz` method
        }
        assert not subject_properties.existing_predicates

        with subject_properties.instrumentation_tracer:
            covered.Foo().foo()
            covered.Bar().bar()

        assert set(subject_properties.instrumentation_tracer.get_trace().executed_code_objects) == {
            0,
            1,
            2,
        }

        with subject_properties.instrumentation_tracer:
            covered.Bar().bar()
            covered.Baz().baz()

        assert set(subject_properties.instrumentation_tracer.get_trace().executed_code_objects) == {
            0,
            1,
            2,
            3,
        }


class _SourceTreeFinder(importlib.abc.MetaPathFinder):
    """Mimics the finder of a meson-python editable install.

    It maps a module name to a file that the PathFinder cannot find.
    """

    def __init__(self, fullname: str, file_path):
        self._fullname = fullname
        self._file_path = file_path

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self._fullname:
            return None
        return importlib.util.spec_from_file_location(fullname, self._file_path)


def test_hook_falls_back_to_other_finders(subject_properties: SubjectProperties, tmp_path):
    module_name = "pynguin_test_editable_install_module"
    module_file = tmp_path / "hidden" / "module.py"
    module_file.parent.mkdir()
    module_file.write_text("def foo(x):\n    if x > 0:\n        return 1\n    return 0\n")
    finder = _SourceTreeFinder(module_name, module_file)
    sys.meta_path.append(finder)
    try:
        assert importlib.machinery.PathFinder.find_spec(module_name) is None
        with install_import_hook(module_name, subject_properties):
            with subject_properties.instrumentation_tracer:
                module = importlib.import_module(module_name)
            assert isinstance(module.__loader__, InstrumentationLoader)
            assert len(subject_properties.existing_code_objects) > 0
            with subject_properties.instrumentation_tracer:
                assert module.foo(1) == 1
            assert subject_properties.instrumentation_tracer.get_trace().executed_code_objects
    finally:
        sys.meta_path.remove(finder)
        sys.modules.pop(module_name, None)
