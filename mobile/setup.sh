#!/bin/bash

# TelegrammBolt Mobile App Setup Script
# Для Linux/macOS

set -e

echo "================================"
echo "TelegrammBolt Mobile App Setup"
echo "================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js 16+ from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed."
    exit 1
fi

echo "✅ npm version: $(npm --version)"

# Check if Expo CLI is installed
if ! command -v expo &> /dev/null; then
    echo "📦 Installing Expo CLI globally..."
    npm install -g expo-cli
fi

echo "✅ Expo CLI is available"

# Create .env file if not exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API_BASE_URL"
    echo ""
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and set API_BASE_URL"
echo "2. Run 'npm start' to start development server"
echo "3. Press 'i' for iOS or 'a' for Android"
echo ""
