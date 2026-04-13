"""API роутеры для взаимодействия с фронтендом."""

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    BankCreate, BankResponse,
    AccountOwnerCreate, AccountOwnerResponse,
    AccountTypeCreate, AccountTypeResponse,
    CurrencyCreate, CurrencyResponse,
    AccountCreate, AccountUpdate, AccountWithDetails,
    InterestCalculation, YieldPoint
)
import crud


# === Роутер для банков ===
router_banks = APIRouter(prefix="/banks", tags=["Справочники: Банки"])


@router_banks.post("/", response_model=BankResponse, status_code=status.HTTP_201_CREATED,
                   summary="Создать банк", description="Создает новый банк в справочнике")
def create_bank(bank: BankCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_bank(db, bank)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_banks.get("/", response_model=List[BankResponse],
                  summary="Получить список банков", description="Возвращает список всех банков с поддержкой пагинации")
def read_banks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_banks(db, skip, limit)


@router_banks.get("/{bank_id}", response_model=BankResponse,
                  summary="Получить банк по ID", description="Возвращает данные банка по его идентификатору")
def read_bank(bank_id: int, db: Session = Depends(get_db)):
    bank = crud.get_bank(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Банк не найден")
    return bank


@router_banks.delete("/{bank_id}", status_code=status.HTTP_204_NO_CONTENT,
                     summary="Удалить банк", description="Удаляет банк из справочника")
def delete_bank(bank_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_bank(db, bank_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === Роутер для владельцев счетов ===
router_owners = APIRouter(prefix="/owners", tags=["Справочники: Владельцы"])


@router_owners.post("/", response_model=AccountOwnerResponse, status_code=status.HTTP_201_CREATED,
                    summary="Создать владельца", description="Создает нового владельца счета")
def create_owner(owner: AccountOwnerCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_owner(db, owner)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_owners.get("/", response_model=List[AccountOwnerResponse],
                   summary="Получить список владельцев", description="Возвращает список всех владельцев с пагинацией")
def read_owners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_owners(db, skip, limit)


@router_owners.get("/{owner_id}", response_model=AccountOwnerResponse,
                   summary="Получить владельца по ID", description="Возвращает данные владельца по его идентификатору")
def read_owner(owner_id: int, db: Session = Depends(get_db)):
    owner = crud.get_owner(db, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    return owner


@router_owners.delete("/{owner_id}", status_code=status.HTTP_204_NO_CONTENT,
                      summary="Удалить владельца", description="Удаляет владельца из справочника")
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_owner(db, owner_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_owners.get("/{owner_id}/accounts/", response_model=List[AccountWithDetails],
                   summary="Получить счета владельца", description="Возвращает все счета указанного владельца")
def read_owner_accounts(owner_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    owner = crud.get_owner(db, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    return crud.get_owner_accounts(db, owner_id, skip, limit)


# === Роутер для типов счетов ===
router_account_types = APIRouter(prefix="/account-types", tags=["Справочники: Типы счетов"])


@router_account_types.post("/", response_model=AccountTypeResponse, status_code=status.HTTP_201_CREATED,
                           summary="Создать тип счета", description="Создает новый тип счета")
def create_account_type(acc_type: AccountTypeCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_account_type(db, acc_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_account_types.get("/", response_model=List[AccountTypeResponse],
                          summary="Получить список типов счетов", description="Возвращает список всех типов счетов")
def read_account_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_account_types(db, skip, limit)


@router_account_types.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT,
                             summary="Удалить тип счета", description="Удаляет тип счета из справочника")
def delete_account_type(type_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_account_type(db, type_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === Роутер для валют ===
router_currencies = APIRouter(prefix="/currencies", tags=["Справочники: Валюты"])


@router_currencies.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED,
                        summary="Создать валюту", description="Создает новую валюту в справочнике")
def create_currency(currency: CurrencyCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_currency(db, currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_currencies.get("/", response_model=List[CurrencyResponse],
                       summary="Получить список валют", description="Возвращает список всех валют")
def read_currencies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_currencies(db, skip, limit)


@router_currencies.delete("/{currency_id}", status_code=status.HTTP_204_NO_CONTENT,
                          summary="Удалить валюту", description="Удаляет валюту из справочника")
def delete_currency(currency_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_currency(db, currency_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === Роутер для счетов ===
router_accounts = APIRouter(prefix="/accounts", tags=["Счета"])


@router_accounts.post("/", response_model=AccountWithDetails, status_code=status.HTTP_201_CREATED,
                      summary="Создать счет", description="Создает новый банковский счет")
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_account(db, account)
    except ValueError as e:
        raise HTTPException(status_code=400 if "уже существует" in str(e) else 404, detail=str(e))


@router_accounts.get("/", response_model=List[AccountWithDetails],
                     summary="Получить список счетов", description="Возвращает список всех счетов с пагинацией")
def read_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_accounts(db, skip, limit)


@router_accounts.get("/{account_id}", response_model=AccountWithDetails,
                     summary="Получить счет по ID", description="Возвращает полные данные о счете включая связанные справочники")
def read_account(account_id: int, db: Session = Depends(get_db)):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return account


@router_accounts.put("/{account_id}", response_model=AccountWithDetails,
                     summary="Обновить счет", description="Обновляет параметры существующего счета")
def update_account(account_id: int, account_update: AccountUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_account(db, account_id, account_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_accounts.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT,
                        summary="Удалить счет", description="Удаляет счет")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_account(db, account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === Роутер для операций с процентами и аналитики ===
router_interest = APIRouter(prefix="/accounts", tags=["Начисление процентов и аналитика"])


@router_interest.post("/{account_id}/calculate-interest/", response_model=InterestCalculation,
                      summary="Рассчитать проценты", description="Рассчитывает начисленные проценты по счету на текущую дату")
def calculate_interest_endpoint(account_id: int, db: Session = Depends(get_db)):
    try:
        return crud.calculate_account_interest(db, account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_interest.post("/{account_id}/accrue-interest/", response_model=AccountWithDetails,
                      summary="Начислить проценты", description="Начисляет проценты на счет (обновляет поле accrued_interest)")
def accrue_interest_endpoint(account_id: int, db: Session = Depends(get_db)):
    try:
        return crud.accrue_interest_on_account(db, account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_interest.get("/expiring/", response_model=List[AccountWithDetails],
                     summary="Истекающие счета", description="Возвращает счета, у которых срок окончания истекает в ближайшие N дней")
def get_expiring_accounts(days_ahead: int = 30, db: Session = Depends(get_db)):
    return crud.get_expiring_accounts(db, days_ahead)


@router_interest.get("/expired/", response_model=List[AccountWithDetails],
                     summary="Истекшие счета", description="Возвращает счета с истекшим сроком")
def get_expired_accounts(db: Session = Depends(get_db)):
    return crud.get_expired_accounts(db)


@router_interest.get("/{account_id}/yield-graph/", response_model=List[YieldPoint],
                     summary="График доходности", description="Построить график доходности счета по месяцам")
def get_yield_graph(account_id: int, months: int = 12, db: Session = Depends(get_db)):
    try:
        return crud.get_yield_graph(db, account_id, months)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
