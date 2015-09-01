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

@pytest.fixture(params=["toml", "yaml"])
def tmplvar(request):
	if request.param == "toml":
		return {"filext": ".toml", "content": "number={}"}
	if request.param == "yaml":
		return {"filext": ".yaml", "content": "number: {}"}

def test_template_in_subdir(tmpdir, tmplvar):
	""" This test contains several steps to test that the variables file
	    is correctly found when the template is placed in sub directory:

	    Step 1:
	        sub/
	          foo.c.jinja
	        foo.toml        <-- should be used

	    Step 2:
	        sub/
	          foo.c.jinja
	          foo.toml      <-- should be used
	        foo.toml 

	    Step 3:
	        sub/
	          foo.c.jinja
	          foo.c.toml    <-- should be used
	          foo.toml      
	        foo.toml

	    Step 4:
	        sub/
	          foo.c.jinja
	          foo.c.toml    
	          foo.toml      <-- explicitly specified
	        foo.toml      

	    Step 5:
	        sub/
	          foo.c.jinja
	          foo.c.toml    
	          foo.toml      
	        foo.toml        <-- explicitly specified
	"""

	cwd = tmpdir.chdir()

	varfile = [v + tmplvar["filext"] for v in
		["foo", "sub/foo", "sub/foo.c"]]

	t = tmpdir.mkdir("sub").join("foo.c.jinja")
	t.write("int x = {{ number }};")

	v0 = tmpdir.join(varfile[0])
	v0.write(tmplvar["content"].format(0))

	errno = subprocess.call(["yasha", "sub/foo.c.jinja"])
	assert errno == 0
	assert path.isfile("sub/foo.c")

	o = tmpdir.join("sub/foo.c")
	assert o.read() == "int x = 0;"

	v1 = tmpdir.join(varfile[1])
	v1.write(tmplvar["content"].format(1))

	subprocess.call(["yasha", "sub/foo.c.jinja"])
	assert o.read() == "int x = 1;"

	v2 = tmpdir.join(varfile[2])
	v2.write(tmplvar["content"].format(2))

	subprocess.call(["yasha", "sub/foo.c.jinja"])
	assert o.read() == "int x = 2;"

	subprocess.call(["yasha", "sub/foo.c.jinja", "--variables", varfile[1]])
	assert o.read() == "int x = 1;"

	subprocess.call(["yasha", "sub/foo.c.jinja", "--variables", varfile[0]])
	assert o.read() == "int x = 0;"

def test_custom_xmlparser(tmpdir):
	cwd = tmpdir.chdir()

	t = tmpdir.join("foo.toml.jinja")
	t.write("""{% for p in persons -%}
	[[persons]]
	name = "{{ p.name }}"
	address = "{{ p.address }}"
	{% endfor -%}
	""")

	vars = tmpdir.join("foo.xml")
	vars.write("""<persons>
	<person>
		<name>Foo</name>"
		<address>Foo Valley</address>
	</person>
	<person>
		<name>Bar</name>
		<address>Bar Valley</address>
	</person>
	</persons>
	""")

	j2ext = tmpdir.join("foo.jinja-ext")
	j2ext.write("""from yasha.parsers import Parser
class XmlParser(Parser):
	file_extension = [".xml"]

	def parse(self, file):
		import xml.etree.ElementTree as et
		tree = et.parse(file.name)
		root = tree.getroot()
		vars = {"persons": []}
		for elem in root.iter("person"):
			vars["persons"].append({
				"name": elem.find("name").text,
				"address": elem.find("address").text,
		})
		return vars
	""")

	errno = subprocess.call(["yasha", "foo.toml.jinja"])
	assert errno == 0
	assert path.isfile("foo.toml")

	o = tmpdir.join("foo.toml")
	print(o.read())
	assert o.read() == """[[persons]]
	name = "Foo"
	address = "Foo Valley"
	[[persons]]
	name = "Bar"
	address = "Bar Valley"
	"""

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
