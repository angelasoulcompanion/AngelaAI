#!/usr/bin/env bash
# testflight_deploy.sh — archive + upload an xcodegen iOS app to TestFlight
# in one shot, using the App Store Connect API key stored in local our_secrets.
#
# Usage:
#   testflight_deploy.sh <project-dir> <scheme> [--bump]
#
#   <project-dir>  dir containing project.yml (e.g. ~/PycharmProjects/angelora/ios-studio)
#   <scheme>       Xcode scheme = target name (e.g. AngeloraStudio, SanJunipero)
#   --bump         auto-increment CURRENT_PROJECT_VERSION in project.yml before building
#
# Key material: Key ID + Issuer read from our_secrets; .p8 auto-discovered at
# ~/.appstoreconnect/private_keys/AuthKey_<KeyID>.p8
set -euo pipefail

PROJECT_DIR="${1:?need project dir}"
SCHEME="${2:?need scheme}"
BUMP="${3:-}"
AAI=/Users/davidsamanyaporn/PycharmProjects/AngelaAI

cd "$PROJECT_DIR"
[ -f project.yml ] || { echo "❌ no project.yml in $PROJECT_DIR"; exit 1; }

# --- read key material from local our_secrets ---
read -r KEY_ID ISSUER < <(python3 - <<PY
import asyncio, sys
sys.path.insert(0, "$AAI")
from angela_core.database import get_secret
async def main():
    kid = await get_secret("asc_api_key_id")
    iss = await get_secret("asc_api_issuer_id")
    print(kid, iss)
asyncio.run(main())
PY
)
[ -n "$KEY_ID" ] && [ "$KEY_ID" != "None" ] || { echo "❌ asc_api_key_id not in our_secrets"; exit 1; }
P8="$HOME/.appstoreconnect/private_keys/AuthKey_${KEY_ID}.p8"
[ -f "$P8" ] || { echo "❌ .p8 missing at $P8"; exit 1; }
echo "🔑 Key $KEY_ID · Issuer ${ISSUER:0:8}… · $P8"

# --- optional build-number bump ---
if [ "$BUMP" = "--bump" ]; then
  CUR=$(grep -E 'CURRENT_PROJECT_VERSION:' project.yml | head -1 | grep -oE '[0-9]+')
  NEW=$((CUR + 1))
  sed -i '' "s/CURRENT_PROJECT_VERSION: \"$CUR\"/CURRENT_PROJECT_VERSION: \"$NEW\"/" project.yml
  echo "⬆️  build $CUR → $NEW"
fi

# --- regenerate + archive ---
xcodegen
TS=$(date +%H%M%S); D=$(date +%Y-%m-%d)
ARCH="$HOME/Library/Developer/Xcode/Archives/$D/${SCHEME}-${TS}.xcarchive"
echo "📦 archiving → $ARCH"
xcodebuild -project "${SCHEME}.xcodeproj" -scheme "$SCHEME" \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath "$ARCH" clean archive -allowProvisioningUpdates -quiet

VER=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$ARCH/Products/Applications/${SCHEME}.app/Info.plist")
BLD=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$ARCH/Products/Applications/${SCHEME}.app/Info.plist")
echo "✅ archived $VER ($BLD)"

# --- export + upload to App Store Connect ---
OUT=$(mktemp -d)
cat > "$OUT/ExportOptions.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>method</key><string>app-store-connect</string>
  <key>destination</key><string>upload</string>
  <key>teamID</key><string>AR3CL49CUL</string>
  <key>signingStyle</key><string>automatic</string>
</dict></plist>
PLIST

echo "🚀 uploading to TestFlight…"
xcodebuild -exportArchive \
  -archivePath "$ARCH" \
  -exportPath "$OUT" \
  -exportOptionsPlist "$OUT/ExportOptions.plist" \
  -allowProvisioningUpdates \
  -authenticationKeyPath "$P8" \
  -authenticationKeyID "$KEY_ID" \
  -authenticationKeyIssuerID "$ISSUER"

echo "💜 $SCHEME $VER ($BLD) uploaded — appears in TestFlight after processing (~5-15m)"
