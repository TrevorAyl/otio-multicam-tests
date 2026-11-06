#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 run_integrated_demo.py
printf '\nReport: %s/demo_output/VALIDATION_REPORT.md\n' "$PWD"
