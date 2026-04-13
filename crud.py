"""Слой бизнес-логики: CRUD операции и расчеты."""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from models import Bank, AccountOwner, AccountType, Currency, Account
from schemas import (
    BankCreate, AccountOwnerCreate, AccountTypeCreate, CurrencyCreate,
    AccountCreate, AccountUpdate, InterestCalculation, YieldPoint
)


# === Вспомогательные функции ===

def calculate_end_date(start_date: date, term_months: int) -> date:
    """Вычисляет дату окончания вклада."""
    year = start_date.year + (start_date.month + term_months - 1) // 12
    month = (start_date.month + term_months - 1) % 12 + 1
    day = min(start_date.day, 28)  # Безопасный день для любого месяца
    return date(year, month, day)


def calculate_interest(principal: float, annual_rate: float, days: int) -> float:
    """Расчет простых процентов: P * r * t / 365."""
    if annual_rate is None or annual_rate <= 0:
        return 0.0
    return round(principal * annual_rate * days / 36500, 2)  # Делим на 100 для процентов и на 365 дней


# === CRUD операции для справочников ===

# --- Банки ---

def get_bank(db: Session, bank_id: int) -> Optional[Bank]:
    """Получить банк по ID."""
    return db.query(Bank).filter(Bank.id == bank_id).first()


def get_banks(db: Session, skip: int = 0, limit: int = 100) -> List[Bank]:
    """Получить список банков с пагинацией."""
    return db.query(Bank).offset(skip).limit(limit).all()


def create_bank(db: Session, bank: BankCreate) -> Bank:
    """Создать новый банк."""
    existing = db.query(Bank).filter(Bank.name == bank.name).first()
    if existing:
        raise ValueError("Банк с таким названием уже существует")
    
    db_bank = Bank(**bank.model_dump())
    db.add(db_bank)
    db.commit()
    db.refresh(db_bank)
    return db_bank


def delete_bank(db: Session, bank_id: int) -> bool:
    """Удалить банк."""
    bank = get_bank(db, bank_id)
    if not bank:
        raise ValueError("Банк не найден")
    db.delete(bank)
    db.commit()
    return True


# --- Владельцы счетов ---

def get_owner(db: Session, owner_id: int) -> Optional[AccountOwner]:
    """Получить владельца по ID."""
    return db.query(AccountOwner).filter(AccountOwner.id == owner_id).first()


def get_owners(db: Session, skip: int = 0, limit: int = 100) -> List[AccountOwner]:
    """Получить список владельцев с пагинацией."""
    return db.query(AccountOwner).offset(skip).limit(limit).all()


def create_owner(db: Session, owner: AccountOwnerCreate) -> AccountOwner:
    """Создать нового владельца счета."""
    if owner.inn:
        existing = db.query(AccountOwner).filter(AccountOwner.inn == owner.inn).first()
        if existing:
            raise ValueError("Владелец с таким ИНН уже существует")
    
    db_owner = AccountOwner(**owner.model_dump())
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner


def delete_owner(db: Session, owner_id: int) -> bool:
    """Удалить владельца."""
    owner = get_owner(db, owner_id)
    if not owner:
        raise ValueError("Владелец не найден")
    db.delete(owner)
    db.commit()
    return True


# --- Типы счетов ---

def get_account_type(db: Session, type_id: int) -> Optional[AccountType]:
    """Получить тип счета по ID."""
    return db.query(AccountType).filter(AccountType.id == type_id).first()


def get_account_types(db: Session, skip: int = 0, limit: int = 100) -> List[AccountType]:
    """Получить список типов счетов с пагинацией."""
    return db.query(AccountType).offset(skip).limit(limit).all()


def create_account_type(db: Session, acc_type: AccountTypeCreate) -> AccountType:
    """Создать новый тип счета."""
    existing = db.query(AccountType).filter(AccountType.name == acc_type.name).first()
    if existing:
        raise ValueError("Тип счета с таким названием уже существует")
    
    db_type = AccountType(**acc_type.model_dump())
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


def delete_account_type(db: Session, type_id: int) -> bool:
    """Удалить тип счета."""
    acc_type = get_account_type(db, type_id)
    if not acc_type:
        raise ValueError("Тип счета не найден")
    db.delete(acc_type)
    db.commit()
    return True


# --- Валюты ---

def get_currency(db: Session, currency_id: int) -> Optional[Currency]:
    """Получить валюту по ID."""
    return db.query(Currency).filter(Currency.id == currency_id).first()


def get_currencies(db: Session, skip: int = 0, limit: int = 100) -> List[Currency]:
    """Получить список валют с пагинацией."""
    return db.query(Currency).offset(skip).limit(limit).all()


