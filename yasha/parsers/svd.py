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

import xml.etree.ElementTree as ET
from . import parser


class SvdParser(parser.Parser):
    """
    CMSIS System View Description format (CMSIS-SVD)
    http://www.keil.com/pack/doc/CMSIS/SVD/html/index.html
    """
    file_extension = [".svd"]

    def parse(self, file):
        f = SvdFile(file)
        f.parse()

        vars = {
            "cpu": f.cpu,
            "device": f.device,
            "peripherals": [f.peripherals[name] for name in f.peripherals_order],
        }
        return vars


class SvdFile():

    def __init__(self, file):
        if type(file) is str:
            self.root = ET.fromstring(file)
        else:
            tree = ET.parse(file)
            self.root = tree.getroot()

    def parse(self):
        self.cpu = Cpu(self.root.find("cpu"))
        self.device = Device(self.root)

        self.peripherals = {}
        self.peripherals_order = []
        self.derived_peripherals = []
        self.peripheral_groups = {}

        for e in self.root.iter("peripheral"):
            p = Peripheral(e, self.device)
            self.peripherals[p.name] = p
            self.peripherals_order.append(p.name)

            if p.derivedFrom:
                self.derived_peripherals.append(p.name)

            if p.groupName:
                try:
                    self.peripheral_groups[p.groupName].append(p.name)
                except:
                    self.peripheral_groups[p.groupName] = [p.name]

        for p in [self.peripherals[name] for name in self.derived_peripherals]:
            base = self.peripherals[p.derivedFrom]
            p.inherit_from(base)


class SvdElement(object):
    type = "svd_element"
    cast_to_integer = []

    def __init__(self, element=None, defaults={}, parent=None):
        self.init()
        if element is not None:
            self.from_element(element, defaults)
        if parent:
            self.parent = parent

    def __repr__(self):
        from pprint import pformat
        return pformat(self.to_dict())

    def init(self):
        """Define object variables within this method"""
        raise NotImplementedError("Please implement")

    def copy(self):
        import copy
        return copy.copy(self)

    def from_element(self, element, defaults={}):
        """Populate object variables from SVD element"""

        def to_mixed_case(snake_case):
            """Return snake_case formatted string in mixedCase"""
            tokens = snake_case.split("_")
            return tokens[0] + "".join(s[0].upper() + s[1:] for s in tokens[1:])

        try:
            defaults = vars(defaults)
        except:
            pass

        for key, value in vars(self).items():
            if isinstance(value, list) or isinstance(value, dict):
                continue
            try:
                value = element.find(to_mixed_case(key)).text
            except:  # Maybe it's attribute?
                default = defaults[key] if key in defaults else None
                value = element.get(to_mixed_case(key), default)

            if value and key in self.cast_to_integer:
                try:
                    value = int(value)
                except:  # It has to be hex
                    value = int(value, 16)

            setattr(self, key, value)

    def inherit_from(self, element):
        for key, value in vars(self).items():
            if not value and key in vars(element):
                value = getattr(element, key)
                setattr(self, key, value)

    def to_dict(self):
        d = {}
        for k in self.props:
            v = getattr(self, k)
            if type(v) == list:
                v = [i.to_dict() for i in v]
            d[k] = v
        return d


class Device(SvdElement):
    type = "device"
    cast_to_integer = ["size"]
    props = [
        "name", "version", "description", "addressUnitBits", "width", "size",
        "access", "resetValue", "resetMask", "vendor", "vendorID", "series",
        "licenseText", "headerSystemFilename", "headerDefinitionsPrefix"]

    def init(self):
        self.name = None
        self.version = None
        self.description = None
        self.addressUnitBits = None
        self.width = None
        self.size = None
        self.access = None
        self.resetValue = None
        self.resetMask = None
        self.vendor = None
        self.vendorID = None
        self.series = None
        self.licenseText = None
        self.headerSystemFilename = None
        self.headerDefinitionsPrefix = None


class Cpu(SvdElement):
    type = "cpu"
    props = [
        "name", "revision", "endian", "mpuPresent", "fpuPresent", "fpuDP",
        "icachePresent", "dcachePresent", "itcmPresent", "dtcmPresent",
        "vtorPresent", "nvicPrioBits", "vendorSystickConfig"]

    def init(self):
        self.name = None
        self.revision = None
        self.endian = None
        self.mpuPresent = None
        self.fpuPresent = None
        self.fpuDP = None
        self.icachePresent = None
        self.dcachePresent = None
        self.itcmPresent = None
        self.dtcmPresent = None
        self.vtorPresent = None
        self.nvicPrioBits = None
        self.vendorSystickConfig = None


class Peripheral(SvdElement):
    type = "peripheral"
    cast_to_integer = ["size", "baseAddress"]
    props = [
        "registers", "interrupts", "derivedFrom", "name", "version",
        "description", "groupName", "prependToName", "appendToName",
        "disableCondition", "baseAddress", "size", "access", "resetValue",
        "resetMask", "alternatePeripheral"]

    def init(self):
        self.registers = []
        self.interrupts = []
        self.derivedFrom = None
        self.name = None
        self.version = None
        self.description = None
        self.groupName = None
        self.prependToName = None
        self.appendToName = None
        self.disableCondition = None
        self.baseAddress = None
        self.size = None
        self.access = None
        self.resetValue = None
        self.resetMask = None
        self.alternatePeripheral = None

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)

        try:  # Because registers may be None
            for r in element.find("registers"):
                if r.tag == "cluster":
                    self.registers.append(Cluster(r, self, parent=self))
                elif r.tag == "register":
                    r = Register(r, self, parent=self)
                    self.registers.extend(r.to_array())
        except:
            pass

        try:  # Because interrupt may be None
            for i in element.findall("interrupt"):
                self.interrupts.append(Interrupt(i))
        except:
            pass


