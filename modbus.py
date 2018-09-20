from pymodbus.client.sync import ModbusTcpClient
import pymodbus.exceptions
from datetime import datetime
import logging

"""
ChannelClass - Stores data about one channel  
"""

class ChannelClass:

    def __init__(self, name, id, device_id, address, timing, conversion_id, modbus_fn_code):

        self.name = name
        self.id = id
        self.device_id = device_id
        self.address = address
        self.timing = timing
        self.conversion_id = conversion_id
        self.modbus_fn_code = modbus_fn_code

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

class ModbusConn:

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.channels = []

    def init_con(self):
        pass

    def load_channel(self, name, id, device_id, address, timing, conversion_id, modbus_fn_code):
        chl = ChannelClass(name, id, device_id, address, timing, conversion_id, modbus_fn_code)
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
        self.channels[chl].last_read_at = datetime.now()

        err = True
        result = None
        try:

            # Read Channel value
            result = self.read_holding_reg(unit, addr, 1)
            ts = datetime.now()
            if result.isError():
                err = True
            else:
                err = False
        except pymodbus.exceptions.ModbusException as e:
            # If timeout, mark error
            err = True
            self.channels[chl].last_status = -1
            logging.error (f"Exception reading: {e.string} ")

        if err:
            logging.error(f"Error reading channel {chl}")
            pass
        else:
            # data arrived, save data in object
            logging.debug(f"Received: {result}")

            # Perform data format decoding
            # Single, Double, Float, Float R W etc...

            # Perform data conversion
            #

            # Write value to Channel
            self.channels[chl].write_data(result.registers[0], ts, 0)

        pass

    def read_holding_reg(self, unit, addr, count):
        logging.debug(f"Reading {unit} {addr} {count}")
        with ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout) as client:
            result = client.read_holding_registers(address=addr, count=count, unit=unit)
            client.close()
        return result
