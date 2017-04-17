# Yasha

[![Join the chat at https://gitter.im/kblomqvist/yasha](https://badges.gitter.im/kblomqvist/yasha.svg)](https://gitter.im/kblomqvist/yasha?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/kblomqvist/yasha.svg?branch=master)](https://travis-ci.org/kblomqvist/yasha)
[![Number of downloads during the last month](https://img.shields.io/pypi/dm/yasha.svg)]( https://pypi.python.org/pypi/yasha/)
![MIT license](https://img.shields.io/pypi/l/yasha.svg)
<img src="https://raw.githubusercontent.com/kblomqvist/yasha/master/yasha.png" align="right" />

Yasha is a code generator based on [Jinja2](http://jinja.pocoo.org/) template engine. At its simplest a command-line call

```bash
yasha foo.jinja
```

will render `foo.jinja` template into a new file named as `foo`. See how the created file name is derived from the template name. The template itself remains unchanged.

The tool was originally written to generate code for the zinc.rs' [I/O register interface](http://zinc.rs/apidocs/ioreg/index.html) from the [CMSIS-SVD](https://www.keil.com/pack/doc/CMSIS/SVD/html/index.html) description file, and was used to interface with [the peripherals of Nordic nRF51](https://github.com/kblomqvist/yasha/tree/master/tests/fixtures) ARM Cortex-M processor-based microcontroller. Yasha has since evolved to be flexible enough to be used in any project where the code generation is needed. The tool allows extending Jinja by domain specific filters, tests and extensions, and it operates smoothly with the commonly used build automation softwares like Make, CMake and SCons.

The built-in template variable file parsers are

- `.svd` files are parsed as [CMSIS-SVD](https://www.keil.com/pack/doc/CMSIS/SVD/html/index.html)
- `.toml` files are parsed as [TOML](https://github.com/toml-lang/toml)
- `.yaml` and `.yml` files are parsed as [YAML](http://www.yaml.org/start.html)

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

  Reads the given Jinja template and renders its content into a new file,
  which name is derived from the given template name. For example, a template
  called foo.c.jinja will be written into foo.c in case when the output
  file is not explicitly specified.

Options:
  -o, --output FILENAME       Place a rendered tempalate into FILENAME.
  -v, --variables FILENAME    Read template variables from FILENAME.
  -e, --extensions FILENAME   Read template extensions from FILENAME.
  -I, --searchpath DIRECTORY  Add DIRECTORY to the list of directories to be
                              searched for referenced templates in TEMPLATE,
                              aka hardcoded template extensions, inclusions
                              and imports.
  --no-variables              Omit template variables.
  --no-extensions             Omit template extensions.
  --no-trim-blocks            Load Jinja with trim_blocks=False.
  --no-lstrip-blocks          Load Jinja with lstrip_blocks=False.
  -M                          Outputs Makefile compatible list of
                              dependencies. Doesn't render the template.
  -MD                         Creates Makefile compatible .d file alongside a
                              rendered template.
  --version                   Print version and exit.
  -h, --help                  Show this message and exit.
```

## Template variables (variable file)

Template variables can be defined in a separate template variable file. If the file is not explicitly given, Yasha will look for it. For example, the command-line call, `yasha foo.jinja`, tries to find the appropriate variable file, e.g. `foo.yaml`, from the same folder with the template itself. To explicitly specifying the variable file use `-v` option flag:

```bash
yasha -v foo.yaml foo.jinja
```

Or give it via environment variable:

```bash
export YASHA_VARIABLES=$HOME/foo.yaml
yasha foo.jinja
```

In case the variable file shouldn't be used in spite of its existence, use ``--no-variables`` option flag:

```bash
yasha --no-variables foo.jinja
```

### Variable file sharing

Imagine that you would be writing C code and have the following two templates in two different folders

```
root/
    include/foo.h.jinja
    source/foo.c.jinja
```

and you would like to share the same variables between these two templates. So instead of creating separate `foo.h.yaml` and `foo.c.yaml` you can create `foo.yaml` under the root folder:

```
root/
    include/foo.h.jinja
    source/foo.c.jinja
    foo.yaml
```

Now when you call

```bash
cd root
yasha include/foo.h.jinja
yasha source/foo.c.jinja
```

the variables defined in `foo.yaml` are used within both templates. This works because subfolders will be checked for the variable file until the current working directory is reached — `root` in this case. For the readers reference, the variables are looked for `include/foo.h.jinja` in following order: `include/foo.h.yaml`, `include/foo.yaml`, `foo.h.yaml`, `foo.yaml`.

## Template extensions (extension file)

You can use custom [Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) and/or [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) within your templates. The functionality is similar to the variable file usage described above. So for a given `foo.jinja` template file, yasha will automatically look for `foo.py` file for template extensions. In case you are generating python code you may like to use `.j2ext` or `.jinja-ext` file suffix instead of `.py`.

Here is an example of the extension file containing a filter and a test:

```python
def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def test_even(number):
    return number % 2 == 0
```

Note that the functions intended to work as a filter have to be prefixed by `filter_`. Similarly test functions have to be prefixed by `test_`. In addition to filters and tests, [Jinja extension classes](http://jinja.pocoo.org/docs/dev/extensions/#module-jinja2.ext) are also supported. Meaning that all classes derived from `jinja2.ext.Extension` are loaded and available within the template.

And as you might guess, instead of relying on the automatic extension file look up, the file can be given explicitly as well.

```bash
yasha -e foo.py foo.jinja
```

There's also `--no-extensions` option flag operating in a similar manner with `--no-variables`. Additionally the file sharing works for the extension file as it works for the variable file. The environment variable name `YASHA_EXTENSIONS` is supported too.

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

By default the referenced templates, i.e. template [extensions](http://jinja.pocoo.org/docs/dev/templates/#extends), [inclusions](http://jinja.pocoo.org/docs/dev/templates/#include) and [imports](http://jinja.pocoo.org/docs/dev/templates/#import), are searched in relation to the template location. To extend the search path you can use command-line option `-I` — like you would do with the GCC to include C header files.

```bash
yasha -I$HOME/jinja foo.jinja
```

The above command-line call allows you to reuse files from `$HOME/jinja` folder within your template, like this

```jinja
{% extends "skeleton.jinja" %}
{% from "macros.jinja" import macro %}
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
cat foo.jinja | yasha -v foo.yaml -
```

## Build automation

Yasha command-line options `-M` and `-MD` return the list of the template dependencies in a Makefile compatible format. The later creates the separate `.d` file alongside the template rendering instead of printing to stdout. These options allow integration with the build automation tools. Below are given examples for CMake, Make and SCons.

### CMakeList.txt (CMake)

```CMake
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

How to use:

```Bash
mkdir build && cd $_
cmake ..
make
```

### Makefile (GNU Make)

```Makefile
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

### SConstruct (SCons)

Below is shown a simple example how to use Yasha with [SCons](http://scons.org/) for C files. There are too different kind of builders available in `yasha.scons`, Builder and CBuilder. The difference is that CBuilder doesn't include generated C header files into its return value so you can append it directly to sources list, like it's done below.

```python
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

Another example with separate `build/` and `src/` directories.

```python
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
