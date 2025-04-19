from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class ARLocation(Base):
    __tablename__ = "ar_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    name = Column(String)
    description = Column(String)
    meta_data = Column(JSON)
    tags = Column(JSON)
    
    user = relationship("User", back_populates="ar_locations")
    objects = relationship("ARObject", back_populates="location")

class ARObject(Base):
    __tablename__ = "ar_objects"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("ar_locations.id"))
    name = Column(String)
    object_type = Column(String)
    scale = Column(JSON)  # x, y, z
    rotation = Column(JSON)  # x, y, z
    position = Column(JSON)  # x, y, z
    meta_data = Column(JSON)
    tags = Column(JSON)
    
    location = relationship("ARLocation", back_populates="objects")
