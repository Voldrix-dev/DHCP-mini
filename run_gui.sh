#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SCRIPT_DIR/dhcpenv" ]; then
echo "Ошибка: виртуальное окружение dhcpenv не найдено"
exit 1
fi

echo "Запуск GUI DHCP сервера..."
sudo "$SCRIPT_DIR/dhcpenv/bin/python" "$SCRIPT_DIR/dhcp_gui.py"
