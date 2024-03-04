# a class for interpreting a modbus register as a higher level datatype

import struct
from enum import Enum
from .inverter import Inverter


class RegisterValue:
    class RegisterType(Enum):
        HOLDING = "holding"
        INPUT = "input"

        @classmethod
        def from_str(cls, string):
            if string == "holding":
                return cls.HOLDING
            elif string == "input":
                return cls.INPUT
            else:
                raise Exception("Unsupported register type " + string)

    class Endianness(Enum):
        BIG = "big"
        LITTLE = "little"

        @classmethod
        def from_str(cls, string):
            if string == "big" or string == "be" or string == ">":
                return cls.BIG
            elif string == "little" or string == "le" or string == "<":
                return cls.LITTLE
            else:
                raise Exception("Unsupported endianess " + string)

    class Type(Enum):
        UINT = "uint"
        INT = "int"
        FLOAT = "float"
        ASCII = "ascii"
        UTF16 = "utf16"
        NONE = "none"

        @classmethod
        def from_str(cls, string):
            if string == "uint":
                return cls.UINT
            elif string == "int":
                return cls.INT
            elif string == "float":
                return cls.FLOAT
            elif string == "ascii":
                return cls.ASCII
            elif string == "utf16":
                return cls.UTF16
            elif string == "none" or string == "raw" or string == "":
                return cls.NONE
            else:
                raise Exception("Unsupported datatype " + string)

    def __init__(
        self,
        address,
        size,
        register_type: RegisterType,
        datatype: Type,
        endianness: Endianness,
    ):
        self.address = address
        self.size = size
        self.datatype = datatype
        self.endianness = endianness
        self.regType = register_type

    def read_value(self, inverter: Inverter):
        """Reads the value of the register from the inverter"""
        if self.regType == RegisterValue.RegisterType.HOLDING:
            registers = inverter.read_holding_registers(self.address, self.size)
        else:
            registers = inverter.read_input_registers(self.address, self.size)

        # currently we convert the raw values that are word based to bytearray
        self.raw = bytearray()
        for register in registers:
            byte_arr = register.to_bytes(2, "big")
            self.raw.extend(byte_arr)

        if self.datatype != RegisterValue.Type.NONE:
            return self.raw, self.get_value(self.raw)
        return self.raw, None

    def get_value(self, raw: bytearray):
        """Converts a list of bytes to a value based on the datatype and endianness of the register"""
        value = None
        endianess = self.endianness

        if self.datatype == RegisterValue.Type.UINT:
            value = int.from_bytes(raw, byteorder=endianess.value, signed=False)
        elif self.datatype == RegisterValue.Type.INT:
            value = int.from_bytes(raw, byteorder=endianess.value, signed=True)
        elif self.datatype == RegisterValue.Type.FLOAT:
            if endianess == RegisterValue.Endianness.BIG:
                endianess = ">"
            else:
                endianess = "<"

            if len(raw) == 4:
                value = struct.unpack(f"{endianess}f", raw)[0]
            elif len(raw) == 8:
                value = struct.unpack(f"{endianess}d", raw)[0]
            else:
                raise Exception(f"Unsupported float length : {len(raw)}")

        elif self.datatype == RegisterValue.Type.ASCII:
            value = raw.decode("ascii")
        elif self.datatype == RegisterValue.Type.UTF16:
            value = raw.decode("utf-16" + ("be" if endianess.value == "big" else "le"))
        else:
            raise Exception("Unsupported datatype " + self.datatype.value)

        return value