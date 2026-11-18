#!/bin/bash

# Настройки
IFACE="enp3s0f1"
IPADDR="192.168.88.1/24"

echo "[+] Настройка интерфейса $IFACE с IP $IPADDR"

# Удалим старый IP (если есть)
sudo ip addr flush dev $IFACE

# Задаём новый IP и поднимаем интерфейс
sudo ip addr add $IPADDR dev $IFACE
sudo ip link set $IFACE up

echo "[+] Перезапуск isc-dhcp-server"
sudo systemctl restart isc-dhcp-server

# Проверим статус
sudo systemctl status isc-dhcp-server --no-pager

echo "[✓] Готово."
