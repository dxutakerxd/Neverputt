package com.miniputt.mobile;

import android.content.Context;
import android.content.res.AssetManager;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;

import org.libsdl.app.SDLActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * MiniPutt Mobile - based on Neverputt
 * Licensed under GPL v3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
 * Original authors: Robert Kooima and Neverball contributors
 * Source code: https://github.com/user/miniputt-mobile
 */
public class MySDLActivity extends SDLActivity {
    private AssetManager assetManager;
    public String baseDir;
    private static Vibrator sVibrator;

    /** Public accessor for the singleton Activity (mSingleton is protected). */
    public static MySDLActivity getActivity() {
        return (MySDLActivity) mSingleton;
    }

    /**
     * Called from native C code (share/haptic.c) via JNI.
     * Directly vibrates the device without going through SDL's haptic handler.
     */
    public static void vibrate(float intensity, int lengthMs) {
        if (sVibrator == null || !sVibrator.hasVibrator())
            return;

        if (intensity <= 0.0f)
            return;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            int amplitude = Math.round(intensity * 255);
            if (amplitude < 1) amplitude = 1;
            if (amplitude > 255) amplitude = 255;
            try {
                sVibrator.vibrate(VibrationEffect.createOneShot(lengthMs, amplitude));
            } catch (Exception e) {
                sVibrator.vibrate(lengthMs);
            }
        } else {
            sVibrator.vibrate(lengthMs);
        }
    }

    public boolean copyAssetFile(String fromAssetPath) {
        try {
            InputStream in = assetManager.open("data/" + fromAssetPath);
            File toFile = new File(baseDir + "/data/" + fromAssetPath);

            if (toFile.exists() && toFile.length() == in.available())
                return true;

            toFile.getParentFile().mkdirs();
            OutputStream out = new FileOutputStream(toFile);
            copyFile(in, out);
            in.close();
            out.flush();
            out.close();
            return true;
        } catch(Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    public boolean copyAsset(String fromAssetPath) {
        if (fromAssetPath.isEmpty())
            return false;

        try {
            String[] files = assetManager.list("data/" + fromAssetPath);
            if (files.length == 0)
                copyAssetFile(fromAssetPath);
            else {
                for (String file : files)
                    copyAsset(fromAssetPath + "/" + file);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
        return true;
    }

    private void copyFile(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[4096];
        int read;
        while((read = in.read(buffer)) != -1){
            out.write(buffer, 0, read);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        assetManager = getApplication().getResources().getAssets();

        File baseFileDir = getApplicationContext().getFilesDir();
        baseFileDir.mkdirs();
        baseDir = baseFileDir.getAbsolutePath();

        sVibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);

        super.onCreate(savedInstanceState);
    }

    @Override
    protected String[] getLibraries() {
        return new String[] {
                "never" + BuildConfig.FLAVOR_version
        };
    }
}
