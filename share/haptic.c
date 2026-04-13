/*
 * Copyright (C) 2026 MiniPutt Mobile Contributors
 *
 * NEVERBALL is  free software; you can redistribute  it and/or modify
 * it under the  terms of the GNU General  Public License as published
 * by the Free  Software Foundation; either version 2  of the License,
 * or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT  ANY  WARRANTY;  without   even  the  implied  warranty  of
 * MERCHANTABILITY or  FITNESS FOR A PARTICULAR PURPOSE.   See the GNU
 * General Public License for more details.
 */

#include "haptic.h"
#include "config.h"

#ifdef ANDROID

#include <jni.h>
#include <SDL.h>

/*
 * Call MySDLActivity.vibrate(float intensity, int lengthMs) directly.
 * This bypasses SDL's haptic handler which requires pollHapticDevices()
 * to have registered the VIBRATOR_SERVICE device first — something that
 * may never happen on a phone without a connected gamepad.
 */

static jclass    activity_class  = NULL;
static jmethodID vibrate_method  = NULL;

void haptic_init(void)
{
    JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

    if (env)
    {
        jclass local = (*env)->FindClass(env,
            "com/miniputt/mobile/MySDLActivity");

        if (local)
        {
            activity_class = (*env)->NewGlobalRef(env, local);
            (*env)->DeleteLocalRef(env, local);

            vibrate_method = (*env)->GetStaticMethodID(env,
                activity_class, "vibrate", "(FI)V");
        }
    }
}

void haptic_free(void)
{
    if (activity_class)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->DeleteGlobalRef(env, activity_class);

        activity_class = NULL;
        vibrate_method = NULL;
    }
}

static void haptic_vibrate(float intensity, int length_ms)
{
    if (!config_get_d(CONFIG_HAPTIC))
        return;

    if (activity_class && vibrate_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
        {
            if (intensity > 1.0f) intensity = 1.0f;
            if (intensity < 0.0f) intensity = 0.0f;

            (*env)->CallStaticVoidMethod(env, activity_class,
                vibrate_method,
                (jfloat) intensity,
                (jint) length_ms);
        }
    }
}

void haptic_bump(float intensity)
{
    haptic_vibrate(0.3f * intensity, 30);
}

void haptic_putt(void)
{
    haptic_vibrate(0.5f, 50);
}

void haptic_goal(void)
{
    haptic_vibrate(0.8f, 150);
}

void haptic_fall(void)
{
    haptic_vibrate(0.6f, 200);
}

void haptic_switch(void)
{
    haptic_vibrate(0.3f, 40);
}

void haptic_jump(void)
{
    haptic_vibrate(0.4f, 60);
}

#else /* !ANDROID */

void haptic_init(void)   { }
void haptic_free(void)   { }

void haptic_bump(float intensity) { (void) intensity; }
void haptic_putt(void)   { }
void haptic_goal(void)   { }
void haptic_fall(void)   { }
void haptic_switch(void) { }
void haptic_jump(void)   { }

#endif
