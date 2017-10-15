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

import pytest
import sys
from os import path, chdir, mkdir
from subprocess import call, check_output

SCRIPT_PATH = path.dirname(path.realpath(__file__))

requires_py3 = pytest.mark.skipif(sys.version_info < (3,5),
                         reason="Requires Python >= 3.5")

@pytest.fixture()
def clean():
    chdir(SCRIPT_PATH + "/fixtures/c_project")
    call(("make", "clean")) # Case build dir
    call(("make", "-C", "src", "clean")) # Case no build dir


@pytest.mark.slowtest
def test_make(clean):
    # First build
    out = check_output(["make"])
    assert not b"is up to date" in out
    assert path.isfile("build/a.out")

    # Second build shouldn't do anything
    out = check_output(["make"])
    assert b"is up to date" in out

    # Check program output
    out = check_output(["./build/a.out"])
    assert b"bar has 3 chars ...\n" == out

    # Test template dependencies
    for dep in ["foo.toml", "foo.h.jinja", "foo.c.jinja", "foo.c.py", "header.j2inc"]:
        call(["touch", "src/" + dep])
        out = check_output(["make"])
        assert not b"is up to date" in out


@pytest.mark.slowtest
def test_cmake(clean):
    mkdir("build")
    chdir("build")

    # First build
    call(["cmake", ".."])
    out = check_output(["make"])
    assert b"Linking C executable" in out
    assert path.isfile("a.out")

    # Second build shouldn't do anything
    out = check_output(["make"])
    assert not b"Linking C executable" in out

    # Check program output
    out = check_output(["./a.out"])
    assert b"bar has 3 chars ...\n" == out

    # Test template dependencies
    for dep in ["foo.toml", "foo.h.jinja", "foo.c.jinja", "foo.c.py", "header.j2inc"]:
        call(["touch", "../src/" + dep])
        out = check_output(["make"])
        assert b"Linking C executable" in out


@requires_py3
@pytest.mark.slowtest
def test_scons(clean):
    # First build
    out = check_output(["scons"])
    assert not b"is up to date" in out
    assert path.isfile("build/a.out")

    # Second build shouldn't do anything
    out = check_output(["scons"])
    assert b"is up to date" in out

    # Check program output
    out = check_output(["./build/a.out"])
    assert b"bar has 3 chars ...\n" == out

# TODO: Fix race condition. Every now and then fails. Though,
# call() shouldn't return before finished.

    for dep in []:  # ["foo.toml", "foo.h.jinja", "foo.c.jinja"]:
        call(["touch", "src/" + dep])
        out = check_output(["scons"])
        assert not b"is up to date" in out
