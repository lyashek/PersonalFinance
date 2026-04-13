import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Справочники
export const banksApi = {
  getAll: () => api.get('/api/banks'),
  getById: (id) => api.get(`/api/banks/${id}`),
  create: (data) => api.post('/api/banks', data),
  update: (id, data) => api.put(`/api/banks/${id}`, data),
  delete: (id) => api.delete(`/api/banks/${id}`),
};

export const accountOwnersApi = {
  getAll: () => api.get('/api/account-owners'),
  getById: (id) => api.get(`/api/account-owners/${id}`),
  create: (data) => api.post('/api/account-owners', data),
  update: (id, data) => api.put(`/api/account-owners/${id}`, data),
  delete: (id) => api.delete(`/api/account-owners/${id}`),
};

export const accountTypesApi = {
  getAll: () => api.get('/api/account-types'),
  getById: (id) => api.get(`/api/account-types/${id}`),
  create: (data) => api.post('/api/account-types', data),
  update: (id, data) => api.put(`/api/account-types/${id}`, data),
  delete: (id) => api.delete(`/api/account-types/${id}`),
};

export const currenciesApi = {
  getAll: () => api.get('/api/currencies'),
  getById: (id) => api.get(`/api/currencies/${id}`),
  create: (data) => api.post('/api/currencies', data),
  update: (id, data) => api.put(`/api/currencies/${id}`, data),
  delete: (id) => api.delete(`/api/currencies/${id}`),
};

// Счета
export const accountsApi = {
  getAll: () => api.get('/api/accounts'),
  getById: (id) => api.get(`/api/accounts/${id}`),
  create: (data) => api.post('/api/accounts', data),
  update: (id, data) => api.put(`/api/accounts/${id}`, data),
  delete: (id) => api.delete(`/api/accounts/${id}`),
  calculateInterest: (id) => api.get(`/api/accounts/${id}/calculate-interest`),
  accrueInterest: (id) => api.post(`/api/accounts/${id}/accrue-interest`),
  expiringSoon: (days) => api.get(`/api/accounts/expiring-soon?days=${days}`),
  expired: () => api.get('/api/accounts/expired'),
  profitabilitySchedule: (id) => api.get(`/api/accounts/${id}/profitability-schedule`),
};
