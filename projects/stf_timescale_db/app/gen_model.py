# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Table, Text, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class StfGeomSubarea(Base):
    __tablename__ = 'stf_geom_subarea'

    gid = Column(Integer, primary_key=True, server_default=text("nextval('stf_geom_subarea_gid_seq'::regclass)"))
    subareaid = Column(BigInteger)
    y_centroid = Column(Numeric)
    x_centroid = Column(Numeric)
    catchment = Column(String(80))
    subcatchm = Column(BigInteger)
    subcatchid = Column(String(80))
    region = Column(String(80))
    swift_id = Column(BigInteger)
    calibid = Column(String(80))
    calibname = Column(String(80))
    outhydroid = Column(BigInteger)
    area = Column(Numeric)
    length = Column(Numeric)
    geom = Column(NullType, index=True)


class StfGeomSubcatch(Base):
    __tablename__ = 'stf_geom_subcatch'

    gid = Column(Integer, primary_key=True, server_default=text("nextval('stf_geom_subcatch_gid_seq'::regclass)"))
    subcatchm = Column(String(80))
    catchment = Column(String(80))
    region = Column(String(80))
    subcatchid = Column(String(80))
    swiftid = Column(BigInteger)
    swift_id = Column(BigInteger)
    outflowid = Column(BigInteger)
    geom = Column(NullType, index=True)


class StfMetadatum(Base):
    __tablename__ = 'stf_metadata'

    pk_meta = Column(Integer, primary_key=True, server_default=text("nextval('stf_metadata_pk_meta_seq'::regclass)"))
    awrc_id = Column(String(10), nullable=False, unique=True)
    outlet_node = Column(Integer, nullable=False)
    catchment = Column(String(255), nullable=False)
    region = Column(String(10))
    location = Column(NullType)
    station_name = Column(Text)


t_stf_fc_flow = Table(
    'stf_fc_flow', metadata,
    Column('fc_datetime', DateTime(True), nullable=False, index=True),
    Column('lead_time_hours', Integer, nullable=False),
    Column('meta_id', ForeignKey('stf_metadata.pk_meta'), nullable=False),
    Column('pctl_5', Float(53)),
    Column('pctl_25', Float(53)),
    Column('pctl_50', Float(53)),
    Column('pctl_75', Float(53)),
    Column('pctl_95', Float(53)),
    Index('station_id_fc_datetime_idx', 'meta_id', 'fc_datetime'),
    Index('station_id_lead_time_hours_fc_datetime_idx', 'meta_id', 'lead_time_hours', 'fc_datetime', unique=True)
)


t_stf_obs_flow = Table(
    'stf_obs_flow', metadata,
    Column('obs_datetime', DateTime(True), nullable=False, index=True),
    Column('meta_id', ForeignKey('stf_metadata.pk_meta'), nullable=False),
    Column('value', Float(53)),
    Index('station_id_obs_datetime_idx', 'meta_id', 'obs_datetime', unique=True)
)
