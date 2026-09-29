from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    business_name = Column(String)
    business_type = Column(String)  # restaurant, shop, service, etc.
    phone = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)
    subscription_end = Column(DateTime, nullable=True)

    agents = relationship("Agent", back_populates="client")
    leads = relationship("Lead", back_populates="client")
    payments = relationship("Payment", back_populates="client")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    name = Column(String)
    description = Column(Text)
    target_audience = Column(String)
    business_context = Column(Text)
    message_template = Column(Text)
    is_active = Column(Boolean, default=True)
    leads_generated = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="agents")
    leads = relationship("Lead", back_populates="agent")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    lead_name = Column(String)
    lead_contact = Column(String)
    lead_type = Column(String)  # email, phone, telegram
    message_sent = Column(Text)
    response = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, responded, converted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="leads")
    agent = relationship("Agent", back_populates="leads")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    amount = Column(Float)
    currency = Column(String, default="UZS")
    status = Column(String, default="pending")  # pending, completed, failed
    payment_method = Column(String)  # paypal, card, transfer
    transaction_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="payments")

# Создание таблиц
Base.metadata.create_all(bind=engine)
