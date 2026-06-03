#!/bin/bash
TS=$(date '+%Y-%m-%d %H:%M:%S')
EDGE=$(rocm-smi --showtemp 2>/dev/null | awk '/GPU\[0\].*edge/{print $NF}')
JUNC=$(rocm-smi --showtemp 2>/dev/null | awk '/GPU\[0\].*junction/{print $NF}')
MEM=$(rocm-smi --showtemp 2>/dev/null | awk '/GPU\[0\].*memory/{print $NF}')
USE=$(rocm-smi --showuse 2>/dev/null | awk '/GPU\[0\]/{print $NF}')
echo "$TS  edge=${EDGE}°C  junction=${JUNC}°C  mem=${MEM}°C  use=${USE}%" >> /home/akbar/meritgiving/logs/gpu_temp.log
