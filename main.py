"""
FastAPI приложение с локальной SQLite БД для управления банковскими счетами.
Реализация требований из README.md:
- Управление справочниками: Банки, владельцы счетов, типы счетов, валюта
- Для каждого владельца может быть несколько счетов в разных банках
- Для счетов можно указать ставку (годовую), валюту, дату начала, срок, банк
- Отслеживание начисления процентов по вкладам и контроль срока окончания вклада
- Вывод графика доходности счетов
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from typing import List, Optional
from datetime import date, timedelta
import uvicorn

# === Конфигурация БД ===
DATABASE_URL = "sqlite:///./local_database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Требуется для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# === Модели БД (ORM) - Справочники ===
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


# === Основная модель - Счет ===
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


# === Pydantic схемы (DTO) - Справочники ===
class BankBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    bik: str = Field(..., min_length=9, max_length=9)
    address: Optional[str] = None


class BankCreate(BankBase):
    pass


class BankResponse(BankBase):
    id: int

    class Config:
        from_attributes = True


class AccountOwnerBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    inn: Optional[str] = Field(None, min_length=10, max_length=12)
    passport: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class AccountOwnerCreate(AccountOwnerBase):
    pass


class AccountOwnerResponse(AccountOwnerBase):
    id: int

    class Config:
        from_attributes = True


class AccountTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class AccountTypeCreate(AccountTypeBase):
    pass


class AccountTypeResponse(AccountTypeBase):
    id: int

    class Config:
        from_attributes = True


class CurrencyBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=3)
    name: str = Field(..., min_length=1, max_length=50)
    symbol: Optional[str] = None


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyResponse(CurrencyBase):
    id: int

    class Config:
        from_attributes = True


# === Pydantic схемы - Счета ===
class AccountBase(BaseModel):
    account_number: str = Field(..., min_length=1, max_length=20)
    owner_id: int
    bank_id: int
    account_type_id: int
    currency_id: int
    balance: float = Field(default=0.0, ge=0)
    annual_rate: Optional[float] = Field(None, ge=0, le=100)
    start_date: date
    term_months: Optional[int] = Field(None, ge=1)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    balance: Optional[float] = Field(None, ge=0)
    annual_rate: Optional[float] = Field(None, ge=0, le=100)
    term_months: Optional[int] = Field(None, ge=1)


class InterestCalculation(BaseModel):
    """Результат расчета процентов"""
    account_id: int
    account_number: str
    principal: float  # Основная сумма
    annual_rate: float
    days_elapsed: int
    accrued_interest: float  # Начисленные проценты
    total_amount: float  # Итого с процентами
    end_date: Optional[date]
    is_expired: bool  # Истек ли срок


class YieldPoint(BaseModel):
    """Точка графика доходности"""
    month: int
    year: int
    interest: float
    cumulative_interest: float
    total_balance: float


class AccountWithDetails(AccountBase):
    id: int
    end_date: Optional[date]
    accrued_interest: float
    owner: AccountOwnerResponse
    bank: BankResponse
    account_type: AccountTypeResponse
    currency: CurrencyResponse

    class Config:
        from_attributes = True


# === Инициализация приложения ===
app = FastAPI(
    title="Банковская система управления счетами",
    description="Система для управления банковскими счетами, вкладами и начислением процентов",
    version="1.0.0"
)


# === Зависимости ===
def get_db():
    """Предоставляет сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === Создание таблиц и начальное заполнение справочников ===
