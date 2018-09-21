from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Channels(Base):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=False, )
    bus = relationship("Buses")
    device_id = Column(Integer, nullable=False)
    address = Column(Integer, nullable=False)
    timing = Column(Integer, nullable=False)
    conversion_id = Column(Integer, ForeignKey('conversions.id'), nullable=False)
    conversion = relationship("Conversions")
    func_code = Column(Integer, nullable=False)
    format_code = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False)

    def __repr__(self):
        return self.name

class Buses(Base):
    __tablename__ = 'buses'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    protocol = Column(Integer, nullable=False)
    address = Column(String(50))
    port = Column(Integer)
    timeout = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False)


class Conversions(Base):
    __tablename__ = 'conversions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    expr = Column(String(250))


class Channel_Data(Base):
    __tablename__="channel_data"
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    ts = Column(DateTime, nullable=False)
    value = Column(Numeric(25, 6))


def getdburl(c):
    con = f"{c['db']['dbdialect']}://{c['db']['user']}:{c['db']['pass']}@{c['db']['host']}:{c['db']['port']}/{c['db']['database']}"
    return con

def create_tables(engine):
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')

    con = getdburl(config)
    # Create an engine
    engine = create_engine(con)

    # Create all tables in the engine.
    Base.metadata.create_all(engine)

