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

from os import path, chdir
import subprocess
from subprocess import call, check_output
from textwrap import dedent

import pytest
from yasha.cli import cli
from click.testing import CliRunner

def wrap(text):
    return dedent(text).lstrip()


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


@pytest.fixture(params=('json', 'yaml', 'yml', 'toml', 'ini', 'csv', 'csv_with_header'))
def testdata(request):
    templates = dict(
        default=wrap("""
            {% for item in list_data %}
            "{{ item.key1 }}"=>{{ item.key2 }}
            {% endfor %}
            {{ a_variable }}
            {{ a.nested.variable }}"""),
        # Ini files don't support the kinds of arbitrarily nested data structures found in the default template,
        # so they can only be tested with a template which uses data structured in ini-format (ie a dict (the ini file)
        # of dicts(the sections of the ini file) of keys (whose values can be None or strings)
        ini=wrap("""
            Section One, variable one: {{ section_one.variable_one }}
            {{ section_two.key }}"""),
        # CSV files don't support the kinds of arbitrarily nested data structures found in the default template,
        # so they can only be tested with a template which uses data structured in csv-format
        # ie. a list of dicts if the csv file has a header row, a list of lists if it doesn't
        csv=wrap("""
            {% for row in data %}
            cell 1 is {{ row[0] }}, cell 2 is {{ row[1] }}
            {% endfor %}"""),
        csv_with_header=wrap("""
            {% for row in data %}
            cell 1 is {{ row.first_column }}, cell 2 is {{ row['second column'] }}
            {% endfor %}""")
    )
    output = dict(
        default=wrap("""
            "some value"=>key2 value
            "another value"=>another key2 value
            a variable value
            a nested value"""),
        ini=wrap("""
            Section One, variable one: S1 V1 value
            S2 key value"""),
        csv=wrap("""
            cell 1 is value1, cell 2 is 2
            cell 1 is value3, cell 2 is 4
            cell 1 is value5, cell 2 is 6
            cell 1 is value7, cell 2 is 8
            cell 1 is value9, cell 2 is 10
            """)
    )
    data = dict(
        # Each entry is a list of strings [template, expected_output, data, extension]
        json=[
            templates['default'],
            output['default'],
            wrap("""
                {
                    "list_data": [
                        {
                            "key1": "some value",
                            "key2": "key2 value"
                        },
                        {
                            "key1": "another value",
                            "key2": "another key2 value"
                        }
                    ],
                    "a_variable": "a variable value",
                    "a": {
                        "nested": {
                            "variable": "a nested value"
                        }
                    }
                }"""),
            'json'
        ],
        yaml=[
            templates['default'],
            output['default'],
            wrap("""
                list_data:
                  - key1: some value
                    key2: key2 value
                  - key1: another value
                    key2: another key2 value
                a_variable: a variable value
                a:
                  nested:
                    variable: a nested value
                """),
            'yaml'
        ],
        toml=[
            templates['default'],
            output['default'],
            wrap("""
                a_variable = "a variable value"
                [[list_data]]
                key1 = "some value"
                key2 = "key2 value"
                [[list_data]]
                key1 = "another value"
                key2 = "another key2 value"
                [a.nested]
                variable = "a nested value"
                """),
            'toml'
        ],
        ini=[
            templates['ini'],
            output['ini'],
            wrap("""
                [section_one]
                variable_one = S1 V1 value
                [section_two]
                key = S2 key value
                """),
            'ini'
        ],
        csv=[
            templates['csv'],
            output['csv'],
            wrap("""
                value1,2
                value3,4
                value5,6
                value7,8
                value9,10"""),
            'csv'
        ],
        csv_with_header=[
            templates['csv_with_header'],
            output['csv'],
            wrap("""
                first_column,second column
                value1,2
                value3,4
                value5,6
                value7,8
                value9,10"""),
            'csv'
        ]
    )
    data['yml'] = data['yaml']
    data['yml'][3] = 'yml'
    fmt = request.param
    return data[fmt]


def test_explicit_variable_file(tmpdir, testdata):
    template, expected_output, data, extension = testdata
    tpl = tmpdir.join('template.j2')
    tpl.write(template)
    datafile = tmpdir.join('data.{}'.format(extension))
    datafile.write(data)

    runner = CliRunner()
    result = runner.invoke(cli, ['-v', str(datafile), str(tpl)])
    assert result.exit_code == 0

    output = tmpdir.join('template')
    assert output.read() == expected_output


def test_two_explicitly_given_variables_files(tmpdir):
    # Template to calculate a + b + c:
    tpl = tmpdir.join('template.j2')
    tpl.write('{{ a + b + c }}')

    # First variable file defines a & b:
    a = tmpdir.join('a.yaml')
    a.write('a: 1\nb: 100')

    # Second variable file redefines b & defines c:
    b = tmpdir.join('b.toml')
    b.write('b = 2\nc = 3')

    runner = CliRunner()
    result = runner.invoke(cli, ['-v', str(a), '-v', str(b), str(tpl)])
    assert result.exit_code == 0

    output = tmpdir.join('template')
    assert output.read() == '6'  # a + b + c = 1 + 2 + 3 = 6


