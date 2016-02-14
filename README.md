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

## Template variables (variable file)

Template variables can be defined in a separate template variable file. For example, [YAML](http://www.yaml.org/start.html) is supported. If the variable file is not given explicitly, Yasha will look for it. Thus the above example call, `yasha foo.jinja`, tries to find `foo.yaml` or `foo.yml` from the same folder with the template itself. If the file is not found, subfolders will be checked until the current working directory is reached.

The file containing the template variables can be given explicitly too:

```
$ yasha foo.jinja --variables foo.yaml
```

Or via environment variable:

```
$ export YASHA_VARIABLES=$HOME/foo.yaml
$ yasha foo.jinja
```

In case the variables shouldn't be used in spite of the file existence use ``--no-variables`` option flag:

```
$ yasha foo.jinja --no-variables
```

### Variable file sharing

Imagine that you would be writing C code and have the following two templates in two different folders

```
include/
  foo.h.jinja
source/
  foo.c.jinja
```

and you would like to share the same variables between these two templates. So instead of creating separate `foo.h.yaml` and `foo.c.yaml` files you can make one `foo.yaml` like this:

```
include/
  foo.h.jinja
source/
  foo.c.jinja
foo.yaml
```

Now when you call

```
$ yasha include/foo.h.jinja
$ yasha source/foo.c.jinja
```

the variables defined in `foo.yaml` are used within both templates.

### Built-in default variable parsers

- `.svd` files are parsed as CMSIS-SVD
- `.toml` files are parsed as TOML
- `.yaml` and `.yml` files are parsed as YAML

## Template extensions (extension file)

Seems like the day has arrived when you would like to use custom [Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) and/or [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) within your templates. Fortunately yasha has been a far-wise and supports these out of box. The functionality is similar to the variable file usage described above. So for a given `foo.jinja` template file, yasha will automatically seek `foo.py` file for extensions. In case you are generating python code you may like to use `.j2ext` or `.jinja-ext` file suffix for your template extension file instead of `.py`.

Here is an example of the extension file containing a filter and a test:

```python
def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def test_even(number):
    return number % 2 == 0
```

Note that the functions intended to work as a filter have to be prefixed by `filter_`. Similarly test functions have to be prefixed by `test_`. In addition to filters and tests, [Jinja extension classes](http://jinja.pocoo.org/docs/dev/extensions/#module-jinja2.ext) are also supported. Meaning that all classes derived from `jinja2.ext.Extension` are loaded and available within the template.

And as you might guess, instead of relying on the automatic extension file look up, the file can be given explicitly as well.

```
$ yasha foo.jinja --extensions foo.py
```

There's also `--no-extensions` option flag operating in a similar manner with `--no-variables`. It's also worth mentioning that the file sharing works for the extensions file as it works for the variables and that the environment variable name for the extensions is YASHA_EXTENSIONS.

### Custom variable parser

If none of the built-in parsers fit into your needs, it's possible to declare a your own parser within the extension file. For example, below is shown an example parser for a certain XML file. Note that all classes derived from `yasha.Parser` are considered as a custom parser and will be loaded.

```python
import yasha
import xml.etree.ElementTree as et

class XmlParser(yasha.Parser):
    file_extension = [".xml"]

    def parse(self, file): # file type is click.File
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

### Variable pre-processing before template rendering

If you need to pre-process template variables before those are passed into the template, you can do that within an extension file by declaring a custom parser which overwrites the default parser:

```python
import yasha

def postprocess(vars):
    vars["foo"] = "bar" # foo should always be bar
    return vars

class YamlParser(yasha.YamlParser): # This will overwrite the default parser
    def parse(self, file):
        vars = yasha.YamlParser.parse(file)
        return postprocess(vars)
```

## Build automation examples for C

### CMakeList.txt (CMake)

```CMake
cmake_minimum_required(VERSION 2.8.7)
project(yasha)

file(GLOB sources "src/*.c")
file(GLOB templates "src/*.jinja")

foreach(tmpl ${templates})
    execute_process(COMMAND yasha ${tmpl} -M OUTPUT_VARIABLE deps)
    string(REGEX REPLACE "^.*: " "" deps ${deps})
    string(REPLACE " " ";" deps ${deps})
    string(REGEX REPLACE "\\.[^.]*$" "" output ${tmpl})
    add_custom_command(
        OUTPUT ${output}
        COMMAND yasha ${tmpl} -o ${output}
        DEPENDS ${deps}
    )
    list(APPEND sources ${output})
endforeach()

add_executable(a.out ${sources})
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

Below is shown a simple example how to use Yasha with [SCons](http://scons.org/) for C files. There are too different kind of builders available in `yasha.scons`, Builder and CBuilder. The difference is that CBuilder doesn't include generated C header files into its return list so you can append this directly with your sources list.

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
