#! /usr/bin/env python3
"""This is set up and support script to parse pyproject.toml and env.toml.

This script exports vars to the .env file, in the following order:
pyproject.toml (some vars) > env.toml [prod] > [dev] (if requested)

Not all pyproject.toml variables are fetched and env.toml has precedence over the latter,
prefer updating the env.toml file for execution env vars and leave the other for project vars.

Compatibility with Linux environment:
> A [env var key is a] word consisting only of alphanumeric characters and underscores,
> and beginning with an alphabetic character or an underscore.
    - Keys are case-insensitive, all variable names will be exported upper-cased;
    - All keys must start with a letter or will be ignored;
    - Dashes/hyphens in a key name will be converted to an underline/undescore;
    - Non alphanum characters will be stripped when exporting, except for the underscore char.

To export to Production Envirnoment (default), run from project's root directory:
    `poetry run python setup/dotenv-from-toml.py`
    Note: all variables from the [prod] group in env.toml will be exported

To export to Development Envirnoment, run from project's root directory:
    `run=dev poetry run python setup/dotenv-from-toml.py`
    Note: all variables from the [prod] group in env.toml will be parsed, then all [dev] vars,
          meaning that keys repeted in [prod] and [dev] will be exported with the value in the [dev] group

Any other group set in env.toml can be exported just like dev and such as dev,
prod keys are parsed and updated by this other group:
    `run=other poetry run python setup/dotenv-from-toml.py`

There shall not be a duplicatted key in a same group and file. Use a TOML linter.
Repeated keys in different files or groups will be exported with the last fetched value.
Keys in env.toml starting with or having "-" on any part will not be exported.
"""
import sys
from pathlib import Path
from re import match, sub
from os import environ

if (sys.version_info.major, sys.version_info.minor) < (3, 11):
    try:
        # noinspection PyPackageRequirements
        from tomli import load
        # noinspection PyPackageRequirements
        from tomli import TOMLDecodeError
    except ModuleNotFoundError:
        print('\n\t\033[91mABORTED!\033[0m', file=sys.stderr)
        print('\tAdditional required module for Python <3.11: \033[91mtomli\033[0m\n', file=sys.stderr)
        sys.exit(1)
else:
    from tomllib import load
    from tomllib import TOMLDecodeError

FETCH_AND_TRANSLATE_PYPROJECT = {
    'name': ['PROJECT_NAME', 'APP_NAME'],
    'version': 'APP_VERSION',
    'description': 'PROJECT_DESCRIPTION',
    'documentation': 'PROJECT_DOCS',
}


def main():  # noqa: D103
    parsed = {}

    if Path('pyproject.toml').is_file():
        with open('pyproject.toml', 'br') as f:
            toml = load(f)

            v = toml['tool']['poetry']['dependencies']['python']
            k = 'MINIMAL' if "^" in v else "REQUIRED"
            parsed[f'{k}_PYTHON'] = sub(r'[^\d.]', '', v)

            for k, v in toml['tool']['poetry'].items():
                if k in FETCH_AND_TRANSLATE_PYPROJECT:
                    translate_to = FETCH_AND_TRANSLATE_PYPROJECT[k]
                    if isinstance(translate_to, str):
                        translate_to = [translate_to]
                    for translation in translate_to:
                        parsed[translation] = v

    if Path('env.toml').is_file():
        with open('env.toml', 'br') as f:
            try:
                toml = load(f)
            except TOMLDecodeError as e:
                if 'Cannot overwrite' in str(e):
                    print('\n\033[91mFound a duplicated key in TOML!\033[0m\nPlease fix env.toml: {}.'.format(
                        sub(r'.*line (\d+),.*', r'line \1', str(e))
                    ), file=sys.stderr)
                    sys.exit(2)

            for group in ('prod', environ.get('run')):
                for k, v in toml.get(group, {}).items():
                    if match(r'^[A-Za-z0-9_]', k):
                        parsed.update({k.replace('-', '_').upper(): v})

    if 'APP_NAME' not in parsed:
        parsed['APP_NAME'] = parsed['PROJECT_NAME']
    parsed['PROJECT_NAME'] = parsed['PROJECT_NAME'].lower().replace(' ', '-')

    for key, val in parsed.items():
        if isinstance(val, list):
            val = ','.join(val)
        elif isinstance(val, str) and ' ' in val:
            val = f'{val!r}'

        key = sub(r'\W', '', key)
        print(f'{key}={val}'.replace("'", '"'))


if __name__ == '__main__':
    main()
