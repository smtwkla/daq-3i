from pymodbus.client.sync import ModbusTcpClient
import pymodbus.exceptions
from datetime import datetime
from conversion import do_conversion
import logging

"""
ReadResponse - Return object for Channel Read
"""


class ReadResponse:
    def __init__(self):
        self.result = 0
        self.response = None
        self.exception = None


"""
ChannelClass - Stores data about one channel  
"""


class ChannelState:

    def __init__(self, name, id, device_id, address, timing, conversion_id, modbus_fn_code, conversion_expr):

        self.name = name
        self.id = id
        self.device_id = device_id
        self.address = address
        self.timing = timing
        self.conversion_id = conversion_id
        self.modbus_fn_code = modbus_fn_code
        self.conversion_expr = conversion_expr

        self.value = None
        self.is_dirty = False
        self.last_read_at = None
        self.last_status = 0

    def write_data(self, value, ts, status=0):
        self.value = value
        self.last_status = status
        self.last_read_at = ts
        self.is_dirty = True

    def read_due(self):

        # if last_read + timing > now,
        now = datetime.now()
        last = self.last_read_at

        if self.last_read_at is None:
            return True
        elif (now - last).total_seconds() > self.timing:
            return True
        else:
            return False


"""
ModbusConn - Modbus Connection Class representing a bus  
"""


class BusCon:

    def __init__(self, host, port, timeout, protocol):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.channels = []
        self.protocol = protocol

    def init_con(self):
        pass

    def load_channel(self, name, id, device_id, address, timing, conversion_id, modbus_fn_code, conversion_expr):
        chl = ChannelState(name, id, device_id, address, timing, conversion_id, modbus_fn_code, conversion_expr)
        self.channels.append(chl)

    def timer_tick(self):

        ch = 0
        ln = len(self.channels)
        while ch < ln:
            if self.channels[ch].read_due():
                self.read_channel(ch)
            ch += 1

    def read_channel(self, chl):

        unit = self.channels[chl].device_id
        addr = self.channels[chl].address
        ts = datetime.now()
        self.channels[chl].last_read_at = ts

        # Read Channel value
        if self.protocol == 1:
            res = self.read_modbus_holding_reg(unit, addr, 1)
        else:
            raise Exception(f"Error: Protocol unknown: {self.protocol}")

        self.channels[chl].last_status = -1

        if res.result == -1:
            logging.error(f"Error reading channel {chl}")

            if res.exception is not None:
                logging.error(f"Exception: {res.exception.string} ")

        else:
            # data arrived, save data in object

            self.channels[chl].last_status = 0

            # Perform data format decoding
            # Single, Double, Float, Float R W etc...
            value = res.response.registers[0]

            # Perform data conversion
            #
            value = do_conversion(value, self.channels[chl].conversion_expr)

            # Write value to Channel
            self.channels[chl].write_data(value, ts, 0)

        pass

    def read_modbus_holding_reg(self, unit, addr, count):
        logging.debug(f"Reading {unit} {addr} {count}")

        ret = ReadResponse()

        try:
            with ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout) as client:
                ret.response = client.read_holding_registers(address=addr, count=count, unit=unit)
                client.close()
                if ret.response.isError():
                    ret.result = -1
        except pymodbus.exceptions.ModbusException as e:
            ret.exception = e
            ret.result = -1

        return ret

