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
import click
from .. import yasha

def parse_variables(file, parsers):
    filename, filext = os.path.splitext(file.name)
    for parser in parsers:
        if filext in parser.file_extension:
            return parser.parse(file)
    return {}

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
@click.option("--searchpath", "-I", type=click.Path(exists=True, file_okay=False), multiple=True, help="Add DIRECTORY to the list of directories to be searched for referenced templates in TEMPLATE, aka hardcoded template extensions, inclusions and imports.")
@click.option("--no-variables", is_flag=True, help="Omit template variables.")
@click.option("--no-extensions", is_flag=True, help="Omit template extensions.")
@click.option("--no-trim-blocks", is_flag=True, help="Load Jinja with trim_blocks=False.")
@click.option("--no-lstrip-blocks", is_flag=True, help="Load Jinja with lstrip_blocks=False.")
@click.option("-M", is_flag=True, help="Outputs Makefile compatible list of dependencies. Doesn't render the template.")
@click.option("-MD", is_flag=True, help="Creates Makefile compatible .d file alongside a rendered template.")
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Print version and exit.")
def cli(template, output, variables, extensions, searchpath, no_variables, no_extensions, no_trim_blocks, no_lstrip_blocks, m, md):
    """Reads the given Jinja template and renders its content into a new file,
    which name is derived from the given template name. For example, a template
    called foo.c.jinja will be written into foo.c in case when the output
    file is not explicitly specified."""

    searchpath = [os.path.dirname(template.name)] + list(searchpath)

    ex = {
        "tests": [],
        "filters": [],
        "classes": [],
        "variable_parsers": [],
        "variable_preprocessors": [],
    }

    if not extensions and not no_extensions:
        filext = yasha.EXTENSIONS_FORMAT
        path = yasha.find_template_companion(template.name, filext)
        extensions = click.open_file(path, "rb") if path else None

    if extensions and not no_extensions:
        try:
            e = yasha.load_template_extensions(extensions)
            ex.update(e)
        except SyntaxError as e:
            msg = e.msg[0].upper() + e.msg[1:]
            filename = os.path.relpath(e.filename)
            click.echo("Error: Cannot load extensions", nl=False, err=True)
            click.echo(": {} ({}, line {})".format(msg, filename, e.lineno), err=True)
            raise click.Abort()

    # Default variable parsers
    ex["variable_parsers"] += yasha.DEFAULT_PARSERS

    if not variables and not no_variables:
        filext = sum([p.file_extension for p in ex["variable_parsers"]], [])
        path = yasha.find_template_companion(template.name, filext)
        variables = click.open_file(path, "rb") if path else None

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
        for d in yasha.find_referenced_templates(template, searchpath):
            deps.append(os.path.relpath(d))

        deps = os.path.relpath(output.name) + ": " + " ".join(deps)
        if m:
            click.echo(deps)
            return # Template won't be rendered
        if md:
            deps += os.linesep
            output_d = click.open_file(output.name + ".d", "wb")
            output_d.write(deps.encode("utf-8"))

    # Load Jinja and get template
    jinja = yasha.load_jinja(
        searchpath, ex["tests"], ex["filters"], ex["classes"],
        not no_trim_blocks, not no_lstrip_blocks)
    if template.name == "<stdin>":
        stdin = template.read()
        t = jinja.from_string(stdin)
    else:
        t = jinja.get_template(os.path.basename(template.name))

    # Finally parse variables and render the template
    v = {}
    if variables and not no_variables:
        v.update(parse_variables(variables, ex["variable_parsers"]))
    for preprocessor in ex["variable_preprocessors"]:
        v = preprocessor(v)

    # Write rendered template into file
    chunk_offset = None
    for chunk in t.generate(v):
        chunk_offset = output.tell()
        output.write(chunk.encode("utf-8"))

    # Add newline at the EOF if missing from template
    chunk = chunk.rstrip() + linesep(chunk)
    output.seek(chunk_offset)
    output.truncate()
    output.write(chunk.encode("utf-8"))
