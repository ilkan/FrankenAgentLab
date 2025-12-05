#!/bin/bash
set -e

echo "Installing Firebase CLI..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed."
    echo "Please install Node.js first:"
    echo "  macOS: brew install node"
    echo "  Linux: https://nodejs.org/en/download/"
    exit 1
fi

echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed."
    exit 1
fi

# Install Firebase CLI globally
echo "Installing Firebase CLI via npm..."
npm install -g firebase-tools

# Verify installation
if command -v firebase &> /dev/null; then
    echo "✓ Firebase CLI installed successfully!"
    firebase --version
    echo ""
    echo "Next steps:"
    echo "  1. Login: firebase login"
    echo "  2. Initialize project: firebase init"
else
    echo "✗ Installation failed."
    exit 1
fi
