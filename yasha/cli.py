"""
The MIT License (MIT)

Copyright (c) 2015-2017 Kim Blomqvist

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
import encodings

import click
from click import ClickException

from . import yasha
from .tests import TESTS
from .filters import FILTERS
from .classes import CLASSES
from .parsers import PARSERS

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(yasha.__version__)
    ctx.exit()

def parse_variable_file(file):
    try:
        file_extension = os.path.splitext(file.name)[1]
        return PARSERS[file_extension](file)
    except AttributeError:
        return dict()
    except KeyError:
        error = "Unkown variable file extension '{}'"
        raise ClickException(error.format(file_extension))

def load_python_module(file):
    try:
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader('yasha_extensions', file.name)
        module = loader.load_module()
    except ImportError:  # Fallback to Python2
        import imp
        desc = (".py", "rb", imp.PY_SOURCE)
        module = imp.load_module('yasha_extensions', file, file.name, desc)
    return module

def load_extensions(file):
    from jinja2.ext import Extension
    import inspect

    tests   = dict()
    filters = dict()
    parsers = dict()
    classes = []

    try:
        module = load_python_module(file)
    except NameError as e:
        msg = 'Unable to load extensions, {}'
        raise ClickException(msg.format(e))
    except SyntaxError as e:
        msg = "Unable to load extensions\n{} ({}, line {})"
        error = e.msg[0].upper() + e.msg[1:]
        filename = os.path.relpath(e.filename)
        raise ClickException(msg.format(error, filename, e.lineno))

    for attr in [getattr(module, x) for x in dir(module)]:
        if inspect.isfunction(attr):
            if attr.__name__.startswith('test_'):
                name = attr.__name__[5:]
                tests[name] = attr
            if attr.__name__.startswith('filter_'):
                name = attr.__name__[7:]
                filters[name] = attr
            if attr.__name__.startswith('parse_'):
                name = attr.__name__[6:]
                parsers['.' + name] = attr
        if inspect.isclass(attr):
            if issubclass(attr, Extension):
                classes.append(attr)

    try:
        TESTS.update(module.TESTS)
    except AttributeError:
        TESTS.update(tests)

    try:
        FILTERS.update(module.FILTERS)
    except AttributeError:
        FILTERS.update(filters)

    try:
        PARSERS.update(module.PARSERS)
    except AttributeError:
        PARSERS.update(parsers)


@click.command(context_settings=dict(
    help_option_names=["-h", "--help"],
    ignore_unknown_options=True,
))
@click.argument("template_variables", nargs=-1, type=click.UNPROCESSED)
@click.argument("template", type=click.File("rb"))
@click.option("--output", "-o", type=click.File("wb"), help="Place the rendered template into FILENAME.")
@click.option("--variables", "-v", type=click.File("rb"), help="Read template variables from FILENAME. Built-in parsers are JSON, YAML, TOML and XML.")
@click.option("--extensions", "-e", envvar='YASHA_EXTENSIONS', type=click.File("rb"), help="Read template extensions from FILENAME. A Python file is expected.")
@click.option("--encoding", "-c", default=yasha.ENCODING, help="Default is UTF-8.")
@click.option("--include_path", "-I", type=click.Path(exists=True, file_okay=False), multiple=True, help="Add DIRECTORY to the list of directories to be searched for the referenced templates.")
@click.option("--no-variable-file", is_flag=True, help="Omit template variable file.")
@click.option("--no-extension-file", is_flag=True, help="Omit template extension file.")
@click.option("--no-trim-blocks", is_flag=True, help="Load Jinja with trim_blocks=False.")
@click.option("--no-lstrip-blocks", is_flag=True, help="Load Jinja with lstrip_blocks=False.")
@click.option("--keep-trailing-newline", is_flag=True, help="Load Jinja with keep_trailing_newline=True.")
@click.option("-M", is_flag=True, help="Outputs Makefile compatible list of dependencies. Doesn't render the template.")
@click.option("-MD", is_flag=True, help="Creates Makefile compatible .d file alongside the rendered template.")
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Print version and exit.")
def cli(template_variables, template, output, variables, extensions, encoding, include_path, no_variable_file, no_extension_file, no_trim_blocks, no_lstrip_blocks, keep_trailing_newline, m, md):
    """Reads the given Jinja TEMPLATE and renders its content
    into a new file. For example, a template called 'foo.c.j2'
    will be written into 'foo.c' in case the output file is not
    explicitly given.

    Template variables can be defined in a separate file or
    given as part of the command-line call, e.g.

        yasha --hello=world -o output.txt template.j2

    defines a variable 'hello' for a template like:
    
        Hello {{ hello }} !
    """

    # Set the encoding of the template file
    if encodings.search_function(encoding) is None:
        msg = "Unrecognized encoding name '{}'"
        raise ClickException(msg.format(encoding))
    yasha.ENCODING = encoding

    # Append include path of referenced templates
    include_path = [os.path.dirname(template.name)] + list(include_path)

    if not extensions or not variables:
        template_companion = yasha.find_template_companion(template.name)
        template_companion = list(template_companion)

    if not extensions and not no_extension_file:
        for file in template_companion:
            if file.endswith(yasha.EXTENSION_FILE_FORMATS):
                extensions = click.open_file(file, "rb")
                break

    if extensions:
        load_extensions(extensions)

    if not variables and not no_variable_file:
        for file in template_companion:
            if file.endswith(tuple(PARSERS.keys())):
                variables = click.open_file(file, "rb")
                break

    if not output:
        if template.name == "<stdin>":
            output = click.open_file("-", "wb")
        else:
            output = os.path.splitext(template.name)[0]
            output = click.open_file(output, "wb", lazy=True)

    if m or md:
        deps = [os.path.relpath(template.name)]
        if variables:
            deps.append(os.path.relpath(variables.name))
        if extensions:
            deps.append(os.path.relpath(extensions.name))
        for d in yasha.find_referenced_templates(template, include_path):
            deps.append(os.path.relpath(d))

        deps = os.path.relpath(output.name) + ": " + " ".join(deps)
        if m:
            click.echo(deps)
            return  # Template won't be rendered
        if md:
            deps += os.linesep
            output_d = click.open_file(output.name + ".d", "wb")
            output_d.write(deps.encode(yasha.ENCODING))

    # Load Jinja
    jinja = yasha.load_jinja(
        path=include_path,
        tests=TESTS,
        filters=FILTERS,
        classes=CLASSES,
        trim_blocks=not no_trim_blocks,
        lstrip_blocks=not no_lstrip_blocks,
        keep_trailing_newline=keep_trailing_newline
    )

    # Get template
    if template.name == "<stdin>":
        stdin = template.read()
        t = jinja.from_string(stdin.decode(yasha.ENCODING))
    else:
        t = jinja.get_template(os.path.basename(template.name))

    # Parse variables
    context = parse_variable_file(variables)
    context.update(yasha.parse_cli_variables(template_variables))

    # Finally render template and save it
    t_stream = t.stream(context)
    t_stream.enable_buffering(size=5)
    t_stream.dump(output, encoding=yasha.ENCODING)
