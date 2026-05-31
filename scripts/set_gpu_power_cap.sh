#!/bin/bash
# Set R9700 (0000:03:00.0) power cap to 200W (reduce heat).
# Installed via gpu-powercap.service — runs at boot as root.

PCI="0000:03:00.0"
CAP_WATTS=200
CAP_MICROWATTS=$((CAP_WATTS * 1000000))

HWMON_DIR="/sys/bus/pci/devices/${PCI}/hwmon"

if [ ! -d "$HWMON_DIR" ]; then
  echo "hwmon dir not found for $PCI — GPU may not be present" >&2
  exit 1
fi

CAP_FILE=$(ls "${HWMON_DIR}"/hwmon*/power1_cap 2>/dev/null | head -1)

if [ -z "$CAP_FILE" ]; then
  echo "power1_cap not found under $HWMON_DIR" >&2
  exit 1
fi

echo "$CAP_MICROWATTS" > "$CAP_FILE"
ACTUAL=$(cat "$CAP_FILE")
echo "R9700 power cap set: ${ACTUAL}µW ($(( ACTUAL / 1000000 ))W) → $CAP_FILE"
