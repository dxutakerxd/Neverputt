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

import android.app.Activity;
import android.util.Log;

import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.OnUserEarnedRewardListener;
import com.google.android.gms.ads.interstitial.InterstitialAd;
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback;
import com.google.android.gms.ads.rewarded.RewardedAd;
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback;
import com.google.android.gms.ads.rewarded.RewardItem;

public class AdManager {

    private static final String TAG = "AdManager";

    /*
     * AdMob ad unit IDs.
     *
     * Test IDs:
     *   Interstitial: ca-app-pub-3940256099942544/1033173712
     *   Rewarded:     ca-app-pub-3940256099942544/5224354917
     */
    private static final String INTERSTITIAL_AD_UNIT =
        "ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX";  // Replace with your AdMob interstitial unit ID
    private static final String REWARDED_AD_UNIT =
        "ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX";  // Replace with your AdMob rewarded unit ID

    private static InterstitialAd sInterstitialAd;
    private static RewardedAd sRewardedAd;
    private static volatile int sRewardedState = 0;
    private static volatile int sInterstitialState = 0;

    public static void init() {
        final Activity activity = MySDLActivity.getActivity();
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                MobileAds.initialize(activity, initStatus -> {
                    Log.i(TAG, "AdMob initialized");
                    loadInterstitial();
                    loadRewarded();
                });
            }
        });
    }

    private static void loadInterstitial() {
        Activity activity = MySDLActivity.getActivity();
        AdRequest request = new AdRequest.Builder().build();
        InterstitialAd.load(activity, INTERSTITIAL_AD_UNIT,
            request, new InterstitialAdLoadCallback() {
                @Override
                public void onAdLoaded(InterstitialAd ad) {
                    sInterstitialAd = ad;
                    ad.setFullScreenContentCallback(new FullScreenContentCallback() {
                        @Override
                        public void onAdDismissedFullScreenContent() {
                            sInterstitialAd = null;
                            sInterstitialState = 2;
                            loadInterstitial();
                        }

                        @Override
                        public void onAdFailedToShowFullScreenContent(AdError error) {
                            Log.w(TAG, "Interstitial failed to show: " + error.getMessage());
                            sInterstitialAd = null;
                            sInterstitialState = 2;
                            loadInterstitial();
                        }
                    });
                }

                @Override
                public void onAdFailedToLoad(LoadAdError error) {
                    Log.w(TAG, "Interstitial failed to load: " + error.getMessage());
                    sInterstitialAd = null;
                }
            });
    }

    private static void loadRewarded() {
        Activity activity = MySDLActivity.getActivity();
        AdRequest request = new AdRequest.Builder().build();
        RewardedAd.load(activity, REWARDED_AD_UNIT,
            request, new RewardedAdLoadCallback() {
                @Override
                public void onAdLoaded(RewardedAd ad) {
                    sRewardedAd = ad;
                    ad.setFullScreenContentCallback(new FullScreenContentCallback() {
                        @Override
                        public void onAdDismissedFullScreenContent() {
                            sRewardedAd = null;
                            /* If reward wasn't earned, mark as dismissed. */
                            if (sRewardedState == 1)
                                sRewardedState = 3;
                            loadRewarded();
                        }

                        @Override
                        public void onAdFailedToShowFullScreenContent(AdError error) {
                            Log.w(TAG, "Rewarded failed to show: " + error.getMessage());
                            sRewardedAd = null;
                            if (sRewardedState == 1)
                                sRewardedState = 3;
                            loadRewarded();
                        }
                    });
                }

                @Override
                public void onAdFailedToLoad(LoadAdError error) {
                    Log.w(TAG, "Rewarded failed to load: " + error.getMessage());
                    sRewardedAd = null;
                }
            });
    }

    public static void showInterstitial() {
        sInterstitialState = 1;
        final Activity activity = MySDLActivity.getActivity();
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (sInterstitialAd != null) {
                    sInterstitialAd.show(activity);
                } else {
                    Log.i(TAG, "Interstitial not loaded, skipping");
                    sInterstitialState = 2;
                }
            }
        });
    }

    public static void showRewarded() {
        sRewardedState = 1;
        final Activity activity = MySDLActivity.getActivity();
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (sRewardedAd != null) {
                    sRewardedAd.show(activity,
                        new OnUserEarnedRewardListener() {
                            @Override
                            public void onUserEarnedReward(RewardItem reward) {
                                sRewardedState = 2;
                            }
                        });
                } else {
                    /* No ad loaded — dismiss immediately so game continues. */
                    Log.i(TAG, "Rewarded not loaded, dismissing");
                    sRewardedState = 3;
                }
            }
        });
    }

    public static void dismiss() {
        /*
         * AdMob SDK manages its own ad lifecycle — the user closes ads
         * via the SDK's built-in close button. This is kept as a no-op
         * for JNI interface compatibility.
         */
    }

    public static int getRewardedState() {
        return sRewardedState;
    }

    public static void resetRewardedState() {
        sRewardedState = 0;
    }

    public static int getInterstitialState() {
        return sInterstitialState;
    }

    public static void resetInterstitialState() {
        sInterstitialState = 0;
    }
}
