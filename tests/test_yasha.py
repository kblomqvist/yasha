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

import os
import yasha.yasha as yasha


@pytest.fixture(params=["tmpdir", "curdir"])
def cwd(request, tmpdir):
    if request.param == "tmpdir":
        return str(tmpdir)
    if request.param == "curdir":
        tmpdir.chdir()
        return os.curdir


def test_template_depends_none(tmpdir, cwd):
    dep = yasha.find_template_companion("foo.c.jinja", start=cwd)
    assert dep == None


def test_template_depends_foo_yaml(tmpdir, cwd):
    tmpdir.join("foo.yaml").write("")
    dep = yasha.find_template_companion("foo.c.jinja", start=cwd)
    assert dep == "foo.yaml"


def test_template_depends_foo_c_yaml(tmpdir, cwd):
    tmpdir.join("foo.c.yaml").write("")
    dep = yasha.find_template_companion("foo.c.jinja", start=cwd)
    assert dep == "foo.c.yaml"


def test_template_depends_foo_yaml_in_subdir(tmpdir, cwd):
    sub = tmpdir.mkdir("sub")
    sub.join("foo.yaml").write("")
    dep = yasha.find_template_companion("sub/foo.c.jinja", start=cwd)
    assert dep == "sub/foo.yaml"


def test_template_depends_foo_c_yaml_in_subdir(tmpdir, cwd):
    sub = tmpdir.mkdir("sub")
    sub.join("foo.yaml").write("")
    sub.join("foo.c.yaml").write("")
    dep = yasha.find_template_companion("sub/foo.c.jinja", start=cwd)
    assert dep == "sub/foo.c.yaml"


def test_template_depends_foo_yaml_below_subdir(tmpdir, cwd):
    tmpdir.join("foo.yaml").write("")
    tmpdir.mkdir("sub")
    dep = yasha.find_template_companion("sub/foo.c.jinja", start=cwd)
    assert dep == "foo.yaml"


def test_dependencies_arent_find_below_cwd(tmpdir):
    tmpdir.join("foo.yaml").write("")
    tmpdir.mkdir("sub").chdir()
    dep = yasha.find_template_companion("foo.c.jinja")
    assert dep == None
