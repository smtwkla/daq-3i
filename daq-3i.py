import db_model as db
from sqlalchemy import create_engine
from sqlalchemy.exc import  SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import bus as Bus
import time
import configparser
import logging
import datetime

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
        l_filename = None  # "daq-3i.log" #
        l_level = logging.INFO
        FORMAT = '%(asctime)-15s : %(levelname)s : %(module)s : %(message)s'
        logging.basicConfig(format=FORMAT, filename=l_filename, level=l_level)

    def load_buses(self):

        logging.info("Loading Buses...")
        bus_session = self.Session()
        buses = bus_session.query(db.Buses).filter_by(enabled=True).all()

        bus1 = None

        for bus in buses:
            logging.info(f"Loading Bus {bus.name} with protocol {bus.protocol}...")
            logging.info(f"{bus.address}:{bus.port}, {bus.timeout}")

            if bus.protocol == Bus.MODBUSTCP_PROTOCOL:
                bus1 = Bus.ModbusCon(bus.address, bus.port, bus.timeout, bus.protocol)

            self.buses.append(bus1)

            # Find channels for the current bus
            channels = bus_session.query(db.Channels).filter_by(bus_id=bus.id).filter_by(enabled=True).all()

            for chl in channels:
                logging.info(f"Loading {chl.name} on bus {bus.id}...")

                if chl.conversion_id == 0 or chl.conversion_id is None:
                    conv_exp = None
                else:
                    conv_exp = chl.conversion.expr

                bus1.load_channel(chl.name, chl.id, chl.device_id, chl.address, chl.timing, chl.conversion_id,
                                  chl.func_code,
                                  conv_exp, chl.format_code)

            logging.info(f"Bus {bus.name} has {len(bus1.channels)} channels.")

        bus_session.close()

    def loop(self):
        # Loop Through
        while True:

            # Tick all buses
            last_tick = datetime.datetime.now()

            for bus in self.buses:
                bus.timer_tick()

            # Check all channels for dirty data
            for bus in self.buses:
                for ch in bus.channels:
                    if ch.is_dirty:
                        session = self.Session()
                        try:
                            data = db.Channel_Data()
                            data.channel_id = ch.id
                            data.ts = ch.last_read_at
                            data.value = ch.value
                            print(data.value)
                            session.add(data)
                            session.commit()
                            ch.is_dirty = False
                        except SQLAlchemyError as e:
                            session.rollback()
                            logging.critical("Error: {0}".format(e))

            # time_to_sleep = 1 second  - (now - last_tick)
            elapsed = (datetime.datetime.now() - last_tick).total_seconds()

            if elapsed <= 1:
                time.sleep(1 - elapsed)
            else:
                pass  # we missed the bus already, lets not wait.


"""
Main code entry
"""

# Configure logging:


env = EnvDaq3i()

env.init_logger()
logging.info("daq-3i Starting... Init DB...")
env.init_db()
#db.create_tables(env.engine)
#exit()

env.load_buses()

logging.info(f"Loaded {len(env.buses)} buses.")
logging.info("Starting data acquisition loop...")


env.loop()
