#!/bin/bash

# Скрипт установки Android SDK для локальной сборки APK
# Для Ubuntu/Debian серверов

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════╗"
echo "║      Android SDK Setup для APK сборки         ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED} Запустите скрипт с sudo${NC}"
    echo "   sudo ./setup-android-sdk.sh"
    exit 1
fi

# Установка Java JDK 17 (требуется для Gradle)
echo -e "${YELLOW}[1/5] Установка Java JDK 17...${NC}"
if ! command -v java &> /dev/null; then
    apt-get update -qq
    apt-get install -y openjdk-17-jdk
    echo -e "${GREEN} Java установлена${NC}"
else
    echo -e "${GREEN} Java уже установлена: $(java -version 2>&1 | head -n 1)${NC}"
fi

# Создание директории для Android SDK
ANDROID_HOME="/opt/android-sdk"
echo -e "${YELLOW}[2/5] Создание директории Android SDK: $ANDROID_HOME${NC}"
mkdir -p "$ANDROID_HOME"

# Скачивание Android Command Line Tools
echo -e "${YELLOW}[3/5] Скачивание Android Command Line Tools...${NC}"
cd /tmp
CMDLINE_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"

if [ ! -f "commandlinetools.zip" ]; then
    echo -e "${BLUE} Загрузка с dl.google.com (~150MB)...${NC}"
    wget --progress=bar:force "$CMDLINE_TOOLS_URL" -O commandlinetools.zip 2>&1 | \
        grep --line-buffered "%" | \
        sed -u -e "s/.*\s\+\([0-9]\+%\).*/${BLUE}Загружено: \1${NC}/"
else
    echo -e "${GREEN} Файл уже скачан${NC}"
fi

echo -e "${BLUE} Распаковка архива...${NC}"
unzip -o commandlinetools.zip -d "$ANDROID_HOME" | \
    pv -l -s $(unzip -l commandlinetools.zip | wc -l) > /dev/null 2>&1 || \
    unzip -q -o commandlinetools.zip -d "$ANDROID_HOME"
rm -f commandlinetools.zip
echo -e "${GREEN} Распаковка завершена${NC}"

# Переименование директории (требование Android SDK)
mkdir -p "$ANDROID_HOME/cmdline-tools/latest"
if [ -d "$ANDROID_HOME/cmdline-tools/bin" ]; then
    mv "$ANDROID_HOME/cmdline-tools/bin" "$ANDROID_HOME/cmdline-tools/latest/" 2>/dev/null || true
    mv "$ANDROID_HOME/cmdline-tools/lib" "$ANDROID_HOME/cmdline-tools/latest/" 2>/dev/null || true
fi

echo -e "${GREEN} Command Line Tools установлены${NC}"

# Настройка переменных окружения
echo -e "${YELLOW}[4/5] Настройка переменных окружения...${NC}"
export ANDROID_HOME="$ANDROID_HOME"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/34.0.0"

# Добавление в .bashrc для постоянного использования
if ! grep -q "ANDROID_HOME" /root/.bashrc; then
    cat >> /root/.bashrc << 'EOF'

# Android SDK
export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/34.0.0
EOF
fi

echo -e "${GREEN} Переменные окружения настроены${NC}"

# Установка необходимых Android SDK пакетов
echo -e "${YELLOW}[5/5] Установка Android SDK компонентов...${NC}"
echo -e "${BLUE}Это может занять 5-10 минут...${NC}"
echo ""

# Принять лицензии
echo -e "${BLUE}📝 Принятие Android SDK лицензий...${NC}"
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses > /dev/null 2>&1 || true
echo -e "${GREEN} Лицензии приняты${NC}"
echo ""

# Установка необходимых пакетов с прогрессом
SDK_PACKAGES=(
    "platform-tools:  Platform Tools (adb, fastboot)"
    "platforms;android-34: Android 14.0 (API 34)"
    "build-tools;34.0.0: Build Tools 34.0.0"
    "ndk;25.1.8937393: Android NDK 25.1"
    "cmake;3.22.1: CMake 3.22.1"
)
echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Установка завершена!             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE} Сводка установки:${NC}"
echo ""
echo -e "${GREEN}   ANDROID_HOME:${NC} $ANDROID_HOME"
echo -e "${GREEN}   Java:${NC} $(java -version 2>&1 | head -n 1)"
echo -e "${GREEN}   Android Platform:${NC} $(ls $ANDROID_HOME/platforms/ 2>/dev/null | head -n 1 || echo 'не найден')"
echo -e "${GREEN}   Build Tools:${NC} $(ls $ANDROID_HOME/build-tools/ 2>/dev/null | head -n 1 || echo 'не найден')"

# Проверка размера установки
SDK_SIZE=$(du -sh "$ANDROID_HOME" 2>/dev/null | cut -f1 || echo "N/A")
echo -e "${GREEN}   Размер SDK:${NC} $SDK_SIZE"

# Проверка доступности команд
echo ""
echo -e "${BLUE}🔍 Проверка инструментов:${NC}"
if [ -f "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
    echo -e "${GREEN}   sdkmanager${NC} - доступен"
else
    echo -e "${RED}  sdkmanager${NC} - не найден"
fi

if [ -f "$ANDROID_HOME/platform-tools/adb" ]; then
    echo -e "${GREEN}  adb${NC} - доступен"
else
    echo -e "${RED}  adb${NC} - не найден"
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Важно! Для применения переменных окружения:${NC}"
echo -e "${BLUE}   source /root/.bashrc${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN} Следующие шаги:${NC}"
echo -e "   ${BLUE}1.${NC} source /root/.bashrc"
echo -e "   ${BLUE}2.${NC} cd /root/TelegrammBolt/mobile"
echo -e "   ${BLUE}3.${NC} npm run android-build"
echo """Installing"* ]]; then
                echo -e "${BLUE}   Установка...${NC}"
            elif [[ $line == *"[="* ]]; then
                echo -ne "${BLUE}  $line${NC}\r"
            fi
        done
    
    echo -e "${GREEN}   $pkg_desc установлен${NC}"
done

echo ""
echo -e "${GREEN} Все Android SDK компоненты установлены${NC}"

# Проверка установки
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Установка завершена!             ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Установлено:${NC}"
echo "   ANDROID_HOME: $ANDROID_HOME"
echo "   Java: $(java -version 2>&1 | head -n 1)"
echo "   Android Platform: $(ls $ANDROID_HOME/platforms/ 2>/dev/null | head -n 1)"
echo "   Build Tools: $(ls $ANDROID_HOME/build-tools/ 2>/dev/null | head -n 1)"
echo ""
echo -e "${YELLOW}  Для применения переменных окружения выполните:${NC}"
echo "  source /root/.bashrc"
echo ""
echo -e "${GREEN} Теперь можно собирать APK!${NC}"
echo "  cd /root/TelegrammBolt/mobile"
echo "  npm run android-build"
