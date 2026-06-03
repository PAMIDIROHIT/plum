# =====================================================================
# Database Document Model Stub - Plum OPD Adjudication
# =====================================================================

from sqlalchemy import Column, Integer, String, Text
from ..database import Base

class DocumentModel(Base):
    """
    SQLAlchemy database model stub for uploaded document text attachments.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, index=True, nullable=False)
    document_type = Column(String, nullable=False) # e.g. "prescription", "invoice"
    raw_text = Column(Text, default="")
