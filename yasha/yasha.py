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

DEFAULT_PARSERS = [JsonParser(), YamlParser(), TomlParser(), SvdParser()]
EXTENSIONS_FORMAT = [".py", ".j2ext", ".jinja-ext"]


def find_template_companion(template, format=[".yml", ".yaml"], start=os.curdir):
    """
    Returns the first found template companion file. This can be a variable
    file or extension file.
    """
    if type(format) is str:
        format = [format]

    path = os.path.dirname(template)
    path = os.path.join(start, path)
    template = os.path.basename(template)

    while True:
        file = os.path.join(path, template)
        file, filext = os.path.splitext(file)

        while filext:
            for ext in format:
                if os.path.isfile(file + ext):
                    return os.path.relpath(file + ext, start)
            file, filext = os.path.splitext(file)

        if os.path.normpath(path) == start:
            break
        if os.path.realpath(path) == "/":
            break
        path = os.path.join(path, "..")

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

    for test in tests:
        name = test.__name__.replace("test_", "")
        jinja.tests[name] = test

    for filt in filters:
        name = filt.__name__.replace("filter_", "")
        jinja.filters[name] = filt

    return jinja