def create_currency(db: Session, currency: CurrencyCreate) -> Currency:
    """Создать новую валюту."""
    existing = db.query(Currency).filter(Currency.code == currency.code).first()
    if existing:
        raise ValueError("Валюта с таким кодом уже существует")
    
    db_currency = Currency(**currency.model_dump())
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency


def delete_currency(db: Session, currency_id: int) -> bool:
    """Удалить валюту."""
    currency = get_currency(db, currency_id)
    if not currency:
        raise ValueError("Валюта не найдена")
    db.delete(currency)
    db.commit()
    return True


# === CRUD операции для счетов ===

def get_account(db: Session, account_id: int) -> Optional[Account]:
    """Получить счет по ID."""
    return db.query(Account).filter(Account.id == account_id).first()


def get_accounts(db: Session, skip: int = 0, limit: int = 100) -> List[Account]:
    """Получить список всех счетов с пагинацией."""
    return db.query(Account).offset(skip).limit(limit).all()


def get_owner_accounts(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Account]:
    """Получить все счета владельца."""
    return db.query(Account).filter(Account.owner_id == owner_id).offset(skip).limit(limit).all()


def create_account(db: Session, account: AccountCreate) -> Account:
    """Создать новый счет."""
    # Проверяем существование связанных записей
    owner = get_owner(db, account.owner_id)
    if not owner:
        raise ValueError("Владелец не найден")
    
    bank = get_bank(db, account.bank_id)
    if not bank:
        raise ValueError("Банк не найден")
    
    acc_type = get_account_type(db, account.account_type_id)
    if not acc_type:
        raise ValueError("Тип счета не найден")
    
    currency = get_currency(db, account.currency_id)
    if not currency:
        raise ValueError("Валюта не найдена")
    
    # Проверяем уникальность номера счета
    existing = db.query(Account).filter(Account.account_number == account.account_number).first()
    if existing:
        raise ValueError("Счет с таким номером уже существует")
    
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


def update_account(db: Session, account_id: int, account_update: AccountUpdate) -> Account:
    """Обновить параметры счета."""
    account = get_account(db, account_id)
    if not account:
        raise ValueError("Счет не найден")
    
    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    # Пересчитываем дату окончания если изменился срок
    if 'term_months' in update_data and account.term_months:
        account.end_date = calculate_end_date(account.start_date, account.term_months)
    
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account_id: int) -> bool:
    """Удалить счет."""
    account = get_account(db, account_id)
    if not account:
        raise ValueError("Счет не найден")
    db.delete(account)
    db.commit()
    return True


# === Бизнес-логика: начисление процентов и аналитика ===

def calculate_account_interest(db: Session, account_id: int) -> InterestCalculation:
    """Рассчитать начисленные проценты по счету на текущую дату."""
    account = get_account(db, account_id)
    if not account:
        raise ValueError("Счет не найден")
    
    if account.annual_rate is None or account.annual_rate <= 0:
        raise ValueError("По счету не установлена процентная ставка")
    
    today = date.today()
    days_elapsed = (today - account.start_date).days
    
    if days_elapsed < 0:
        raise ValueError("Дата начала счета в будущем")
    
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


def accrue_interest_on_account(db: Session, account_id: int) -> Account:
    """Начислить проценты на счет (обновить поле accrued_interest)."""
    account = get_account(db, account_id)
    if not account:
        raise ValueError("Счет не найден")
    
    if account.annual_rate is None or account.annual_rate <= 0:
        raise ValueError("По счету не установлена процентная ставка")
    
    today = date.today()
    days_elapsed = (today - account.start_date).days
    
    if days_elapsed < 0:
        raise ValueError("Дата начала счета в будущем")
    
    accrued = calculate_interest(account.balance, account.annual_rate, days_elapsed)
    account.accrued_interest = accrued
    
    db.commit()
    db.refresh(account)
    return account


def get_expiring_accounts(db: Session, days_ahead: int = 30) -> List[Account]:
    """Получить счета, у которых срок окончания истекает в ближайшие N дней."""
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    accounts = db.query(Account).filter(
        Account.end_date != None,
        Account.end_date >= today,
        Account.end_date <= future_date
    ).all()
    
    return accounts


def get_expired_accounts(db: Session) -> List[Account]:
    """Получить счета с истекшим сроком."""
    today = date.today()
    
    accounts = db.query(Account).filter(
        Account.end_date != None,
        Account.end_date < today
    ).all()
    
    return accounts


def get_yield_graph(db: Session, account_id: int, months: int = 12) -> List[YieldPoint]:
    """Построить график доходности счета по месяцам."""
    account = get_account(db, account_id)
    if not account:
        raise ValueError("Счет не найден")
    
    if account.annual_rate is None or account.annual_rate <= 0:
        raise ValueError("По счету не установлена процентная ставка")
    
    result = []
    cumulative_interest = 0.0
    
    # Определяем период для графика
    start_date = account.start_date
    end_limit = account.end_date
    
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