@app.on_event("startup")
def init_database():
    """Создаёт таблицы БД и заполняет начальными данными"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Добавляем базовые валюты если их нет
        default_currencies = [
            {"code": "RUB", "name": "Российский рубль", "symbol": "₽"},
            {"code": "USD", "name": "Доллар США", "symbol": "$"},
            {"code": "EUR", "name": "Евро", "symbol": "€"},
        ]
        for curr in default_currencies:
            if not db.query(Currency).filter(Currency.code == curr["code"]).first():
                db.add(Currency(**curr))
        
        # Добавляем базовые типы счетов если их нет
        default_types = [
            {"name": "Вклад", "description": "Срочный вклад с фиксированной ставкой"},
            {"name": "Текущий", "description": "Расчетный текущий счет"},
            {"name": "Накопительный", "description": "Накопительный счет с возможностью пополнения"},
        ]
        for acc_type in default_types:
            if not db.query(AccountType).filter(AccountType.name == acc_type["name"]).first():
                db.add(AccountType(**acc_type))
        
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


# === Вспомогательные функции ===
def calculate_end_date(start_date: date, term_months: int) -> date:
    """Вычисляет дату окончания вклада"""
    year = start_date.year + (start_date.month + term_months - 1) // 12
    month = (start_date.month + term_months - 1) % 12 + 1
    day = min(start_date.day, 28)  # Безопасный день для любого месяца
    return date(year, month, day)


def calculate_interest(principal: float, annual_rate: float, days: int) -> float:
    """Расчет простых процентов: P * r * t / 365"""
    if annual_rate is None or annual_rate <= 0:
        return 0.0
    return round(principal * annual_rate * days / 36500, 2)  # Делим на 100 для процентов и на 365 дней


# === API Endpoints - Справочники ===

# --- Банки ---
@app.post("/banks/", response_model=BankResponse, status_code=status.HTTP_201_CREATED)
def create_bank(bank: BankCreate, db: Session = Depends(get_db)):
    """Создать новый банк"""
    existing = db.query(Bank).filter(Bank.name == bank.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Банк с таким названием уже существует")
    
    db_bank = Bank(**bank.model_dump())
    db.add(db_bank)
    db.commit()
    db.refresh(db_bank)
    return db_bank


@app.get("/banks/", response_model=List[BankResponse])
def read_banks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех банков"""
    return db.query(Bank).offset(skip).limit(limit).all()


