#!/usr/bin/python3

import argparse
import os
import re
import shutil
import stat
import subprocess

ARGOS_CONFIG_DIR = '~/.config/argos'
ARGOS_EXTENSION_DIR = '~/.local/share/gnome-shell/extensions/argos@pew.worldwidemann.com'
DEFAULT_PYTHON_NAME = 'python3'
DEFAULT_CONFIG_FILE = 'jira.default.ini'
CUSTOM_CONFIG_FILE = 'jira.custom.ini'
PLUGIN_FILE = 'jira-timelog-critic.py.in'
PLUGIN_NAME_TEMPLATE = 'jira-timelog-critic.{position}.{interval}{dropdown_run}.py'
VENV_NAME = 'jira-timelog-venv'
VENV_PYTHON_RELATIVE_PATH = 'bin/python'

ARGOS_INTERVAL_RE = r'\d+[smhd]'
ARGOS_INTERVAL_PATTERN = "'NumberUnit' where Unit is one of s (seconds), m (minutes), h (hours) or d (days) - i.e. 5m"


class STDOutControlCodes:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    BLUE = '\033[34m'
    DARK_GREY = '\033[90m'

    BOLD = '\033[01m'
    RESET = '\033[0m'


def cprint(*args, **kwargs):
    prefix = ''
    if 'bold' in kwargs and kwargs.pop('bold') is True:
        prefix = STDOutControlCodes.BOLD
    if 'colour' in kwargs:
        prefix = f'{prefix}{kwargs.pop("colour")}'
    print(prefix, end='')
    print(*args, **kwargs)
    print(STDOutControlCodes.RESET, end='')


def action_print(msg):
    cprint(msg, colour=STDOutControlCodes.GREEN)


def notice_print(msg):
    cprint(msg, colour=STDOutControlCodes.BLUE)


def skipped_print(msg):
    cprint(msg, colour=STDOutControlCodes.DARK_GREY)


def error_print(msg):
    cprint(msg, colour=STDOutControlCodes.RED)


def get_default_python_path():
    notice_print(f"No Python Interpreter specified, looking up path of default interpreter ({DEFAULT_PYTHON_NAME})")
    path = shutil.which(DEFAULT_PYTHON_NAME)
    if not path:
        raise AttributeError(
            "No Python Interpreter was specified and 'python3' executable cannot be found - "
            "please specify a valid Python 3 interpreter"
        )
    else:
        notice_print(f"Found default interpreter at '{path}'")
        return path


def check_for_argos():
    return os.path.exists(os.path.expanduser(ARGOS_EXTENSION_DIR))


def create_virtualenv(python_interpreter, virtualenv_path):
    """
    Creates a Python virtual environment at virtualenv_path (if one doesn't exist)
    """
    if os.path.exists(virtualenv_path):
        skipped_print("Virtual Environment already exists, skipping creation")
        return

    action_print(f"Creating Python Virtual Environment in '{virtualenv_path}'")
    try:
        subprocess.run(
            [python_interpreter, '-m', 'venv', virtualenv_path],
            shell=False,
            check=True
        )
    except subprocess.CalledProcessError:
        try:
            os.rmdir(virtualenv_path)
        except Exception:
            error_print("Failed to create Virtual Environment and failed to clean up")
        else:
            error_print("Failed to create Virtual Environment - deleted attempt")
        raise


def build_plugin_name(execution_frequency, rerun_on_dropdown):
    return PLUGIN_NAME_TEMPLATE.format(
        position='',
        interval=execution_frequency,
        dropdown_run='+' if rerun_on_dropdown else ''
    )


