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

import distutils
from xml.etree import ElementTree
from . import parser


class SvdParser(parser.Parser):
    """Yasha parser for CMSIS-SVD files"""
    file_extension = [".svd"]

    def parse(self, file):
        svd = SvdFile(file)
        svd.parse()

        variables = {
            "cpu": svd.cpu,
            "device": svd.device,
            "peripherals": svd.peripherals,
        }
        return variables


class SvdFile():
    """SVD File: Entry class to parse CMSIS-SVD file

    SVD = System View Description format
    CMSIS = Cortex Microcontroller Software Interface Standard
    Read more from http://www.keil.com/pack/doc/CMSIS/SVD/html/
    """

    def __init__(self, file):
        if isinstance(file, str):
            self.root = ElementTree.fromstring(file)
        else:
            tree = ElementTree.parse(file)
            self.root = tree.getroot()

        self.cpu = None
        self.device = None
        self.peripherals = []
        self.peripherals_dict = {}  # Lookup by peripheral name

    def parse(self):
        self.cpu = SvdCpu(self.root.find("cpu"))
        self.device = SvdDevice(self.root)

        derived_periphs = []
        for elem in self.root.iter("peripheral"):
            periph = SvdPeripheral(elem, self.device)
            if periph.derivedFrom is not None:
                derived_periphs.append(periph.name)
            self.peripherals.append(periph)
            self.peripherals_dict[periph.name] = periph

        for periph in [self.peripherals_dict[name] for name in derived_periphs]:
            base = self.peripherals_dict[periph.derivedFrom]
            periph.inherit_from(base)


class SvdElement(object):
    props = []
    props_to_integer = []
    props_to_boolean = []

    def __init__(self, element=None, defaults={}, parent=None):
        if element is not None:
            self.from_element(element, defaults)
        if parent is not None:
            self.parent = parent

    def from_element(self, element, defaults={}):
        """Populate object variables from SVD element"""
        if isinstance(defaults, SvdElement):
            defaults = vars(defaults)
        for key in self.props:
            try:
                value = element.find(key).text
            except AttributeError:  # Maybe it's attribute?
                default = defaults[key] if key in defaults else None
                value = element.get(key, default)
            if value is not None:
                if key in self.props_to_integer:
                    try:
                        value = int(value)
                    except ValueError:  # It has to be hex
                        value = int(value, 16)
                elif key in self.props_to_boolean:
                    value = distutils.util.strtobool(value)

            setattr(self, key, value)

    def inherit_from(self, element):
        for key, value in vars(self).items():
            if not value and key in vars(element):
                value = getattr(element, key)
                setattr(self, key, value)

    def copy(self):
        import copy
        return copy.copy(self)

    def __str__(self):
        from pprint import pformat
        return pformat(vars(self), indent=0)


class SvdDevice(SvdElement):
    """SVD Devices element"""
    props = [
        "schemaVersion", "vendor", "vendorID", "name", "series", "version",
        "description", "licenseText", "headerSystemFilename",
        "headerDefinitionsPrefix", "addressUnitBits", "width", "size",
        "access", "protection", "resetValue", "resetMask"
    ]
    props_to_integer = [
        "width", "size", "resetValue", "resetMask", "addressUnitBits"
    ]


class SvdCpu(SvdElement):
    """SVD CPU section"""
    props = [
        "name", "revision", "endian", "mpuPresent", "fpuPresent", "fpuDP",
        "icachePresent", "dcachePresent", "itcmPresent", "dtcmPresent",
        "vtorPresent", "nvicPrioBits", "vendorSystickConfig",
        "deviceNumInterrupts"
    ]
    props_to_boolean = [
        "mpuPresent", "fpuPresent", "fpuDP", "icachePresent", "dcachePresent",
        "itcmPresent", "dtcmPresent", "vtorPresent"
    ]

class SvdPeripheral(SvdElement):
    """SVD Peripherals Level

    A peripheral is a named collection of registers. A peripheral is mapped
    to a defined base address within the device's address space. A peripheral
    allocates one or more exclusive address blocks relative to its base
    address, such that all described registers fit into the allocated address
    blocks. Allocated addresses without an associated register description
    are automatically considered reserved. The peripheral can be assigned to
    a group of peripherals and may be associated with one or more interrupts.
    """
    props = [
        "derivedFrom", "dim", "dimIncrement", "dimIndex", "dimName", "name",
        "version", "description", "alternatePeripheral", "groupName",
        "appendToName", "headerStructName", "disableCondition", "baseAddress",
        "size", "access", "protection", "resetValue", "resetMask"
    ]
    props_to_integer = [
        "dim", "dimIncrement", "baseAddress", "size", "resetValue",
        "resetMask"
    ]

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)
        self.registers = []
        self.interrupts = []
        self.addressBlock = None

        try:
            for reg in element.find("registers"):
                if reg.tag == "cluster":
                    self.registers.append(Cluster(reg, self, parent=self))
                elif reg.tag == "register":
                    reg = SvdRegister(reg, self, parent=self)
                    self.registers.extend(reg.fold())
        except TypeError:  # element.findall() may return None
            pass

        try:
            for i in element.findall("interrupt"):
                self.interrupts.append(SvdInterrupt(i, parent=self))
        except TypeError:  # element.findall() may return None
            pass

        try:
            block = element.find("addressBlock")
            self.addressBlock = SvdAddressBlock(block, parent=self)
        except TypeError:
            pass


