from datetime import datetime
from conversion import do_conversion
import logging
import modbus

MODBUSTCP_PROTOCOL = 1

"""
ChannelClass - Stores data about one channel  
"""


class ChannelState:

    def __init__(self, name, id, device_id, address, timing, conversion_id, modbus_fn_code, conversion_expr, format):

        self.name = name
        self.id = id
        self.device_id = device_id
        self.address = address
        self.timing = timing
        self.conversion_id = conversion_id
        self.modbus_fn_code = modbus_fn_code
        self.conversion_expr = conversion_expr
        self.format = format

        self.value = None
        self.is_dirty = False
        self.last_read_at = None
        self.last_status = 0

    def write_data(self, value, ts, status=0):
        self.value = value
        self.last_status = status
        self.last_read_at = ts
        self.is_dirty = True

    def check_read_due(self):

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
BusCon - Generic Connection Class representing a bus  
"""


class BusCon:

    def __init__(self, name, host, port, timeout, protocol):
        self.name = name
        self.host = host
        self.port = port
        self.timeout = timeout
        self.channels = []
        self.protocol = protocol

    def init_con(self):
        pass

    def load_channel(self, name, id, device_id, address, timing, conversion_id, modbus_fn_code, conversion_expr,
                     format):
        chl = ChannelState(name, id, device_id, address, timing, conversion_id, modbus_fn_code, conversion_expr,
                           format)
        self.channels.append(chl)

    def timer_tick(self):

        ch = 0
        ln = len(self.channels)
        while ch < ln:
            if self.channels[ch].check_read_due():
                self.read_channel(ch)
            ch += 1

    def read_channel(self, chl):

        ts = datetime.now()
        self.channels[chl].last_read_at = ts

        # Read Channel value

        res = self.read_register(self.channels[chl])

        self.channels[chl].last_status = -1

        if res.result == -1:
            logging.error(f"Error reading channel {self.channels[chl].name}")

            if res.exception is not None:
                logging.error(f"Exception: {res.exception.string} ")

        else:
            # data arrived, save data in object

            self.channels[chl].last_status = 0

            # Perform data format decoding
            # Single, Double, Float, Float R W etc...
            value = self.decode_data_format(self.channels[chl], res)

            # Perform data conversion
            #
            if self.channels[chl].conversion_expr is not None:
                value = do_conversion(value, self.channels[chl].conversion_expr)

            # Write value to Channel
            self.channels[chl].write_data(value, ts, 0)

        pass

    def read_register(self, *args):
        print("Base method called: read_holding_reg")
        pass

    def decode_data_format(self, *args):
        print("Base method called: decode_data_format")
        pass



"""
ModbusCon
"""


class ModbusCon(modbus.ModbusMixin, BusCon):
    pass
