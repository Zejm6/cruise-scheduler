from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from .db import Base


class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    max_berths = Column(Integer, nullable=False)
    daily_pax_capacity = Column(Integer, nullable=False)

    max_ship_length_m = Column(Float, nullable=False)
    max_draft_m = Column(Float, nullable=False)

    ships = relationship("Ship", back_populates="port")


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    length_m = Column(Float, nullable=False)
    draft_m = Column(Float, nullable=False)
    pax_capacity = Column(Integer, nullable=False)

    port_id = Column(Integer, ForeignKey("ports.id"), nullable=True)
    port = relationship("Port", back_populates="ships")

    requests = relationship("CruiseRequest", back_populates="ship")


class CruiseRequest(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)

    ship_id = Column(Integer, ForeignKey("ships.id"), nullable=False)
    pax_expected = Column(Integer, nullable=False)

    eta_earliest = Column(Date, nullable=False)
    eta_latest = Column(Date, nullable=False)

    preferred_port = Column(Integer, ForeignKey("ports.id"), nullable=True)
    priority = Column(Integer, nullable=False, default=1)

    ship = relationship("Ship", back_populates="requests")
    port = relationship("Port")


class RuleSet(Base):
    __tablename__ = "rulesets"

    id = Column(Integer, primary_key=True, index=True)

    # polja koja frontend šalje:
    kotor_target_share = Column(Float, nullable=False)
    big_ship_length_threshold = Column(Float, nullable=False)
    big_ship_pax_threshold = Column(Integer, nullable=False)
    bar_big_ship_mandatory = Column(Boolean, nullable=False, default=True)
    max_calls_per_day_per_port = Column(Integer, nullable=False)
