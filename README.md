# Yasha
[![Build Status](https://travis-ci.org/kblomqvist/yasha.svg?branch=master)](https://travis-ci.org/kblomqvist/yasha)
![MIT license](https://img.shields.io/pypi/l/yasha.svg)
<img src="https://raw.githubusercontent.com/kblomqvist/yasha/master/yasha.png" align="right" />

Yasha is a code generator based on [Jinja2](http://jinja.pocoo.org/) template engine. At its simplest, a command-line call

```bash
yasha -v variables.yaml template.txt.j2
```

will render `template.txt.j2` into a new file named as `template.txt`. See how the created file name is derived from the template name. The template itself remains unchanged.

The tool was originally written to generate code for the zinc.rs' [I/O register interface](http://zinc.rs/apidocs/ioreg/index.html) from the [CMSIS-SVD](https://www.keil.com/pack/doc/CMSIS/SVD/html/index.html) description file, and was used to interface with [the peripherals of Nordic nRF51](https://github.com/kblomqvist/yasha/tree/master/tests/fixtures) ARM Cortex-M processor-based microcontroller. Yasha has since evolved to be flexible enough to be used in any project where the code generation is needed. The tool allows extending Jinja by domain specific filters, tests and extensions, and it operates smoothly with the commonly used build automation software like Make, CMake and SCons.

## Installation

As a regular user:

```bash
pip install yasha
```

or if you like to get the latest development version:

```bash
pip install git+https://github.com/kblomqvist/yasha.git
```

or if you would like to take part into the development process:

```bash
git clone https://github.com/kblomqvist/yasha.git
pip install -e yasha
```

## Usage

```
Usage: yasha [OPTIONS] [TEMPLATE_VARIABLES]... TEMPLATE

  Reads the given Jinja TEMPLATE and renders its content into a new file.
  For example, a template called 'foo.c.j2' will be written into 'foo.c' in
  case the output file is not explicitly given.

  Template variables can be defined in a separate file or given as part of
  the command-line call, e.g.

      yasha --hello=world -o output.txt template.j2

  defines a variable 'hello' for a template like:

      Hello {{ hello }} !

Options:
  -o, --output FILENAME         Place the rendered template into FILENAME.
  -v, --variables FILENAME      Read template variables from FILENAME. Built-
                                in parsers are JSON, YAML, TOML and XML.
  -e, --extensions FILENAME     Read template extensions from FILENAME. A
                                Python file is expected.
  -c, --encoding TEXT           Default is UTF-8.
  -I, --include_path DIRECTORY  Add DIRECTORY to the list of directories to be
                                searched for the referenced templates.
  --no-variable-file            Omit template variable file.
  --no-extension-file           Omit template extension file.
  --no-trim-blocks              Load Jinja with trim_blocks=False.
  --no-lstrip-blocks            Load Jinja with lstrip_blocks=False.
  --keep-trailing-newline       Load Jinja with keep_trailing_newline=True.
  -M                            Outputs Makefile compatible list of
                                dependencies. Doesn't render the template.
  -MD                           Creates Makefile compatible .d file alongside
                                the rendered template.
  --version                     Print version and exit.
  -h, --help                    Show this message and exit.
```

## Template variables

Template variables can be defined in a separate file. [JSON](http://www.json.org), [YAML](http://www.yaml.org/start.html), [TOML](https://github.com/toml-lang/toml) and [XML](https://github.com/martinblech/xmltodict) are supported.

```bash
yasha -v variables.yaml template.j2
```

Additionally you may define variables as part of the command-line call, e.g.

```bash
yasha -v variables.yaml --foo=bar template.j2
```

A variable defined via command-line will overwrite a variable defined in file.

### Automatic variable file look up

If the variable file is not explicitly given, Yasha will look for it by searching a file named in the same way than the corresponding template but with the file extension either `.json`, `.yaml`, `.yml`, `.toml`, or `.xml`.

For example, consider the following template and variable files

```
template.j2
template.yaml
```

Because of automatic variable file look up, the command-line call

```bash
yasha template.j2
```

equals to

```bash
yasha -v template.yaml template.j2
```

In case you want to omit the variable file in spite of its existence, use ``--no-variable-file`` option flag.

### Variable file sharing

Imagine that you would be writing C code and have the following two templates in two different folders

```
root/
    include/foo.h.j2
    source/foo.c.j2
```

and you would like to share the same variables between these two templates. So instead of creating separate `foo.h.yaml` and `foo.c.yaml` you can create `foo.yaml` under the root folder:

```
root/
    include/foo.h.j2
    source/foo.c.j2
    foo.yaml
```

Now when you call

```bash
cd root
yasha include/foo.h.j2
yasha source/foo.c.j2
```

the variables defined in `foo.yaml` are used within both templates. This works because subfolders will be checked for the variable file until the current working directory is reached — `root` in this case. For instance, variables are looked for `foo.h.j2` in following order:

```
include/foo.h.yaml
include/foo.yaml
foo.h.yaml
foo.yaml
```

## Template extensions

You can extend Yasha by custom [Jinja extensions](http://jinja.pocoo.org/docs/dev/extensions/#module-jinja2.ext), [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) and [filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) by declaring those in a separate Python source file given via command-line option `-e`, or `--extensions` as it is shown below

```bash
yasha -e extensions.py -v variables.yaml template.j2
```

Like for variable file, Yasha supports automatic extension file look up and sharing too. To avoid file collisions consider using the following naming convention for your template, extension, and variable files:

```
template.py.j2
template.py.py
template.py.yaml
```

Now the command-line call

```bash
yasha template.py.j2
```

is equal to

```bash
yasha -e template.py.py -v template.py.yaml template.py.j2
```

### Tests

Functions intended to work as a test have to be either prefixed by `test_`

```python
def test_even(number):
    return number % 2 == 0
```

of defined in `TESTS` dictionary

```python
def is_even(number):
    return number % 2 == 0

TESTS = {
    'even': is_even,
}
```

### Filters

Functions intended to work as a filter have to be either prefixed by `filter_`

```python
def filter_replace(s, old, new):
    return s.replace(old, new)
```

or defined in `FILTERS` dictionary

```python
def do_replace(s, old, new):
    return s.replace(old, new)

FILTERS = {
    'replace': do_replace,
}
```

### Classes

All classes derived from `jinja2.ext.Extension` are considered as Jinja extensions and will be added to the environment used to render the template.

### Parsers

If none of the built-in parsers fit into your needs, it's possible to declare your own parser within the extension file. Either create a function named as `parse_` + `<file extension>`, or define the parse-function in `PARSERS` dictionary with the key indicating the file extension. Yasha will then pass the variable file object for the function to be parsed and expects to get dictionary as a return value.

For example, below is shown an example XML file and a custom parser for that.

```xml
<!-- variables.xml -->
<persons>
    <person>
        <name>Foo</name>
        <address>Foo Valley</address>
    </person>
    <person>
        <name>Bar</name>
        <address>Bar Valley</address>
    </person>
</persons>
```

```python
# extensions.py
import xml.etree.ElementTree as et

def parse_xml(file):
    assert file.name.endswith('.xml')
    tree = et.parse(file.name)
    root = tree.getroot()

    persons = []
    for elem in root.iter('person'):
        persons.append({
            'name': elem.find('name').text,
            'address': elem.find('address').text,
        })

    return dict(persons=persons)
```

## Built-in filters

### env

Reads system environment variable in a template like

```jinja
sqlalchemy:
  url: {{ 'POSTGRES_URL' | env }}
```

Params: *default=None*

### shell

Allows to spawn new processes and connect to their standard output. The output is decoded and stripped by default.

```jinja
os:
  type: {{ "lsb_release -a | grep Distributor | awk '{print $3}'" | shell }}
  version: {{ 'cat /etc/debian_version' | shell }}
```

```yaml
os:
  type: Debian
  version: 9.1
```

Requires: *Python >= 3.5*  
Params: *strip=True, check=True, timeout=2*

### subprocess

Allows to spawn new processes, but unlike `shell` behaves like Python's standard library.

```jinja
{% set r = "uname" | subprocess(check=False) %}
{# Returns either CompletedPorcess or CalledProcessError instance #}

{% if r.returncode -%}
  platform: Unknown
{% else -%}
  platform: {{ r.stdout.decode() }}
{%- endif %}
```

```yaml
platform: Linux
```

Requires: *Python >= 3.5*  
Params: *stdout=True, stderr=True, check=True, timeout=2*

## Tips and tricks

### Working with STDIN and STDOUT

Yasha can render templates from STDIN to STDOUT. For example, the below command-line call will render template from STDIN to STDOUT.

```bash
cat template.j2 | yasha -v variables.yaml -
```

### Python literals as part of the command-line call

Variables given as part of the command-line call can be Python literals, e.g. a list would be defined like this

```bash
yasha --foo="['foo', 'bar', 'baz']" template.j2
```

The following is also interpreted as a list

```bash
yasha --foo=foo,bar,baz template.j2
```

Other possible literals are:

- `-1`, `0`, `1`, `2` (an integer)
- `2+3j`, `0+5j` (a complex number)
- `3.5`, `-2.7` (a float)
- `(1,)`, `(1, 2)` (a tuple)
- `{'a': 2}` (a dict)
- `{1, 2, 3}` (a set)
- `True`, `False` (boolean)

### Common extension file

Sometimes it would make sense to have common extensions over multiple templates, e.g. for the sake of filters. This can be achieved by setting `YASHA_EXTENSIONS` environment variable.

```
export YASHA_EXTENSIONS=$HOME/.yasha/extensions.py
yasha -v variables.yaml -o output.txt template.j2
```

### Append search path for referenced templates

By default the referenced templates, i.e. files referred to via Jinja's [extends](http://jinja.pocoo.org/docs/dev/templates/#extends), [include](http://jinja.pocoo.org/docs/dev/templates/#include) or [import](http://jinja.pocoo.org/docs/dev/templates/#import) statements, are searched in relation to the template location. To extend the search path you can use the command-line option `-I` — like you would do with GCC to include C header files.

```bash
yasha -v variables.yaml -I $HOME/.yasha template.j2
```

```jinja
{% extends "skeleton.j2" %}
{# 'skeleton.j2' is searched also from $HOME/.yasha #}

{% block main %}
    {{ super() }}
    ...
{% endblock %}
```

### Variable pre-processing before template rendering

If you need to pre-process template variables before those are passed into the template, you can do that within an extension file by wrapping the built-in parsers.

```python
# extensions.py
from yasha.parsers import PARSERS

def wrapper(parse):
   def postprocess(file):
       variables = parse(file)
       variables['foo'] = 'bar' # foo should always be bar
       return variables
   return postprocess

for name, function in PARSERS.items():
    PARSERS[name] = wrapper(function)
```

### Using tests and filters from Ansible

[Ansible](http://docs.ansible.com/ansible/latest/intro.html) is an IT automation platform that makes your applications and systems easier to deploy. It is based on Jinja2 and offers a large set of [custom tests and filters](http://docs.ansible.com/ansible/latest/playbooks_templating.html), which can be easily taken into use via Yasha extensions.

```bash
pip install ansible
```

```python
# extensions.py
from ansible.plugins.test.core import TestModule
from ansible.plugins.filter.core import FilterModule

FILTERS = FilterModule().filters()
FILTERS.update(TestModule().tests())  # Ansible tests are filter like
```

### Using Python objects of any type in YAML

For security reasons, the built-in YAML parser is using the `safe_load` of [PyYaml](http://pyyaml.org/wiki/PyYAML). This limits variables to simple Python objects like integers or lists. To work with a Python object of any type, you can overwrite the built-in implementation of the parser.

```python
# extensions.py
import yaml

def parse_yaml(file):
    assert file.name.endswith(('.yaml', '.yml'))
    variables = yaml.load(file)
    return variables if variables else dict()

def parse_yml(file):
    return parse_yaml(file)
```

## Build automation

Yasha command-line options `-M` and `-MD` return the list of the template dependencies in a Makefile compatible format. The later creates the separate `.d` file alongside the template rendering instead of printing to stdout. These options allow integration with the build automation tools. Below are given examples for C files using CMake, Make and SCons.

### CMake

```CMake
# CMakeList.txt

cmake_minimum_required(VERSION 2.8.7)
project(yasha)

file(GLOB sources "src/*.c")
file(GLOB templates "src/*.jinja")

foreach(template ${templates})
    string(REGEX REPLACE "\\.[^.]*$" "" output ${template})
    execute_process(
        COMMAND yasha -M ${template}
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        OUTPUT_VARIABLE deps
    )
    string(REGEX REPLACE "^.*: " "" deps ${deps})
    string(REPLACE " " ";" deps ${deps})
    add_custom_command(
        OUTPUT ${output}
        COMMAND yasha -o ${output} ${template}
        DEPENDS ${deps}
    )
    list(APPEND sources ${output})
endforeach()

add_executable(a.out ${sources})
```

### GNU Make

```Makefile
# Makefile

# User variables
SOURCES    = $(wildcard src/*.c)
TEMPLATES  = $(wildcard src/*.jinja)
EXECUTABLE = build/a.out

# Add rendered .c templates to sources list
SOURCES += $(filter %.c, $(basename $(TEMPLATES)))

# Resolve build dir from executable
BUILDDIR = $(dir $(EXECUTABLE))

# Resolve object files
OBJECTS = $(addprefix $(BUILDDIR), $(SOURCES:.c=.o))

# Resolve .d files which list what files the object
# and template files depend on
OBJECTS_D   = $(OBJECTS:.o=.d)
TEMPLATES_D = $(addsuffix .d,$(basename $(TEMPLATES)))

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

### SCons

```python
# SConstruct

import os
import yasha.scons

env = Environment(
    ENV = os.environ,
    BUILDERS = {"Yasha": yasha.scons.CBuilder()}
)

sources = ["main.c"]
sources += env.Yasha(["foo.c.jinja", "foo.h.jinja"]) # foo.h not appended to sources
env.Program("a.out", sources)
```

Another example with separate `build` and `src` directories.

```python
# SConstruct

import os
import yasha.scons

env = Environment(
    ENV = os.environ,
    BUILDERS = {"Yasha": yasha.scons.CBuilder()}
)

sources = ["build/main.c"]

duplicate = 0 # See how the duplication affects to the file paths
env.VariantDir("build", "src", duplicate=duplicate)

if duplicate:
    tmpl = ["build/foo.c.jinja", "build/foo.h.jinja"]
    sources += env.Yasha(tmpl)

else:
    tmpl = ["src/foo.c.jinja", "src/foo.h.jinja"]
    sources += env.Yasha(tmpl)

env.Program("build/a.out", sources)
```
