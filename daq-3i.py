import db_model as db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bus as Bus
import time
import configparser
import logging

"""
EnvDaq3i -- Main application App
"""


class EnvDaq3i:

    def __init__(self):
        self.dbe = None
        self.dbs = None
        self.conf = None
        self.engine = None
        self.Session = None

        self.buses = []

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

    def write_channel_data(self):
        pass

    def init_logger(self):
        # Configure Logger
        l_filename = None
        l_level = logging.INFO
        FORMAT = '%(asctime)-15s : %(levelname)s : %(module)s : %(message)s'
        logging.basicConfig(format=FORMAT, filename=l_filename, level=l_level)

"""
Main code entry
"""
env = EnvDaq3i()

env.init_logger()
env.init_db()
#db.create_tables(env.engine)
#exit()

session = env.Session()

buses = session.query(db.Buses).filter_by(enabled=True).all()
bus1 = None

for bus in buses:
    logging.info(f"Loading Bus {bus.name} with protocol {bus.protocol}...")
    logging.info(f"{bus.address}:{bus.port}, {bus.timeout}")

    if bus.protocol == 1:
        bus1 = Bus.ModbusCon(bus.address, bus.port, bus.timeout, bus.protocol)

    env.buses.append(bus1)

    # Find channels for the current bus
    channels = session.query(db.Channels).filter_by(bus_id=bus.id).filter_by(enabled=True).all()
    for chl in channels:
        logging.info(f"Loading {chl.name} on bus {bus.id}...")
        str = f"{chl.name}, {chl.id}, {chl.device_id}, {chl.address}, {chl.timing}, {chl.conversion_id}, {chl.func_code}"
        logging.info(str)

        if chl.conversion_id == 0 or chl.conversion_id is None:
            conv_exp = None
        else:
            conv_exp = chl.conversion.expr

        bus1.load_channel(chl.name, chl.id, chl.device_id, chl.address, chl.timing, chl.conversion_id, chl.func_code,
                          conv_exp)

    logging.info(f"{bus.name} has {len(bus1.channels)} channels.")
logging.info(f"Loaded {len(env.buses)} buses.")

# Loop Through
while True:

    # Tick all buses
    for bus in env.buses:
        bus.timer_tick()

    # Check all channels for dirty data
    for bus in env.buses:
        for ch in bus.channels:
            if ch.is_dirty:
                data = db.Channel_Data()
                data.channel_id = ch.id
                data.ts = ch.last_read_at
                data.value = ch.value
                print(data.value)
                session.add(data)
                session.commit()
                ch.is_dirty = False
    time.sleep(1)

