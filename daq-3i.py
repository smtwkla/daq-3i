import db_model as db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import modbus
import time
import configparser


class EnvDaq3i:

    def __init__(self):
        self.dbe = None
        self.dbs = None
        self.conf = None
        self.engine = None
        self.Session = None

    def read_conf(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.conf = config

    def init_db(self):
        self.read_conf()
        con = db.getdburl(self.conf)
        print(con)

        # Create an engine
        self.engine = create_engine(con)

        self.Session = sessionmaker(bind=self.engine)


env = EnvDaq3i()

env.init_db()

session = env.Session()
channels = session.query(db.Channels).all()

for c in channels:
    print(c.name)
print("Connecting...")
bus1 = modbus.ModbusConn("192.168.16.59", 502, 1000)
print("Connect.")
while True:
    res = bus1.read_holding_reg(6, 104, 2)
    print(res.registers[0]/100)
    time.sleep(1)