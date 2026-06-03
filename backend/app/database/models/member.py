# =====================================================================
# Database Member Model Stub - Plum OPD Adjudication
# =====================================================================

from sqlalchemy import Column, Integer, String
from ..database import Base

class MemberModel(Base):
    """
    SQLAlchemy database model stub for covered employees and dependents.
    """
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String, unique=True, index=True, nullable=False)
    member_name = Column(String, nullable=False)
    join_date = Column(String, nullable=False)
