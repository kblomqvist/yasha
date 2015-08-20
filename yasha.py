"""
Copyright (c) 2015 Kim Blomqvist, https://kblomqvist.github.io

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import click

class TomlParser():
    file_extension = [".toml"]

    def parse(self, file):
        import pytoml as toml
        return toml.load(file)

class YamlParser():
    file_extension = [".yaml", ".yml"]

    def parse(self, file):
        import yaml
        return yaml.load(file)

def possible_variables_filepaths(template):
    paths = [os.path.dirname(template)]
    src_path = os.path.abspath(template)
    for _ in range(src_path.count(os.path.sep)):
        paths.append(os.path.join(paths[-1], ".."))
    return paths

def possible_variables_filenames(template):
    files = []
    src_name, src_extension = os.path.splitext(template)
    src_name = os.path.basename(src_name)
    src_name = src_name.split(".")
    for i, _ in enumerate(src_name):
        files.insert(0, ".".join(src_name[0:i+1]))
    return files

def find_variables(template, filext):
    varpath = None
    filepaths = possible_variables_filepaths(template)
    filenames = possible_variables_filenames(template)
    
    for path in filepaths:
        if varpath:
            break
        for variables_name in filenames:
            if varpath:
                break
            for ext in filext:
                test = os.path.join(path, variables_name + ext)
                if os.path.isfile(test):
                    varpath = os.path.abspath(test)
                    break

    return varpath

def find_extensions(template):
    return find_variables(template, [".jinja-ext"])

def parse_variables(file, parsers):
    if file:
        filename, filext = os.path.splitext(file.name)
        for parser in parsers:
            if filext in parser.file_extension:
                return parser.parse(file)
    return {}

def load_extensions(file):
    if file:
        import imp
        pathname = os.path.basename(file.name)
        name = os.path.splitext(pathname)[0]
        name = name.replace(".", "_")
        desc = (".py", "rb", imp.PY_SOURCE)
        return imp.load_module(name, file, pathname, desc)
    return None

def parse_extensions(extmodule, extdict):
    from jinja2.ext import Extension
    import inspect

    attrs = [getattr(extmodule, x) for x in dir(extmodule) if not x.startswith("__")]
    for x in attrs:
        if inspect.isfunction(x):
            if x.__name__.startswith("test_"):
                extdict["jinja_tests"].append(x)
            elif x.__name__.startswith("filter_"):
                extdict["jinja_filters"].append(x)
        elif inspect.isclass(x):
            if issubclass(x, Extension):
                extdict["jinja_extensions"].append(x)
            elif x.__name__.endswith("Parser"):
                extdict["variable_parsers"].insert(0, x()) # Parsers are prepended

    return extdict

def load_jinja(searchpath, extdict):
    from jinja2 import Environment, FileSystemLoader

    jinja = Environment(extensions=extdict["jinja_extensions"],
        loader=FileSystemLoader(searchpath))

    for test in extdict["jinja_tests"]:
        jinja.tests[test.__name__.replace("test_", "")] = test
    for filt in extdict["jinja_filters"]:
        jinja.filters[filt.__name__.replace("filter_", "")] = filt

    return jinja

@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("template", type=click.File("rb"))
@click.option("--variables", "-a", type=click.File("rb"), envvar="YASHA_VARIABLES", help="Template variables file name.")
@click.option("--extensions", "-e", type=click.File("rb"), envvar="YASHA_EXTENSIONS", help="Custom Jinja extensions file name.")
@click.option("--output", "-o", type=click.File("wb"), help="Output file name. Standard output works too.")
@click.option("--no-variables", is_flag=True, help="Omit template variables.")
@click.option("--no-extensions", is_flag=True, help="Omit Jinja extensions.")
@click.option("-MM", is_flag=True, help="Works as GCC's -MM.")
@click.option("-MT", type=click.STRING, help="Works as GCC's -MT.")
def cli(template, variables, extensions, output, no_variables, no_extensions, mm, mt):
    """This script reads the given Jinja template and renders its content
    into new file, which name is derived from the given template name. For
    example the rendered foo.c.jinja template will be written into foo.c if
    not explicitly specified."""

    t_realpath = os.path.realpath(template.name)
    t_basename = os.path.basename(t_realpath)
    t_dirname = os.path.dirname(t_realpath)
    
    vardict = {

    }
    
    extdict = {
        "jinja_tests": [],
        "jinja_filters": [],
        "jinja_extensions": [],
        "variable_parsers": [TomlParser(), YamlParser()],
    }

    if not extensions and not no_extensions:
        extpath = find_extensions(template.name)
        extensions = click.open_file(extpath, "rb") if extpath else None

    if extensions and not no_extensions:
        extmodule = load_extensions(extensions)
        extdict = parse_extensions(extmodule, extdict)

    if not variables and not no_variables:
        filext = [p.file_extension for p in extdict["variable_parsers"]]
        varpath = find_variables(template.name, sum(filext, []))
        variables = click.open_file(varpath, "rb") if varpath else None

    if mm:
        if mt:
            deps = mt + ": "
        else:
            deps = os.path.relpath(template.name)
            deps = os.path.splitext(deps)[0] + ": "
        if variables:
            deps += os.path.relpath(variables.name) + " "
        if extensions:
            deps += os.path.relpath(extensions.name)
        click.echo(deps)
        return

    if variables and not no_variables:
        vardict = parse_variables(variables, extdict["variable_parsers"])

    jinja = load_jinja(t_dirname, extdict)
    t = jinja.get_template(t_basename)

    if not output:
        o_realpath = os.path.splitext(t_realpath)[0]
        output = click.open_file(o_realpath, "wb")

    output.write(t.render(vardict))
