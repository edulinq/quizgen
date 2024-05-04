import contextlib
import glob
import json
import importlib
import io
import os
import re
import sys

import tests.base

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TEST_CASES_DIR = os.path.join(THIS_DIR, "test_cases")
DATA_DIR = os.path.join(THIS_DIR, "data")

TEST_CASE_SEP = '---'
DATA_DIR_ID = '__DATA_DIR__'

class CLITest(tests.base.BaseTest):
    """
    Test CLI tools.
    """

    def _get_test_info(self, path):
        options, expected_output = _read_test_file(path)

        module_name = options['cli']
        exit_status = options.get('exit_status', 0)
        is_error = options.get('error', False)

        if (is_error):
            expected_output = expected_output.strip()

        arguments = self.get_base_arguments()
        for key, value in options.get('overrides', {}).items():
            arguments[key] = value

        cli_arguments = []

        for key, value in arguments.items():
            cli_arguments += ["--%s" % (str(key)), str(value)]

        cli_arguments += options.get('arguments', [])

        # Make any substitutions.
        expected_output = _prepare_string(expected_output)
        for i in range(len(cli_arguments)):
            cli_arguments[i] = _prepare_string(cli_arguments[i])

        return module_name, cli_arguments, expected_output, exit_status, is_error

    def get_base_arguments(self):
        return {}

def _prepare_string(text):
    match = re.search(r'%s\(([^)]*)\)' % (DATA_DIR_ID), text)
    if (match is not None):
        filename = match.group(1)

        if (filename == ''):
            path = DATA_DIR
        else:
            path = os.path.join(DATA_DIR, filename)

        text = text.replace(match.group(0), path)

    return text

def _read_test_file(path):
    json_lines = []
    output_lines = []

    with open(path, 'r') as file:
        accumulator = json_lines
        for line in file:
            if (line.strip() == TEST_CASE_SEP):
                accumulator = output_lines
                continue

            accumulator.append(line)

    options = json.loads(''.join(json_lines))
    output = ''.join(output_lines)

    return options, output

def _discover_test_cases():
    for path in sorted(glob.glob(os.path.join(TEST_CASES_DIR, "**", "*.txt"), recursive = True)):
        try:
            _add_test_case(path)
        except Exception as ex:
            raise ValueError("Failed to parse test case '%s'." % (path)) from ex

def _add_test_case(path):
    test_name = 'test_cli__' + os.path.splitext(os.path.basename(path))[0]
    setattr(CLITest, test_name, _get_test_method(path))

def _get_test_method(path):
    def __method(self):
        module_name, cli_arguments, expected_output, expected_exit_status, is_error = self._get_test_info(path)
        module = importlib.import_module(module_name)

        old_args = sys.argv
        sys.argv = [module.__file__] + cli_arguments

        try:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                actual_exit_status = module.main()
            actual_output = output.getvalue()

            if (is_error):
                self.fail("No error was not raised when one was expected ('%s')." % (str(expected_output)))
        except BaseException as ex:
            if (not is_error):
                raise ex

            if (isinstance(ex, SystemExit)):
                if (ex.__context__ is None):
                    self.fail("Unexpected exit without context.")

                ex = ex.__context__

            self.assertEqual(expected_output, str(ex))
            return
        finally:
            sys.argv = old_args

        self.assertEqual(expected_exit_status, actual_exit_status)
        self.assertEqual(expected_output, actual_output)

    return __method

_discover_test_cases()
