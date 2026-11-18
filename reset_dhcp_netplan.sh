#!/bin/bash

# Скрипт для отката DHCP-сервера и восстановления сетевых настроек netplan
# Работает только если были сделаны бэкапы предыдущим скриптом установки

set -e

echo "🧼 [1/5] Остановка DHCP-сервера..."
sudo systemctl stop isc-dhcp-server || true

echo "🗑 [2/5] Удаление isc-dhcp-server..."
sudo apt remove -y isc-dhcp-server
sudo apt purge -y isc-dhcp-server
sudo apt autoremove -y

echo "📂 [3/5] Восстановление конфигурации netplan..."
BACKUP_DIR="/etc/netplan/backups"
if [ -d "$BACKUP_DIR" ]; then
    echo "→ Директория бэкапов найдена: $BACKUP_DIR"
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "→ Восстановление: $LATEST_BACKUP"
        sudo cp "$BACKUP_DIR/$LATEST_BACKUP" /etc/netplan/
        sudo chmod 600 /etc/netplan/"$LATEST_BACKUP"
    else
        echo "⚠ Нет доступных бэкапов в $BACKUP_DIR"
    fi
else
    echo "⚠ Директория $BACKUP_DIR не найдена!"
fi

echo "🔄 Применение netplan..."
sudo netplan apply || sudo systemctl restart NetworkManager

echo "🧽 [4/5] Очистка DHCP-конфига (если остался)..."
if [ -f /etc/dhcp/dhcpd.conf ]; then
    sudo mv /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.old
    echo "→ Перемещено: /etc/dhcp/dhcpd.conf → .old"
fi

echo "🚮 [5/5] Удаление кастомного netplan (если есть)..."
if [ -f /etc/netplan/01-dhcp-static.yaml ]; then
    sudo rm -f /etc/netplan/01-dhcp-static.yaml
    echo "→ Удалён: 01-dhcp-static.yaml"
fi

echo "✅ Откат завершён. Система очищена от DHCP-сервера и кастомной настройки."