def test_variable_file_lookup(tmpdir, vartpl):
    # /cwd
    #   /sub
    #     foo.c.j2
    cwd = tmpdir.chdir()
    tpl = tmpdir.mkdir('sub').join('foo.c.j2')
    tpl.write('int x = {{ int }};')

    # /cwd
    #   /sub
    #     foo.c.j2
    #     foo.c.json    int = 2
    #     foo.json      int = 1
    #   foo.json        int = 0
    for i, varfile in enumerate(('foo', 'sub/foo', 'sub/foo.c')):
        varfile += '.' + vartpl[1]
        varfile = tmpdir.join(varfile)
        varfile.write(vartpl[0].format(int=i))

        runner = CliRunner()
        result = runner.invoke(cli, ['sub/foo.c.j2'])
        assert result.exit_code == 0
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
def parse_xml(file):
    import xml.etree.ElementTree as et
    tree = et.parse(file.name)
    root = tree.getroot()
    variables = {"persons": []}
    for elem in root.iter("person"):
        variables["persons"].append({
            "name": elem.find("name").text,
            "address": elem.find("address").text,
        })
    return variables
    """

    cwd = tmpdir.chdir()

    file = tmpdir.join("foo.xml")
    file.write(variables)

    file = tmpdir.join("foo.toml.jinja")
    file.write(template)

    file = tmpdir.join("foo.j2ext")
    file.write(extensions)

    runner = CliRunner()
    result = runner.invoke(cli, ['foo.toml.jinja'])
    assert result.exit_code == 0
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

    runner = CliRunner()
    result = runner.invoke(cli, ['foo.jinja'])
    assert result.exit_code == 1
    assert result.exception
    assert "Invalid syntax (foo.j2ext, line 1)" in result.stdout


def test_broken_extensions_name_error(tmpdir):
    from subprocess import CalledProcessError, STDOUT
    tmpdir.chdir()

    extensions = "asd"

    tpl = tmpdir.join("foo.jinja")
    tpl.write("")

    ext = tmpdir.join("foo.j2ext")
    ext.write(extensions)

    runner = CliRunner()
    result = runner.invoke(cli, ['foo.jinja'])
    assert result.exit_code == 1
    assert result.exception
    assert "name 'asd' is not defined" in result.stdout


def test_render_template_from_stdin_to_stdout():
    cmd = r'yasha --foo=bar -'
    out = check_output(cmd, shell=True, input=b"{{ foo }}")
    assert out == b'bar'


def test_json_template(tmpdir):
    """gh-34, and gh-35"""
    tmpdir.chdir()

    tmpl = tmpdir.join('template.json')
    tmpl.write('{"foo": {{\'"%s"\'|format(bar)}}}')

    out = check_output(('yasha', '--bar=baz', '-o-', 'template.json'))
    assert out == b'{"foo": "baz"}'


def test_mode_is_none():
    """gh-42, and gh-44"""
    cmd = r'yasha -'
    out = check_output(cmd, shell=True, input=b"{{ foo }}")
    assert out == b''


def test_mode_is_pedantic():
    """gh-42, and gh-48"""
    with pytest.raises(subprocess.CalledProcessError) as err:
        cmd = r'yasha --mode=pedantic -'
        out = check_output(cmd, shell=True, stderr=subprocess.STDOUT, input=b"{{ foo }}")
    out = err.value.output
    assert out == b"Error: Variable 'foo' is undefined\n"


def test_mode_is_debug():
    """gh-44"""
    cmd = r'yasha --mode=debug -'
    out = check_output(cmd, shell=True, input=b"{{ foo }}")
    assert out == b'{{ foo }}'


def test_template_syntax_for_latex(tmpdir):
    """gh-43"""
    template = r"""
\begin{itemize}
<% for x in range(0, 3) %>
    \item Counting: << x >>
<% endfor %>
\end{itemize}
"""

    extensions = r"""
BLOCK_START_STRING = '<%'
BLOCK_END_STRING = '%>'
VARIABLE_START_STRING = '<<'
VARIABLE_END_STRING = '>>'
COMMENT_START_STRING = '<#'
COMMENT_END_STRING = '#>'
"""

    expected_output = r"""
\begin{itemize}
    \item Counting: 0
    \item Counting: 1
    \item Counting: 2
\end{itemize}
"""

    tpl = tmpdir.join('template.tex')
    tpl.write(template)

    ext = tmpdir.join('extensions.py')
    ext.write(extensions)

    out = check_output(('yasha', '-e', str(ext), '-o-', str(tpl)))
    assert out.decode() == expected_output


def test_extensions_file_with_do(tmpdir):
    """gh-52"""
    tmpdir.chdir()

    extensions = tmpdir.join('extensions.py')
    extensions.write('from jinja2.ext import do')

    tmpl = tmpdir.join('template.j2')
    tmpl.write(r'{% set list = [1, 2, 3] %}{% do list.append(4) %}{{ list }}')

    out = check_output(('yasha', '-e', str(extensions), '-o-', str(tmpl)))
    assert out == b'[1, 2, 3, 4]'
