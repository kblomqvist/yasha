Version 5.0
-----------

Major release, unreleased

- The option `--keep-trailing-newline` was removed in favor of making
  it default. The old behaviour can be achieved with the new option
  `--remove-trailing-newline`.
- Fixed an exit code in case of undefined variable from 0 to 1.
- Fixed a bug that caused extension classes not to load.

Version 4.3
-----------

Minor release, released 1 May 2018

- Added new option `--mode [pedantic|debug]`. In pedantic mode Yasha
  becomes extremely picky on templates, e.g. undefined variables will
  raise an error. In debug mode undefined variables will print as is.
- [Jinja's default configurations](https://github.com/pallets/jinja/blob/master/jinja2/defaults.py)
  can be set in file extensions. This allows changing the template
  syntax to mimic LaTeX, for example.

Version 4.2
-----------

Minor release, released 18 March 2018

- Added support for multiple variables files.

Version 4.1
-----------

Minor release, released 29 Oct 2017

- Fixed a bug related to automatic variable file lookup. Variable
  file like templates, e.g. templates with `.json` extension, were
  erronously used as a variable file too.

Version 4.0
-----------

Major release, released 8 Oct 2017

- Reverted the change introduced in version 3.0 to use uppercase `-E`
  and `-V` option flags for extension and variable files. Fixes
  the SCons builder, which was still using lowercase options.
- Changed the way how template variables given as part of the
  command-line call are defined. From this version all unknown long
  options which has a proper value are interpreted as a template
  variable, e.g. `--foo=bar` or `--foo bar`. Note that `-v foo bar` is
  not working anymore.
- Fixed an issue where the command-line call `yasha ../template.j2`
  searched for template companion files till root folder.
- Python literals can be used as part of the command-line call,
  e.g. `yasha --foo "['bar', 'baz']" template.j2`.
- Added `env` template filter to read system environment variable.
- Added `shell` template filter to run a shell command. and to connect
  its standard output. Requires Python >= 3.5.
- Added `subprocess` template filter to spawn new processes, but unlike
  shell a CompletedProcess instance is returned, or CalledProcessError
  in case of error. Requires Python >= 3.5.
- Added parser for XML type of variable files. Uses xmltodict.
- Added command-line option `-c` to set template encoding. Default is UTF-8.
- JSON parser updated to use `safe_load` (security).
- Within extension file, custom variable file parsers are now defined
  either as a function named as `parse_`+ `<file extension>`, or the
  parse-function is given via `PARSERS` dictionary with the key indicating
  the file extension.
- Within extension file, custom filters and tests can be also given
  via `FILTERS` and `TESTS` dictionary. This allows using external
  filters easily, e.g. from Ansible.
- Common extension file can be now set via `YASHA_EXTENSIONS` system
  environment variable.
- Command-line option `--no-variables` changed to `--no-variable-file`.
- Command-line option `--no-extensions` changed to `--no-extension-file`.
- Removed the variable/extension file overwrite protection introduced
  in version 3.1. Caused more confusion than protection.


Version 3.1
-----------

Minor release

- Support JSON formatted variable files.
- Prevent misoverwrition of the variable/extension file by the
  rendered template.


Version 3.0
-----------

Major release

- Added support for so called inline variables given as part of the
  command-line call using -v option. This change breaks backward
  compatibility as variable and extension files are now given via
  -V and -E, respectively.
- Added --keep-trailing-newline option to load Jinja with
  keep-trailing-newline=True.
