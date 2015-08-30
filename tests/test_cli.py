"""
The MIT License (MIT)

Copyright (c) 2015 Kim Blomqvist

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
import subprocess
from os import path, chdir

SCRIPT_PATH = path.dirname(path.realpath(__file__))

@pytest.fixture(params=["foo.c.jinja", "sub/foo.c.jinja"])
def template(request, tmpdir):
	""" Returns template. The current working directory (cwd)
	is changed to the root of the template."""
	cwd = tmpdir.chdir()
	subdir = request.param.rsplit("/", 1)
	if len(subdir) > 1:
		p = tmpdir.mkdir(subdir[0]).join(subdir[1])
	else:
		p = tmpdir.join(subdir[0])
	return p, request.param

def test_empty_template(template):
	t, t_name = template
	t.write("")

	errno = subprocess.call(["yasha", t_name])
	assert errno == 0
	assert path.isfile(t_name.replace(".jinja", ""))

def test_makefile_for_c():
	chdir(SCRIPT_PATH)
	chdir("makefile_for_c")

	# Initial build
	subprocess.call(["make"])
	out = subprocess.check_output("./program")
	assert out == b"foo has 3 chars ...\n"

	# Test Make dependencies
	for touch in ["foo.toml", "foo.h.jinja", "foo.c.jinja"]:
		subprocess.call(["touch", touch])
		out = subprocess.check_output(["make"])
		assert not b"is up to date" in out

	# Remember to clean the build
	subprocess.call(["make", "clean"])
