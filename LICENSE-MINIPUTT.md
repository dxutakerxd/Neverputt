# MiniPutt Mobile - Licensing

## About This Project

MiniPutt Mobile is a mobile port of Neverputt, which is part of the
Neverball open-source project. This derivative work is distributed
under the terms of the GNU General Public License version 3 (GPLv3).

## Original Work

- **Original Project**: Neverball / Neverputt
- **Original Authors**: Robert Kooima and Neverball contributors
- **Original Repository**: https://github.com/Neverball/neverball
- **Mobile Port Base**: https://github.com/drodin/neverball (by Dmitry Rodin)
- **Original License**: GPL v2 or later

## This Derivative Work

- **Project**: MiniPutt Mobile
- **License**: GNU General Public License v3 (GPLv3)
- **Source Code**: https://github.com/dxutakerxd/Neverputt

The full text of GPLv3 is included in `doc/legal/`.

## Your Rights Under GPLv3

You are free to:
- Use this software for any purpose
- Study the source code and modify it
- Redistribute copies
- Distribute modified versions

Under the condition that:
- Any distribution includes the complete corresponding source code
- Any derivative work is also licensed under GPLv3
- All copyright notices and license text are preserved
- No additional restrictions are imposed on recipients

## Modifications Made

This derivative work includes the following high-level changes from the
original:
- Ported and optimized for 2026 mobile phones
- Rebranded from "Neverputt" to "MiniPutt Mobile"
- Updated Android SDK/NDK targets for modern devices
- Added touch-optimized controls and haptic feedback
- Added Google AdMob integration (Java-layer SDK bridged to the C engine via JNI; isolated to the `play` build flavor) and Solana Mobile Wallet Adapter integration
- Hardened the SOL level-data loader against pre-existing binary
  corruption in shipped assets
- Updated build system for current Android / Gradle / CMake toolchain

A detailed, per-area record of modifications (the prominent notices
required by GPL v3 §5(a)) is maintained in [`CHANGES-MINIPUTT.md`](CHANGES-MINIPUTT.md).

## License Interpretation: Bundled Advertising SDK

MiniPutt Mobile's `play` build flavor ships with the Google Mobile Ads
SDK ("AdMob") as a runtime dependency. Because Neverball/Neverputt is
GPL-licensed and AdMob is proprietary, an explicit statement of our
interpretation is appropriate.

**Structural separation.** The GPL-covered C engine (`libneverputt.so`)
does not link against, dynamically load, or directly invoke any AdMob
library. All ad-related calls cross a JNI boundary into a Java class
(`AdManager.java`) that we authored from scratch and which is not
derived from Neverball. The AdMob SDK is invoked only from that Java
layer. No GPL-covered source file `#include`s an AdMob header, and no
GPL-covered object code is statically or dynamically linked against an
AdMob library.

**Interpretation under GPL v3 §1 and §5.** We rely on two related
provisions of GPL v3:

1. The Google Mobile Ads SDK is delivered as part of Google Play
   Services, which is preinstalled on every Google-certified Android
   device and is a normal component of the platform. We treat Google
   Play Services as a "System Library" under GPL v3 §1 — it ships with
   the Android runtime (the Major Component on which the work runs),
   and the AdMob client API constitutes a Standard Interface for which
   a public, documented specification exists. Corresponding Source
   obligations under §1 therefore do not extend to it.
2. Independent of the System Library question, the combination of the
   GPL C engine and the AdMob SDK within a single APK is a "mere
   aggregation" within the meaning of GPL v3 §5: the two works are
   independent, are not by their nature extensions of one another (the
   game is fully functional with no ads), and are packaged together but
   not combined to form a larger program in the derivative-work sense.

**Limits of this interpretation.** We acknowledge that the Free
Software Foundation has taken a stricter position on dynamic linkage in
some of its published guidance, and that no court has ruled on the
application of GPL v3 to runtime SDK bundling on mobile platforms.
Distributors who prefer a stricter reading of the GPL — including
downstream redistributors targeting FSF-aligned distribution channels
such as F-Droid — should use the `dapp` build flavor, which compiles to
a binary that contains no AdMob code, no AdMob Gradle dependency, and
no AdMob runtime symbols. The Java AdManager class in the `dapp` source
set is a stub that exposes the same public API as the AdMob-backed
implementation but performs no ad operations. See
`android/BUILD_VARIANTS.md` for the flavor matrix.

**Source availability.** All GPL-covered source code is published at
https://github.com/dxutakerxd/Neverputt, in compliance with GPL v3 §6.
The AdMob SDK is not GPL-covered and is not included in that source
distribution; users who wish to rebuild the AdMob-containing APK can
obtain the SDK directly from Google under its own license terms.

## Third Party Components

See the original `LICENSE.md` for information about third-party
libraries, fonts, and assets included in the Neverball project.

### Removed Assets
- The Octocat ball (`data/ball/octocat/`) has been removed as its
  special permission from GitHub may not extend to this derivative work.

## Warranty Disclaimer

This program is distributed WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
