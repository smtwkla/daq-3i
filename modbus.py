import logging
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient
import pymodbus.exceptions
import buscommon


MODBUS_FUNC_READHOLDING = 3

MODBUS_SINT16 = 0
MODBUS_SINT32 = 1
MODBUS_SINT32_RWORDS = 2
MODBUS_SKIP2 = 3
MODBUS_UINT16 = 4
MODBUS_UINT32 = 5
MODBUS_UINT32_RWORDS = 6
MODBUS_FLOAT = 7
MODBUS_FLOAT_SKIP2 = 8
MODBUS_FLOAT_RBYTES = 9
MODBUS_FLOAT_RWORDS = 10
MODBUS_FLOAT_RSKIP2 = 11
MODBUS_ABB_REAL32_U = 12
MODBUS_ABB_REAL32_S = 13

FORMAT_LENGTH = {MODBUS_SINT16: 1, MODBUS_SINT32: 2, MODBUS_SINT32_RWORDS: 2, MODBUS_SKIP2: 3,
                 MODBUS_UINT16: 4, MODBUS_UINT32: 5, MODBUS_UINT32_RWORDS: 6, MODBUS_FLOAT: 7,
                 MODBUS_FLOAT_SKIP2: 8, MODBUS_FLOAT_RBYTES: 9, MODBUS_FLOAT_RWORDS: 10,
                 MODBUS_FLOAT_RSKIP2: 11, MODBUS_ABB_REAL32_U: 2, MODBUS_ABB_REAL32_S: 2}

"""
ModbusMixin - Mixin for Modbus specific functionality
"""


class ModbusMixin:
    def read_register(self, chl):
        #print(f"Reading {chl.name}")

        ret = buscommon.ReadResponse()

        try:
            with ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout) as client:
                if chl.modbus_fn_code == MODBUS_FUNC_READHOLDING:
                    count = FORMAT_LENGTH[chl.format]
                    ret.response = client.read_holding_registers(address=chl.address, count=count, unit=chl.device_id)
                    client.close()
                else:
                    raise pymodbus.exceptions.ModbusException("Function code not yet implemented.")
                if ret.response.isError():
                    ret.result = -1
        except pymodbus.exceptions.ModbusException as e:
            ret.exception = e
            ret.result = -1

        return ret

    def decode_data_format(self, chl, res):

        value = None
        byteorder = Endian.Big
        wordorder = Endian.Little


        if chl.format == MODBUS_UINT16:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_SINT16:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_UINT32:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_UINT32_RWORDS:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_SINT32:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_SINT32_RWORDS:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_SKIP2:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_FLOAT:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_FLOAT_SKIP2:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_FLOAT_RBYTES:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_FLOAT_RWORDS:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_FLOAT_RSKIP2:
            byteorder = Endian.Big
            wordorder = Endian.Little

        if chl.format == MODBUS_ABB_REAL32_U or chl.format == MODBUS_ABB_REAL32_S:
            byteorder = Endian.Big
            wordorder = Endian.Big

        decoder = BinaryPayloadDecoder.fromRegisters(res.response.registers, byteorder=byteorder, wordorder=wordorder)


        if chl.format == MODBUS_UINT16:
            value = decoder.decode_16bit_uint()

        if chl.format == MODBUS_SINT16:
            value = decoder.decode_16bit_int()

        if chl.format == MODBUS_SINT32:
            value = decoder.decode_32bit_int()

        if chl.format == MODBUS_UINT32:
            value = decoder.decode_32bit_uint()

        if chl.format == MODBUS_SINT32_RWORDS:
            value = decoder.decode_32bit_int()

        if chl.format == MODBUS_SKIP2:
            pass

        if chl.format == MODBUS_UINT32_RWORDS:
            pass

        if chl.format == MODBUS_FLOAT:
            value = decoder.decode_32bit_float()

        if chl.format == MODBUS_FLOAT_SKIP2:
            pass

        if chl.format == MODBUS_FLOAT_RBYTES:
            pass

        if chl.format == MODBUS_FLOAT_RWORDS:
            pass

        if chl.format == MODBUS_FLOAT_RSKIP2:
            pass

        if chl.format == MODBUS_ABB_REAL32_U:
            value = decoder.decode_16bit_uint()
            # print("Reg 1 : %d" % res.response.registers[0])
            # print("Reg 2 : %d" % res.response.registers[1])

        if chl.format == MODBUS_ABB_REAL32_S:

            value = int(format(res.response.registers[1], "b").zfill(16) + format(res.response.registers[0], "b").zfill(16),2)

        # decoder.decode_bits()
        return value



