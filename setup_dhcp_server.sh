#!/bin/bash

set -e

IFACE="enp3s0f1"
STATIC_IP="192.168.88.1/24"
DHCP_CONF="/etc/dhcp/dhcpd.conf"
INTERFACES_FILE="/etc/default/isc-dhcp-server"
SUBNET="192.168.88.0"
NETMASK="255.255.255.0"
RANGE_START="192.168.88.100"
RANGE_END="192.168.88.102"
ROUTER_IP="192.168.88.1"
DNS_IP="8.8.8.8"

echo "[1/6] Установка isc-dhcp-server..."
sudo apt update
sudo apt install -y isc-dhcp-server

echo "[2/6] Настройка интерфейса $IFACE с IP $STATIC_IP..."
sudo ip addr flush dev "$IFACE" || true
sudo ip addr add "$STATIC_IP" dev "$IFACE"
sudo ip link set "$IFACE" up

echo "[3/6] Настройка DHCP-сервера..."

if [ -f "$DHCP_CONF" ]; then
    sudo cp "$DHCP_CONF" "${DHCP_CONF}.backup.$(date +%s)"
    echo "Резервная копия создана: ${DHCP_CONF}.backup.*"
fi

# Минимальная конфигурация DHCP
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

echo "[4/6] Настройка интерфейса в /etc/default/isc-dhcp-server..."
sudo sed -i "s/^INTERFACESv4=.*$/INTERFACESv4=\"$IFACE\"/" "$INTERFACES_FILE" || \
echo "INTERFACESv4=\"$IFACE\"" | sudo tee -a "$INTERFACES_FILE" > /dev/null

echo "[5/6] Перезапуск и включение в автозагрузку..."
sudo systemctl restart isc-dhcp-server
sudo systemctl enable isc-dhcp-server

echo "[6/6] Проверка статуса DHCP-сервера:"
sudo systemctl status isc-dhcp-server --no-pager

echo "[✓] DHCP-сервер успешно установлен и настроен."
