"""
SQLite Database for CRM
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from config.settings import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    company = Column(String(255))
    linkedin_url = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    source = Column(String(50))  # hunter / apollo / manual / csv
    status = Column(String(50), default="new")  # new, drafted, approved, sent, replied, bounced, opted_out
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    emails = relationship("EmailLog", back_populates="contact")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    email_type = Column(String(50))  # initial / followup_1 / followup_2
    subject = Column(String(500))
    body = Column(Text)
    status = Column(String(50), default="draft")  # draft, approved, sent, failed
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="emails")


class Suppression(Base):
    __tablename__ = "suppressions"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    reason = Column(String(100))  # opted_out / bounce / manual
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


# Initialize on import
init_db()