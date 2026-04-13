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

#include "ad.h"
#include "config.h"

#ifdef ANDROID

#include <jni.h>
#include <SDL.h>

static jclass    ad_manager_class     = NULL;
static jmethodID ad_init_method       = NULL;
static jmethodID ad_interstitial_method = NULL;
static jmethodID ad_rewarded_method   = NULL;
static jmethodID ad_dismiss_method    = NULL;
static jmethodID ad_get_state_method  = NULL;
static jmethodID ad_reset_state_method = NULL;
static jmethodID ad_get_interstitial_state_method   = NULL;
static jmethodID ad_reset_interstitial_state_method  = NULL;

void ad_init(void)
{
    JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

    if (env)
    {
        jclass local = (*env)->FindClass(env,
            "com/miniputt/mobile/AdManager");

        if (local)
        {
            ad_manager_class = (*env)->NewGlobalRef(env, local);
            (*env)->DeleteLocalRef(env, local);

            ad_init_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "init", "()V");
            ad_interstitial_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "showInterstitial", "()V");
            ad_rewarded_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "showRewarded", "()V");
            ad_dismiss_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "dismiss", "()V");
            ad_get_state_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "getRewardedState", "()I");
            ad_reset_state_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "resetRewardedState", "()V");
            ad_get_interstitial_state_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "getInterstitialState", "()I");
            ad_reset_interstitial_state_method = (*env)->GetStaticMethodID(env,
                ad_manager_class, "resetInterstitialState", "()V");

            (*env)->CallStaticVoidMethod(env, ad_manager_class,
                ad_init_method);
        }
    }
}

void ad_free(void)
{
    if (ad_manager_class)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->DeleteGlobalRef(env, ad_manager_class);

        ad_manager_class      = NULL;
        ad_init_method        = NULL;
        ad_interstitial_method = NULL;
        ad_rewarded_method    = NULL;
        ad_dismiss_method     = NULL;
        ad_get_state_method   = NULL;
        ad_reset_state_method = NULL;
        ad_get_interstitial_state_method  = NULL;
        ad_reset_interstitial_state_method = NULL;
    }
}

void ad_show_interstitial(void)
{
    if (config_get_d(CONFIG_AD_FREE))
        return;

    if (ad_manager_class && ad_interstitial_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, ad_manager_class,
                ad_interstitial_method);
    }
}

void ad_show_rewarded(void)
{
    if (config_get_d(CONFIG_AD_FREE))
        return;

    if (ad_manager_class && ad_rewarded_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, ad_manager_class,
                ad_rewarded_method);
    }
}

void ad_dismiss(void)
{
    if (ad_manager_class && ad_dismiss_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, ad_manager_class,
                ad_dismiss_method);
    }
}

int ad_rewarded_state(void)
{
    if (ad_manager_class && ad_get_state_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            return (*env)->CallStaticIntMethod(env, ad_manager_class,
                ad_get_state_method);
    }
    return 0;
}

void ad_rewarded_reset(void)
{
    if (ad_manager_class && ad_reset_state_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, ad_manager_class,
                ad_reset_state_method);
    }
}

int ad_interstitial_state(void)
{
    if (ad_manager_class && ad_get_interstitial_state_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            return (*env)->CallStaticIntMethod(env, ad_manager_class,
                ad_get_interstitial_state_method);
    }
    return 0;
}

void ad_interstitial_reset(void)
{
    if (ad_manager_class && ad_reset_interstitial_state_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, ad_manager_class,
                ad_reset_interstitial_state_method);
    }
}

#else /* !ANDROID */

void ad_init(void)             { }
void ad_free(void)             { }
void ad_show_interstitial(void) { }
void ad_show_rewarded(void)    { }
void ad_dismiss(void)          { }
int  ad_rewarded_state(void)   { return 0; }
void ad_rewarded_reset(void)   { }
int  ad_interstitial_state(void)  { return 0; }
void ad_interstitial_reset(void)  { }

#endif
