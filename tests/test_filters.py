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
from subprocess import check_output

import pytest


def test_env(template):
    template.write("{{ 'POSTGRES_URL' | env('postgresql://localhost') }}")

    out = check_output(['yasha', str(template), '-o-'])
    assert out == b'postgresql://localhost'

    os.environ['POSTGRES_URL'] = 'postgresql://127.0.0.1'
    out = check_output(['yasha', str(template), '-o-'])
    assert out == b'postgresql://127.0.0.1'


@pytest.mark.skipif(sys.version_info < (3,5), reason="Requires Python>=3.5")
def test_shell(template):
    template.write('{{ "uname" | shell }}')
    out = check_output(('yasha', str(template), '-o-'))
    assert out.decode() == os.uname().sysname


@pytest.mark.skipif(sys.version_info < (3,5), reason="Requires Python>=3.5")
def test_subprocess(template):
    template.write('{% set return = "uname" | subprocess %}{{ return.stdout.decode() }}')
    out = check_output(('yasha', str(template), '-o-'))
    assert out.decode().strip() == os.uname().sysname


@pytest.mark.skipif(sys.version_info < (3,5), reason="Requires Python>=3.5")
def test_subprocess_unknown_cmd(template):
    template.write('{{ "unknown_cmd" | subprocess }}')
    # out = check_output(('yasha', str(template), '-o-'))
    # assert 'unknown_cmd: not found' in out.decode()


@pytest.mark.skipif(sys.version_info < (3,5), reason="Requires Python>=3.5")
def test_subprocess_dont_check(template):
    template.write('{% set r = "unknown_cmd" | subprocess(check=False) %}{{ r.returncode > 0 }}')
    out = check_output(('yasha', str(template), '-o-'))
    assert out == b'True'
