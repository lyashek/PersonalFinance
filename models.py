"""Модели данных SQLAlchemy для банковских сущностей."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship

from database import Base


class Bank(Base):
    """Справочник: Банки"""
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    bik = Column(String(9), nullable=False)  # Банковский идентификационный код
    address = Column(String(255), nullable=True)

    # Связь со счетами
    accounts = relationship("Account", back_populates="bank", cascade="all, delete-orphan")


class AccountOwner(Base):
    """Справочник: Владельцы счетов"""
    __tablename__ = "account_owners"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    inn = Column(String(12), nullable=True, unique=True)  # ИНН
    passport = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True, unique=True)

    # Связь со счетами (один владелец - много счетов)
    accounts = relationship("Account", back_populates="owner", cascade="all, delete-orphan")


class AccountType(Base):
    """Справочник: Типы счетов"""
    __tablename__ = "account_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # например: "Вклад", "Текущий", "Накопительный"
    description = Column(String(255), nullable=True)

    # Связь со счетами
    accounts = relationship("Account", back_populates="account_type")


class Currency(Base):
    """Справочник: Валюты"""
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), nullable=False, unique=True, index=True)  # RUB, USD, EUR
    name = Column(String(50), nullable=False)  # Рубль, Доллар США, Евро
    symbol = Column(String(5), nullable=True)  # ₽, $, €

    # Связь со счетами
    accounts = relationship("Account", back_populates="currency")


class Account(Base):
    """Таблица: Банковские счета"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(20), nullable=False, unique=True, index=True)  # Номер счета
    
    # Внешние ключи к справочникам
    owner_id = Column(Integer, ForeignKey("account_owners.id"), nullable=False, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=False, index=True)
    account_type_id = Column(Integer, ForeignKey("account_types.id"), nullable=False, index=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False, index=True)
    
    # Параметры счета
    balance = Column(Float, nullable=False, default=0.0)  # Текущий баланс
    annual_rate = Column(Float, nullable=True)  # Годовая процентная ставка (%)
    start_date = Column(Date, nullable=False)  # Дата начала
    term_months = Column(Integer, nullable=True)  # Срок в месяцах
    end_date = Column(Date, nullable=True)  # Дата окончания (вычисляется)
    
    # Накопленные проценты
    accrued_interest = Column(Float, nullable=False, default=0.0)

    # Связи со справочниками
    owner = relationship("AccountOwner", back_populates="accounts")
    bank = relationship("Bank", back_populates="accounts")
    account_type = relationship("AccountType", back_populates="accounts")
    currency = relationship("Currency", back_populates="accounts")
