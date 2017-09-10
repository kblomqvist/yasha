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
import sys
import subprocess

from .yasha import ENCODING

def do_env(value, default=None):
    return os.environ.get(value, default)

def do_subprocess(args, stdout=True, stderr=True, shell=True, check=True):
    kwargs = dict(
        args=args,
        stdout=subprocess.PIPE if stdout else None,
        stderr=subprocess.PIPE if stderr else None,
        shell=shell,
        check=check,
    )
    assert sys.version_info >= (3,5)
    return subprocess.run(**kwargs)

def do_stdout(cp, encoding=ENCODING):
    assert sys.version_info >= (3,5)
    assert isinstance(cp, subprocess.CompletedProcess)
    return cp.stdout.decode(encoding=encoding) if cp.stdout else None

def do_stderr(cp, encoding=ENCODING):
    assert sys.version_info >= (3,5)
    assert isinstance(cp, subprocess.CompletedProcess)
    return cp.stderr.decode(encoding=encoding) if cp.stderr else None

FILTERS = {
    'env': do_env,
    'subprocess': do_subprocess,
    'stdout': do_stdout,
    'stderr': do_stderr,
}
