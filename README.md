# Yasha
[![Build Status](https://travis-ci.org/kblomqvist/yasha.svg?branch=master)](https://travis-ci.org/kblomqvist/yasha)
![MIT license](https://img.shields.io/pypi/l/yasha.svg)
<img src="https://raw.githubusercontent.com/kblomqvist/yasha/master/yasha.png" align="right" />

Yasha is a code generator based on [Jinja2](http://jinja.pocoo.org/) template engine. At its simplest, a command-line call

```bash
yasha -V variables.yaml template.j2
```

will render `template.j2` into a new file named as `template`. See how the created file name is derived from the template name. The template itself remains unchanged.

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
Usage: yasha [OPTIONS] TEMPLATE

  Reads the given Jinja template and renders its content into a new file.
  For example, a template called foo.c.j2 will be written into foo.c when
  the output file is not explicitly given.

Options:
  -v <TEXT TEXT>...            Define template variable.
  -o, --output FILENAME        Place a rendered template into FILENAME.
  -V, --variables FILENAME     Read template variables from FILENAME.
  -E, --extensions FILENAME    Read template extensions from FILENAME.
  -I, --includepath DIRECTORY  Add DIRECTORY to the list of directories to be
                               searched for the referenced templates.
  --no-variables               Omit template variable file.
  --no-extensions              Omit template extension file.
  --no-trim-blocks             Load Jinja with trim_blocks=False.
  --no-lstrip-blocks           Load Jinja with lstrip_blocks=False.
  --keep-trailing-newline      Load Jinja with keep_trailing_newline=True.
  -M                           Outputs Makefile compatible list of
                               dependencies. Doesn't render the template.
  -MD                          Creates Makefile compatible .d file alongside a
                               rendered template.
  --version                    Print version and exit.
  -h, --help                   Show this message and exit.
```

## Template variables

Simple template variables can be defined via command-line using `-v` option

```bash
yasha -v var value template.j2
```

However, in many cases it is more convenient to define variables in a separate file

```bash
yasha -V variables.yaml template.j2
```

Yasha supports [JSON](http://www.json.org), [YAML](http://www.yaml.org/start.html) and [TOML](https://github.com/toml-lang/toml), but custom parsers are also possible (see below).

### Automatic variable file look up

If the variable file is not explicitly given, Yasha will look for it by searching a file named in the same way than the corresponding template but with the file extension of JSON, YAML or TOML. For example, consider the following template and template variables files

```
template.j2
template.yaml
```

Because of automatic variable file look up, the command-line call

```
yasha template.j2
```

equals to

```
yasha -V template.yaml template.j2
```

In case you want to omit the variable file in spite of its existence, use ``--no-variables`` option flag.

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

1. `include/foo.h.yaml`
2. `include/foo.yaml`
3. `foo.h.yaml`
4. `foo.yaml`

## Template extensions

You can use custom [Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) and [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) within your templates by declaring those in separate Python source file

```bash
yasha -E extensions.py -V variables.yaml template.j2
```

Functions intended to work as a filter have to be prefixed by `filter_`. Similarly test functions have to be prefixed by `test_`, like shown below

```python
# extensions.py

def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def test_even(number):
    return number % 2 == 0
```

In addition to filters and tests, [Jinja extension classes](http://jinja.pocoo.org/docs/dev/extensions/#module-jinja2.ext) are also supported. All classes derived from `jinja2.ext.Extension` are loaded by Yasha and available within the template.

### Automatic extension file look up and sharing

Like for variables file, Yasha supports automatic extension file look up and sharing too. In case you are generating Python code and you are relying to Yasha's automatic extension file look up, consider using the following naming convention for your files:

```
template.py.j2
template.py.py
template.py.yaml
```

In this case the command-line call

```
yasha template.py.j2
```

equals to

```
yasha -E template.py.py -V template.py.yaml template.py.j2
```

This guarantees that there's no collision between the names of rendered template and extension files.

### Custom variable file parser

If none of the built-in parsers fit into your needs, it's possible to declare your own parser within the extension file. Note that all classes derived from `yasha.Parser` are considered as a custom parser and will be loaded. For example, below is shown an example XML file and a custom parser for that.

```xml
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
import yasha
import xml.etree.ElementTree as et

class XmlParser(yasha.Parser):
    file_extension = [".xml"]

    def parse(self, file):
        tree = et.parse(file.name)
        root = tree.getroot()

        variables = {"persons": []}
        for elem in root.iter("person"):
            variables["persons"].append({
                "name": elem.find("name").text,
                "address": elem.find("address").text,
            })

        return variables  # Return value has to be dictionary
```

## Tips and tricks

### Append search path for referenced templates

By default the referenced templates, i.e. files referred to via Jinja's [extends](http://jinja.pocoo.org/docs/dev/templates/#extends), [include](http://jinja.pocoo.org/docs/dev/templates/#include) or [import](http://jinja.pocoo.org/docs/dev/templates/#import) statements, are searched in relation to the template location. To extend the search path you can use the command-line option `-I` — like you would do with GCC to include C header files.

```bash
yasha -I $HOME/jinja -V variables.yaml template.j2
```

The above command-line call allows you, for example, to inherit your template from `$HOME/jinja/skeleton.j2` template

```jinja
{% extends "skeleton.j2" %}
{% block main %}
    {{ super() }}
    ...
{% endblock %}
```

### Variable pre-processing before template rendering

If you need to pre-process template variables before those are passed into the template, you can do that within an extension file by declaring a custom parser which "overwrites" (is used before) the default parser.

```python
import yasha

def postprocess(variables):
    variables["foo"] = "bar"  # foo should always be bar
    return variables

class YamlParser(yasha.YamlParser):

    def parse(self, file):
        variables = yasha.YamlParser.parse(self, file)
        return postprocess(variables)
```

### Working with STDIN and STDOUT

Yasha can render templates from STDIN to STDOUT. For example, the below command-line call will render template from STDIN to STDOUT.

```bash
cat template.j2 | yasha -V variables.yaml -
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
