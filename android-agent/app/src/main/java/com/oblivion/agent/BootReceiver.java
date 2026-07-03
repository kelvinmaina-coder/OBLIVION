package com.OBLIVION.agent;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) ||
            Intent.ACTION_QUICKBOOT_POWERON.equals(intent.getAction())) {
            
            // Start service on boot
            OBLIVIONService service = new OBLIVIONService();
            service.start(context);
        }
    }
}