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
from .parsers import *

__version__ = "dev"

ENCODING = 'utf-8'
DEFAULT_PARSERS = [JsonParser(), YamlParser(), TomlParser(), SvdParser()]
EXTENSIONS_FORMAT = (".py", ".j2ext", ".jinja-ext")


def find_template_companion(template, extension, check=True):
    """
    Returns the first found template companion file
    """

    if check and not os.path.isfile(template):
        return None # May be '<stdin>' (click)

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
                if not template_basename[:-i] == file[:-1]:
                    continue

                # Template companion file found!
                return os.path.join(current_path, '.'.join(file))

        if current_path == stop_path:
            break

        # cd ..
        current_path = os.path.split(current_path)[0]

    return None


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


def load_template_extensions(file):
    """
    Returns a dictionary of template extensions, which are
    Jinja tests, filters and classes, template variable parsers
    and variable preprocessors.
    """
    from jinja2.ext import Extension
    import inspect

    try:
        from importlib.machinery import SourceFileLoader
        module = SourceFileLoader("extensions", file.name).load_module()
    except ImportError:  # Fallback to Python2
        import imp
        desc = (".py", "rb", imp.PY_SOURCE)
        module = imp.load_module("extensions", file, file.name, desc)

    e = {
        "tests": [],
        "filters": [],
        "classes": [],
        "variable_parsers": [],
        "variable_preprocessors": [],
    }

    for attr in [getattr(module, x) for x in dir(module)]:
        if inspect.isfunction(attr):
            name = attr.__name__
            if name.startswith("test_"):
                e["tests"].append(attr)
            elif name.startswith("filter_"):
                e["filters"].append(attr)
            elif name.startswith("preprocess_"):
                e["variable_preprocessors"].append(attr)

        elif inspect.isclass(attr):
            if issubclass(attr, Extension):
                e["classes"].append(attr)
            elif issubclass(attr, Parser):
                e["variable_parsers"].append(attr())

    return e


def load_jinja(search_path, tests=[], filters=[], classes=[], trim=True, lstrip=True, keep_trailing_newline=False):
    from jinja2 import Environment, FileSystemLoader
    jinja = Environment(
        loader=FileSystemLoader(search_path),
        extensions=classes,
        trim_blocks=trim,
        lstrip_blocks=lstrip,
        keep_trailing_newline=keep_trailing_newline
    )

    from .filters import FILTERS as BUILTIN_FILTERS
    jinja.filters.update(BUILTIN_FILTERS)

    for test in tests:
        name = test.__name__.replace("test_", "")
        jinja.tests[name] = test

    for filt in filters:
        name = filt.__name__.replace("filter_", "")
        jinja.filters[name] = filt

    return jinja
