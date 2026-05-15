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

package com.miniputt.mobile;

/**
 * Stub AdManager for the `dapp` build flavor.
 *
 * The `dapp` flavor targets distribution channels (Solana dApp Store,
 * F-Droid-compatible builds, etc.) that do not bundle the proprietary
 * Google Mobile Ads SDK. This class exposes the same public API as the
 * play-flavor AdManager so that the C engine's JNI bridge
 * (`share/ad.c`) can call into it without conditional compilation, but
 * every operation is a no-op or immediate completion: `showInterstitial`
 * reports the ad as already dismissed, and `showRewarded` reports a
 * dismissal without a reward.
 *
 * No `com.google.android.gms.*` symbols are referenced in this file,
 * and the AdMob Gradle dependency is scoped to `playImplementation`,
 * so `dapp` builds compile and link without the AdMob SDK present.
 */
public class AdManager {

    private static volatile int sRewardedState     = 0;
    private static volatile int sInterstitialState = 0;

    public static void init() { /* no-op in dapp flavor */ }

    public static void showInterstitial() {
        /* No proprietary SDK in this flavor — report as already dismissed. */
        sInterstitialState = 2;
    }

    public static void showRewarded() {
        /* No proprietary SDK in this flavor — report dismissal without reward. */
        sRewardedState = 3;
    }

    public static void dismiss() { /* no-op */ }

    public static int  getRewardedState()       { return sRewardedState; }
    public static void resetRewardedState()     { sRewardedState = 0; }

    public static int  getInterstitialState()    { return sInterstitialState; }
    public static void resetInterstitialState()  { sInterstitialState = 0; }
}
