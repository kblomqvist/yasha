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
    dep = yasha.find_dependencies("foo.c.jinja", start=cwd)
    assert dep == None


def test_template_depends_foo_yaml(tmpdir, cwd):
    foo_yaml = tmpdir.join("foo.yaml")
    foo_yaml.write("")
    dep = yasha.find_dependencies("foo.c.jinja", start=cwd)
    assert dep == "foo.yaml"


def test_template_depends_foo_c_yaml(tmpdir, cwd):
    foo_c_yml = tmpdir.join("foo.c.yaml")
    foo_c_yml.write("")
    dep = yasha.find_dependencies("foo.c.jinja", start=cwd)
    assert dep == "foo.c.yaml"


def test_template_depends_foo_yaml_in_subdir(tmpdir, cwd):
    sub = tmpdir.mkdir("sub")
    sub_foo_yaml = sub.join("foo.yaml")
    sub_foo_yaml.write("")
    dep = yasha.find_dependencies("sub/foo.c.jinja", start=cwd)
    assert dep == "sub/foo.yaml"


def test_template_depends_foo_c_yaml_in_subdir(tmpdir, cwd):
    sub = tmpdir.mkdir("sub")
    sub_foo_yaml = sub.join("foo.yaml")
    sub_foo_yaml.write("")

    sub_foo_c_yaml = sub.join("foo.c.yaml", start=cwd)
    sub_foo_c_yaml.write("")

    dep = yasha.find_dependencies("sub/foo.c.jinja", start=cwd)
    assert dep == "sub/foo.c.yaml"


def test_template_depends_foo_yaml_below_subdir(tmpdir, cwd):
    tmpdir.mkdir("sub")
    foo_yaml = tmpdir.join("foo.yaml")
    foo_yaml.write("")

    dep = yasha.find_dependencies("sub/foo.c.jinja", start=cwd)
    assert dep == "foo.yaml"


def test_dependencies_arent_find_below_cwd(tmpdir):
    foo_yaml = tmpdir.join("foo.yaml")
    foo_yaml.write("")

    sub = tmpdir.mkdir("sub")
    sub.chdir()

    dep = yasha.find_dependencies("foo.c.jinja")
    assert dep == None
