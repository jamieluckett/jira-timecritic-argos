# jira-timelog-critic

## Description

### Screenshots
![Screenshot of Jira Timelog Critic showing hours logged for the last 3 weeks
](docs/images/screenshot-1.png "Screenshot #1")

## Requirements
* Python 3.8 (or newer)
* 'venv' module
* Argos GNOME Shell extension ([github.com/p-e-w/argos](https://github.com/p-e-w/argos))

## Installation
Installation of the Jira Timelog Critic plugin is all managed via the bundled
`install.py` Python script.

To install the agent simply run the `install.py` script - no additional
arguments are needed except to configure the following:

#### Python Interpreter
By default, the installation script will create a Python Virtual Environment
using the system's built-in `python3` binary found via `shutil.which`. To check
which this is `which python3` can be run in a terminal.

```
$ which python3
/usr/bin/python3
```

To use an alternative Python binary to create the virtual environment pass the
full path of the executable to the installation script via `-p` or
`--python-interpreter`.

```shell
./install.py -p /usr/local/bin/python3
```

#### Skipping Argos Check
On execution the installation script will check for the Argos GNOME extension,
throwing an error if it is not found in the expected place. To bypass this
check `-a` or `--assume-argos ` can be passed.

```shell
./install.py -a
```

#### Execution Frequency
By default, the plugin will check Jira for new timelog data every 5 minutes. To
configure this the `-t` or `--execution-frequency` arguments can be passed with
a value in the following format:

`<VALUE><UNIT>` where UNIT is one of 's', 'm', 'h' or 'd' (seconds, minutes,
hours or days).

```shell
# Query Jira for data every 30 minutes
./install.py -t 30m
```
