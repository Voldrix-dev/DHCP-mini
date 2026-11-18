#!/usr/bin/env python3
import sys, subprocess, threading, atexit
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from scapy.all import *
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.layers.dhcp import DHCP, BOOTP
import psutil

class DhcpWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, lan_iface, wan_iface, server_ip, assigned_ip, dns):
        super().__init__()
        self.lan_iface = lan_iface
        self.wan_iface = wan_iface
        self.server_ip = server_ip
        self.assigned_ip = assigned_ip
        self.dns = dns
        self.running = True

    def run(self):
        self.setup_network()
        self.log_signal.emit(f"🚀 DHCP+NAT сервер запущен ({self.lan_iface} → {self.wan_iface})")
        sniff(filter="udp and (port 67 or 68)", iface=self.lan_iface,
              prn=self.handle_dhcp, store=0, stop_filter=lambda _: not self.running)

    def handle_dhcp(self, pkt):
        if DHCP in pkt:
            dhcp_type = pkt[DHCP].options[0][1]
            mac = pkt[Ether].src
            xid = pkt[BOOTP].xid
            chaddr = pkt[BOOTP].chaddr

            ether = Ether(dst=mac, src=get_if_hwaddr(self.lan_iface))
            ip = IP(src=self.server_ip, dst="255.255.255.255")
            udp = UDP(sport=67, dport=68)
            bootp = BOOTP(op=2, yiaddr=self.assigned_ip, siaddr=self.server_ip, chaddr=chaddr, xid=xid)

            base_opts = [
                ("server_id", self.server_ip),
                ("subnet_mask", "255.255.255.0"),
                ("lease_time", 60),
                ("router", self.server_ip),
                ("name_server", self.dns),
            ]

            if dhcp_type == 1:  # DISCOVER
                self.log_signal.emit(f"📡 DISCOVER от {mac} — предлагаем {self.assigned_ip}")
                dhcp = DHCP(options=[("message-type", "offer")] + base_opts + ["end"])
            elif dhcp_type == 3:  # REQUEST
                self.log_signal.emit(f"✅ REQUEST от {mac} — подтверждаем {self.assigned_ip}")
                dhcp = DHCP(options=[("message-type", "ack")] + base_opts + ["end"])
            else:
                return

            sendp(ether / ip / udp / bootp / dhcp, iface=self.lan_iface, verbose=0)

    def setup_network(self):
        subprocess.run(["ip", "addr", "flush", "dev", self.lan_iface], check=True)
        subprocess.run(["ip", "addr", "add", f"{self.server_ip}/24", "dev", self.lan_iface], check=True)
        subprocess.run(["ip", "link", "set", self.lan_iface, "up"], check=True)
        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", self.wan_iface, "-j", "MASQUERADE"], check=True)
        subprocess.run(["iptables", "-A", "FORWARD", "-i", self.lan_iface, "-o", self.wan_iface, "-j", "ACCEPT"], check=True)

    def stop(self):
        self.running = False
        subprocess.run(["iptables", "-t", "nat", "-F"], check=False)
        subprocess.run(["iptables", "-F"], check=False)
        subprocess.run(["ip", "addr", "flush", "dev", self.lan_iface], check=False)
        self.log_signal.emit("⏹️ DHCP сервер остановлен.")


class DhcpGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini DHCP + NAT Server")
        self.setFixedWidth(480)
        layout = QVBoxLayout(self)

        self.ifaces = list(psutil.net_if_addrs().keys())

        # --- Параметры ---
        self.lan_combo = QComboBox(); self.lan_combo.addItems(self.ifaces)
        self.wan_combo = QComboBox(); self.wan_combo.addItems(self.ifaces)

        self.ip_edit = QLineEdit("15.15.15.1")
        self.assigned_edit = QLineEdit("15.15.15.15")
        self.dns_edit = QLineEdit("8.8.8.8")

        layout.addWidget(QLabel("LAN интерфейс:")); layout.addWidget(self.lan_combo)
        layout.addWidget(QLabel("WAN интерфейс:")); layout.addWidget(self.wan_combo)
        layout.addWidget(QLabel("IP сервера:")); layout.addWidget(self.ip_edit)
        layout.addWidget(QLabel("Выдаваемый IP:")); layout.addWidget(self.assigned_edit)
        layout.addWidget(QLabel("DNS:")); layout.addWidget(self.dns_edit)

        # --- Кнопки ---
        btns = QHBoxLayout()
        self.start_btn = QPushButton("▶️ Запустить")
        self.stop_btn = QPushButton("⏹ Остановить")
        self.stop_btn.setEnabled(False)
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        layout.addLayout(btns)

        # --- Логи ---
        self.log = QTextEdit(); self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.worker = None
        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)

    def log_message(self, msg):
        self.log.append(msg)

    def start_server(self):
        lan = self.lan_combo.currentText()
        wan = self.wan_combo.currentText()
        ip = self.ip_edit.text()
        assigned = self.assigned_edit.text()
        dns = self.dns_edit.text()

        self.worker = DhcpWorker(lan, wan, ip, assigned, dns)
        self.worker.log_signal.connect(self.log_message)
        self.worker.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_server(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DhcpGui()
    gui.show()
    sys.exit(app.exec_())
