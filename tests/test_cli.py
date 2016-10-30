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
from os import path, chdir
from subprocess import call, check_output

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

    errno = call(["yasha", "sub/foo.c.jinja"])
    assert errno == 0
    assert path.isfile("sub/foo.c")

    o = tmpdir.join("sub/foo.c")
    assert o.read() == "int x = 0;"

    v1 = tmpdir.join(varfile[1])
    v1.write(tmplvar["content"].format(1))

    call(["yasha", "sub/foo.c.jinja"])
    assert o.read() == "int x = 1;"

    v2 = tmpdir.join(varfile[2])
    v2.write(tmplvar["content"].format(2))

    call(["yasha", "sub/foo.c.jinja"])
    assert o.read() == "int x = 2;"

    call(["yasha", "sub/foo.c.jinja", "--variables", varfile[1]])
    assert o.read() == "int x = 1;"

    call(["yasha", "sub/foo.c.jinja", "--variables", varfile[0]])
    assert o.read() == "int x = 0;"

def test_custom_xmlparser(tmpdir):
    template = """
    {% for p in persons %}
    [[persons]]
    name = "{{ p.name }}"
    address = "{{ p.address }}"
    {% endfor %}"""

    variables = """
    <persons>
        <person>
            <name>Foo</name>"
            <address>Foo Valley</address>
        </person>
        <person>
            <name>Bar</name>
            <address>Bar Valley</address>
        </person>
    </persons>
    """

    extensions = """
import yasha
class XmlParser(yasha.Parser):
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
    """

    cwd = tmpdir.chdir()

    file = tmpdir.join("foo.xml")
    file.write(variables)

    file = tmpdir.join("foo.toml.jinja")
    file.write(template)

    file = tmpdir.join("foo.j2ext")
    file.write(extensions)

    errno = call(["yasha", "foo.toml.jinja"])
    assert errno == 0
    assert path.isfile("foo.toml")

    o = tmpdir.join("foo.toml")
    assert o.read() == """
    [[persons]]
    name = "Foo"
    address = "Foo Valley"
    [[persons]]
    name = "Bar"
    address = "Bar Valley"\n"""

def test_broken_extensions(tmpdir):
    from subprocess import CalledProcessError, STDOUT
    tmpdir.chdir()

    extensions = """def foo()
    return "foo"
    """

    tpl = tmpdir.join("foo.jinja")
    tpl.write("")

    ext = tmpdir.join("foo.j2ext")
    ext.write(extensions)

    with pytest.raises(CalledProcessError) as e:
        cmd = ["yasha", "foo.jinja"]
        check_output(cmd, stderr=STDOUT)
    assert e.value.returncode == 1
    assert b"Invalid syntax (foo.j2ext, line 1)" in e.value.output

def test_stdin_and_out():
    cmd = ("echo -n \"foo\"", "|", "yasha", "-")
    out = check_output(cmd, shell=True)
    assert out == b"foo"

def test_stdin_and_out_with_extensions_and_variables(fixtures_dir):
    tpl = path.join(fixtures_dir, "nrf51.rs.jinja")
    ext = path.join(fixtures_dir, "nrf51.rs.py")
    var = path.join(fixtures_dir, "nrf51.svd")

    expected_output = path.join(fixtures_dir, "nrf51.rs.expected")
    with open(expected_output, "rb") as f:
        cmd = "cat {} | yasha -e {} -v {} -".format(tpl, ext, var)
        out = check_output(cmd, shell=True)
        assert out == f.read()
