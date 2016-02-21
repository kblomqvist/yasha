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
from .parsers import *

__version__ = "dev"

def find_dependencies(template, format=[".yml", ".yaml"], start=os.curdir):
    """
    Returns the first found template dependency file
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
