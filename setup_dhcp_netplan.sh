#!/bin/bash

set -e

# === НАСТРОЙКИ ===
IFACE="enp3s0f1"
STATIC_IP="192.168.88.1/24"
SUBNET="192.168.88.0"
NETMASK="255.255.255.0"
RANGE_START="192.168.88.100"
RANGE_END="192.168.88.105"
ROUTER_IP="192.168.88.1"
DNS_IP="8.8.8.8"
NETPLAN_DIR="/etc/netplan"
NETPLAN_FILE="$NETPLAN_DIR/01-dhcp-static.yaml"
DHCP_CONF="/etc/dhcp/dhcpd.conf"
INTERFACES_FILE="/etc/default/isc-dhcp-server"

echo "[1/7] Установка isc-dhcp-server..."
sudo apt update
sudo apt install -y isc-dhcp-server

echo "[2/7] Настройка статического IP через netplan..."

# Резервная копия всех netplan-файлов
sudo mkdir -p "$NETPLAN_DIR/backups"
timestamp=$(date +%Y%m%d_%H%M%S)
sudo cp "$NETPLAN_DIR"/*.yaml "$NETPLAN_DIR/backups/" 2>/dev/null || true
echo "  → Резервные копии сделаны в $NETPLAN_DIR/backups/"

# Создание нового netplan-файла
sudo tee "$NETPLAN_FILE" > /dev/null <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    $IFACE:
      dhcp4: no
      addresses: [$STATIC_IP]
EOF

echo "  → Применение netplan..."
sudo netplan apply

echo "[3/7] Настройка DHCP-сервера..."

if [ -f "$DHCP_CONF" ]; then
    sudo cp "$DHCP_CONF" "${DHCP_CONF}.backup.$timestamp"
    echo "  → Резервная копия DHCP-конфига: ${DHCP_CONF}.backup.$timestamp"
fi

sudo tee "$DHCP_CONF" > /dev/null <<EOF
default-lease-time 60;
max-lease-time 180;
authoritative;

subnet $SUBNET netmask $NETMASK {
    range $RANGE_START $RANGE_END;
    option routers $ROUTER_IP;
    option domain-name-servers $DNS_IP;
}
EOF

echo "[4/7] Настройка интерфейса в /etc/default/isc-dhcp-server..."
if grep -q "^INTERFACESv4=" "$INTERFACES_FILE"; then
    sudo sed -i "s|^INTERFACESv4=.*|INTERFACESv4=\"$IFACE\"|" "$INTERFACES_FILE"
else
    echo "INTERFACESv4=\"$IFACE\"" | sudo tee -a "$INTERFACES_FILE" > /dev/null
fi

echo "[5/7] Перезапуск DHCP-сервера..."
sudo systemctl restart isc-dhcp-server
sudo systemctl enable isc-dhcp-server

echo "[6/7] Проверка статуса:"
sudo systemctl status isc-dhcp-server --no-pager

echo "[7/7] Готово."
echo "✓ Сервер DHCP работает на $IFACE с IP $STATIC_IP"
