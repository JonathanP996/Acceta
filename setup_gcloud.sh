#!/bin/bash
# Setup script to add gcloud to PATH and initialize if needed

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GCLOUD_DIR="$SCRIPT_DIR/google-cloud-sdk"

# Add gcloud to PATH
export PATH="$GCLOUD_DIR/bin:$PATH"

# Check if gcloud is initialized
if ! gcloud config list --format="value(core.account)" 2>/dev/null | grep -q .; then
    echo "gcloud is not initialized. Running gcloud init..."
    gcloud init
else
    echo "gcloud is already configured."
    echo "Current account: $(gcloud config get-value core.account)"
    echo "Current project: $(gcloud config get-value core.project)"
fi

echo ""
echo "gcloud is ready to use!"
echo "To use gcloud in this session, run: source setup_gcloud.sh"