class Register(SvdElement):
    type = "register"
    cast_to_integer = ["size", "addressOffset", "dim",
                       "dimIncrement", "resetValue", "resetMask"]
    props = [
        "fields", "derivedFrom", "dim", "dimIncrement", "dimIndex", "name",
        "displayName", "description", "alternateGroup", "addressOffset", "size",
        "access", "resetValue", "resetMask", "modifiedWriteValues",
        "readAction", "alternateRegister", "dataType"]

    def init(self):
        self.fields = []
        self.derivedFrom = None
        self.dim = None
        self.dimIncrement = None
        self.dimIndex = None
        self.name = None
        self.displayName = None
        self.description = None
        self.alternateGroup = None
        self.addressOffset = None
        self.size = None
        self.access = None
        self.resetValue = None
        self.resetMask = None
        self.modifiedWriteValues = None
        self.readAction = None
        self.alternateRegister = None
        self.dataType = None

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)

        if self.dim:
            try:
                self.dimIndex = int(self.dimIndex)
            except:
                try:
                    start, stop = self.dimIndex.split("-")
                    start, stop = (int(start), int(stop)+1)
                    self.dimIndex = list(range(start, stop))
                except:
                    self.dimIndex = self.dimIndex.split(",")

        try:  # Because fields may be None
            for e in element.find("fields"):
                field = Field(e, self, parent=self)
                self.fields.append(field)
        except:
            pass

    def to_array(self):
        """Replicate the register in accordance with it's dimensions
        and return a list of these replicates.

        - If the register is dimensionless, the returned list just
          contains the register itself unchanged.

        - In case the register name looks like a C array, the returned
          list contains the register itself, where nothing else than
          the '%s' placeholder in it's name has been replaced with value
          of the dim element.
        """
        if not self.dim:
            return [self]
        if self.name.endswith("[%s]"):  # C array like
            self.name = self.name.replace("%s", str(self.dim))
            self.dim = self.dimIndex = self.dimIncrement = None
            return [self]

        replicates = []
        for increment, index in enumerate(self.dimIndex):
            r = self.copy()
            r.fields = [f.copy() for f in r.fields]
            for f in r.fields:
                f.parent = r
            r.name = r.name.replace("%s", str(index))
            r.addressOffset += increment * r.dimIncrement
            r.dim = r.dimIndex = r.dimIncrement = None
            replicates.append(r)
        return replicates


class Cluster(SvdElement):
    type = "cluster"
    cast_to_integer = ["addressOffset", "dim", "dimIncrement"]
    props = [
        "registers", "derivedFrom", "dim", "dimIncrement", "dimIndex", "name",
        "description", "alternateCluster", "headerStructName", "addressOffset"]

    def init(self):
        self.registers = []
        self.derivedFrom = None
        self.dim = None
        self.dimIncrement = None
        self.dimIndex = None
        self.name = None
        self.description = None
        self.alternateCluster = None
        self.headerStructName = None
        self.addressOffset = None

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, {})

        # TODO: Should work like Register.to_array(), if there's self.dim
        self.name = self.name.replace("%s", str(self.dim))

        try:
            for e in element.findall("*"):
                if e.tag == "cluster":  # Cluster may include yet another cluster
                    self.registers.append(Cluster(e, defaults, parent=self))
                elif e.tag == "register":
                    r = Register(e, defaults, parent=self)
                    self.registers.extend(r.to_array())
        except:
            pass


class Field(SvdElement):
    type = "field"
    cast_to_integer = ["bitOffset", "bitWidth", "lsb", "msb"]
    props = [
        "enumeratedValues", "derivedFrom", "name", "description", "bitOffset",
        "bitWidth", "lsb", "msb", "bitRange", "access", "modifiedWriteValues",
        "writeConstraint", "readAction"]

    def init(self):
        self.enumeratedValues = {
            "read": [],
            "write": [],
            "read-write": [],
        }
        self.derivedFrom = None
        self.name = None
        self.description = None
        self.bitOffset = None
        self.bitWidth = None
        self.lsb = None
        self.msb = None
        self.bitRange = None
        self.access = None
        self.modifiedWriteValues = None
        self.writeConstraint = None
        self.readAction = None

    def from_element(self, element, defaults={}):
        SvdElement.from_element(self, element, defaults)

        if self.bitRange:
            self.msb, self.lsb = self.bitRange[1:-1].split(":")
            self.msb = int(self.msb)
            self.lsb = int(self.lsb)
        elif self.bitOffset:
            self.lsb = self.bitOffset
            self.msb = self.bitWidth + self.lsb
        self.bitOffset = self.lsb
        self.bitWidth = self.msb - self.lsb + 1
        self.bitRange = "[{}:{}]".format(self.msb, self.lsb)

        try:  # Because enumeratedValues may be None
            for e in element.findall("enumeratedValues"):
                try:
                    usage = e.find("usage").text
                except:
                    usage = "read-write"
                for e in e.findall("enumeratedValue"):
                    enum = EnumeratedValue(e, {}, parent=self)
                    self.enumeratedValues[usage].append(enum)
        except:
            pass


class EnumeratedValue(SvdElement):
    type = "enumeratedValue"
    cast_to_integer = ["value"]
    props = ["derivedFrom", "name", "description", "value", "isDefault"]

    def init(self):
        self.derivedFrom = None
        self.name = None
        self.description = None
        self.value = None
        self.isDefault = None


class Interrupt(SvdElement):
    type = "interrupt"
    cast_to_integer = ["value"]
    props = ["name", "value"]

    def init(self):
        self.name = None
        self.value = None
