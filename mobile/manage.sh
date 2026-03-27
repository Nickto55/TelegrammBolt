#!/bin/bash

# TelegrammBolt Mobile App Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_menu() {
    echo ""
    echo "================================"
    echo "TelegrammBolt Mobile App Manager"
    echo "================================"
    echo "1. Start development server"
    echo "2. Build for iOS"
    echo "3. Build for Android"
    echo "4. Install dependencies"
    echo "5. Clean cache"
    echo "6. View logs"
    echo "7. Exit"
    echo ""
}

start_dev() {
    echo -e "${GREEN}Starting development server...${NC}"
    npm start
}

build_ios() {
    echo -e "${GREEN}Building for iOS...${NC}"
    npm run ios
}

build_android() {
    echo -e "${GREEN}Building for Android...${NC}"
    npm run android
}

install_deps() {
    echo -e "${GREEN}Installing dependencies...${NC}"
    npm install
}

clean_cache() {
    echo -e "${YELLOW}Cleaning cache...${NC}"
    npm start -- --clear
}

view_logs() {
    echo -e "${YELLOW}Viewing logs (Ctrl+C to exit)...${NC}"
    npx react-native log-ios
}

while true; do
    show_menu
    read -p "Select option (1-7): " choice
    
    case $choice in
        1) start_dev ;;
        2) build_ios ;;
        3) build_android ;;
        4) install_deps ;;
        5) clean_cache ;;
        6) view_logs ;;
        7)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
done
