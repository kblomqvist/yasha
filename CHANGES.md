Version 4.0
-----------

Major release, unreleased

- Reverted the change introduced in version 3.0 to use uppercase `-E`
  and `-V` option flags for extension and variable files. Fixes
  the SCons builder, which was still using lowercase options.
- Changed the way how template variables given as part of the
  command-line call are defined. From this version all unknown long
  options which has a proper value are interpreted as a template
  variable, e.g. `--foo=bar` or `--foo bar`. Note that `-v foo bar` is
  not working anymore.
- Python literals can be used as part of the command-line call,
  e.g. `yasha --foo "['bar', 'baz']" template.j2`.
- Added new command-line option `-c` to set template encoding.
  Default is UTF-8.
- Added `env` template filter to read environment variable.
- Added `shell` template filter to run a shell command. and to connect
  its standard output. Requires Python >= 3.5.
- Added `subprocess` template filter to spawn new processes, but unlike
  shell a CompletedProcess instance is returned, or CalledProcessError
  in case of error. Requires Python >= 3.5.
- Fixed an issue where the command-line call `yasha ../template.j2`
  searched for template companion files till root folder.
- Removed the variable/extension file overwrite protection introduced
  in version 3.1. Caused more confusion than protection.
- Command-line option `--no-variables` is now `--no-variable-file`.
- Command-line option `--no-extensions` is now `--no-extension-file`.


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