def install_plugin(src_plugin_path, dest_plugin_path, virtualenv_path):
    with open(src_plugin_path, 'r') as f:
        src_plugin_txt = f.read()

    shebang = f'#!{virtualenv_path}/{VENV_PYTHON_RELATIVE_PATH}'
    templated_plugin = f'{shebang}\n{src_plugin_txt}'

    if os.path.exists(dest_plugin_path):
        with open(dest_plugin_path, 'r') as f:
            dest_plugin_txt = f.read()

        if dest_plugin_txt == templated_plugin:
            skipped_print("Current installed plugin is identical to latest version, skipping plugin install",)
            return

    with open(dest_plugin_path, 'w') as f:
        action_print(f"Installing plugin {src_plugin_path} → {dest_plugin_path}")
        f.write(templated_plugin)

    action_print("Setting plugin permissions")
    current_perms = os.stat(dest_plugin_path)
    os.chmod(dest_plugin_path, current_perms.st_mode | stat.S_IEXEC)


def install_default_config_file(src_config_file, dest_config_file):
    action_print(f"Copying default config file to '{dest_config_file}'")

    try:
        shutil.copy(src_config_file, dest_config_file)
    except Exception:
        error_print("Failed to copy default config file")
        raise


def get_args():

    def python_interpreter(python_path):
        if os.access(python_path, os.X_OK):
            return python_path
        if os.path.isfile(python_path):
            raise argparse.ArgumentTypeError("Python interpreter not valid (file not executable)")
        raise argparse.ArgumentTypeError("Python interpreter not valid (file not found)")

    def argos_interval(interval_str):
        match = re.search(ARGOS_INTERVAL_RE, interval_str)
        if not match:
            raise argparse.ArgumentTypeError(
                f"Execution frequency invalid, must be in the pattern {ARGOS_INTERVAL_PATTERN}"
            )
        return interval_str

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--python-interpreter', type=python_interpreter,
        help="ddd"
    )
    parser.add_argument(
        '-a', '--assume-argos', action='store_true',
        help="if passed then installation script won't check for an argos installation"
    )
    parser.add_argument(
        '-t', '--execution-frequency', type=argos_interval, default="5m",
        help=f"How often the plugin will be executed, must be in the pattern {ARGOS_INTERVAL_PATTERN}"
    )
    parser.add_argument(
        '-r', '--rerun-on-dropdown', action='store_true',
        help="if passed then jira-timelog-critic will update when viewing the dropdown"
    )

    args = parser.parse_args()

    if not args.python_interpreter:
        args.python_interpreter = get_default_python_path()

    return args


if __name__ == '__main__':
    args = get_args()
    plugin_name = build_plugin_name(args.execution_frequency, args.rerun_on_dropdown)

    # Get the full paths of the plugin and the various destination files/folders
    full_argos_dir = os.path.expanduser(ARGOS_CONFIG_DIR)

    install_script_dir = os.path.dirname(__file__)

    full_plugin_source_path = os.path.abspath(f'{install_script_dir}/{PLUGIN_FILE}')
    full_plugin_dest_path = f'{full_argos_dir}/{plugin_name}'

    full_config_source_path = os.path.abspath(f'{install_script_dir}/{DEFAULT_CONFIG_FILE}')
    full_config_dest_path = f'{full_argos_dir}/{DEFAULT_CONFIG_FILE}'

    full_virtualenv_path = f'{full_argos_dir}/venv'

    if not args.assume_argos:
        if not check_for_argos():
            error_print("Unable to locate installed copy of argos")
            notice_print(
                "Please install argos from https://github.com/p-e-w/argos (or pass arg '-a' to skip this check)"
            )
            exit(1)
    else:
        skipped_print("Skipping checking for argos (-a/--assume-argos passed)")

    create_virtualenv(args.python_interpreter, full_virtualenv_path)
    install_default_config_file(full_config_source_path, full_config_dest_path)
    install_plugin(full_plugin_source_path, full_plugin_dest_path, full_virtualenv_path)

    cprint("Jira Timelog Critic plugin installed!", bold=True)
    cprint("Installed Path: ", bold=True, end='')
    print(full_plugin_dest_path)
    cprint("Virtual Env Path: ", bold=True, end='')
    print(full_virtualenv_path)
