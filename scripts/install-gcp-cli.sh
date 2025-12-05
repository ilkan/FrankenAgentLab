#!/bin/bash
set -e

echo "Installing Google Cloud CLI..."

# Detect OS
OS="$(uname -s)"

case "${OS}" in
    Darwin*)
        echo "Detected macOS"
        
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            echo "Error: Homebrew is not installed. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        
        # Install gcloud CLI via Homebrew
        echo "Installing gcloud CLI via Homebrew..."
        brew install --cask google-cloud-sdk
        
        # Add to PATH (for current session)
        if [ -f "/opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc" ]; then
            source "/opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc"
        elif [ -f "/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc" ]; then
            source "/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc"
        fi
        ;;
        
    Linux*)
        echo "Detected Linux"
        
        # Download and install gcloud CLI
        echo "Downloading gcloud CLI..."
        curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
        
        echo "Extracting..."
        tar -xf google-cloud-cli-linux-x86_64.tar.gz
        
        echo "Installing..."
        ./google-cloud-sdk/install.sh --quiet
        
        # Add to PATH
        source ./google-cloud-sdk/path.bash.inc
        
        # Cleanup
        rm google-cloud-cli-linux-x86_64.tar.gz
        ;;
        
    *)
        echo "Unsupported OS: ${OS}"
        echo "Please install gcloud CLI manually from: https://cloud.google.com/sdk/docs/install"
        exit 1
        ;;
esac

# Verify installation
if command -v gcloud &> /dev/null; then
    echo "✓ Google Cloud CLI installed successfully!"
    gcloud version
    echo ""
    echo "Next steps:"
    echo "  1. Run: gcloud init"
    echo "  2. Authenticate: gcloud auth login"
    echo "  3. Set project: gcloud config set project PROJECT_ID"
else
    echo "✗ Installation failed. Please install manually from:"
    echo "  https://cloud.google.com/sdk/docs/install"
    exit 1
fi
