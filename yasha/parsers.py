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

from .yasha import ENCODING

def parse_json(file):
    import json
    assert file.name.endswith('.json')
    variables = json.loads(file.read().decode(ENCODING))
    return variables if variables else dict()

def parse_yaml(file):
    import yaml
    assert file.name.endswith(('.yaml', '.yml'))
    variables = yaml.safe_load(file)
    return variables if variables else dict()

def parse_toml(file):
    import pytoml as toml
    assert file.name.endswith('.toml')
    variables = toml.load(file)
    return variables if variables else dict()

def parse_xml(file):
    import xmltodict
    assert file.name.endswith('.xml')
    variables = xmltodict.parse(file.read().decode(ENCODING))
    return variables if variables else dict()

def parse_ini(inifile):
    import configparser
    cnf = configparser.ConfigParser()
    cnf.read(inifile)
    return cnf

def parse_svd(file):
    # TODO: To be moved into its own repo
    from .cmsis import SVDFile
    svd = SVDFile(file)
    svd.parse()
    return {
        "cpu": svd.cpu,
        "device": svd.device,
        "peripherals": svd.peripherals,
    }

PARSERS = {
    '.json': parse_json,
    '.yaml': parse_yaml,
    '.yml': parse_yaml,
    '.toml': parse_toml,
    '.xml': parse_xml,
    '.ini': parse_ini,
    '.svd': parse_svd,
}
