[![Build Status](https://travis-ci.org/kblomqvist/yasha.svg?branch=master)](https://travis-ci.org/kblomqvist/yasha)

# yasha

Yasha is a code generator based on [Jinja](http://jinja.pocoo.org/) template engine.

```
$ yasha foo.jinja
```

will render `foo.jinja` template into a new file named as `foo`. See how the created file name is derived from the template name. The template itself remains unchanged.

Template variables can be defined in a separate template configuration file. By default [TOML](https://github.com/toml-lang/toml) and [YAML](http://www.yaml.org/start.html) are supported. Yasha will look for this file if not given explicitly. For example, the above example tries to find `foo.toml` or `foo.yaml` (or `foo.yml`) from the same folder with the template. If the file is not found, subfolders will be checked until the root directory is reached.

Explicitly the file containing the template variables can be given as:

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

Seems like the day has arrived when you would like to use custom [Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) and/or [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) within your templates. Fortunately yasha has been a far-wise and supports these out of box. The functionality is similar to the variables file usage described above. So for a given `foo.jinja` template file, yasha will automatically seek `foo.jinja-ext` file.

Here is an example of the `foo.jinja-ext` file containing a filter and a test.

```python
def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)
    
def test_even(number):
    return number % 2 == 0
```

As can be seen the file is standard Python, although the file extension is not `.py` but `.jinja-ext`. Furthermore, note that the functions intended to work as a filter have to be prefixed by `filter_`. Similarly test functions have to be prefixed by `test_`.

Here is shown how the two extensions described above would be used within a template.

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

By default Yasha supports TOML and YAML files for template variables. However, it's possible to declare custom parser in `.jinja-ext` file. For example, below is shown an example parser for [CMSIS-SVD](http://www.keil.com/pack/doc/CMSIS/SVD/html/index.html) files. All classes derived from `yasha.parser.Parser` are considered as a custom parser and will be loaded.

```python
from yasha.parser import Parser

class CmsisSvdParser(Parser):
    file_extension = [".xml"]

    def parse(self, file):
        """Has to return Python dict. File is click.File object"""
        from cmsis_svd.parser import SVDParser
        parser = SVDParser.for_xml_file(file.name)
        return parser.get_device().to_dict()
```

If you need to post-process the parsed variables accomplished by the built-in TOML and YAML parsers, cou can just declare new parsers to handle TOML and YAML files.

```python
from yasha.parser import TomlParser, YamlParser

def postprocess(vars):
    vars["foo"] = "bar" # foo should always be bar
    return vars

class NewTomlParser(TomlParser):
    def parse(self, file):
        vars = TomlParser.parse(file)
        return postprocess(vars)

class NewYamlParser(YamlParser):
    def parse(self, file):
        vars = YamlParser.parse(file)
        return postprocess(vars)
```

## Example Makefile utilizing yasha for C

```Makefile
TEMPLATES = foo.c.jinja foo.h.jinja
SOURCES   = main.c $(filter %.c, $(basename $(TEMPLATES)))
OBJECTS   = $(SOURCES:.c=.o)

program : $(OBJECTS)
        $(CC) $^ -o $@

%.o : %.c | $(filter %.h, $(basename $(TEMPLATES)))
        $(CC) -Wall $< -c -o $@
        $(CC) -MM -MT $@ $< > $*.d

%.c : %.c.jinja
        yasha $< -o $@
        yasha -MM -MT $@ $< > $@.d

%.h : %.h.jinja
        yasha $< -o $@
        yasha -MM -MT $@ $< > $@.d

# Make sure that this built-in implicit rule is cancelled
%.o : %.c

# Prevent Make to consider rendered templates as intermediate file
.secondary : $(basename $(TEMPLATES))

# Pull in dependency info for existing .o files
-include $(OBJECTS:.o=.d)
-include $(TEMPLATES:.jinja=.d)

clean :
        -rm -f program *.o *.d $(basename $(TEMPLATES))

.phony : clean
```
