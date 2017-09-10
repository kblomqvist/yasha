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

from yasha.parsers import svd
import xml.etree.ElementTree as et

from os import path
from subprocess import call, check_output


def test_peripheral_element():
    periph = svd.SvdPeripheral(et.fromstring(
        """
        <peripheral>
            <name>TIMER0</name>
            <version>1.0</version>
            <description>A standard timer</description>
            <baseAddress>0x40002000</baseAddress>
            <addressBlock>
                <offset>0x0</offset>
                <size>0x400</size>
                <usage>registers</usage>
                <protection>s</protection>
            </addressBlock>
            <interrupt>
                <name>TIM0_INT</name>
                <value>34</value>
            </interrupt>
        </peripheral>
        """
    ))

    assert len(periph.interrupts) == 1
    assert periph.name == "TIMER0"
    assert periph.version == "1.0"
    assert periph.description == "A standard timer"
    assert periph.baseAddress == 1073750016
    assert periph.addressBlock.offset == 0
    assert periph.addressBlock.size == 1024
    assert periph.addressBlock.usage == "registers"
    assert periph.addressBlock.protection == "s"


def test_peripheral_interrupt_inheritance():
    timer0 = svd.SvdPeripheral(et.fromstring(
        """
        <peripheral>
            <name>TIMER0</name>
            <baseAddress>0x40000</baseAddress>
            <interrupt>
                <name>TIMER0_INT</name>
                <value>42</value>
            </interrupt>
        </peripheral>
        """
    ))
    timer1 = svd.SvdPeripheral(et.fromstring(
        """
        <peripheral derivedFrom="TIMER0">
            <name>TIMER1</name>
            <baseAddress>0x40400</baseAddress>
            <interrupt>
                <name>TIMER1_INT</name>
                <value>43</value>
            </interrupt>
        </peripheral>
        """
    ))
    timer1.inherit_from(timer0)

    assert len(timer1.interrupts) == 1
    assert timer1.interrupts[0].name == "TIMER1_INT"
    assert timer1.interrupts[0].value == 43

    timer1 = svd.SvdPeripheral(et.fromstring(
        """
        <peripheral derivedFrom="TIMER0">
            <name>TIMER1</name>
            <baseAddress>0x40400</baseAddress>
        </peripheral>
        """
    ))
    timer1.inherit_from(timer0)

    assert len(timer1.interrupts) == 1
    assert timer1.interrupts[0].name == "TIMER0_INT"
    assert timer1.interrupts[0].value == 42


def test_register_element():
    reg = svd.SvdRegister(et.fromstring(
        """
        <register>
            <name>TimerCtrl0</name>
            <description>Timer Control Register</description>
            <addressOffset>0x0</addressOffset>
            <access>read-write</access>
            <resetValue>0x00008001</resetValue>
            <resetMask>0x0000ffff</resetMask>
            <size>32</size>
            <writeConstraint>
                <writeAsRead>true</writeAsRead>
                <useEnumeratedValues>true</useEnumeratedValues>
                <range>
                    <minimum>0</minimum>
                    <maximum>5</maximum>
                </range>
            </writeConstraint>
        </register>
        """
    ))
    assert reg.name == "TimerCtrl0"
    assert reg.description == "Timer Control Register"
    assert reg.addressOffset == 0
    assert reg.access == "read-write"
    assert reg.resetValue == 0x8001
    assert reg.resetMask == 0xffff
    assert reg.size == 32
    assert reg.writeConstraint.writeAsRead == True
    assert reg.writeConstraint.useEnumeratedValues == True
    assert reg.writeConstraint.range == (0,5)


def test_register_folding_commaseparated_index():
    r = svd.SvdRegister(et.fromstring(
        """
        <register>
            <dim>3</dim>
            <dimIncrement>4</dimIncrement>
            <dimIndex>A,B,C</dimIndex>
            <name>GPIO_%s</name>
            <addressOffset>4</addressOffset>
        </register>
        """
    ))
    a = r.fold()

    assert len(a) == 3
    assert a[0].name == "GPIO_A"
    assert a[1].name == "GPIO_B"
    assert a[2].name == "GPIO_C"