class SvdRegister(SvdElement):
    """SVD Registers Level

    A register is a named, programmable resource that belongs to a
    peripheral. Registers are mapped to a defined address in the address
    space of the device. An address is specified relative to the peripheral
    base address. The description of a register documents the purpose and
    function of the resource. A debugger requires information about the
    permitted access to a resource as well as side effects triggered by
    read and write accesses respectively.
    """
    props = [
        "derivedFrom", "dim", "dimIncrement", "dimIndex", "dimName",
        "name", "displayName", "description", "alternateGroup",
        "alternateRegister", "addressOffset", "size", "access", "protection",
        "resetValue", "resetMask", "dataType", "modifiedWriteValues",
        "readAction"
    ]
    props_to_integer = [
        "dim", "dimIncrement", "addressOffset", "size", "resetValue",
        "resetMask"
    ]

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)
        self.fields = []

        if self.dim is not None:
            try:
                self.dimIndex = int(self.dimIndex)
            except ValueError:
                try:
                    start, stop = self.dimIndex.split("-")
                    start, stop = (int(start), int(stop)+1)
                    self.dimIndex = list(range(start, stop))
                except ValueError:
                    self.dimIndex = self.dimIndex.split(",")

        try:
            for elem in element.find("fields"):
                field = SvdField(elem, self, parent=self)
                self.fields.append(field)
        except TypeError:  # element.findall() may return None
            pass

        try:
            elem = element.find("writeConstraint")
            self.writeConstraint = SvdWriteConstraint(elem, parent=self)
        except TypeError:
            pass


    def fold(self):
        """Folds the Register in accordance with it's dimensions.

        If the register is dimensionless, the returned list just
        contains the register itself unchanged. In case the register
        name looks like a C array, the returned list contains the register
        itself, where nothing else than the '%s' placeholder in it's name
        has been replaced with value of the dim element.
        """
        if self.dim is None:
            return [self]
        if self.name.endswith("[%s]"):  # C array like
            self.name = self.name.replace("%s", str(self.dim))
            return [self]

        registers = []
        for offset, index in enumerate(self.dimIndex):
            reg = self.copy()
            reg.name = self.name.replace("%s", str(index))
            reg.addressOffset += offset * reg.dimIncrement

            reg.fields = [field.copy() for field in reg.fields]
            for field in reg.fields:
                field.parent = reg

            reg.dim = reg.dimIndex = reg.dimIncrement = None  # Dimensionless
            registers.append(reg)

        return registers


class Cluster(SvdElement):
    """SVD Cluster extension level

    Cluster adds an optional sub-level within the CMSIS SVD registers level.
    A cluster describes a sequence of neighboring registers within
    a peripheral.
    """
    props = [
        "registers", "derivedFrom", "dim", "dimIncrement", "dimIndex", "name",
        "description", "alternateCluster", "headerStructName", "addressOffset"
    ]
    props_to_integer = ["addressOffset", "dim", "dimIncrement"]

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, {})
        self.registers = []

        # TODO: Should work like Register.to_array(), if there's self.dim
        self.name = self.name.replace("%s", str(self.dim))

        try:
            for elem in element.findall("*"):
                if elem.tag == "cluster":  # Cluster may include yet another cluster
                    self.registers.append(Cluster(elem, defaults, parent=self))
                elif elem.tag == "register":
                    reg = SvdRegister(elem, defaults, parent=self)
                    self.registers.extend(reg.fold())
        except TypeError:  # element.findall() may return None
            pass


class SvdField(SvdElement):
    """SVD Fields level

    All fields of a register are enclosed between the <fields>
    opening and closing tags.
    """
    props = [
        "derivedFrom", "name", "description", "bitOffset", "bitWidth",
        "lsb", "msb", "bitRange", "access", "modifiedWriteValues",
        "readAction"
    ]
    props_to_integer = ["bitOffset", "bitWidth", "lsb", "msb"]

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)
        self.enumeratedValues = {
            "read": [],
            "write": [],
            "read-write": [],
        }

        if self.bitRange is not None:
            self.msb, self.lsb = self.bitRange[1:-1].split(":")
            self.msb = int(self.msb)
            self.lsb = int(self.lsb)
            self.bitOffset = self.lsb
            self.bitWidth = self.msb - self.lsb + 1
        elif self.bitOffset is not None and self.bitWidth is not None:
            self.lsb = self.bitOffset
            self.msb = self.bitWidth + self.lsb
        self.bitRange = (self.msb, self.lsb)

        try:
            for e in element.findall("enumeratedValues"):
                try:
                    usage = e.find("usage").text
                except AttributeError:
                    usage = "read-write"
                for e in e.findall("enumeratedValue"):
                    enum = SvdEnumeratedValue(e, {}, parent=self)
                    self.enumeratedValues[usage].append(enum)
        except TypeError:  # element.findall() may return None
            pass

        try:
            elem = element.find("writeConstraint")
            self.writeConstraint = SvdWriteConstraint(elem, parent=self)
        except TypeError:
            pass


class SvdEnumeratedValue(SvdElement):
    """SVD Enumerated values Level

    The concept of enumerated values creates a map between unsigned
    integers and an identifier string.
    """
    props = ["derivedFrom", "name", "description", "value", "isDefault"]
    props_to_integer = ["value"]


class SvdInterrupt(SvdElement):
    props = ["name", "description", "value"]
    props_to_integer = ["value"]


class SvdAddressBlock(SvdElement):
    props = ["addressBlock", "offset", "size", "usage", "protection"]
    props_to_integer = ["offset", "size"]


class SvdWriteConstraint(SvdElement):
    props = ["writeAsRead", "useEnumeratedValues"]
    props_to_boolean = ["writeAsRead", "useEnumeratedValues"]

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)
        try:
            elem = element.find("range")
            minimum = elem.find("minimum").text
            maximum = elem.find("maximum").text
            self.range = (int(minimum), int(maximum))
        except:  # No range
            pass
