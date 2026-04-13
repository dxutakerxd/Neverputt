# Build Variants

The Android build uses two Gradle flavor dimensions to produce separate APKs for different games and distribution channels.

## Flavor Dimensions

### `version` — which game

| Flavor | Native target | Description |
|--------|--------------|-------------|
| `ball` | `libneverball.so` | Neverball (obstacle course, tilt controls) |
| `putt` | `libneverputt.so` | Neverputt (mini golf) |

### `store` — distribution channel

| Flavor | Description |
|--------|-------------|
| `dapp` | Solana dApp Store. Includes wallet connect (Solana Mobile Wallet Adapter) and genesis token ball skin (Seeker). |
| `play` | Google Play Store. Clean mini-golf game with ads, no crypto features. |

## Build Commands

```bash
# From drodin-fork/android/

# Neverputt — dApp Store
./gradlew assemblePuttDappDebug
./gradlew assemblePuttDappRelease

# Neverputt — Play Store
./gradlew assemblePuttPlayDebug
./gradlew assemblePuttPlayRelease

# Neverball — dApp Store
./gradlew assembleBallDappDebug
./gradlew assembleBallDappRelease

# Neverball — Play Store
./gradlew assembleBallPlayDebug
./gradlew assembleBallPlayRelease

# All putt variants
./gradlew assemblePutt

# All dapp variants
./gradlew assembleDapp
```

## How It Works

### Gradle (`app/build.gradle`)

- The `dapp` flavor passes `-DENABLE_WALLET=ON` to CMake as an extra argument.
- The `play` flavor passes no wallet-related CMake arguments.
- Solana dependencies use `dappImplementation` scope so they are excluded from `play` builds entirely:
  - `com.solanamobile:mobile-wallet-adapter-clientlib-ktx`
  - `org.jetbrains.kotlinx:kotlinx-coroutines-android`
  - `com.squareup.okhttp3:okhttp`

### CMake (`CMakeLists.txt`)

When `ENABLE_WALLET` is set:
- `share/wallet.c` is appended to the `PUTT_SRC` source list.
- `-DENABLE_WALLET=1` is added as a C preprocessor define.

When not set, `wallet.c` is not compiled and the define does not exist.

### C code guards

All wallet-related C code is wrapped in `#ifdef ENABLE_WALLET`:

- **`putt/main.c`** — `#include "wallet.h"`, `wallet_init()`, seeker ball skin config, `wallet_free()`
- **`putt/st_all.c`** — `#include "wallet.h"`, "Connect Wallet" / "Disconnect Wallet" button in the title screen, `TITLE_WALLET` action handler, entire `st_wallet` state machine and struct
- **`putt/st_all.h`** — `extern struct state st_wallet` declaration

### Java/Kotlin source sets

`SolanaWalletManager.kt` lives in the `dapp`-only source set:

```
app/src/dapp/java/com/miniputt/mobile/SolanaWalletManager.kt
```

Gradle automatically includes `src/dapp/` sources only in `dapp` variant builds. The `play` variant never sees this file.

### Native library loading

`MySDLActivity.getLibraries()` uses `BuildConfig.FLAVOR_version` (not `BuildConfig.FLAVOR`) to load the correct native library. With multi-dimension flavors, `FLAVOR` is the combined name (e.g. `"puttPlay"`) while `FLAVOR_version` gives just `"putt"` or `"ball"`.

## Variant Matrix

| Variant | Task | Wallet | Seeker ball | Solana libs |
|---------|------|--------|-------------|-------------|
| `puttDappDebug` | `assemblePuttDappDebug` | Yes | Yes | Yes |
| `puttDappRelease` | `assemblePuttDappRelease` | Yes | Yes | Yes |
| `puttPlayDebug` | `assemblePuttPlayDebug` | No | No | No |
| `puttPlayRelease` | `assemblePuttPlayRelease` | No | No | No |
| `ballDappDebug` | `assembleBallDappDebug` | No* | No | Yes** |
| `ballPlayDebug` | `assembleBallPlayDebug` | No | No | No |

\* Ball has no wallet code in its C sources, so `ENABLE_WALLET` has no effect.
\** Solana Kotlin/Java deps are still pulled in but unused. This is harmless.
