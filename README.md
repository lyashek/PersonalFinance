# Bank Accounts Service

## Описание
Система управления банковскими счетами и вкладами.

### Функциональные требования:
1. Управление справочниками: Банки, владельцы счетов, типы счетов, валюта.
2. Для каждого владельца может быть несколько счетов в разных банках.
3. Для счетов можно указать ставку (годовую), валюту, дату начала, срок, банк.
4. Необходимо отслеживать начисление процентов по вкладам и контролировать срок окончания вклада.
5. Выводить график доходности счетов.

---

## Развертывание на сервере

### Требования
- Ubuntu/Debian сервер с root-доступом
- Python 3.13
- Node.js и npm

### Быстрый старт (локальный запуск)

Если вы находитесь непосредственно на сервере, где нужно развернуть приложение:

```bash
# Запуск через скрипт деплоя
sudo ./deploy.sh
```

Или вручную через Ansible:

```bash
# Установите Ansible если не установлен
sudo apt update && sudo apt install -y ansible

# Запустите playbook
ansible-playbook -i inventory.ini playbook.yml --become
```

### Ручная установка (без Ansible)

1. **Установка зависимостей:**
```bash
sudo apt update
sudo apt install -y python3.13 python3.13-venv nodejs npm nginx git curl
```

2. **Создание пользователя и директории:**
```bash
sudo groupadd bankapp
sudo useradd -r -g bankapp -d /opt/bankapp -s /bin/bash bankapp
sudo mkdir -p /opt/bankapp
sudo chown bankapp:bankapp /opt/bankapp
```

3. **Копирование файлов:**
```bash
sudo cp *.py requirements.txt /opt/bankapp/
sudo cp -r frontend/ /opt/bankapp/
sudo chown -R bankapp:bankapp /opt/bankapp
```

4. **Настройка виртуального окружения Python:**
```bash
cd /opt/bankapp
sudo -u bankapp python3.13 -m venv venv
sudo -u bankapp ./venv/bin/pip install -r requirements.txt
```

5. **Инициализация базы данных:**
```bash
sudo -u bankapp ./venv/bin/python init_db.py
```

6. **Сборка фронтенда:**
```bash
cd /opt/bankapp/frontend
npm install
npm run build
```

7. **Настройка systemd сервисов:**

Создайте файл `/etc/systemd/system/bankapp-backend.service`:
```ini
[Unit]
Description=Bank Accounts Backend API
After=network.target

[Service]
User=bankapp
Group=bankapp
WorkingDirectory=/opt/bankapp
Environment="PATH=/opt/bankapp/venv/bin"
ExecStart=/opt/bankapp/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

8. **Настройка Nginx:**

Создайте файл `/etc/nginx/sites-available/bankapp`:
```nginx
server {
    listen 80;
    server_name _;

    root /opt/bankapp/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Активируйте сайт:
```bash
sudo ln -s /etc/nginx/sites-available/bankapp /etc/nginx/sites-enabled/bankapp
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

9. **Запуск сервисов:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bankapp-backend
sudo systemctl start bankapp-backend
```

---

## Доступ к приложению

После развертывания сервисы будут доступны по адресам:

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost/docs

---

## Проверка статуса

```bash
# Статус backend сервиса
sudo systemctl status bankapp-backend

# Статус Nginx
sudo systemctl status nginx

# Логи backend
sudo journalctl -u bankapp-backend -f
```