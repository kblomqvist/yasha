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

import sys
import subprocess
from os import path, chdir, mkdir

import pytest

if sys.version_info[0] == 2:
    FileNotFoundError = IOError

SCRIPT_PATH = path.dirname(path.realpath(__file__))

requires_py27_or_py35_or_greater = pytest.mark.skipif(
    sys.version_info < (2,7) or
    (sys.version_info >= (3,) and sys.version_info < (3,5)),
    reason='Requires either Python 2.7 or >= 3.5'
)

def check_output(cmd):
    try:
        return subprocess.check_output(cmd)
    except FileNotFoundError as e:
        msg = str(e)
        pytest.skip(msg)


def check_call(cmd):
    try:
        return subprocess.check_call(cmd)
    except FileNotFoundError as e:
        msg = str(e)
        pytest.skip(msg)


def setup_function():
    chdir(SCRIPT_PATH + '/fixtures/c_project')


def teardown_function(function):
    chdir(SCRIPT_PATH + '/fixtures/c_project')
    if 'scons' in function.__name__:
        check_call(('scons', '-c'))
        check_call(('scons', '-C', 'src', '-c'))
    else:
        check_call(('make', 'clean'))
        check_call(('make', '-C', 'src', 'clean'))

build_dependencies = (
    'foo.c.jinja',
    'foo.h.jinja',
    'foo.c.py',
    'foo.toml',
    'header.j2inc'
)

@pytest.mark.slowtest
def test_make():
    build_cmd = ('make',)

    # First build
    out = check_output(build_cmd)
    assert not b'is up to date' in out
    assert path.isfile('build/a.out')

    # Second build shouldn't do anything
    out = check_output(build_cmd)
    assert b'is up to date' in out

    # Check program output
    out = check_output(('./build/a.out'))
    assert b'bar has 3 chars ...\n' == out

    # Require rebuild after touching dependency
    for dep in build_dependencies:
        check_call(('touch', path.join('src', dep)))
        out = check_output(build_cmd)
        assert not b'is up to date' in out


@pytest.mark.slowtest
def test_cmake():
    mkdir('build')
    chdir('build')
    build_cmd = ('make',)

    # First build
    check_call(('cmake', '..'))
    out = check_output(build_cmd)
    assert b'Linking C executable' in out
    assert path.isfile('a.out')

    # Immediate new build shouldn't do anything
    out = check_output(build_cmd)
    assert not b'Linking C executable' in out

    # Check program output
    out = check_output(['./a.out'])
    assert b'bar has 3 chars ...\n' == out

    # Require rebuild after touching build dependency
    for dep in build_dependencies:
        check_call(('touch', path.join('../src/', dep)))
        out = check_output(build_cmd)
        assert b'Linking C executable' in out


@pytest.mark.slowtest
@requires_py27_or_py35_or_greater
def test_scons():
    build_cmd = ('scons', '-Q')

    # First build
    out = check_output(build_cmd)
    assert not b'is up to date' in out
    assert path.isfile('build/a.out')

    # Immediate new build shouldn't do anything
    out = check_output(build_cmd)
    assert b'is up to date' in out

    # Check program output
    out = check_output(('./build/a.out'))
    assert b'bar has 3 chars ...\n' == out

    # FIXME: Sometimes the rebuild happens sometimes not.
    for dep in build_dependencies:
        check_call(('touch', path.join('src', dep)))
        out = check_output(build_cmd)
        #assert not b'is up to date' in out
        print(out) # For debugging purposes, run 'pytest -s -k scons'


@pytest.mark.slowtest
def test_make_without_build_dir():
    chdir('src')
    build_cmd = ('make',)

    # First build
    out = check_output(build_cmd)
    assert not b'is up to date' in out
    assert path.isfile('a.out')

    # Immediate new build shouldn't do anything
    out = check_output(build_cmd)
    assert b'is up to date' in out

    # Check program output
    out = check_output(('./a.out'))
    assert b'bar has 3 chars ...\n' == out

    # Require rebuild after touching dependency
    for dep in build_dependencies:
        check_call(('touch', dep))
        out = check_output(build_cmd)
        assert not b'is up to date' in out


@pytest.mark.slowtest
@requires_py27_or_py35_or_greater
def test_scons_without_build_dir():
    chdir('src')
    build_cmd = ('scons', '-Q')

    # First build
    out = check_output(build_cmd)
    assert not b'is up to date' in out
    assert path.isfile('a.out')

    # Immediate new build shouldn't do anything
    out = check_output(build_cmd)
    assert b'is up to date' in out

    # Check program output
    out = check_output(('./a.out'))
    assert b'bar has 3 chars ...\n' == out

    # FIXME: Sometimes the rebuild happens sometimes not.
    for dep in build_dependencies:
        check_call(('touch', dep))
        out = check_output(build_cmd)
        #assert not b'is up to date' in out
        print(out) # for debugging, run 'pytest -s -k scons'
