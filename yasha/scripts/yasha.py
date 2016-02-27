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

import os
from os import path
import click
from ..parsers import *
from .. import yasha

def find_variables(template, filext):
    return yasha.find_dependencies(template, filext)

def find_extensions(template):
    return yasha.find_dependencies(template, [".py", ".j2ext", ".jinja-ext"])

def parse_variables(file, parsers):
    if file:
        filename, filext = path.splitext(file.name)
        for parser in parsers:
            if filext in parser.file_extension:
                return parser.parse(file)
    return {}

def load_extensions(file):
    def error_handler(e):
        msg = e.msg[0].upper() + e.msg[1:]
        filename = path.relpath(e.filename)
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
        loader=FileSystemLoader(searchpath), trim_blocks=True, lstrip_blocks=True)

    for test in extdict["jinja_tests"]:
        jinja.tests[test.__name__.replace("test_", "")] = test
    for filt in extdict["jinja_filters"]:
        jinja.filters[filt.__name__.replace("filter_", "")] = filt

    return jinja

def referenced_templates(template, include_paths):
    def template_realpath(referenced_template):
        for include in include_paths:
            t = path.join(include, referenced_template)
            t = path.realpath(t)
            if path.isfile(t):
                return t
        return None

    from jinja2 import Environment, meta
    env = Environment()
    ast = env.parse(template.read())

    templates = list(meta.find_referenced_templates(ast))
    return [template_realpath(t) for t in templates if t is not None]

def linesep(string):
    n = string.find("\n")
    if n < 1:
        return "\n"
    return "\r\n" if string[n-1] == "\r" else "\n"

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(yasha.__version__)
    ctx.exit()

@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("template", type=click.File("rb"))
@click.option("--output", "-o", type=click.File("wb"), help="Place a rendered tempalate into FILENAME.")
@click.option("--variables", "-v", type=click.File("rb"), envvar="YASHA_VARIABLES", help="Read template variables from FILENAME.")
@click.option("--extensions", "-e", type=click.File("rb"), envvar="YASHA_EXTENSIONS", help="Read template extensions from FILENAME.")
@click.option("--include", "-I", type=click.Path(exists=True, file_okay=False), multiple=True, help="Add DIRECTORY to the list of directories to be searched for referenced templates in TEMPLATE, aka hardcoded template extensions, inclusions and imports.")
@click.option("--no-variables", is_flag=True, help="Omit template variables.")
@click.option("--no-extensions", is_flag=True, help="Omit template extensions.")
@click.option("--trim", is_flag=True, help="Strips extra whitespace. Spares the single empty lines, though.")
@click.option("-M", is_flag=True, help="Outputs Makefile compatible list of dependencies. Doesn't render the template.")
@click.option("-MD", is_flag=True, help="Creates Makefile compatible .d file alongside a rendered template.")
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Print version and exit.")
def cli(template, output, variables, extensions, include, no_variables, no_extensions, trim, m, md):
    """This script reads the given Jinja template and renders its content
    into a new file, which name is derived from the given template name.

    For example, a template called "foo.c.jinja" will be written into "foo.c" if
    the output file is not explicitly specified."""

    include = [path.dirname(template.name)] + list(include)

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
            output = click.open_file("-", "wb")
        else:
            output = path.splitext(template.name)[0]
            output = click.open_file(output, "wb", lazy=True)

    if m or md:
        deps = [path.relpath(template.name)]
        if variables:
            deps.append(path.relpath(variables.name))
        if extensions:
            deps.append(path.relpath(extensions.name))
        for d in referenced_templates(template, include):
            deps.append(path.relpath(d))

        deps = path.relpath(output.name) + ": " + " ".join(deps)
        if m:
            click.echo(deps)
            return # Template won't be rendered
        if md:
            deps += os.linesep
            output_d = click.open_file(output.name + ".d", "wb")
            output_d.write(deps.encode("utf-8"))

    for preprocessor in extdict["variable_preprocessors"]:
        vardict = preprocessor(vardict)

    # Time to load Jinja
    jinja = load_jinja(include, extdict)

    if template.name == "<stdin>":
        stdin = template.read()
        t = jinja.from_string(stdin)
    else:
        t = jinja.get_template(path.basename(template.name))

    # Finally render the template
    t_rendered = t.render(vardict)

    # Add newline at the EOF if missing from template
    t_linesep = linesep(t_rendered)
    t_rendered = t_rendered.rstrip() + t_linesep

    if trim:
        prevline = None
        for line in t_rendered.splitlines():
            line = line.rstrip() + t_linesep
            if line == t_linesep and prevline == line:
                continue
            if line == t_linesep and prevline == None:
                continue
            output.write(line.encode("utf-8"))
            prevline = line
    else:
        output.write(t_rendered.encode("utf-8"))
