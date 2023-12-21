from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..exceptions import ExecutionFailedError, TestsFailedError
from ..utils.files import copy_files
from ..utils.print import print_info
from .tester import Tester


class ClippyTester(Tester):
    @dataclass
    class TaskTestConfig(Tester.TaskTestConfig):
        test_timeout: int = 60  # seconds

        public_test_files: list[str] = field(default_factory=list)
        private_test_files: list[str] = field(default_factory=list)

    def _gen_build(  # type: ignore[override]
            self,
            test_config: TaskTestConfig,
            build_dir: Path,
            source_dir: Path,
            public_tests_dir: Path | None,
            private_tests_dir: Path | None,
            tests_root_dir: Path,
            sandbox: bool = True,
            verbose: bool = False,
            normalize_output: bool = False,
    ) -> None:
        if public_tests_dir is not None:
            self._executor(
                copy_files,
                source=public_tests_dir,
                target=source_dir,
                patterns=test_config.public_test_files,
                verbose=verbose,
            )

        if private_tests_dir is not None:
            self._executor(
                copy_files,
                source=private_tests_dir,
                target=source_dir,
                patterns=test_config.private_test_files,
                verbose=verbose,
            )

    def _clean_build(  # type: ignore[override]
            self,
            test_config: TaskTestConfig,
            build_dir: Path,
            source_dir: Path,
            verbose: bool = False,
    ) -> None:
        # self._executor(
        #     ['rm', '-rf', str(build_dir)],
        #     check=False,
        #     verbose=verbose,
        # )
        pass

    def _run_tests(  # type: ignore[override]
            self,
            test_config: TaskTestConfig,
            build_dir: Path,
            source_dir: Path,
            sandbox: bool = False,
            verbose: bool = False,
            normalize_output: bool = False,
    ) -> float:
        cmake_cmd = ['/opt/shad/clippy/bin/clippy', 'cmake']

        cmake_err = None
        try:
            print_info('Running cmake...', color='orange')
            cmake_output = self._executor(
                cmake_cmd,
                sandbox=sandbox,
                cwd=str(source_dir),
                verbose=verbose,
                capture_output=True,
            )
            print_info(cmake_output, end='')
        except ExecutionFailedError as e:
            cmake_err = e
            print_info(e.output, end='')
            print_info('ERROR', color='red')

        if cmake_err is not None:
            raise TestsFailedError('Cmake error', output=cmake_err.output) from cmake_err

        tests_cmd = ['/opt/shad/clippy/bin/clippy', 'test']

        tests_err = None
        try:
            print_info('Running tests...', color='orange')
            output = self._executor(
                tests_cmd,
                sandbox=sandbox,
                cwd=str(source_dir),
                timeout=test_config.test_timeout,
                verbose=verbose,
                capture_output=True,
            )
            print_info(output, end='')
            print_info('OK', color='green')
        except ExecutionFailedError as e:
            tests_err = e
            print_info(e.output, end='')
            print_info('ERROR', color='red')

        if tests_err is not None:
            raise TestsFailedError('Tests error', output=tests_err.output) from tests_err

        return 1.
