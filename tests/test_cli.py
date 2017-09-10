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
from os import path, chdir
from subprocess import call, check_output

@pytest.fixture(params=('json', 'yaml', 'yml', 'toml'))
def vartpl(request):
    template = {
        'json': '{{"int": {int}}}',
        'yaml': 'int: {int}',
        'yml': 'int: {int}',
        'toml': 'int={int}',
    }
    fmt = request.param  # format
    return (template[fmt], fmt)


@pytest.fixture
def varfile(vartpl, tmpdir):
    content = {'int': 1}
    template, filext = vartpl
    file = tmpdir.join('variables.{}'.format(filext))
    file.write(template.format(**content))
    return file


def test_explicit_variable_file(tmpdir, varfile):
    tpl = tmpdir.join('template.j2')
    tpl.write('{{ int }}')

    errno = call(('yasha', '-v', str(varfile), str(tpl)))
    assert errno == 0

    output = tmpdir.join('template')
    assert output.read() == '1'


def test_variable_file_lookup(tmpdir, vartpl):
    # cwd/
    #   sub/
    #     foo.c.j2
    cwd = tmpdir.chdir()
    tpl = tmpdir.mkdir('sub').join('foo.c.j2')
    tpl.write('int x = {{ int }};')

    # /cwd
    #   sub/
    #     foo.c.j2
    #     foo.c.json    int = 2
    #     foo.json      int = 1
    #   foo.json        int = 0
    for i, varfile in enumerate(('foo', 'sub/foo', 'sub/foo.c')):
        varfile += '.' + vartpl[1]
        varfile = tmpdir.join(varfile)
        varfile.write(vartpl[0].format(int=i))

        errno = call(('yasha', 'sub/foo.c.j2'))
        assert errno == 0
        assert path.isfile('sub/foo.c')

        output = tmpdir.join('sub/foo.c')
        assert output.read() == 'int x = {};'.format(i)


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
