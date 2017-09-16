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

from click import ClickException
from .yasha import ENCODING

def do_env(value, default=None):
    return os.environ.get(value, default)

def do_subprocess(cmd, encoding=ENCODING, check=True, strip=True):
    assert sys.version_info >= (3,5)
    kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        check=False,
    )
    result = subprocess.run(cmd, **kwargs)
    if result.returncode and check:
        errno = result.returncode
        error = result.stderr.decode().strip()
        msg = "Command '{}' returned non-zero exit status {}\n{}"
        raise ClickException(msg.format(cmd, errno, error))
    if not strip:
        return result.stdout.decode(encoding=encoding)
    else:
        return result.stdout.decode(encoding=encoding).strip()

FILTERS = {
    'env': do_env,
    'subprocess': do_subprocess,
}
