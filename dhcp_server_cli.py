#!/usr/bin/env python3
# Запускать с sudo
# pip install scapy

import argparse
import sys
import subprocess
import atexit
import ipaddress
from scapy.all import *
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.layers.dhcp import DHCP, BOOTP


def is_system_interface(iface):
    """Проверяет, является ли интерфейс системным (default route, IP, бридж, WiFi)."""
    # WiFi интерфейсы
    if iface.startswith("wl"):
        return True
    try:
        # Default route
        result = subprocess.run(["ip", "route", "show", "default", "dev", iface],
                                capture_output=True, text=True, check=False)
        if result.stdout.strip():
            return True
        # IPv4 адрес (кроме link-local)
        result = subprocess.run(["ip", "-4", "addr", "show", "dev", iface],
                                capture_output=True, text=True, check=False)
        for line in result.stdout.splitlines():
            if "inet " in line and not line.strip().startswith("inet 169.254."):
                return True
        # Бридж (slave или master)
        result = subprocess.run(["ip", "link", "show", "dev", iface],
                                capture_output=True, text=True, check=False)
        output = result.stdout
        if "master " in output:
            return True  # слейв бриджа
        if "master" not in output and "bridge" in output.lower():
            return True  # сам бридж
    except Exception:
        pass
    return False


def get_available_interfaces():
    """Возвращает список доступных несистемных интерфейсов."""
    try:
        interfaces = get_if_list()
        interfaces = [iface for iface in interfaces if iface.strip()]
        # Фильтруем системные
        return [iface for iface in interfaces if not is_system_interface(iface)]
    except Exception:
        return []


def parse_args():
    parser = argparse.ArgumentParser(description="Мини-DHCP сервер (CLI)")
    parser.add_argument("-i", "--interface", default=None,
                        help="Сетевой интерфейс (default: первый доступный)")
    parser.add_argument("-s", "--server-ip", default="15.15.15.1",
                        help="IP адрес сервера (default: 15.15.15.1)")
    parser.add_argument("-a", "--assigned-ip", default="15.15.15.15",
                        help="IP адрес для выдачи клиенту (default: 15.15.15.15)")
    parser.add_argument("-m", "--subnet-mask", default="255.255.255.0",
                        help="Маска подсети (default: 255.255.255.0)")
    parser.add_argument("-l", "--lease-time", type=int, default=60,
                        help="Время аренды в секундах (default: 60)")
    parser.add_argument("--list-interfaces", action="store_true",
                        help="Показать список доступных интерфейсов и выйти")
    return parser.parse_args()


# === НАСТРОЙКИ ===
args = parse_args()

if args.list_interfaces:
    ifaces = get_available_interfaces()
    if ifaces:
        print("Доступные интерфейсы:")
        for iface in ifaces:
            print(f"  {iface}")
    else:
        print("Подходящих интерфейсов не найдено.")
    sys.exit(0)

# Выбор интерфейса по умолчанию
if args.interface is None:
    ifaces = get_available_interfaces()
    if ifaces:
        args.interface = ifaces[0]
        print(f"Интерфейс не указан, используем: {args.interface}")
    else:
        print("Ошибка: не найдено подходящих интерфейсов. Укажите вручную через -i.")
        sys.exit(1)

INTERFACE = args.interface
SERVER_IP = args.server_ip
ASSIGNED_IP = args.assigned_ip
SUBNET_MASK = args.subnet_mask
LEASE_TIME = args.lease_time


def assign_ip():
    print(f"Назначение IP {SERVER_IP} на интерфейс {INTERFACE}")
    subprocess.run(["ip", "addr", "flush", "dev", INTERFACE], check=True)
    # Вычисляем CIDR из маски подсети
    network = ipaddress.IPv4Network(f"{SERVER_IP}/{SUBNET_MASK}", strict=False)
    cidr = network.prefixlen
    subprocess.run(["ip", "addr", "add", f"{SERVER_IP}/{cidr}", "dev", INTERFACE], check=True)
    subprocess.run(["ip", "link", "set", INTERFACE, "up"], check=True)
    # Очистка ARP/neighbor кеша для чистой выдачи фиксированного IP
    subprocess.run(["ip", "neigh", "flush", "dev", INTERFACE], check=False)


def cleanup_ip():
    print(f"Очистка IP с интерфейса {INTERFACE}")
    subprocess.run(["ip", "addr", "flush", "dev", INTERFACE], check=False)
    subprocess.run(["ip", "link", "set", INTERFACE, "down"], check=False)


atexit.register(cleanup_ip)  # очистка при выходе


def get_dhcp_message_type(dhcp_options):
    for opt in dhcp_options:
        if isinstance(opt, tuple) and opt[0] == "message-type":
            return opt[1]
    return None


def get_dhcp_option(dhcp_options, name):
    for opt in dhcp_options:
        if isinstance(opt, tuple) and opt[0] == name:
            return opt[1]
    return None


def compute_broadcast(server_ip, subnet_mask):
    network = ipaddress.IPv4Network(f"{server_ip}/{subnet_mask}", strict=False)
    return str(network.broadcast_address)


def handle_dhcp(pkt):
    if DHCP not in pkt or BOOTP not in pkt or Ether not in pkt:
        return

    dhcp_type = get_dhcp_message_type(pkt[DHCP].options)
    if dhcp_type is None:
        return

    requested_ip = get_dhcp_option(pkt[DHCP].options, "requested_addr")

    mac = pkt[Ether].src
    xid = pkt[BOOTP].xid
    chaddr = pkt[BOOTP].chaddr
    ciaddr = pkt[BOOTP].ciaddr

    ether = Ether(dst=mac, src=get_if_hwaddr(INTERFACE))
    ip = IP(src=SERVER_IP, dst="255.255.255.255")
    udp = UDP(sport=67, dport=68)
    bootp = BOOTP(op=2, yiaddr=ASSIGNED_IP, siaddr=SERVER_IP, chaddr=chaddr, xid=xid)

    broadcast_address = compute_broadcast(SERVER_IP, SUBNET_MASK)

    options_common = [
        ("server_id", SERVER_IP),
        ("subnet_mask", SUBNET_MASK),
        ("router", SERVER_IP),
        ("broadcast_address", broadcast_address),
        ("lease_time", LEASE_TIME),
        ("renewal_time", LEASE_TIME // 2),
        ("rebinding_time", int(LEASE_TIME * 0.875)),
        ("name_server", "8.8.8.8"),
    ]

    if dhcp_type == 1:  # DHCPDISCOVER
        print(f"DISCOVER от {mac} — предлагаем {ASSIGNED_IP}")
        dhcp = DHCP(options=[("message-type", "offer")] + options_common + ["end"])
    elif dhcp_type == 3:  # DHCPREQUEST
        if requested_ip and requested_ip != ASSIGNED_IP:
            print(f"REQUEST от {mac} — просит {requested_ip}, принудительно NAK")
            dhcp = DHCP(options=[("message-type", "nak"), ("server_id", SERVER_IP), "end"])
        elif not requested_ip and ciaddr and ciaddr != "0.0.0.0" and ciaddr != ASSIGNED_IP:
            print(f"REQUEST от {mac} — ciaddr {ciaddr}, принудительно NAK")
            dhcp = DHCP(options=[("message-type", "nak"), ("server_id", SERVER_IP), "end"])
        else:
            print(f"REQUEST от {mac} — подтверждаем {ASSIGNED_IP}")
            dhcp = DHCP(options=[("message-type", "ack")] + options_common + ["end"])
    else:
        return

    sendp(ether / ip / udp / bootp / dhcp, iface=INTERFACE, verbose=0)


# === ПУСК ===
assign_ip()
print(f"Мини-DHCP сервер запущен на {INTERFACE} → выдаёт {ASSIGNED_IP}")
try:
    sniff(filter="udp and (port 67 or 68)", iface=INTERFACE, prn=handle_dhcp, store=0)
except KeyboardInterrupt:
    print("Остановлено пользователем.")
