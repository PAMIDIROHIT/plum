# =====================================================================
# Database Claim Model Schema - Plum OPD Adjudication
# =====================================================================

from sqlalchemy import Column, Integer, String, Float, Text
from ..database import Base

class ClaimModel(Base):
    """
    SQLAlchemy Database model for processed insurance claims.
    Stores patient demographics, claimed/approved amounts, status decisions,
    rejection reason codes, reasoning traces, and audit logs.
    """
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, unique=True, index=True, nullable=False)
    member_id = Column(String, index=True, nullable=False)
    member_name = Column(String, nullable=False)
    treatment_date = Column(String, nullable=False)
    claim_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, nullable=False)
    decision = Column(String, nullable=False)
    rejection_reasons = Column(Text, default="[]") # Serialized JSON string array
    notes = Column(Text, default="")
    next_steps = Column(Text, default="")
    
    # Store full JSON inputs/outputs for complete debugging/auditing
    raw_input = Column(Text, default="{}") # Serialized input details
    adjudication_meta = Column(Text, default="{}") # Serialized DeepSeek details
