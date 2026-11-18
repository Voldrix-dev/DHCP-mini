[English](#english) | [Русский](#русский)

---

# DHCP Mini Server

GUI and CLI tools for running a minimal DHCP server on Linux. Written in Python using PySide6/Scapy.

## Features

- Run DHCP server on a selected network interface
- Configure server IP, client-assigned IP, subnet mask, and lease time
- Configuration persistence between runs (`dhcp_config.json`)
- Protection against running on system interfaces (default route, IP assigned, bridge member, WiFi)
- Real-time DHCP packet logging (DISCOVER, REQUEST, ACK, NAK)
- Dark theme (QSS) for GUI

## Requirements

- Linux with root privileges (sudo)
- Python 3.8+
- Required packages:
  - `scapy`
  - `PySide6` (GUI only)
  - `qtawesome` (GUI only)

## Installation

```bash
# Clone
git clone https://github.com/Voldrix-dev/DHCP-mini.git
cd DHCP-mini

# Install dependencies (in virtual environment)
python3 -m venv dhcpenv
source dhcpenv/bin/activate
pip install scapy PySide6 qtawesome

# Or system-wide (not recommended)
sudo pip install scapy PySide6 qtawesome
```

## Running GUI

```bash
# With sudo (required for interface configuration)
sudo dhcpenv/bin/python dhcp_gui.py

# Or using launch script
sudo ./run_gui.sh
```

### GUI Usage

1. Select network interface (system interfaces are hidden automatically)
2. Configure parameters:
   - **Server IP** — DHCP server IP on this interface
   - **Client IP** — IP address to assign to clients
   - **Subnet Mask** — e.g. `255.255.255.0`
   - **Lease Time (sec)** — client lease duration
3. Click **Start**
4. Connect a client to this interface — it will receive an IP via DHCP

## Running CLI

```bash
# Show available interfaces
sudo python3 dhcp_server_cli.py --list-interfaces

# Run with auto-selected interface
sudo python3 dhcp_server_cli.py

# Run with explicit parameters
sudo python3 dhcp_server_cli.py -i enp1s0f0 -s 10.0.0.1 -a 10.0.0.100 -m 255.255.255.0 -l 300

# Help
python3 dhcp_server_cli.py --help
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-i`, `--interface` | Network interface | first available |
| `-s`, `--server-ip` | Server IP address | `15.15.15.1` |
| `-a`, `--assigned-ip` | IP to assign to clients | `15.15.15.15` |
| `-m`, `--subnet-mask` | Subnet mask | `255.255.255.0` |
| `-l`, `--lease-time` | Lease time (seconds) | `60` |
| `--list-interfaces` | List interfaces and exit | — |

## Project Structure

```
DHCP-mini/
├── dhcp_gui.py           # Main GUI application
├── dhcp_server_cli.py    # CLI server version
├── style.qss             # Dark theme styles
├── dhcp_1.svg            # App icon
├── dhcp_2.svg            # Alternative icon
├── README.md             # Documentation
└── .gitignore
```

## How It Works

The application:
1. Flushes IP on the interface and assigns the configured `server_ip/mask`
2. Brings the interface up
3. Listens on UDP ports 67/68 (DHCP)
4. On DISCOVER responds with OFFER using the configured `assigned_ip`
5. On REQUEST responds with ACK (or NAK if client requests a different IP)
6. On stop — cleans up the interface (flush IP, down)

## License

MIT

---

# DHCP Mini Server (Русский)

GUI и CLI инструменты для запуска мини-DHCP сервера на Linux. Написано на Python с использованием PySide6/Scapy.

## Возможности

- Запуск DHCP сервера на выбранном интерфейсе
- Настройка IP сервера, выдаваемого IP клиенту, маски подсети и времени аренды
- Сохранение конфигурации между запусками (файл `dhcp_config.json`)
- Защита от запуска на системных интерфейсах (с default route, IP, в бридже, WiFi)
- Логирование DHCP пакетов (DISCOVER, REQUEST, ACK, NAK)
- Тёмная тема (QSS) для GUI

## Требования

- Linux с правами root (sudo)
- Python 3.8+
- Установленные пакеты:
  - `scapy`
  - `PySide6` (только для GUI)
  - `qtawesome` (только для GUI)

## Установка

```bash
# Клонирование
git clone https://github.com/Voldrix-dev/DHCP-mini.git
cd DHCP-mini

# Установка зависимостей (в виртуальное окружение)
python3 -m venv dhcpenv
source dhcpenv/bin/activate
pip install scapy PySide6 qtawesome

# Или системно (не рекомендуется)
sudo pip install scapy PySide6 qtawesome
```

## Запуск GUI

```bash
# Через sudo (нужно для настройки интерфейсов)
sudo dhcpenv/bin/python dhcp_gui.py

# Или скрипт запуска
sudo ./run_gui.sh
```

### Использование GUI

1. Выберите сетевой интерфейс (системные скрыты автоматически)
2. Настройте параметры:
   - **IP сервера** — IP адрес DHCP сервера на этом интерфейсе
   - **IP клиенту** — адрес, который будет выдан клиенту
   - **Маска подсети** — например `255.255.255.0`
   - **Время аренды (сек)** — время аренды IP клиентом
3. Нажмите **Запустить**
4. Подключите клиент к этому интерфейсу — он получит IP по DHCP

## Запуск CLI

```bash
# Показать доступные интерфейсы
sudo python3 dhcp_server_cli.py --list-interfaces

# Запуск с автовыбором интерфейса
sudo python3 dhcp_server_cli.py

# Запуск с явными параметрами
sudo python3 dhcp_server_cli.py -i enp1s0f0 -s 10.0.0.1 -a 10.0.0.100 -m 255.255.255.0 -l 300

# Справка
python3 dhcp_server_cli.py --help
```

### Аргументы CLI

| Аргумент | Описание | По умолчанию |
|----------|----------|--------------|
| `-i`, `--interface` | Сетевой интерфейс | первый доступный |
| `-s`, `--server-ip` | IP адрес сервера | `15.15.15.1` |
| `-a`, `--assigned-ip` | IP адрес для выдачи клиенту | `15.15.15.15` |
| `-m`, `--subnet-mask` | Маска подсети | `255.255.255.0` |
| `-l`, `--lease-time` | Время аренды (сек) | `60` |
| `--list-interfaces` | Показать интерфейсы и выйти | — |

## Структура проекта

```
DHCP-mini/
├── dhcp_gui.py           # Основной GUI приложение
├── dhcp_server_cli.py    # CLI версия сервера
├── style.qss             # Стили (тёмная тема)
├── dhcp_1.svg            # Иконка приложения
├── dhcp_2.svg            # Альтернативная иконка
├── README.md             # Документация
└── .gitignore
```

## Как это работает

Приложение:
1. Сбрасывает IP на интерфейсе и назначает заданный `server_ip/маска`
2. Поднимает интерфейс
3. Слушает UDP порты 67/68 (DHCP)
4. На DISCOVER отвечает OFFER с заданным `assigned_ip`
5. На REQUEST отвечает ACK (или NAK, если клиент просит другой IP)
6. При остановке — чистит интерфейс (flush IP, down)

## Лицензия

MIT