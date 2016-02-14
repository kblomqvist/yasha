"""
The MIT License (MIT)

Copyright (c) 2015-2016 Kim Blomqvist

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

import os, sys
import click
from ..parsers import *
from .. import yasha

def find_variables(template, filext):
    return yasha.find_dependencies(template, filext)

def find_extensions(template):
    return yasha.find_dependencies(template, [".py", ".j2ext", ".jinja-ext"])

def parse_variables(file, parsers):
    if file:
        filename, filext = os.path.splitext(file.name)
        for parser in parsers:
            if filext in parser.file_extension:
                return parser.parse(file)
    return {}

def load_extensions(file):
    def error_handler(e):
        msg = e.msg[0].upper() + e.msg[1:]
        filename = os.path.relpath(e.filename)
        click.echo("Error: Cannot load extensions", nl=False, err=True)
        click.echo(": {} ({}, line {})".format(msg, filename, e.lineno), err=True)
        raise click.Abort()

    try:
        from importlib.machinery import SourceFileLoader
        module = SourceFileLoader("extensions", file.name).load_module()
    except SyntaxError as e:
        error_handler(e)
    except ImportError:
        pass # fallback to Python2

    try:
        import imp
        desc = (".py", "rb", imp.PY_SOURCE)
        module = imp.load_module("extensions", file, file.name, desc)
    except SyntaxError as e:
        error_handler(e)

    return module

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
            elif x.__name__.startswith("preprocess_"):
                extdict["variable_preprocessors"].append(x)
        elif inspect.isclass(x):
            if issubclass(x, Extension):
                extdict["jinja_extensions"].append(x)
            elif issubclass(x, Parser):
                extdict["variable_parsers"].insert(0, x()) # Prepend custom parser

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
@click.option("--output", "-o", type=click.File("wt"), help="Place a rendered tempalate into FILENAME.")
@click.option("--variables", "-v", type=click.File("rb"), envvar="YASHA_VARIABLES", help="Read template variables from FILENAME.")
@click.option("--extensions", "-e", type=click.File("rb"), envvar="YASHA_EXTENSIONS", help="Read template extensions from FILENAME.")
@click.option("--no-variables", is_flag=True, help="Omit template variables.")
@click.option("--no-extensions", is_flag=True, help="Omit template extensions.")
@click.option("--trim", is_flag=True, help="Strips extra whitespace. Spares the single empty lines, though.")
@click.option("-MD", is_flag=True, help="Creates Makefile compatible .d file alongside a rendered template.")
@click.option("-M", is_flag=True, help="Outputs Makefile compatible list of dependencies. Doesn't render the template.")
def cli(template, output, variables, extensions, no_variables, no_extensions, trim, md, m):
    """This script reads a given Jinja template and renders its content
    into new file, which name is derived from the given template name.

    For example, a template file "foo.c.jinja" will be written into "foo.c" if
    the output file is not explicitly specified."""

    t_realpath = os.path.realpath(template.name)
    t_basename = os.path.basename(t_realpath)
    t_dirname = os.path.dirname(t_realpath)

    vardict = {

    }

    extdict = {
        "jinja_tests": [],
        "jinja_filters": [],
        "jinja_extensions": [],
        "variable_parsers": [TomlParser(), YamlParser(), SvdParser()],
        "variable_preprocessors": [],
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

    if variables and not no_variables:
        vardict = parse_variables(variables, extdict["variable_parsers"])

    if not output:
        if template.name == "<stdin>":
            output = click.open_file("-", "wt")
        else:
            output = os.path.splitext(t_realpath)[0]
            output = click.open_file(output, "wt", lazy=True)

    if m or md:
        deps = os.path.relpath(output.name) + ": "
        deps += os.path.relpath(template.name)
        if variables:
            deps += " " + os.path.relpath(variables.name)
        if extensions:
            deps += " " + os.path.relpath(extensions.name)
        if m:
            click.echo(deps)
            return # Template won't be rendered
        if md:
            output_d = click.open_file(output.name + ".d", "wt")
            output_d.write(deps)

    for preprocessor in extdict["variable_preprocessors"]:
        vardict = preprocessor(vardict)

    jinja = load_jinja(t_dirname, extdict)

    if template.name == "<stdin>":
        template_string = ""
        while True:
            chunk = template.read(1024)
            if not chunk:
                break
            template_string += chunk.decode("utf-8")
        t = jinja.from_string(template_string)
    else:
        t = jinja.get_template(t_basename)

    if trim:
        prevline = os.linesep
        for line in t.render(vardict).splitlines():
            line = line.rstrip() + os.linesep
            if line == os.linesep and line == prevline:
                continue
            if sys.version_info[0] < 3:
                output.write(line.encode("utf-8"))
            else:
                output.write(line)
            prevline = line
    else:
        if sys.version_info[0] < 3:
            output.write(t.render(vardict).encode("utf-8"))
        else:
            output.write(t.render(vardict))