def test_register_folding_integerrange_index():
    r = svd.SvdRegister(et.fromstring(
        """
        <register>
            <dim>4</dim>
            <dimIncrement>4</dimIncrement>
            <dimIndex>3-6</dimIndex>
            <name>IRQ%s</name>
            <addressOffset>4</addressOffset>
        </register>
        """
    ))
    a = r.fold()

    assert len(a) == 4
    assert a[0].name == "IRQ3"
    assert a[1].name == "IRQ4"
    assert a[2].name == "IRQ5"
    assert a[3].name == "IRQ6"

    for i in range(4):
        assert a[i].addressOffset == 4 + (i * 4)


def test_register_is_dimensionless_after_fold_up():
    r = svd.SvdRegister(et.fromstring(
        """
        <register>
            <dim>4</dim>
            <dimIncrement>4</dimIncrement>
            <dimIndex>3-6</dimIndex>
            <name>IRQ%s</name>
            <addressOffset>4</addressOffset>
        </register>
        """
    ))
    for r in r.fold():
        assert r.dim == None
        assert r.dimIndex == None
        assert r.dimIncrement == None


def test_field_element():
    field = svd.SvdField(et.fromstring(
        """
        <field>
            <name>TIMER0</name>
            <description>This is TIMER0.</description>
            <bitOffset>1</bitOffset>
            <bitWidth>3</bitWidth>
            <access>read-write</access>
            <modifiedWriteValues>oneToSet</modifiedWriteValues>
            <writeConstraint>
                <range>
                    <minimum>0</minimum>
                    <maximum>5</maximum>
                </range>
            </writeConstraint>
            <readAction>clear</readAction>
        </field>
        """
    ))
    assert field.name == "TIMER0"
    assert field.description == "This is TIMER0."
    assert field.bitOffset == 1
    assert field.bitWidth == 3
    assert field.access == "read-write"
    assert field.modifiedWriteValues == "oneToSet"
    assert field.writeConstraint.range == (0,5)
    assert field.readAction == "clear"

    # These are generated from bitOffset and bitWidth
    assert field.lsb == 1
    assert field.msb == 4
    assert field.bitRange == (4,1)

    field = svd.SvdField(et.fromstring(
        """
        <field>
            <bitRange>[7:0]</bitRange>
        </field>
        """
    ))
    assert field.bitRange == (7,0)

    # These are generated from bitRange
    assert field.lsb == 0
    assert field.msb == 7
    assert field.bitOffset == 0
    assert field.bitWidth == 8

def test_svdfile():
    file = svd.SvdFile(
        """
        <device>
            <peripherals>
                <peripheral>
                    <name>TIMER0</name>
                </peripheral>
                <peripheral>
                    <name>TIMER1</name>
                </peripheral>
                <peripheral>
                    <name>TIMER2</name>
                </peripheral>
                <peripheral>
                    <name>TIMER3</name>
                </peripheral>
            </peripherals>
        </device>
        """
    )
    file.parse()

    assert len(file.peripherals) == 4
    for idx, periph in enumerate(file.peripherals):
        assert periph.name == "TIMER{}".format(idx)


def test_nrf51svd_to_rust(fixtures_dir):
    tpl = path.join(fixtures_dir, "nrf51.rs.jinja")
    ext = path.join(fixtures_dir, "nrf51.rs.py")
    var = path.join(fixtures_dir, "nrf51.svd")

    expected_output = path.join(fixtures_dir, "nrf51.rs.expected")
    with open(expected_output, "rb") as f:
        cmd = "cat {} | yasha -e {} -v {} -".format(tpl, ext, var)
        out = check_output(cmd, shell=True)
        assert out.strip() == f.read().strip()
