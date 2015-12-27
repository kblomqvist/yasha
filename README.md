# Yasha
[![Build Status](https://travis-ci.org/kblomqvist/yasha.svg?branch=master)](https://travis-ci.org/kblomqvist/yasha)
[![Number of downloads during the last month](https://img.shields.io/pypi/dm/yasha.svg)]( https://pypi.python.org/pypi/yasha/)
![MIT license](https://img.shields.io/pypi/l/yasha.svg)
<img src="https://raw.githubusercontent.com/kblomqvist/yasha/master/yasha.png" align="right" />

Yasha is a code generator based on [Jinja2](http://jinja.pocoo.org/) template engine. The following command-line call

```
$ yasha foo.jinja
```

will render `foo.jinja` template into a new file named as `foo`. See how the created file name is derived from the template name. The template itself remains unchanged.

Template variables can be defined in a separate template variable/configuration file. For example, [TOML](https://github.com/toml-lang/toml) and [YAML](http://www.yaml.org/start.html) are supported. If the variable file is not given explicitly, Yasha will look for it. Thus the above example tries to find `foo.toml`, `foo.yaml` or `foo.yml` from the same folder with the template itself. If the file is not found, subfolders will be checked until the root directory is reached.

The file containing the template variables can be given explicitly too:

```
$ yasha foo.jinja --variables foo.toml
```

Or via environment variable:

```
$ export YASHA_VARIABLES=$HOME/foo.toml
$ yasha foo.jinja
```

In case the variables shouldn't be used in spite of the file existence use ``--no-variables`` option flag:

```
$ yasha foo.jinja --no-variables
```

#### Default variable parsers

- `.svd` files are parsed as CMSIS-SVD
- `.toml` files are parsed as TOML
- `.yaml` and `.yml` files are parsed as YAML

## Installation

As a regular user:

```
pip install yasha
```

As a developer (for the latest development version):

```
git clone https://github.com/kblomqvist/yasha
pip install -e yasha
```

## Template variables sharing

Imagine that you would be writing C code and have the following two templates in two different folders

```
include/
  foo.h.jinja
source/
  foo.c.jinja
```

and you would like to share the same variables between these two templates. So instead of creating separate `foo.h.toml` and `foo.c.toml` files you can make one `foo.toml` like this:

```
include/
  foo.h.jinja
source/
  foo.c.jinja
foo.toml
```

Now when you call

```
$ yasha include/foo.h.jinja
$ yasha source/foo.c.jinja
```

the variables defined in `foo.toml` are used within both templates. For your convenience here is the file listing after the above two yasha calls:

```
include/
  foo.h
  foo.h.jinja
source/
  foo.c
  foo.c.jinja
foo.toml
```

## Custom Jinja extensions

Seems like the day has arrived when you would like to use custom [Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) and/or [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) within your templates. Fortunately yasha has been a far-wise and supports these out of box. The functionality is similar to the variables file usage described above. So for a given `foo.jinja` template file, yasha will automatically seek `foo.j2ext` file (`.jinja-ext` extension works too).

Here is an example of the `foo.j2ext` file containing a filter and a test.

```python
def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def test_even(number):
    return number % 2 == 0
```

As can be seen the file is standard Python, although the file extension is not `.py` but `.j2ext`. Furthermore, note that the functions intended to work as a filter have to be prefixed by `filter_`. Similarly test functions have to be prefixed by `test_`.

Here it is shown how the two extensions described above would be used within a template.

```jinja
{{ date|datetimeformat }}
{{ date|datetimeformat('%d-%m-%Y') }}

{% if 42 is even %}
    42 is even
{% endif %}
```

In addition to filters and tests, [extension classes](http://jinja.pocoo.org/docs/dev/extensions/#module-jinja2.ext) are also supported. Meaning that all classes derived from `jinja2.ext.Extension` are loaded and available within the template.

And as you might guess, instead of relying on the automatic extension file look up, it can be given explicitly as well.

```
$ yasha foo.jinja --extensions foo.py
```

There's also `--no-extensions` option flag operating in a similar manner with `--no-variables`. It's also worth mentioning that the file sharing works for the extensions file as it works for the variables and that the environment variable name for the extensions is YASHA_EXTENSIONS.

## Custom template variables parser

By default Yasha supports TOML and YAML files for template variables. However, it's possible to declare custom parser in `.j2ext` file. For example, below is shown an example parser for a certain XML file. Note that all classes derived from `yasha.parsers.Parser` are considered as a custom parser and will be loaded.

```python
from yasha.parsers import Parser

class XmlParser(Parser):
    file_extension = [".xml"]

    def parse(self, file): # file type is click.File
        import xml.etree.ElementTree as et
        tree = et.parse(file.name)
        root = tree.getroot()

        vars = {"persons": []}
        for elem in root.iter("person"):
            vars["persons"].append({
                "name": elem.find("name").text,
                "address": elem.find("address").text,
            })

        return vars # Return value has to be dictionary
```

If you need to post-process the parsed variables accomplished by the built-in TOML and YAML parsers, you can just declare new parsers to handle TOML and YAML files.

```python
from yasha.parsers import TomlParser, YamlParser

def postprocess(vars):
    vars["foo"] = "bar" # foo should always be bar
    return vars

class MyTomlParser(TomlParser):
    def parse(self, file):
        vars = TomlParser.parse(file)
        return postprocess(vars)

class MyYamlParser(YamlParser):
    def parse(self, file):
        vars = YamlParser.parse(file)
        return postprocess(vars)
```

## Utilizing Yasha for C

#### Makefile

The below Makefile can work with or without separate build directory.
It can be given as part of EXECUTABLE name.

```Makefile
# User variables
SOURCES    = $(wildcard src/*.c)
TEMPLATES  = $(wildcard src/*.jinja)
EXECUTABLE = build/a.out

# Add rendered .c templates to sources list
SOURCES += $(filter %.c, $(basename $(TEMPLATES)))

# Resolve build dir from executable
BUILDDIR = $(dir $(EXECUTABLE))

# Resolve object files along with the .d files which lists what files
# the object and template file depends on
OBJECTS     = $(addprefix $(BUILDDIR), $(SOURCES:.c=.o))
OBJECTS_D   = $(OBJECTS:.o=.d)
TEMPLATES_D = $(TEMPLATES:.jinja=.d)

$(EXECUTABLE) : $(OBJECTS)
    $(CC) $^ -o $@

$(BUILDDIR)%.o : %.c | $(filter %.h, $(basename $(TEMPLATES)))
    @mkdir -p $(dir $@)
    $(CC) -MMD -MP $< -c -o $@

%.c : %.c.jinja
    yasha -MD $< -o $@

%.h : %.h.jinja
    yasha -MD $< -o $@

# Make sure that the following built-in implicit rule is cancelled
%.o : %.c

# Pull in dependency info for existing .o and template files
-include $(OBJECTS_D) $(TEMPLATES_D)

# Prevent Make to consider rendered templates as intermediate file
.secondary : $(basename $(TEMPLATES))

clean :
ifeq ($(BUILDDIR),./)
    -rm -f $(EXECUTABLE)
    -rm -f $(OBJECTS)
    -rm -f $(OBJECTS_D)
else
    -rm -rf $(BUILDDIR)
endif
    -rm -f $(TEMPLATES_D)
    -rm -f $(basename $(TEMPLATES))

.phony : clean
```

#### SConstruct (SCons)

```python
import os
import yasha.scons

env = Environment(
    ENV = os.environ,
    BUILDERS = {"Yasha": yasha.scons.CBuilder()}
)

sources = ["main.c"]
sources += env.Yasha(["foo.c.jinja", "foo.h.jinja"])

env.Program("a.out", sources)
```

Another example with separate build directory with sources in `src/`

```python
import os
import yasha.scons

env = Environment(
    ENV = os.environ,
    BUILDERS = {"Yasha": yasha.scons.CBuilder()}
)

# See how the duplication of sources affect to paths
duplicate = 1

if duplicate:
    env.VariantDir("build", "src", duplicate=duplicate)
    sources = ["build/main.c"]
    sources += env.Yasha(["build/foo.c.jinja", "build/foo.h.jinja"])
else:
    env.VariantDir("build", "src", duplicate=duplicate)
    sources = ["build/main.c"]
    sources += env.Yasha(["src/foo.c.jinja", "src/foo.h.jinja"])

env.Program("build/a.out", sources)
```
