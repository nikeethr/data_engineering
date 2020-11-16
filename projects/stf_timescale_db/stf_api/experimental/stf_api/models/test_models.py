"""
    This file has been modified after generation from `sqlacodegen` to fit with
    flask + sqlalchemy + geoalchemy
"""
# coding: utf-8
from .base import db
# from sqlalchemy import (
#     BigInteger, Column, DateTime, Float, ForeignKey, Index,
#     Integer, Numeric, String, Table, Text, text
# )
from geoalchemy2 import Geometry


SRID = 4238

class StfGeomSubarea(db.Model):
    __tablename__ = 'stf_geom_subarea'

    gid = db.Column(db.Integer, primary_key=True,
        server_default=db.text("nextval('stf_geom_subarea_gid_seq'::regclass)"))
    subareaid = db.Column(db.BigInteger)
    y_centroid = db.Column(db.Numeric)
    x_centroid = db.Column(db.Numeric)
    catchment = db.Column(db.String(80))
    subcatchm = db.Column(db.BigInteger)
    subcatchid = db.Column(db.String(80))
    region = db.Column(db.String(80))
    swift_id = db.Column(db.BigInteger)
    calibid = db.Column(db.String(80))
    calibname = db.Column(db.String(80))
    outhydroid = db.Column(db.BigInteger)
    area = db.Column(db.Numeric)
    length = db.Column(db.Numeric)
    geom = db.Column(Geometry(geometry_type='MULTIPOLYGON', srid=SRID),
        index=True)


class StfGeomSubcatch(db.Model):
    __tablename__ = 'stf_geom_subcatch'

    gid = db.Column(db.Integer, primary_key=True,
        server_default=db.text("nextval('stf_geom_subcatch_gid_seq'::regclass)"))
    subcatchm = db.Column(db.String(80))
    catchment = db.Column(db.String(80))
    region = db.Column(db.String(80))
    subcatchid = db.Column(db.String(80))
    swiftid = db.Column(db.BigInteger)
    swift_id = db.Column(db.BigInteger)
    outflowid = db.Column(db.BigInteger)
    geom = db.Column(Geometry(geometry_type='MULTIPOLYGON', srid=SRID),
        index=True)


class StfMetadatum(db.Model):
    __tablename__ = 'stf_metadata'

    pk_meta = db.Column(db.Integer, primary_key=True,
        server_default=db.text("nextval('stf_metadata_pk_meta_seq'::regclass)"))
    awrc_id = db.Column(db.String(10), nullable=False, unique=True)
    outlet_node = db.Column(db.Integer, nullable=False)
    catchment = db.Column(db.String(255), nullable=False)
    region = db.Column(db.String(10))
    location = db.Column(Geometry(geometry_type='POINT', srid=SRID))
    station_name = db.Column(db.Text)

t_stf_fc_flow = db.Table(
    'stf_fc_flow',
    db.Column('fc_datetime', db.DateTime(True), nullable=False, index=True),
    db.Column('lead_time_hours', db.Integer, nullable=False),
    db.Column('meta_id', db.ForeignKey('stf_metadata.pk_meta'), nullable=False),
    db.Column('pctl_5', db.Float(53)),
    db.Column('pctl_25', db.Float(53)),
    db.Column('pctl_50', db.Float(53)),
    db.Column('pctl_75', db.Float(53)),
    db.Column('pctl_95', db.Float(53)),
    db.Index('station_id_fc_datetime_idx', 'meta_id', 'fc_datetime'),
    db.Index('station_id_lead_time_hours_fc_datetime_idx', 'meta_id',
        'lead_time_hours', 'fc_datetime', unique=True)
)

class StfFcFlow(db.Model):
    __table__ = t_stf_fc_flow

    # timescaledb doesn't automatically create a primary key so we're using a
    # implicit one since SQLAlchemy mandates it.
    __mapper_args__ = {
        'primary_key': [
            t_stf_fc_flow.c.meta_id,
            t_stf_fc_flow.c.lead_time_hours,
            t_stf_fc_flow.c.fc_datetime
        ]
    }

t_stf_obs_flow = db.Table(
    'stf_obs_flow',
    db.Column('obs_datetime', db.DateTime(True), nullable=False, index=True),
    db.Column('meta_id', db.ForeignKey('stf_metadata.pk_meta'), nullable=False),
    db.Column('value', db.Float(53)),
    db.Index('station_id_obs_datetime_idx', 'meta_id', 'obs_datetime',
        unique=True)
)

class StfObsFlow(db.Model):
    __table__ = t_stf_obs_flow

    # timescaledb doesn't automatically create a primary key so we're using a
    # implicit one since SQLAlchemy mandates it.
    __mapper_args__ = {
        'primary_key': [
            t_stf_obs_flow.c.meta_id,
            t_stf_obs_flow.c.obs_datetime
        ]
    }

