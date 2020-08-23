"""
The MIT License (MIT)

Copyright (c) 2015-2020 Kim Blomqvist

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

import pytest

requires_py3 = pytest.mark.skipif(sys.version_info < (3,5),
                                  reason="Requires Python >= 3.5")

def check_output(*args, **kwargs):
    params = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=2,
    )
    if 'stdin' in kwargs:
        stdin = kwargs['stdin']
        params['input'] = stdin.encode() if stdin else None

    if sys.version_info < (3, 5):
        return (subprocess.check_output(args), 0)
    else:
        cp = subprocess.run(args, **params)
        return (cp.stdout, cp.returncode)


def test_env(tmpdir):
    template = tmpdir.join('template.j2')
    template.write("{{ 'POSTGRES_URL' | env('postgresql://localhost') }}")

    out, retcode = check_output('yasha', str(template), '-o-')
    assert out == b'postgresql://localhost'

    os.environ['POSTGRES_URL'] = 'postgresql://127.0.0.1'
    out, retcode = check_output('yasha', str(template), '-o-')
    assert out == b'postgresql://127.0.0.1'


@requires_py3
def test_shell():
    template = '{{ "uname" | shell }}'
    out, retcode = check_output('yasha', '-', stdin=template)
    assert out.decode() == os.uname().sysname


@requires_py3
def test_subprocess():
    template = (
        '{% set r = "uname" | subprocess %}'
        '{{ r.stdout.decode() }}'
    )
    out, retcode = check_output('yasha', '-', stdin=template)
    assert out.decode().strip() == os.uname().sysname


@requires_py3
def test_subprocess_with_unknown_cmd():
    template = '{{ "unknown_cmd" | subprocess }}'
    out, retcode = check_output('yasha', '-', stdin=template)
    assert retcode != 0
    assert b'not found' in out


@requires_py3
def test_subprocess_with_unknown_cmd_while_check_is_false():
    template = (
        '{% set r = "unknown_cmd" | subprocess(check=False) %}'
        '{{ r.returncode > 0 }}'
    )
    out, retcode = check_output('yasha', '-', stdin=template)
    assert out == b'True'
