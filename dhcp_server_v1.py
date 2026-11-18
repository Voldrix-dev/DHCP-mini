#Запускать с sudo
#pip install scapy
#!/usr/bin/env python3

import subprocess
from scapy.all import *
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.layers.dhcp import DHCP, BOOTP

# === НАСТРОЙКИ ===
INTERFACE = "enp3s0f1"
SERVER_IP = "24.10.95.1"
SERVER_CIDR = "24.10.95.1/24"
ASSIGNED_IP = "24.10.95.10"
SUBNET_MASK = "255.255.255.0"
LEASE_TIME = 60

# === ПОДНЯТИЕ IP НА ИНТЕРФЕЙСЕ ===
def assign_ip():
    # Проверим, назначен ли уже IP
    check = subprocess.run(
        ["ip", "addr", "show", INTERFACE],
        stdout=subprocess.PIPE, text=True
    )
    if SERVER_IP in check.stdout:
        print(f"[!] IP {SERVER_IP} уже назначен на {INTERFACE}")
        return

    # Назначаем IP вручную
    print(f"[+] Назначаем IP {SERVER_IP} на интерфейс {INTERFACE}")
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", INTERFACE])
    subprocess.run(["sudo", "ip", "addr", "add", SERVER_CIDR, "dev", INTERFACE])
    subprocess.run(["sudo", "ip", "link", "set", INTERFACE, "up"])

# === ОБРАБОТКА DHCP-ПАКЕТОВ ===
def handle_dhcp(pkt):
    if DHCP in pkt and pkt[DHCP].options[0][1] == 1:  # DHCPDISCOVER
        mac = pkt[Ether].src
        xid = pkt[BOOTP].xid
        chaddr = pkt[BOOTP].chaddr
        print(f"📡 DISCOVER от {mac} — предлагаем {ASSIGNED_IP}")

        ether = Ether(dst=mac, src=get_if_hwaddr(INTERFACE))
        ip = IP(src=SERVER_IP, dst="255.255.255.255")
        udp = UDP(sport=67, dport=68)
        bootp = BOOTP(op=2, yiaddr=ASSIGNED_IP, siaddr=SERVER_IP, chaddr=chaddr, xid=xid)
        dhcp = DHCP(options=[
            ("message-type", "offer"),
            ("server_id", SERVER_IP),
            ("subnet_mask", SUBNET_MASK),
            ("lease_time", LEASE_TIME),
            ("router", SERVER_IP),
            "end"
        ])
        sendp(ether / ip / udp / bootp / dhcp, iface=INTERFACE, verbose=0)

    elif DHCP in pkt and pkt[DHCP].options[0][1] == 3:  # DHCPREQUEST
        mac = pkt[Ether].src
        xid = pkt[BOOTP].xid
        chaddr = pkt[BOOTP].chaddr
        print(f"✅ REQUEST от {mac} — подтверждаем {ASSIGNED_IP}")

        ether = Ether(dst=mac, src=get_if_hwaddr(INTERFACE))
        ip = IP(src=SERVER_IP, dst="255.255.255.255")
        udp = UDP(sport=67, dport=68)
        bootp = BOOTP(op=2, yiaddr=ASSIGNED_IP, siaddr=SERVER_IP, chaddr=chaddr, xid=xid)
        dhcp = DHCP(options=[
            ("message-type", "ack"),
            ("server_id", SERVER_IP),
            ("subnet_mask", SUBNET_MASK),
            ("lease_time", LEASE_TIME),
            ("router", SERVER_IP),
            "end"
        ])
        sendp(ether / ip / udp / bootp / dhcp, iface=INTERFACE, verbose=0)

# === ЗАПУСК ===
if __name__ == "__main__":
    assign_ip()
    print(f"🚀 Мини-DHCP сервер запущен на {INTERFACE} → выдаёт {ASSIGNED_IP}")
    sniff(filter="udp and (port 67 or 68)", iface=INTERFACE, prn=handle_dhcp, store=0)