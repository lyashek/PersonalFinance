"""
FastAPI приложение с локальной SQLite БД для управления банковскими счетами.
Точка входа приложения.

Запуск: python3 main.py
Документация API: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, SessionLocal
from models import Currency, AccountType  # noqa: F401 - импортируем для регистрации моделей
from api import (
    router_banks,
    router_owners,
    router_account_types,
    router_currencies,
    router_accounts,
    router_interest
)


# === Инициализация приложения ===
app = FastAPI(
    title="Банковская система управления счетами",
    description="""
Система для управления банковскими счетами, вкладами и начислением процентов.

## Возможности:
- **Управление справочниками**: Банки, владельцы счетов, типы счетов, валюты
- **Управление счетами**: Создание, редактирование, удаление счетов
- **Начисление процентов**: Расчет и начисление процентов по вкладам
- **Контроль сроков**: Отслеживание истекающих и истекших вкладов
- **Аналитика**: Построение графика доходности по месяцам

## Связи между сущностями:
- Один владелец может иметь несколько счетов в разных банках
- Каждый счет привязан к типу счета, валюте и банку
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Настройка CORS для доступа с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Создание таблиц и начальное заполнение справочников ===
@app.on_event("startup")
def init_database():
    """Создаёт таблицы БД и заполняет начальными данными."""
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


# === Подключение роутеров ===
app.include_router(router_banks)
app.include_router(router_owners)
app.include_router(router_account_types)
app.include_router(router_currencies)
app.include_router(router_accounts)
app.include_router(router_interest)


# === Корневой endpoint ===
@app.get("/", tags=["Главная"])
def root():
    """Информация о приложении и доступных эндпоинтах."""
    return {
        "message": "Система управления банковскими счетами запущена",
        "version": "1.0.0",
        "docs": "/docs - Интерактивная документация Swagger UI",
        "redoc": "/redoc - Документация ReDoc",
        "openapi": "/openapi.json - OpenAPI спецификация",
        "endpoints": {
            "banks": "/banks/ - Управление банками",
            "owners": "/owners/ - Управление владельцами счетов",
            "account_types": "/account-types/ - Управление типами счетов",
            "currencies": "/currencies/ - Управление валютами",
            "accounts": "/accounts/ - Управление счетами",
            "interest_calculation": "/accounts/{id}/calculate-interest/ - Расчет процентов",
            "yield_graph": "/accounts/{id}/yield-graph/ - График доходности",
            "expiring_accounts": "/accounts/expiring/ - Истекающие счета",
            "expired_accounts": "/accounts/expired/ - Истекшие счета"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
