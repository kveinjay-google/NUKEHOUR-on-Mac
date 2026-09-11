# NUKEHOUR on Mac

[NUKE HOUR](https://nukehour.com) for Apple Silicon macOS is an independent,
free and open-source real-time strategy project based on the OpenRA engine.

## Important notice

NUKE HOUR is not affiliated with, endorsed by, sponsored by, or supported by
Electronic Arts, Apple, or Google. This repository contains no commercial game
assets or other third-party retail game files. Players must import compatible
data from a legally purchased copy that they own.

The software is free of charge. If somebody sold it to you, request a refund
and report the seller. Download source code and future notarized releases only
from this repository or the [official NUKE HOUR website](https://nukehour.com).

## Publication status

- Version: **1.0.3 (Build 3)**
- Platform: **Apple Silicon macOS 12 or later**
- Distribution: **Developer ID signed PublicClean DMG and source code**
- Source provenance: `7730020ca7b38feea0ca42db38cfa11c21fbb20c`

The public-clean application package has passed the repository's resource
audit, clean-install gate, launcher verification, and Developer ID signature
verification. The current DMG has not completed Apple notarization, so macOS
may require users to control-click the app and choose Open on first launch.

## Download

Download the audited macOS installer from the
[latest GitHub release](https://github.com/kveinjay-google/NUKEHOUR-on-Mac/releases/latest)
or the [official NUKE HOUR website](https://nukehour.com/downloads.html).

## What is included

- GPL-licensed source code
- Reproducible OpenRA engine patch series
- macOS launcher and PublicClean packaging scripts
- Local content-import workflow
- Automated launcher, packaging, and resource-audit tests

No retail maps, MIX archives, SHP/VXL assets, audio, video, credentials, or
private development artifacts are included. Community news, automatic update
checks, anonymous system-information reporting, and legacy OpenRA public
services are disabled by the macOS launcher; Local Multiplayer and the
NUKE HOUR online lobby remain available.

## Build from source

Prerequisites:

- Apple Silicon Mac running macOS 12 or later
- Xcode Command Line Tools (`clang`, `codesign`, and `hdiutil`)
- .NET SDK capable of building the `net6` target
- Python 3 and PyInstaller 6
- `make`, `curl` or `wget`, and `unzip`

Fetch the pinned OpenRA engine and apply the replayable patch series:

```sh
./fetch-engine.sh
```

Build the game runtime:

```sh
DOTNET_ROLL_FORWARD=Major make \
  RUNTIME=net6 \
  TARGETPLATFORM=osx-arm64 \
  CONFIGURATION=Release \
  all
```

Run the public-source verification profile:

```sh
python3 -m unittest \
  packaging.tests.test_macos_launcher_layout \
  packaging.tests.test_macos_public_clean_launcher \
  packaging.tests.test_launcher_language \
  -q
```

Create and audit a PublicClean DMG locally:

```sh
packaging/macos/build-public-clean.sh --output artifacts/public-macos
```

The generated package contains the application runtime but no retail gameplay
content. On first launch, the user is asked to import compatible files locally
from a legally owned source. Imported files remain on the user's Mac and are
not uploaded by the launcher.

## Documentation

- [Public distribution policy](docs/legal/PUBLIC_DISTRIBUTION.md)
- [Public source export notice](PUBLIC-SOURCE-NOTICE.txt)
- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## License

This source code is licensed under the GNU General Public License, version 3 or
any later version. See [LICENSE](LICENSE).
