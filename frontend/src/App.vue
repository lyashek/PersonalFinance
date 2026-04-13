<template>
  <div id="app">
    <header>
      <h1>Управление счетами</h1>
      <nav>
        <button :class="{ active: currentTab === 'accounts' }" @click="currentTab = 'accounts'">Счета</button>
        <button :class="{ active: currentTab === 'banks' }" @click="currentTab = 'banks'">Банки</button>
        <button :class="{ active: currentTab === 'owners' }" @click="currentTab = 'owners'">Владельцы</button>
        <button :class="{ active: currentTab === 'types' }" @click="currentTab = 'types'">Типы счетов</button>
        <button :class="{ active: currentTab === 'currencies' }" @click="currentTab = 'currencies'">Валюты</button>
        <button :class="{ active: currentTab === 'analytics' }" @click="currentTab = 'analytics'">Аналитика</button>
      </nav>
    </header>

    <main>
      <!-- Счета -->
      <div v-if="currentTab === 'accounts'">
        <CrudTable
          title="Счета"
          :api="accountsApi"
          :columns="accountColumns"
          :form-fields="accountFormFields"
          :default-form-data="defaultAccountData"
          @updated="loadSelectOptions"
        >
          <template #extra-actions>
            <button @click="showExpiringModal = true" class="btn btn-warning">Истекающие</button>
            <button @click="loadExpired" class="btn btn-danger">Просроченные</button>
          </template>
        </CrudTable>
      </div>

      <!-- Банки -->
      <div v-if="currentTab === 'banks'">
        <CrudTable
          title="Банки"
          :api="banksApi"
          :columns="bankColumns"
          :form-fields="bankFormFields"
          :default-form-data="defaultBankData"
        />
      </div>

      <!-- Владельцы -->
      <div v-if="currentTab === 'owners'">
        <CrudTable
          title="Владельцы счетов"
          :api="accountOwnersApi"
          :columns="ownerColumns"
          :form-fields="ownerFormFields"
          :default-form-data="defaultOwnerData"
        />
      </div>

      <!-- Типы счетов -->
      <div v-if="currentTab === 'types'">
        <CrudTable
          title="Типы счетов"
          :api="accountTypesApi"
          :columns="typeColumns"
          :form-fields="typeFormFields"
          :default-form-data="defaultTypeData"
        />
      </div>

      <!-- Валюты -->
      <div v-if="currentTab === 'currencies'">
        <CrudTable
          title="Валюты"
          :api="currenciesApi"
          :columns="currencyColumns"
          :form-fields="currencyFormFields"
          :default-form-data="defaultCurrencyData"
        />
      </div>

      <!-- Аналитика -->
      <div v-if="currentTab === 'analytics'">
        <div class="analytics-section">
          <h2>График доходности</h2>
          <div class="form-group">
            <label for="account-select">Выберите счет:</label>
            <select id="account-select" v-model="selectedAccountId" @change="loadProfitabilitySchedule">
              <option value="">-- Выберите --</option>
              <option v-for="acc in accounts" :key="acc.id" :value="acc.id">
                {{ acc.account_number }} ({{ acc.owner_name }})
              </option>
            </select>
          </div>
          <div v-if="profitabilitySchedule.length > 0">
            <table>
              <thead>
                <tr>
                  <th>Месяц</th>
                  <th>Начисленные проценты</th>
                  <th>Баланс после начисления</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in profitabilitySchedule" :key="item.month">
                  <td>{{ item.month }}</td>
                  <td>{{ formatCurrency(item.interest) }}</td>
                  <td>{{ formatCurrency(item.balance_after) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else-if="selectedAccountId">Нет данных</p>
        </div>
      </div>
    </main>

    <!-- Модальное окно истекающих счетов -->
    <div v-if="showExpiringModal" class="modal-overlay">
      <div class="modal">
        <h3>Счета, истекающие в ближайшие дни</h3>
        <div class="form-group">
          <label for="days-input">Количество дней:</label>
          <input id="days-input" type="number" v-model.number="expiringDays" min="1" />
        </div>
        <button @click="loadExpiringAccounts" class="btn btn-primary">Показать</button>
        <button @click="showExpiringModal = false" class="btn">Закрыть</button>
        
        <div v-if="expiringAccounts.length > 0" class="results">
          <h4>Найдено счетов: {{ expiringAccounts.length }}</h4>
          <ul>
            <li v-for="acc in expiringAccounts" :key="acc.id">
              {{ acc.account_number }} - {{ acc.owner_name }} (до {{ formatDate(acc.end_date) }})
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Модальное окно просроченных счетов -->
    <div v-if="showExpiredModal" class="modal-overlay">
      <div class="modal">
        <h3>Просроченные счета</h3>
        <div v-if="expiredAccounts.length > 0">
          <ul>
            <li v-for="acc in expiredAccounts" :key="acc.id">
              {{ acc.account_number }} - {{ acc.owner_name }} (истек {{ formatDate(acc.end_date) }})
              <button @click="accrueInterest(acc.id)" class="btn btn-sm btn-primary">Начислить проценты</button>
            </li>
          </ul>
        </div>
        <p v-else>Нет просроченных счетов</p>
        <button @click="showExpiredModal = false" class="btn">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
  banksApi,
  accountOwnersApi,
  accountTypesApi,
  currenciesApi,
  accountsApi,
} from './api';
import CrudTable from './components/CrudTable.vue';

const currentTab = ref('accounts');

// Данные для справочников
const banks = ref([]);
const owners = ref([]);
const types = ref([]);
const currencies = ref([]);
const accounts = ref([]);

// Аналитика
const selectedAccountId = ref('');
const profitabilitySchedule = ref([]);

// Модальные окна
const showExpiringModal = ref(false);
const expiringDays = ref(30);
const expiringAccounts = ref([]);

const showExpiredModal = ref(false);
const expiredAccounts = ref([]);

// Конфигурация таблиц
const bankColumns = [
  { key: 'name', label: 'Название' },
  { key: 'bik', label: 'БИК' },
  { key: 'address', label: 'Адрес' },
];

const bankFormFields = [
  { name: 'name', label: 'Название', type: 'text', required: true },
  { name: 'bik', label: 'БИК', type: 'text', required: true },
  { name: 'address', label: 'Адрес', type: 'text', required: true },
];

const ownerColumns = [
  { key: 'full_name', label: 'ФИО' },
  { key: 'inn', label: 'ИНН' },
  { key: 'passport', label: 'Паспорт' },
  { key: 'phone', label: 'Телефон' },
  { key: 'email', label: 'Email' },
];

const ownerFormFields = [
  { name: 'full_name', label: 'ФИО', type: 'text', required: true },
  { name: 'inn', label: 'ИНН', type: 'text', required: true },
  { name: 'passport', label: 'Паспорт', type: 'text', required: true },
  { name: 'phone', label: 'Телефон', type: 'text', required: true },
  { name: 'email', label: 'Email', type: 'email', required: true },
];

const typeColumns = [
  { key: 'name', label: 'Название' },
  { key: 'code', label: 'Код' },
];

const typeFormFields = [
  { name: 'name', label: 'Название', type: 'text', required: true },
  { name: 'code', label: 'Код', type: 'text', required: true },
];

const currencyColumns = [
  { key: 'code', label: 'Код' },
  { key: 'name', label: 'Название' },
  { key: 'symbol', label: 'Символ' },
];

const currencyFormFields = [
  { name: 'code', label: 'Код', type: 'text', required: true },
  { name: 'name', label: 'Название', type: 'text', required: true },
  { name: 'symbol', label: 'Символ', type: 'text', required: true },
];

const accountColumns = [
  { key: 'account_number', label: 'Номер' },
  { key: 'owner_name', label: 'Владелец' },
  { key: 'bank_name', label: 'Банк' },
  { key: 'type_name', label: 'Тип' },
  { key: 'currency_code', label: 'Валюта' },
  { key: 'balance', label: 'Баланс', format: 'currency' },
  { key: 'interest_rate', label: 'Ставка', format: 'percent' },
  { key: 'start_date', label: 'Дата начала', format: 'date' },
  { key: 'end_date', label: 'Дата окончания', format: 'date' },
];

const accountFormFields = [
  { name: 'account_number', label: 'Номер счета', type: 'text', required: true },
  { name: 'owner_id', label: 'Владелец', type: 'select', required: true, options: [] },
  { name: 'bank_id', label: 'Банк', type: 'select', required: true, options: [] },
  { name: 'type_id', label: 'Тип', type: 'select', required: true, options: [] },
  { name: 'currency_id', label: 'Валюта', type: 'select', required: true, options: [] },
  { name: 'balance', label: 'Баланс', type: 'number', required: true, step: '0.01' },
  { name: 'interest_rate', label: 'Годовая ставка (%)', type: 'number', required: true, step: '0.01' },
  { name: 'start_date', label: 'Дата начала', type: 'date', required: true },
  { name: 'term_months', label: 'Срок (месяцев)', type: 'number', required: true },
];

// Данные по умолчанию
const defaultBankData = { name: '', bik: '', address: '' };
const defaultOwnerData = { full_name: '', inn: '', passport: '', phone: '', email: '' };
const defaultTypeData = { name: '', code: '' };
const defaultCurrencyData = { code: '', name: '', symbol: '' };
const defaultAccountData = {
  account_number: '',
  owner_id: '',
  bank_id: '',
  type_id: '',
  currency_id: '',
  balance: 0,
  interest_rate: 0,
  start_date: new Date().toISOString().split('T')[0],
  term_months: 12,
};

// Загрузка опций для select
const loadSelectOptions = async () => {
  try {
    const [ownersRes, banksRes, typesRes, currenciesRes, accountsRes] = await Promise.all([
      accountOwnersApi.getAll(),
      banksApi.getAll(),
      accountTypesApi.getAll(),
      currenciesApi.getAll(),
      accountsApi.getAll(),
    ]);
    
    owners.value = ownersRes.data;
    banks.value = banksRes.data;
    types.value = typesRes.data;
    currencies.value = currenciesRes.data;
    accounts.value = accountsRes.data;

    // Обновляем опции в форме счетов
    accountFormFields[1].options = owners.value.map(o => ({ value: o.id, label: o.full_name }));
    accountFormFields[2].options = banks.value.map(b => ({ value: b.id, label: b.name }));
    accountFormFields[3].options = types.value.map(t => ({ value: t.id, label: t.name }));
    accountFormFields[4].options = currencies.value.map(c => ({ value: c.id, label: `${c.code} (${c.name})` }));
  } catch (error) {
    console.error('Ошибка загрузки справочников:', error);
  }
};

// Загрузка истекающих счетов
const loadExpiringAccounts = async () => {
  try {
    const response = await accountsApi.expiringSoon(expiringDays.value);
    expiringAccounts.value = response.data;
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    alert('Не удалось загрузить данные');
  }
};

// Загрузка просроченных счетов
const loadExpired = async () => {
  try {
    const response = await accountsApi.expired();
    expiredAccounts.value = response.data;
    showExpiredModal.value = true;
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    alert('Не удалось загрузить данные');
  }
};

// Начисление процентов
const accrueInterest = async (accountId) => {
  try {
    await accountsApi.accrueInterest(accountId);
    alert('Проценты начислены');
    await loadSelectOptions();
  } catch (error) {
    console.error('Ошибка начисления:', error);
    alert('Не удалось начислить проценты');
  }
};

// Загрузка графика доходности
const loadProfitabilitySchedule = async () => {
  if (!selectedAccountId.value) {
    profitabilitySchedule.value = [];
    return;
  }
  try {
    const response = await accountsApi.profitabilitySchedule(selectedAccountId.value);
    profitabilitySchedule.value = response.data;
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    profitabilitySchedule.value = [];
  }
};

// Форматирование
const formatCurrency = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(value);
};

const formatDate = (dateStr) => {
  return dateStr ? new Date(dateStr).toLocaleDateString('ru-RU') : '-';
};

onMounted(loadSelectOptions);
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  margin-bottom: 2rem;
}

h1 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

h2 {
  margin-bottom: 1rem;
  color: #34495e;
}

nav {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

nav button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: #e0e0e0;
  font-size: 1rem;
  transition: background 0.2s;
}

nav button.active {
  background: #42b983;
  color: white;
}

nav button:hover {
  background: #d0d0d0;
}

nav button.active:hover {
  background: #3aa876;
}

main {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.analytics-section {
  margin-top: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  max-width: 300px;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.results {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
}

.results ul {
  list-style: none;
  margin-top: 0.5rem;
}

.results li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h3 {
  margin-bottom: 1rem;
}

.modal .form-group {
  margin-bottom: 1rem;
}

.modal button {
  margin-right: 0.5rem;
  margin-top: 0.5rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background: #f5f5f5;
  font-weight: 600;
}
</style>
