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

#include "wallet.h"

#ifdef ANDROID

#include <jni.h>
#include <string.h>
#include <SDL.h>

static jclass    wallet_class          = NULL;
static jmethodID wallet_init_method    = NULL;
static jmethodID wallet_connect_method = NULL;
static jmethodID wallet_state_method   = NULL;
static jmethodID wallet_seeker_method  = NULL;
static jmethodID wallet_pubkey_method  = NULL;
static jmethodID wallet_disconnect_method = NULL;

static char pubkey_buf[128] = "";

void wallet_init(void)
{
    JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

    if (env)
    {
        jclass local = (*env)->FindClass(env,
            "com/miniputt/mobile/SolanaWalletManager");

        if (local)
        {
            wallet_class = (*env)->NewGlobalRef(env, local);
            (*env)->DeleteLocalRef(env, local);

            wallet_init_method = (*env)->GetStaticMethodID(env,
                wallet_class, "init", "()V");
            wallet_connect_method = (*env)->GetStaticMethodID(env,
                wallet_class, "connect", "()V");
            wallet_state_method = (*env)->GetStaticMethodID(env,
                wallet_class, "getState", "()I");
            wallet_seeker_method = (*env)->GetStaticMethodID(env,
                wallet_class, "isSeeker", "()Z");
            wallet_pubkey_method = (*env)->GetStaticMethodID(env,
                wallet_class, "getPubkey",
                "()Ljava/lang/String;");
            wallet_disconnect_method = (*env)->GetStaticMethodID(env,
                wallet_class, "disconnect", "()V");

            (*env)->CallStaticVoidMethod(env, wallet_class,
                wallet_init_method);
        }
    }
}

void wallet_free(void)
{
    if (wallet_class)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->DeleteGlobalRef(env, wallet_class);

        wallet_class             = NULL;
        wallet_init_method       = NULL;
        wallet_connect_method    = NULL;
        wallet_state_method      = NULL;
        wallet_seeker_method     = NULL;
        wallet_pubkey_method     = NULL;
        wallet_disconnect_method = NULL;
    }
}

void wallet_connect(void)
{
    if (wallet_class && wallet_connect_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, wallet_class,
                wallet_connect_method);
    }
}

int wallet_state(void)
{
    if (wallet_class && wallet_state_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            return (*env)->CallStaticIntMethod(env, wallet_class,
                wallet_state_method);
    }
    return 0;
}

int wallet_is_seeker(void)
{
    if (wallet_class && wallet_seeker_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            return (*env)->CallStaticBooleanMethod(env, wallet_class,
                wallet_seeker_method) ? 1 : 0;
    }
    return 0;
}

const char *wallet_pubkey(void)
{
    if (wallet_class && wallet_pubkey_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
        {
            jstring jstr = (jstring) (*env)->CallStaticObjectMethod(env,
                wallet_class, wallet_pubkey_method);

            if (jstr)
            {
                const char *utf = (*env)->GetStringUTFChars(env, jstr, NULL);

                if (utf)
                {
                    strncpy(pubkey_buf, utf, sizeof (pubkey_buf) - 1);
                    pubkey_buf[sizeof (pubkey_buf) - 1] = '\0';
                    (*env)->ReleaseStringUTFChars(env, jstr, utf);
                }

                (*env)->DeleteLocalRef(env, jstr);
            }

            return pubkey_buf;
        }
    }
    return "";
}

void wallet_disconnect(void)
{
    if (wallet_class && wallet_disconnect_method)
    {
        JNIEnv *env = (JNIEnv *) SDL_AndroidGetJNIEnv();

        if (env)
            (*env)->CallStaticVoidMethod(env, wallet_class,
                wallet_disconnect_method);
    }
}

#else /* !ANDROID */

void        wallet_init(void)       { }
void        wallet_free(void)       { }
void        wallet_connect(void)    { }
int         wallet_state(void)      { return 0; }
int         wallet_is_seeker(void)  { return 0; }
const char *wallet_pubkey(void)     { return ""; }
void        wallet_disconnect(void) { }

#endif
