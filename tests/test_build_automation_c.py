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

import pytest, sys
from os import path, chdir
from subprocess import call, check_output

SCRIPT_PATH = path.dirname(path.realpath(__file__))

def test_make():
    chdir(SCRIPT_PATH)
    chdir("yasha_for_c")

    # First build
    out = check_output(["make"])
    assert not b"is up to date" in out
    assert path.isfile("build/a.out")

    # Second build shouldn't do anything
    out = check_output(["make"])
    assert b"is up to date" in out

    # Check program output
    out = check_output(["./build/a.out"])
    assert b"foo has 3 chars ...\n" == out

    # Test template dependencies
    for dep in ["foo.toml", "foo.h.jinja", "foo.c.jinja"]:
        call(["touch", "src/" + dep])
        out = check_output(["make"])
        assert not b"is up to date" in out

    # Clean the build
    call(["make", "clean"])
    for f in ["foo.c", "foo.c.d", "foo.h", "foo.h.d"]:
        assert not path.isfile("src/" + f)

@pytest.mark.skipif(sys.version_info[0] > 2,
    reason="requires python2")
def test_scons():
    chdir(SCRIPT_PATH)
    chdir("yasha_for_c")

    # First build
    out = check_output(["scons"])
    assert not b"is up to date" in out
    assert path.isfile("build/a.out")

    # Second build shouldn't do anything
    out = check_output(["scons"])
    assert b"is up to date" in out

    # Check program output
    out = check_output(["./build/a.out"])
    assert b"foo has 3 chars ...\n" == out

# TODO: Fix race condition. Every now and then fails. Though,
# call() shouldn't return before finished.

    for dep in []: #["foo.toml", "foo.h.jinja", "foo.c.jinja"]:
        call(["touch", "src/" + dep])
        out = check_output(["scons"])
        assert not b"is up to date" in out

    # Clean the build
    call(["scons", "-c"])
    for f in ["foo.c", "foo.c.d", "foo.h", "foo.h.d"]:
        assert not path.isfile("build/"+f)
