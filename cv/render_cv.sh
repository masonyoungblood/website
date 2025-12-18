#!/bin/bash

# Script to update publications from BibTeX and render CV

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Updating publications from BibTeX..."
uv run python bibtex_wrangler.py

echo "Rendering CV..."
uv run rendercv render Mason_Youngblood_CV.yaml

echo "Moving to docs..."
mv rendercv_output/Mason_Youngblood_CV.pdf ../docs/mason_youngblood_cv.pdf

echo "Done!"

