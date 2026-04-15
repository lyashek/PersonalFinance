#!/bin/bash
# Скрипт для запуска Ansible playbook локально на сервере

set -e

echo "=== Запуск деплоя Bank Accounts Service ==="
echo ""

# Проверка наличия Ansible
if ! command -v ansible-playbook &> /dev/null; then
    echo "Ошибка: Ansible не установлен!"
    echo "Установите Ansible командой:"
    echo "  sudo apt update && sudo apt install -y ansible"
    exit 1
fi

echo "Версия Ansible: $(ansible --version | head -n1)"
echo ""

# Запуск playbook с локальным подключением
echo "Запуск playbook.yml..."
ansible-playbook -i inventory.ini playbook.yml --become

echo ""
echo "=== Деплой завершен успешно! ==="
echo ""
echo "Сервисы доступны по адресам:"
echo "  - Frontend: http://localhost"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost/docs"
echo ""
echo "Для проверки статуса сервисов выполните:"
echo "  sudo systemctl status bankapp-backend"
echo "  sudo systemctl status nginx"
