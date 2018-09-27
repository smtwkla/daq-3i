import logging
from sqlalchemy.exc import SQLAlchemyError
import db_model as db
import datetime

STATUS_RUNNING = 1
STATUS_OK = 1

"""
class DaqStatus - Manage Daq Status table
"""


class DaqStatus:

    def __init__(self, env):
        self.env = env

    def flush_parameters(self):
        #  Get new session
        session = self.env.Session()

        try:
            #  Flush all old parameters
            session.query(db.Daq_Status).delete()
            #  Commit
            session.commit()
            #  Close
            session.close()

        except SQLAlchemyError as e:
            session.rollback()
            logging.critical("Error: {0}".format(e))


    def update_parameter(self, parameter, status):

        #  Get new session
        session = self.env.Session()

        try:

            # Get parameter object
            record = session.query(db.Daq_Status)\
                .filter(db.Daq_Status.parameter == parameter)\
                .first()

            if record is None:
                # update value
                record = db.Daq_Status()
                record.parameter = parameter
                record.status = status
                record.ts = datetime.datetime.now()
                session.add(record)
            else:
                record.status = status
                record.ts = datetime.datetime.now()

            #  Commit
            session.commit()
            #  Close
            session.close()
            return False

        except SQLAlchemyError as e:
            session.rollback()
            logging.critical("Error: {0}".format(e))
            return False


