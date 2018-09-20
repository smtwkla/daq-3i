from readconf import readconfig
import db_model as db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class EnvDaq3i:

    def __init__(self):
        self.dbe = None
        self.dbs = None
        self.conf = None
        self.engine = None
        self.Session = None

    def read_conf(self):
        self.conf = readconfig()

    def init_db(self):
        con = db.getdburl(self.conf)
        print(con)

        # Create an engine
        self.engine = create_engine(con)

        self.Session = sessionmaker(bind=self.engine)


env = EnvDaq3i()
env.read_conf()
env.init_db()

session = env.Session()
channels = session.query(db.Channels).all()

for c in channels:
    print(c.name)