@app.get("/banks/{bank_id}", response_model=BankResponse)
def read_bank(bank_id: int, db: Session = Depends(get_db)):
    """Получить банк по ID"""
    bank = db.query(Bank).filter(Bank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Банк не найден")
    return bank


@app.delete("/banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank(bank_id: int, db: Session = Depends(get_db)):
    """Удалить банк"""
    bank = db.query(Bank).filter(Bank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Банк не найден")
    db.delete(bank)
    db.commit()


# --- Владельцы счетов ---
@app.post("/owners/", response_model=AccountOwnerResponse, status_code=status.HTTP_201_CREATED)
def create_owner(owner: AccountOwnerCreate, db: Session = Depends(get_db)):
    """Создать нового владельца счета"""
    if owner.inn:
        existing = db.query(AccountOwner).filter(AccountOwner.inn == owner.inn).first()
        if existing:
            raise HTTPException(status_code=400, detail="Владелец с таким ИНН уже существует")
    
    db_owner = AccountOwner(**owner.model_dump())
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner


@app.get("/owners/", response_model=List[AccountOwnerResponse])
def read_owners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех владельцев"""
    return db.query(AccountOwner).offset(skip).limit(limit).all()


@app.get("/owners/{owner_id}", response_model=AccountOwnerResponse)
def read_owner(owner_id: int, db: Session = Depends(get_db)):
    """Получить владельца по ID"""
    owner = db.query(AccountOwner).filter(AccountOwner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    return owner


@app.delete("/owners/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    """Удалить владельца"""
    owner = db.query(AccountOwner).filter(AccountOwner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    db.delete(owner)
    db.commit()


# --- Типы счетов ---
@app.post("/account-types/", response_model=AccountTypeResponse, status_code=status.HTTP_201_CREATED)
def create_account_type(acc_type: AccountTypeCreate, db: Session = Depends(get_db)):
    """Создать новый тип счета"""
    existing = db.query(AccountType).filter(AccountType.name == acc_type.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Тип счета с таким названием уже существует")
    
    db_type = AccountType(**acc_type.model_dump())
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


@app.get("/account-types/", response_model=List[AccountTypeResponse])
def read_account_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех типов счетов"""
    return db.query(AccountType).offset(skip).limit(limit).all()


@app.delete("/account-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account_type(type_id: int, db: Session = Depends(get_db)):
    """Удалить тип счета"""
    acc_type = db.query(AccountType).filter(AccountType.id == type_id).first()
    if not acc_type:
        raise HTTPException(status_code=404, detail="Тип счета не найден")
    db.delete(acc_type)
    db.commit()


# --- Валюты ---
@app.post("/currencies/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
def create_currency(currency: CurrencyCreate, db: Session = Depends(get_db)):
    """Создать новую валюту"""
    existing = db.query(Currency).filter(Currency.code == currency.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Валюта с таким кодом уже существует")
    
    db_currency = Currency(**currency.model_dump())
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency


@app.get("/currencies/", response_model=List[CurrencyResponse])
def read_currencies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех валют"""
    return db.query(Currency).offset(skip).limit(limit).all()


@app.delete("/currencies/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(currency_id: int, db: Session = Depends(get_db)):
    """Удалить валюту"""
    currency = db.query(Currency).filter(Currency.id == currency_id).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Валюта не найдена")
    db.delete(currency)
    db.commit()


# === API Endpoints - Счета ===

@app.post("/accounts/", response_model=AccountWithDetails, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Создать новый счет"""
    # Проверяем существование связанных записей
    owner = db.query(AccountOwner).filter(AccountOwner.id == account.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    
    bank = db.query(Bank).filter(Bank.id == account.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Банк не найден")
    
    acc_type = db.query(AccountType).filter(AccountType.id == account.account_type_id).first()
    if not acc_type:
        raise HTTPException(status_code=404, detail="Тип счета не найден")
    
    currency = db.query(Currency).filter(Currency.id == account.currency_id).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Валюта не найдена")
    
    # Проверяем уникальность номера счета
    existing = db.query(Account).filter(Account.account_number == account.account_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Счет с таким номером уже существует")
    
    # Вычисляем дату окончания
    end_date = None
    if account.term_months:
        end_date = calculate_end_date(account.start_date, account.term_months)
    
    db_account = Account(
        **account.model_dump(),
        end_date=end_date,
        accrued_interest=0.0
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@app.get("/accounts/", response_model=List[AccountWithDetails])
def read_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех счетов"""
    return db.query(Account).offset(skip).limit(limit).all()


@app.get("/accounts/{account_id}", response_model=AccountWithDetails)
def read_account(account_id: int, db: Session = Depends(get_db)):
    """Получить счет по ID"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return account


@app.get("/owners/{owner_id}/accounts/", response_model=List[AccountWithDetails])
def read_owner_accounts(owner_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить все счета владельца"""
    owner = db.query(AccountOwner).filter(AccountOwner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    
    return db.query(Account).filter(Account.owner_id == owner_id).offset(skip).limit(limit).all()


@app.put("/accounts/{account_id}", response_model=AccountWithDetails)
def update_account(account_id: int, account_update: AccountUpdate, db: Session = Depends(get_db)):
    """Обновить параметры счета"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    # Пересчитываем дату окончания если изменился срок
    if 'term_months' in update_data and account.term_months:
        account.end_date = calculate_end_date(account.start_date, account.term_months)
    
    db.commit()
    db.refresh(account)
    return account


@app.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Удалить счет"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    db.delete(account)
    db.commit()


# === API Endpoints - Начисление процентов и аналитика ===

@app.post("/accounts/{account_id}/calculate-interest/", response_model=InterestCalculation)
def calculate_account_interest(account_id: int, db: Session = Depends(get_db)):
    """
    Рассчитать начисленные проценты по счету на текущую дату.
    Используется формула простых процентов.
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    if account.annual_rate is None or account.annual_rate <= 0:
        raise HTTPException(status_code=400, detail="По счету не установлена процентная ставка")
    
    today = date.today()
    days_elapsed = (today - account.start_date).days
    
    if days_elapsed < 0:
        raise HTTPException(status_code=400, detail="Дата начала счета в будущем")
    
    accrued = calculate_interest(account.balance, account.annual_rate, days_elapsed)
    total = account.balance + accrued
    
    is_expired = False
    if account.end_date and today > account.end_date:
        is_expired = True
    
    return InterestCalculation(
        account_id=account.id,
        account_number=account.account_number,
        principal=account.balance,
        annual_rate=account.annual_rate,
        days_elapsed=days_elapsed,
        accrued_interest=accrued,
        total_amount=total,
        end_date=account.end_date,
        is_expired=is_expired
    )


@app.post("/accounts/{account_id}/accrue-interest/", response_model=AccountWithDetails)
def accrue_interest(account_id: int, db: Session = Depends(get_db)):
    """
    Начислить проценты на счет (обновить поле accrued_interest).
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    if account.annual_rate is None or account.annual_rate <= 0:
        raise HTTPException(status_code=400, detail="По счету не установлена процентная ставка")
    
    today = date.today()
    days_elapsed = (today - account.start_date).days
    
    if days_elapsed < 0:
        raise HTTPException(status_code=400, detail="Дата начала счета в будущем")
    
    accrued = calculate_interest(account.balance, account.annual_rate, days_elapsed)
    account.accrued_interest = accrued
    
    db.commit()
    db.refresh(account)
    return account


@app.get("/accounts/expiring/", response_model=List[AccountWithDetails])
def get_expiring_accounts(days_ahead: int = 30, db: Session = Depends(get_db)):
    """
    Получить счета, у которых срок окончания истекает в ближайшие N дней.
    """
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    accounts = db.query(Account).filter(
        Account.end_date != None,
        Account.end_date >= today,
        Account.end_date <= future_date
    ).all()
    
    return accounts


@app.get("/accounts/expired/", response_model=List[AccountWithDetails])
def get_expired_accounts(db: Session = Depends(get_db)):
    """
    Получить счета с истекшим сроком.
    """
    today = date.today()
    
    accounts = db.query(Account).filter(
        Account.end_date != None,
        Account.end_date < today
    ).all()
    
    return accounts


@app.get("/accounts/{account_id}/yield-graph/", response_model=List[YieldPoint])
def get_yield_graph(account_id: int, months: int = 12, db: Session = Depends(get_db)):
    """
    Построить график доходности счета по месяцам.
    Возвращает данные о начислении процентов по каждому месяцу.
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    if account.annual_rate is None or account.annual_rate <= 0:
        raise HTTPException(status_code=400, detail="По счету не установлена процентная ставка")
    
    result = []
    cumulative_interest = 0.0
    
    # Определяем период для графика
    start_date = account.start_date
    end_limit = start_date.replace(month=start_date.month + months) if account.term_months is None else account.end_date
    
    if end_limit is None:
        # Если нет даты окончания, строим график на months месяцев вперед
        from dateutil.relativedelta import relativedelta
        end_limit = start_date + relativedelta(months=months)
    
    current_date = start_date
    month_num = 0
    
    while current_date < end_limit and month_num < months:
        month_num += 1
        
        # Определяем конец текущего месяца
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)
        
        # Конец периода для расчета - либо конец месяца, либо дата окончания вклада
        period_end = min(next_month, end_limit)
        days_in_period = (period_end - current_date).days
        
        # Расчет процентов за период
        period_interest = calculate_interest(account.balance, account.annual_rate, days_in_period)
        cumulative_interest += period_interest
        
        result.append(YieldPoint(
            month=next_month.month,
            year=next_month.year,
            interest=round(period_interest, 2),
            cumulative_interest=round(cumulative_interest, 2),
            total_balance=round(account.balance + cumulative_interest, 2)
        ))
        
        current_date = next_month
    
    return result


# === Корневой endpoint ===
@app.get("/")
def root():
    """Информация о приложении"""
    return {
        "message": "Система управления банковскими счетами запущена",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "banks": "/banks/",
            "owners": "/owners/",
            "account_types": "/account-types/",
            "currencies": "/currencies/",
            "accounts": "/accounts/",
            "interest_calculation": "/accounts/{id}/calculate-interest/",
            "yield_graph": "/accounts/{id}/yield-graph/",
            "expiring_accounts": "/accounts/expiring/",
            "expired_accounts": "/accounts/expired/"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
