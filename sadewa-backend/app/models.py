from sqlalchemy import Column, String, Text
from app.database import Base

class ICD10(Base):
    __tablename__ = "icds"
    
    code = Column(String(255), primary_key=True, index=True)
    name_en = Column(Text, nullable=False)
    name_id = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<ICD10(code='{self.code}', name_id='{self.name_id}')>"