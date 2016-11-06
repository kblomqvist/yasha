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


def filter_access(access):
    return {
        "read-only": "ro",
        "write-only": "wo",
        "writeOnce": "wo",
        "read-write": "rw",
        "read-writeOnce": "rw",
    }[access]


def filter_bitrange(bitrange):
    msb, lsb = bitrange[1:-1].split(":")
    if msb == lsb:
        return "{}".format(lsb)
    else:
        return "{}..{}".format(lsb, msb)


def filter_enumlist(lst):
    values = []
    if lst["read-write"]:
        values = lst["read-write"]
    elif lst["read"]:
        values = lst["read"]
    elif lst["write"]:
        values = lst["write"]
    return sorted(values, key=lambda x: x.value)


def filter_enumvalue(value):
    if value < 256:
        return value
    return "{:#x}".format(value)
