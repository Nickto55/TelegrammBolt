#!/bin/bash

# =============================================================================
# БЫСТРЫЙ СТАРТ - TelegrammBot
# =============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          TelegrammBot - Быстрый старт                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Выберите сценарий установки:"
echo ""
echo "1. 🚀 Быстрая установка с самоподписанным SSL (рекомендуется)"
echo "   - Работает сразу без домена"
echo "   - HTTPS на любом IP"
echo "   - Идеально для тестирования"
echo ""
echo "2. 🌐 Установка с Let's Encrypt SSL"
echo "   - Требует валидный домен"
echo "   - Бесплатный доверенный SSL"
echo "   - Для публичных сайтов"
echo ""
echo "3. 📦 Базовая установка без SSL"
echo "   - Только HTTP"
echo "   - Быстрее всего"
echo "   - Для локальной сети"
echo ""
echo "4. 🔧 Полная настройка (интерактивная)"
echo "   - Все опции"
echo "   - Шаг за шагом"
echo ""
echo "0. ❌ Выход"
echo ""
read -p "Ваш выбор (1-4): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "🚀 Запуск быстрой установки с самоподписанным SSL..."
        echo ""
        
        # Запуск установки с предварительными ответами
        export QUICK_INSTALL=true
        export SSL_TYPE=selfsigned
        ./setup.sh
        
        echo ""
        echo "✅ Установка завершена!"
        echo ""
        echo "📝 Следующие шаги:"
        echo "1. Откройте браузер: https://$(hostname -I | awk '{print $1}')"
        echo "2. При предупреждении нажмите 'Дополнительно' → 'Перейти на сайт'"
        echo "3. Запустите бота: ./manage.sh"
        echo ""
        echo "💡 См. SELF_SIGNED_SSL.md для убрания предупреждений браузера"
        ;;
    2)
        echo ""
        echo "🌐 Запуск установки с Let's Encrypt..."
        echo ""
        read -p "Введите ваш домен: " DOMAIN
        echo ""
        echo "Проверка DNS..."
        ./check-dns.sh
        echo ""
        read -p "DNS настроен правильно? Продолжить? (y/n): " CONTINUE
        
        if [[ $CONTINUE =~ ^[Yy]$ ]]; then
            export QUICK_INSTALL=true
            export SSL_TYPE=letsencrypt
            export DOMAIN=$DOMAIN
            ./setup.sh
        else
            echo "Установка отменена. Используйте опцию 1 для самоподписанного SSL."
        fi
        ;;
    3)
        echo ""
        echo "📦 Запуск базовой установки..."
        echo ""
        export QUICK_INSTALL=true
        export SSL_TYPE=none
        ./setup.sh
        
        echo ""
        echo "✅ Установка завершена!"
        echo "Доступ: http://$(hostname -I | awk '{print $1}'):5000"
        ;;
    4)
        echo ""
        echo "🔧 Запуск полной настройки..."
        ./setup.sh
        ;;
    0)
        echo "Выход..."
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac
