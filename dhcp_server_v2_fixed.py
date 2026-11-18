#Запускать с sudo
#pip install scapy
#!/usr/bin/env python3

import subprocess
import atexit
import ipaddress
from scapy.all import *
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.layers.dhcp import DHCP, BOOTP

# === НАСТРОЙКИ ===
INTERFACE = "enp1s0f0"
SERVER_IP = "15.15.15.1"
ASSIGNED_IP = "15.15.15.15"
SUBNET_MASK = "255.255.255.0"
LEASE_TIME = 60


def assign_ip():
    print(f"Назначение IP {SERVER_IP} на интерфейс {INTERFACE}")
    subprocess.run(["ip", "addr", "flush", "dev", INTERFACE], check=True)
    subprocess.run(["ip", "addr", "add", f"{SERVER_IP}/24", "dev", INTERFACE], check=True)
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
