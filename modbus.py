import logging
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

FORMAT_LENGTH = {MODBUS_SINT16: 1, MODBUS_SINT32: 1, MODBUS_SINT32_RWORDS: 2, MODBUS_SKIP2: 3,
                 MODBUS_UINT16: 4, MODBUS_UINT32: 5, MODBUS_UINT32_RWORDS: 6, MODBUS_FLOAT: 7,
                 MODBUS_FLOAT_SKIP2: 8, MODBUS_FLOAT_RBYTES: 9, MODBUS_FLOAT_RWORDS: 10,
                 MODBUS_FLOAT_RSKIP2: 11}

"""
ModbusMixin - Mixin for Modbus specific functionality
"""


class ModbusMixin:
    def read_register(self, chl):
        logging.debug(f"Reading {chl.device_id}")

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

        if chl.format == MODBUS_UINT16:
            value = res.response.registers[0]

        if chl.format == MODBUS_SINT16:
            value = buscommon.getSignedNumber(res.response.registers[0], 16)

        return value
