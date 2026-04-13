"""Pydantic схемы для валидации данных API (запросы и ответы)."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# === Схемы для справочников ===

class BankBase(BaseModel):
    """Базовая схема для банка."""
    name: str = Field(..., min_length=1, max_length=100, description="Название банка")
    bik: str = Field(..., min_length=9, max_length=9, description="Банковский идентификационный код (9 цифр)")
    address: Optional[str] = Field(None, description="Адрес банка")


class BankCreate(BankBase):
    """Схема для создания банка."""
    pass


class BankResponse(BankBase):
    """Схема ответа с данными банка."""
    id: int

    class Config:
        from_attributes = True


class AccountOwnerBase(BaseModel):
    """Базовая схема для владельца счета."""
    full_name: str = Field(..., min_length=1, max_length=200, description="ФИО владельца")
    inn: Optional[str] = Field(None, min_length=10, max_length=12, description="ИНН (10-12 цифр)")
    passport: Optional[str] = Field(None, description="Паспортные данные")
    phone: Optional[str] = Field(None, description="Телефон")
    email: Optional[str] = Field(None, description="Email")


class AccountOwnerCreate(AccountOwnerBase):
    """Схема для создания владельца счета."""
    pass


class AccountOwnerResponse(AccountOwnerBase):
    """Схема ответа с данными владельца."""
    id: int

    class Config:
        from_attributes = True


class AccountTypeBase(BaseModel):
    """Базовая схема для типа счета."""
    name: str = Field(..., min_length=1, max_length=50, description="Название типа счета")
    description: Optional[str] = Field(None, description="Описание типа счета")


class AccountTypeCreate(AccountTypeBase):
    """Схема для создания типа счета."""
    pass


class AccountTypeResponse(AccountTypeBase):
    """Схема ответа с данными типа счета."""
    id: int

    class Config:
        from_attributes = True


class CurrencyBase(BaseModel):
    """Базовая схема для валюты."""
    code: str = Field(..., min_length=3, max_length=3, description="Код валюты (ISO 4217)")
    name: str = Field(..., min_length=1, max_length=50, description="Название валюты")
    symbol: Optional[str] = Field(None, description="Символ валюты")


class CurrencyCreate(CurrencyBase):
    """Схема для создания валюты."""
    pass


class CurrencyResponse(CurrencyBase):
    """Схема ответа с данными валюты."""
    id: int

    class Config:
        from_attributes = True


# === Схемы для счетов ===

class AccountBase(BaseModel):
    """Базовая схема для счета."""
    account_number: str = Field(..., min_length=1, max_length=20, description="Номер счета")
    owner_id: int = Field(..., description="ID владельца счета")
    bank_id: int = Field(..., description="ID банка")
    account_type_id: int = Field(..., description="ID типа счета")
    currency_id: int = Field(..., description="ID валюты")
    balance: float = Field(default=0.0, ge=0, description="Текущий баланс")
    annual_rate: Optional[float] = Field(None, ge=0, le=100, description="Годовая процентная ставка (%)")
    start_date: date = Field(..., description="Дата начала действия счета")
    term_months: Optional[int] = Field(None, ge=1, description="Срок действия в месяцах")


class AccountCreate(AccountBase):
    """Схема для создания счета."""
    pass


class AccountUpdate(BaseModel):
    """Схема для обновления параметров счета."""
    balance: Optional[float] = Field(None, ge=0, description="Текущий баланс")
    annual_rate: Optional[float] = Field(None, ge=0, le=100, description="Годовая процентная ставка (%)")
    term_months: Optional[int] = Field(None, ge=1, description="Срок действия в месяцах")


class InterestCalculation(BaseModel):
    """Результат расчета процентов по счету."""
    account_id: int = Field(..., description="ID счета")
    account_number: str = Field(..., description="Номер счета")
    principal: float = Field(..., description="Основная сумма вклада")
    annual_rate: float = Field(..., description="Годовая процентная ставка")
    days_elapsed: int = Field(..., description="Количество прошедших дней")
    accrued_interest: float = Field(..., description="Начисленные проценты")
    total_amount: float = Field(..., description="Итоговая сумма с процентами")
    end_date: Optional[date] = Field(None, description="Дата окончания вклада")
    is_expired: bool = Field(..., description="Флаг истечения срока вклада")


class YieldPoint(BaseModel):
    """Точка данных для графика доходности."""
    month: int = Field(..., description="Месяц")
    year: int = Field(..., description="Год")
    interest: float = Field(..., description="Проценты за период")
    cumulative_interest: float = Field(..., description="Накопленные проценты")
    total_balance: float = Field(..., description="Общий баланс с процентами")


class AccountWithDetails(AccountBase):
    """Схема ответа с полными данными о счете включая связанные справочники."""
    id: int
    end_date: Optional[date] = Field(None, description="Дата окончания вклада")
    accrued_interest: float = Field(..., description="Накопленные проценты")
    owner: AccountOwnerResponse = Field(..., description="Данные владельца")
    bank: BankResponse = Field(..., description="Данные банка")
    account_type: AccountTypeResponse = Field(..., description="Тип счета")
    currency: CurrencyResponse = Field(..., description="Валюта счета")

    class Config:
        from_attributes = True
