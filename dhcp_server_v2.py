#Запускать с sudo
#pip install scapy
#!/usr/bin/env python3

import subprocess
import atexit
from scapy.all import *
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.layers.dhcp import DHCP, BOOTP

# === НАСТРОЙКИ ===
INTERFACE = "enp3s0f1"
SERVER_IP = "15.15.15.1"
ASSIGNED_IP = "15.15.15.15"
SUBNET_MASK = "255.255.255.0"
LEASE_TIME = 60

def assign_ip():
    print(f"🔧 Назначение IP {SERVER_IP} на интерфейс {INTERFACE}")
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", INTERFACE], check=True)
    subprocess.run(["sudo", "ip", "addr", "add", f"{SERVER_IP}/24", "dev", INTERFACE], check=True)
    subprocess.run(["sudo", "ip", "link", "set", INTERFACE, "up"], check=True)

def cleanup_ip():
    print(f"🧹 Очистка IP с интерфейса {INTERFACE}")
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", INTERFACE], check=False)

atexit.register(cleanup_ip)  # очистка при выходе

def handle_dhcp(pkt):
    if DHCP in pkt:
        dhcp_type = pkt[DHCP].options[0][1]
        mac = pkt[Ether].src
        xid = pkt[BOOTP].xid
        chaddr = pkt[BOOTP].chaddr

        ether = Ether(dst=mac, src=get_if_hwaddr(INTERFACE))
        ip = IP(src=SERVER_IP, dst="255.255.255.255")
        udp = UDP(sport=67, dport=68)
        bootp = BOOTP(op=2, yiaddr=ASSIGNED_IP, siaddr=SERVER_IP, chaddr=chaddr, xid=xid)

        options_common = [
            ("server_id", SERVER_IP),
            ("subnet_mask", SUBNET_MASK),
            ("router", SERVER_IP),
            ("broadcast_address", "15.15.15.255"),
            ("lease_time", LEASE_TIME),
            ("renewal_time", LEASE_TIME // 2),
            ("rebinding_time", int(LEASE_TIME * 0.875)),
            ("name_server", "8.8.8.8"),
        ]

        if dhcp_type == 1:  # DHCPDISCOVER
            print(f"📡 DISCOVER от {mac} — предлагаем {ASSIGNED_IP}")
            dhcp = DHCP(options=[("message-type", "offer")] + options_common + ["end"])

        elif dhcp_type == 3:  # DHCPREQUEST
            print(f"✅ REQUEST от {mac} — подтверждаем {ASSIGNED_IP}")
            dhcp = DHCP(options=[("message-type", "ack")] + options_common + ["end"])
        else:
            return

        sendp(ether / ip / udp / bootp / dhcp, iface=INTERFACE, verbose=0)

# === ПУСК ===
assign_ip()
print(f"🚀 Мини-DHCP сервер запущен на {INTERFACE} → выдаёт {ASSIGNED_IP}")
try:
    sniff(filter="udp and (port 67 or 68)", iface=INTERFACE, prn=handle_dhcp, store=0)
except KeyboardInterrupt:
    print("⏹️  Остановлено пользователем.")