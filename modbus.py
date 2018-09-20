from pymodbus.client.sync import ModbusTcpClient


class ModbusConn:

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout

    def init_con(self):
        pass

    def read_holding_reg(self, unit, addr, count):

        with ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout) as client:
            result = client.read_holding_registers(address=addr, count=count, unit=unit)
            client.close()
        return result
