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
import ast

__version__ = "dev"

ENCODING = 'utf-8'
EXTENSION_FILE_FORMATS = ('.py', '.yasha', '.j2ext', '.jinja-ext')

def find_template_companion(template, extension='', check=True):
    """
    Returns the first found template companion file
    """

    if check and not os.path.isfile(template):
        yield ''
        return # May be '<stdin>' (click)

    template = os.path.abspath(template)
    template_basename = os.path.basename(template).split('.')

    current_path = os.path.dirname(template)
    stop_path = os.path.commonprefix((os.getcwd(), current_path))
    stop_path = os.path.dirname(stop_path) # Make sure to remove 'test_' from '/tmp/pytest-of-foo/pytest-111/test_'

    token = template_basename[0] + '.'

    while True:
        for file in sorted(os.listdir(current_path)):
            if not file.startswith(token):
                continue
            if not file.endswith(extension):
                continue
            file = file.split('.')
            for i in range(1, len(template_basename)):
                if template_basename[:-i] == file[:-1]:
                    yield os.path.join(current_path, '.'.join(file))

        if current_path == stop_path:
            break

        # cd ..
        current_path = os.path.split(current_path)[0]


def find_referenced_templates(template, search_path):
    """
    Returns a list of files which can be either {% imported %},
    {% extended %} or {% included %} within a template.
    """
    from jinja2 import Environment, meta
    env = Environment()
    ast = env.parse(template.read())
    referenced_templates = list(meta.find_referenced_templates(ast))

    def realpath(tpl):
        for path in search_path:
            t = os.path.realpath(os.path.join(path, tpl))
            if os.path.isfile(t):
                return t
        return None

    return [realpath(t) for t in referenced_templates if t is not None]


def parse_cli_variables(args):
    variables = dict()
    for i, arg in enumerate(args):
        if arg[:2] != '--':
            continue
        if '=' in arg:
            opt, val = arg[2:].split('=', 1)
        else:
            try:
                if args[i+1] != '--':
                    opt = arg[2:]
                    val = args[i+1]
            except IndexError:
                break
        try:
            val = ast.literal_eval(val)
        except ValueError:
            pass
        except SyntaxError:
            pass
        if isinstance(val, str) and ',' in val:
            # Convert foo,bar,baz to list ['foo', 'bar', 'baz']
            val = val.split(',')
        variables[opt] = val
    return variables


def load_jinja(path, tests, filters, classes, trim_blocks, lstrip_blocks, keep_trailing_newline):
    from jinja2 import Environment, FileSystemLoader
    jinja = Environment(
        loader=FileSystemLoader(path),
        extensions=classes,
        trim_blocks=trim_blocks,
        lstrip_blocks=lstrip_blocks,
        keep_trailing_newline=keep_trailing_newline
    )
    jinja.tests.update(tests)
    jinja.filters.update(filters)
    return jinja
