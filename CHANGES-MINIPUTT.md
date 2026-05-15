# Modifications in MiniPutt Mobile

This file documents modifications made to the original Neverball/Neverputt
codebase in this derivative work, satisfying GPL v3 §5(a):

> The work must carry prominent notices stating that you modified it,
> and giving a relevant date.

The original source — both the Neverball/Neverputt upstream and Dmitry
Rodin's Android fork that this work is based on — remains available at:

- Upstream Neverball: https://github.com/Neverball/neverball
- Android fork (drodin): https://github.com/drodin/neverball

Files not listed below are unchanged from the upstream sources.

---

## 2026 — MiniPutt Mobile port

Modifications by the MiniPutt Mobile Contributors, made from February 2026
onward.

### C engine (`share/`, `putt/`, `ball/`)

- **SOL file format loader hardening** (`share/solid_base.c`,
  `share/solid_draw.c`, `putt/game.c`, `ball/game_draw.c`) — added sentinel-pair
  skipping in goal/switch/jump loaders, filesize-based `iv[]` shift detection,
  ball-extras detection, duplicate-ball skipping, zero-radius ball clamping,
  bounds checks in mesh building, and switch-beam color clamps. Fixes runtime
  corruption in pre-compiled `.sol` files shipped with the original data set.
  See `sol-file-fixes.md` for the full incident write-up.
- **Mobile rendering and video** (`share/video.c`, `share/video.h`,
  `share/geom.c`, `share/geom.h`, `share/base_image.c`) — safe-area insets for
  notches and rounded corners, OpenGL ES 1.1 fixups for modern devices.
- **Touch controls** (`putt/game.c`, `putt/game.h`, `putt/hole.c`,
  `putt/hole.h`, `putt/course.c`, `putt/st_all.c`, `putt/st_all.h`,
  `putt/st_conf.c`, `share/gui.c`, `share/tilt_loop.c`) — drag-to-aim,
  tap-SWING-to-putt, touch sensitivity slider, touch-friendly menus, quit
  button on title screen, inverted-aiming fix, SIGSEGV-on-quit fix
  (`game_free` state reset + null guards).
- **Audio** (`share/audio.c`) — fixes to vorbis includes and asset path
  handling for Android.
- **Filesystem** (`share/fs_stdio.c`) — path handling adjustments for
  Android's app-files directory layout.
- **Configuration** (`share/config.c`, `share/config.h`) — added
  `CONFIG_HAPTIC`, `CONFIG_AD_FREE`, `CONFIG_AD_INTERVAL`,
  `CONFIG_WALLET_SEEKER` options, persisted in `neverputt.cfg`.
- **Engine entry points** (`putt/main.c`, `ball/main.c`,
  `ball/game_draw.c`) — JNI initialization wiring, mobile branding updates,
  wallet/ad/haptic system initialization, disabled buggy shadow path on
  mobile.

### New C source files

- `share/haptic.c`, `share/haptic.h` — JNI bridge to Android Vibrator
  service (`VibrationEffect.createOneShot` on API 26+).
- `share/ad.c`, `share/ad.h` — JNI bridge to `AdManager` Java class for
  interstitial and rewarded ads.
- `share/wallet.c`, `share/wallet.h` — JNI bridge to
  `SolanaWalletManager` (Solana Mobile Wallet Adapter, Seeker Genesis Token
  verification); compiled only when `-DENABLE_WALLET=1` is set.

### Android layer (`android/`)

- Package renamed from `com.drodin.neverball` to `com.miniputt.mobile`;
  legacy package directory removed.
- `MySDLActivity.java` rewritten for the new package, with asset path
  traversal guard added and `vibrate()` JNI entry point.
- `AdManager.java` added — JNI bridge to the Google Mobile Ads SDK.
  Lives in the `play` source set (`app/src/play/java/`); a no-op stub
  of the same public API is provided for the `dapp` flavor at
  `app/src/dapp/java/`. The AdMob SDK is referenced only from this Java
  layer, never from any GPL-covered C source. See `LICENSE-MINIPUTT.md`
  for the interpretation of GPL v3 §1 and §5 under which this bundling
  is permitted.
- `SolanaWalletManager.kt` added (Kotlin, MWA + Solana RPC + SGT
  verification, dApp-flavor source set only).
- `AndroidManifest.xml` rewritten with required permissions
  (`INTERNET`, `ACCESS_NETWORK_STATE`, `VIBRATE`), portrait orientation,
  fullscreen theme, MiniPutt Mobile branding.
- Gradle build: `compileSdk 35`, `targetSdk 35`, `minSdk 24`, NDK
  `25.1.8937393`, CMake `3.22.1`, ABI filter for `arm64-v8a` /
  `armeabi-v7a`, two flavor dimensions (`version`: `putt`/`ball`,
  `store`: `play`/`dapp`), release-signing config loaded from
  external `keystore.properties`, `copyGameData` task to stage
  `data/` into Android assets, `-DENABLE_WALLET=ON` passed in dApp
  builds.
- SDL library updated (`org.libsdl.app.*`) to SDL2 2.0.22 from
  upstream SDL2 sources.

### Build system

- `CMakeLists.txt` — added `share/wallet.c` (gated on
  `ENABLE_WALLET`), `share/haptic.c`, `share/ad.c` to `PUTT_SRC` /
  `BALL_SRC`; added `-Wl,-z,max-page-size=16384` link flag required by
  Android 15 / Google Play page-size compliance; `VERSION_NAME` define
  threaded through from Gradle.

### Assets (`data/`)

- **Removed**: `data/ball/octocat/` — GitHub's 2013 Octocat-design
  permission was granted to upstream Neverball; this rebranded derivative
  cannot rely on that permission, so the ball was removed.
  `doc/legal/license-octocat.md` removed for the same reason.
- **Added**: `data/ball/solana-seeker/` — exclusive ball skin for Solana
  Seeker phone owners who verify their Seeker Genesis Token. (Texture is
  currently a placeholder gradient.)
- **Patched in place**: several `.sol` files in `data/map-ckk/` and
  `data/map-iCourse/` had binary-level corruption (misaligned ball/view
  sections, embedded ball entries in jump sections). Patches documented
  in `sol-file-fixes.md`.

### Branding

- App name set to "MiniPutt Mobile".
- App icons (all `mipmap-*` densities) regenerated for the new
  branding.
- BlackBerry / PlayBook icon assets removed (legacy platforms no longer
  targeted).

### Project documentation added

- `LICENSE-MINIPUTT.md` — derivative-work licensing summary (this file's
  parent).
- `CHANGES-MINIPUTT.md` — this file.
- `android/BUILD_VARIANTS.md` — flavor matrix.
- `data/ball/CUSTOM_BALLS.md` — ball-skin authoring notes.
- `AGENTS.md`, `plans.md`, `sol-file-fixes.md`, `wallet-integration.md`,
  `admob.md` — internal engineering notes (not all of these are required
  for source-code redistribution; see the public repository for the
  shipped set).

---

## Earlier history

For modifications made by Dmitry Rodin (the Android fork this work is based
on) and modifications made by upstream Neverball maintainers, see:

- `doc/release-notes.md` — upstream Neverball release notes.
- `doc/authors.txt` — upstream contributor credits.
- The git history of https://github.com/drodin/neverball (the immediate
  parent fork).
- The git history of https://github.com/Neverball/neverball (the original
  project).
