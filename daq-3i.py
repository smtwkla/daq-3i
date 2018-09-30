import db_model as db
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import bus as Bus
from threading import Thread
import time
import configparser
import logging
import datetime
import daq_status
import signal
import sys
from CmdArgParse import process_args

"""
EnvDaq3i -- Main application App
"""

PULSE_SECONDS = 15
PULSE_PARAMETER = "daq-3i"
TRUNC_HIST_INTERVAL = 15


class EnvDaq3i:

    def __init__(self):
        self.dbe = None
        self.dbs = None
        self.conf = None
        self.engine = None
        self.Session = None

        self.daq_stat = None
        self.buses = []
        self.pulse_timer = 0

        self.stopping = False
        self.print_live = False

        self.l_filename = None
        self.l_level = logging.INFO

        self.conf_file = "config.ini"
        self.action_clear_history = True

    def read_conf(self):
        config = configparser.ConfigParser()
        config.read(self.conf_file)
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
        FORMAT = '%(asctime)-15s : %(levelname)s : %(module)s : %(message)s'
        logging.basicConfig(format=FORMAT, filename=self.l_filename, level=self.l_level)


    def prep_daq_status(self):

        logging.info("Preparing Daq Status...")
        self.daq_stat = daq_status.DaqStatus(self)
        self.daq_stat.flush_parameters()

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

    def pulse(self):

        while not self.stopping:
            # Sleep 10 times of 0.1 sec for every PULSE_SECONDS second, checking for stopping flag
            for i in range(0, PULSE_SECONDS * 10):
                if self.stopping:
                    break
                time.sleep(.1)
            self.daq_stat.update_parameter(PULSE_PARAMETER, 1)

    def process_cmd_line_args(self):
        # Process command line arguments
        if len(sys.argv) >= 1:
            (switches, flags) = process_args(sys.argv)
            for i in switches:
                if i[0] == "-c":
                    self.conf_file = str(i[1])
                elif i[0] == "-L":
                    if i[1].strip().upper() == "DEBUG":
                        self.l_level = logging.DEBUG
                elif i[0] == "-LF":
                    self.l_filename = i[1]
                else:
                    logging.critical("Error : Unknown command line switch " + i[0])
                    self.quit(-1)
            for i in flags:
                if "NO_TRUNC_HISTORY" == i.strip().upper():
                    self.action_clear_history = False
                if "PRINT_LIVE" == i.strip().upper():
                    self.print_live = True
                else:
                    logging.critical("Error : Unknown command line flag " + i)
                    self.quit(-1)

    def trunc_history(self):
        # Separate thread to delete old history records
        #
        # count = SELECT COUNT(id) FROM Channel_Data WHERE Channel_id = Channel
        # must replace this code with simple, single SQL command
        # DELETE FROM Channel_Data WHERE id IN (SELECT id FROM Channel_Data WHERE Channel_id = Channel ORDER BY id ASC LIMIT to_del)

        while not self.stopping:

            # Sleep 10 times of 0.1 sec for every TRUNC_HIST_INTERVAL second, checking for stopping flag
            for i in range(0, TRUNC_HIST_INTERVAL * 10):
                if self.stopping:
                    break
                time.sleep(.1)

            session = self.Session()

            # Get All Channels
            all_chl = session.query(db.Channels).all()

            for chl in all_chl:

                if self.stopping:
                    break

                count = session.query(db.Channel_Data.id).filter(db.Channel_Data.channel_id == chl.id).count()
                history_len = session.query(db.Channels).filter(db.Channels.id == chl.id).one().history_len
                to_del = count - history_len
                logging.debug("Channel %s : History Len: %d." % (chl.name, history_len))
                if to_del > 0 and not self.stopping:
                    logging.debug("To delete %d of a total of %d records." % (to_del, count))
                    res = session.query(db.Channel_Data.id).filter(db.Channel_Data.channel_id == chl.id).order_by(db.Channel_Data.id.asc()).limit(to_del)
                    for row in res:
                        session.query(db.Channel_Data).filter(db.Channel_Data.id == row[0]).delete()
                        if self.stopping:
                            break
                        time.sleep(0.01)
                    session.commit()
            time.sleep(0.1)

    def load(self):

        self.process_cmd_line_args()
        self.init_logger()
        logging.info("daq-3i Starting... Init DB...")
        self.init_db()

        self.prep_daq_status()
        self.load_buses()
        # db.create_tables(env.engine)
        # exit()
        logging.info(f"Loaded {len(env.buses)} buses.")

        # write status - 1 = Running
        self.daq_stat.update_parameter(PULSE_PARAMETER, daq_status.STATUS_RUNNING)

    def acquire(self):
        while not self.stopping:

            # Tick all buses
            last_tick = datetime.datetime.now()

            # Acquire data
            for bus in self.buses:
                if self.stopping:
                    break
                bus.timer_tick()

            # time_to_sleep = 1 second  - (now - last_tick)
            elapsed = (datetime.datetime.now() - last_tick).total_seconds()

            if not self.stopping:
                if elapsed <= 1:
                    time.sleep(1 - elapsed)
                else:
                    pass  # we missed the bus already, lets not wait.

    def persist(self):

        while not self.stopping:

            # Check all channels for dirty data
            for bus in self.buses:
                for ch in bus.channels:
                    if self.stopping:
                        break
                    if ch.is_dirty:
                        session = self.Session()
                        try:
                            data = db.Channel_Data()
                            data.channel_id = ch.id
                            data.ts = ch.last_read_at
                            data.value = ch.value
                            if self.print_live:
                                print(f"{ch.name}= {data.value}")
                            session.add(data)
                            session.commit()
                            session.close()
                            ch.is_dirty = False
                            self.daq_stat.update_parameter("CHL: %d" % ch.id, daq_status.STATUS_OK)

                        except SQLAlchemyError as e:
                            session.rollback()
                            logging.critical("Error: {0}".format(e))
                if self.stopping:
                    break
            if not self.stopping:
                time.sleep(0.1)

    def sigterm_handler(self, _signo, _stack_frame):
        logging.info("Signalling quit...")
        self.stopping = True

    def quit(self, code=0):
        exit(0)

"""
SIGTERM Handler function
"""




"""
Main code entry
"""

env = EnvDaq3i()
env.load()
logging.info("Starting data acquisition loop...")

acq = Thread(target=env.acquire)
persist = Thread(target=env.persist)
pulse = Thread(target=env.pulse)

if env.action_clear_history:
    trunc_history = Thread(target=env.trunc_history)

acq.start()
persist.start()
pulse.start()

if env.action_clear_history:
    trunc_history.start()

signal.signal(signal.SIGTERM, env.sigterm_handler)
signal.signal(signal.SIGINT, env.sigterm_handler)

print("Use SIGTERM, SIGINT or Press ^C to quit.")

while True:
    if env.stopping:
        break
    else:
        time.sleep(1)

logging.info("Waiting for pulse thread to quit...")
pulse.join()

logging.info("Waiting for persist thread to quit...")
persist.join()

logging.info("Waiting for acquire thread to quit...")
acq.join()

logging.info("Waiting for truncate thread to quit...")
trunc_history.join()

env.quit()

