#!/bin/bash
set -e

echo "[1/3] Создание override.conf для isc-dhcp-server..."

OVERRIDE_DIR="/etc/systemd/system/isc-dhcp-server.service.d"
OVERRIDE_FILE="$OVERRIDE_DIR/override.conf"

# Создаём директорию, если не существует
sudo mkdir -p "$OVERRIDE_DIR"

# Записываем настройки
sudo tee "$OVERRIDE_FILE" > /dev/null <<EOF
[Service]
ExecStartPre=/bin/rm -f /var/lib/dhcp/dhcpd.leases
ExecStartPre=/bin/touch /var/lib/dhcp/dhcpd.leases
EOF

echo "[2/3] Перезагрузка systemd..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "[3/3] Перезапуск isc-dhcp-server..."
sudo systemctl restart isc-dhcp-server

echo "✓ Готово. Проверка статуса:"
sudo systemctl status isc-dhcp-server --no-pager

