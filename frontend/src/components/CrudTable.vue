<template>
  <div class="crud-table">
    <h2>{{ title }}</h2>
    
    <div class="actions">
      <button @click="showCreateForm = true" class="btn btn-primary">Добавить</button>
      <slot name="extra-actions"></slot>
    </div>

    <table v-if="items.length > 0">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
          <th>Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td v-for="column in columns" :key="column.key">
            {{ formatValue(item[column.key], column.format) }}
          </td>
          <td>
            <button @click="editItem(item)" class="btn btn-sm">Изменить</button>
            <button @click="deleteItem(item.id)" class="btn btn-sm btn-danger">Удалить</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>Нет данных</p>

    <!-- Форма создания/редактирования -->
    <div v-if="showCreateForm || editingItem" class="modal-overlay">
      <div class="modal">
        <h3>{{ editingItem ? 'Редактирование' : 'Создание' }}</h3>
        <form @submit.prevent="saveItem">
          <div v-for="field in formFields" :key="field.name" class="form-group">
            <label :for="field.name">{{ field.label }}</label>
            <input
              v-if="field.type === 'number'"
              :id="field.name"
              v-model.number="formData[field.name]"
              :type="field.type"
              :required="field.required"
              :step="field.step || 'any'"
            />
            <input
              v-else-if="field.type === 'date'"
              :id="field.name"
              v-model="formData[field.name]"
              type="date"
              :required="field.required"
            />
            <select
              v-else-if="field.type === 'select'"
              :id="field.name"
              v-model="formData[field.name]"
              :required="field.required"
            >
              <option value="">Выберите...</option>
              <option v-for="opt in field.options" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
            <input
              v-else
              :id="field.name"
              v-model="formData[field.name]"
              :type="field.type || 'text'"
              :required="field.required"
            />
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn btn-primary">Сохранить</button>
            <button type="button" @click="closeForm" class="btn">Отмена</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
  title: String,
  api: Object,
  columns: Array,
  formFields: Array,
  defaultFormData: Object,
});

const emit = defineEmits(['updated']);

const items = ref([]);
const showCreateForm = ref(false);
const editingItem = ref(null);
const formData = ref({});

const loadItems = async () => {
  try {
    const response = await props.api.getAll();
    items.value = response.data;
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    alert('Не удалось загрузить данные');
  }
};

const editItem = (item) => {
  editingItem.value = item;
  formData.value = { ...props.defaultFormData, ...item };
  showCreateForm.value = true;
};

const closeForm = () => {
  showCreateForm.value = false;
  editingItem.value = null;
  formData.value = { ...props.defaultFormData };
};

const saveItem = async () => {
  try {
    if (editingItem.value) {
      await props.api.update(editingItem.value.id, formData.value);
    } else {
      await props.api.create(formData.value);
    }
    closeForm();
    await loadItems();
    emit('updated');
  } catch (error) {
    console.error('Ошибка сохранения:', error);
    alert('Не удалось сохранить данные: ' + (error.response?.data?.detail || error.message));
  }
};

const deleteItem = async (id) => {
  if (!confirm('Вы уверены?')) return;
  try {
    await props.api.delete(id);
    await loadItems();
    emit('updated');
  } catch (error) {
    console.error('Ошибка удаления:', error);
    alert('Не удалось удалить');
  }
};

const formatValue = (value, format) => {
  if (format === 'currency') {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(value);
  }
  if (format === 'percent') {
    return value + '%';
  }
  if (format === 'date') {
    return value ? new Date(value).toLocaleDateString('ru-RU') : '-';
  }
  return value;
};

onMounted(loadItems);
</script>

<style scoped>
.crud-table {
  margin-bottom: 2rem;
}

.actions {
  margin-bottom: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
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

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: #e0e0e0;
  margin-right: 0.5rem;
}

.btn-primary {
  background: #42b983;
  color: white;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
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
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
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
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.modal-actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 0.5rem;
}
</style>
