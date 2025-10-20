#!/usr/bin/env python3
"""
🔧 УТИЛИТЫ TelegrammBolt
Набор полезных инструментов для диагностики и управления
"""
import os
import sys
import json
import subprocess
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{msg:^70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


# ============================================================================
# 1. ПРОВЕРКА СИСТЕМЫ
# ============================================================================

def check_system():
    """Проверка состояния системы"""
    print_header("🔍 Проверка системы")
    
    issues = []
    
    # Проверка bot_data.json
    print_info("Проверка bot_data.json...")
    try:
        with open('data/bot_data.json', 'r', encoding='utf-8') as f:
            bot_data = json.load(f)
        
        total = sum(len(records) for records in bot_data.values())
        print_success(f"Загружено: {len(bot_data)} пользователей, {total} заявок")
    except FileNotFoundError:
        issues.append("data/bot_data.json не найден")
        print_error("data/bot_data.json не найден!")
    except json.JSONDecodeError as e:
        issues.append(f"data/bot_data.json поврежден: {e}")
        print_error(f"Ошибка JSON: {e}")
    
    # Проверка конфигурации
    print_info("Проверка конфигурации...")
    try:
        with open('config/ven_bot.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not config.get('BOT_TOKEN') or config.get('BOT_TOKEN') == 'YOUR_BOT_TOKEN_HERE':
            issues.append("BOT_TOKEN не настроен")
            print_warning("BOT_TOKEN не настроен!")
        else:
            print_success("BOT_TOKEN настроен")
        
        if not config.get('ADMIN_IDS'):
            issues.append("ADMIN_IDS не настроены")
            print_warning("ADMIN_IDS не настроены!")
        else:
            print_success(f"ADMIN_IDS: {config.get('ADMIN_IDS')}")
            
    except FileNotFoundError:
        issues.append("config/ven_bot.json не найден")
        print_error("config/ven_bot.json не найден!")
    except json.JSONDecodeError as e:
        issues.append(f"config/ven_bot.json поврежден: {e}")
        print_error(f"Ошибка JSON: {e}")
    
    # Проверка зависимостей
    print_info("Проверка зависимостей...")
    required = ['telegram', 'flask', 'openpyxl', 'reportlab', 'nest_asyncio']
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        issues.append(f"Отсутствуют модули: {', '.join(missing)}")
        print_error(f"Отсутствуют: {', '.join(missing)}")
    else:
        print_success("Все зависимости установлены")
    
    # Проверка процессов
    print_info("Проверка запущенных процессов...")
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            output = result.stdout
        else:  # Linux/Mac
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            output = result.stdout
        
        bot_running = 'bot.py' in output or 'python' in output
        web_running = 'web_app.py' in output
        
        if bot_running:
            print_success("Бот запущен")
        else:
            print_warning("Бот не запущен")
        
        if web_running:
            print_success("Веб-интерфейс запущен")
        else:
            print_warning("Веб-интерфейс не запущен")
            
    except Exception as e:
        print_warning(f"Не удалось проверить процессы: {e}")
    
    # Итоги
    print()
    if issues:
        print_error(f"Найдено проблем: {len(issues)}")
        for issue in issues:
            print(f"  • {issue}")
        print("\nРекомендации:")
        if any('BOT_TOKEN' in i for i in issues):
            print("  → Настройте config/ven_bot.json")
        if any('модули' in i for i in issues):
            print("  → Запустите: pip install -r requirements.txt")
        if any('bot_data.json' in i for i in issues):
            print("  → Создайте файл: python install.py")
    else:
        print_success("✅ Система в порядке!")
    
    return len(issues) == 0


# ============================================================================
# 2. ПОИСК ЗАЯВКИ
# ============================================================================

def find_dse(dse_id):
    """Поиск заявки по ID"""
    print_header(f"🔍 Поиск заявки: {dse_id}")
    
    try:
        with open('data/bot_data.json', 'r', encoding='utf-8') as f:
            bot_data = json.load(f)
    except FileNotFoundError:
        print_error("data/bot_data.json не найден!")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Ошибка JSON: {e}")
        return False
    
    # Поиск
    found = False
    for user_id, records in bot_data.items():
        for i, record in enumerate(records, 1):
            generated_id = f"{user_id}_{i}"
            record_dse = record.get('dse', '')
            
            if (str(generated_id) == str(dse_id) or 
                str(record_dse) == str(dse_id) or
                str(record.get('id', '')) == str(dse_id)):
                
                found = True
                print_success("Заявка найдена!")
                print(f"\n  User ID: {user_id}")
                print(f"  Generated ID: {generated_id}")
                print(f"  DSE Number: {record_dse}")
                print(f"  Problem Type: {record.get('problem_type', 'N/A')}")
                print(f"  DateTime: {record.get('datetime', 'N/A')}")
                print(f"  RC: {record.get('rc', 'N/A')}")
                print(f"  Has Photo: {'photo_file_id' in record or 'photos' in record}")
                print(f"\nПолная запись:")
                print(json.dumps(record, ensure_ascii=False, indent=2))
                return True
    
    if not found:
        print_error(f"Заявка '{dse_id}' не найдена!")
        print("\nДоступные ID:")
        for user_id, records in bot_data.items():
            for i, record in enumerate(records[:5], 1):  # Показываем первые 5
                print(f"  • {user_id}_{i} (DSE: {record.get('dse', 'N/A')})")
            if len(records) > 5:
                print(f"  ... и ещё {len(records) - 5} заявок")
    
    return found


# ============================================================================
# 3. ДИАГНОСТИКА ДАННЫХ
# ============================================================================

def diagnose_data():
    """Диагностика структуры данных"""
    print_header("📊 Диагностика данных")
    
    try:
        with open('data/bot_data.json', 'r', encoding='utf-8') as f:
            bot_data = json.load(f)
    except FileNotFoundError:
        print_error("data/bot_data.json не найден!")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Ошибка JSON: {e}")
        return False
    
    total_users = len(bot_data)
    total_records = sum(len(records) for records in bot_data.values())
    records_with_photos = 0
    problematic = []
    
    print_info(f"Пользователей: {total_users}")
    print_info(f"Всего заявок: {total_records}")
    print()
    
    # Анализ
    for user_id, records in bot_data.items():
        print(f"👤 Пользователь {user_id}: {len(records)} заявок")
        
        for i, record in enumerate(records, 1):
            # Подсчет фото
            if record.get('photo_file_id') or record.get('photos'):
                records_with_photos += 1
            
            # Проверка обязательных полей
            required = ['dse', 'problem_type', 'datetime']
            missing = [f for f in required if not record.get(f)]
            
            if missing:
                problematic.append({
                    'user_id': user_id,
                    'index': i,
                    'dse': record.get('dse', 'N/A'),
                    'missing': missing
                })
    
    print()
    print_info(f"Заявок с фото: {records_with_photos}")
    print_info(f"Проблемных записей: {len(problematic)}")
    
    if problematic:
        print()
        print_warning("Найдены проблемы:")
        for p in problematic[:10]:  # Показываем первые 10
            print(f"  • User {p['user_id']}, запись #{p['index']} (DSE: {p['dse']})")
            print(f"    Отсутствуют поля: {', '.join(p['missing'])}")
        
        if len(problematic) > 10:
            print(f"  ... и ещё {len(problematic) - 10} проблемных записей")
    else:
        print_success("\n✅ Все записи корректны!")
    
    return len(problematic) == 0


# ============================================================================
# 4. ПОКАЗАТЬ ПОЛЬЗОВАТЕЛЕЙ И РОЛИ
# ============================================================================

def show_users():
    """Показать всех пользователей и их роли"""
    print_header("👥 Пользователи системы")
    
    try:
        with open('data/users_data.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    except FileNotFoundError:
        print_error("data/users_data.json не найден!")
        return False
    except json.JSONDecodeError as e:
        print_error(f"Ошибка JSON: {e}")
        return False
    
    if not users_data:
        print_warning("Нет зарегистрированных пользователей")
        return True
    
    print(f"Всего пользователей: {len(users_data)}\n")
    
    for user_id, user_info in users_data.items():
        role = user_info.get('role', 'user')
        name = user_info.get('name', 'N/A')
        dept = user_info.get('department', 'N/A')
        
        role_icon = {
            'admin': '👑',
            'responder': '💼',
            'initiator': '📝',
            'user': '👤'
        }.get(role, '👤')
        
        print(f"{role_icon} {name}")
        print(f"   ID: {user_id}")
        print(f"   Роль: {role}")
        print(f"   Отдел: {dept}")
        print()
    
    return True


# ============================================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================================

def show_menu():
    """Показать меню утилит"""
    print("\n" + "="*70)
    print(f"{Colors.BOLD}{'🔧 УТИЛИТЫ TelegrammBolt':^70}{Colors.END}")
    print("="*70 + "\n")
    
    print("1. 🔍 Проверка системы")
    print("2. 🔎 Найти заявку по ID")
    print("3. 📊 Диагностика данных")
    print("4. 👥 Показать пользователей")
    print("0. ❌ Выход")
    print()

def main():
    """Главная функция"""
    
    # Переходим в корень проекта
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    if len(sys.argv) > 1:
        # Режим командной строки
        command = sys.argv[1].lower()
        
        if command == 'check' or command == 'status':
            return 0 if check_system() else 1
        
        elif command == 'find' and len(sys.argv) > 2:
            dse_id = sys.argv[2]
            return 0 if find_dse(dse_id) else 1
        
        elif command == 'diagnose':
            return 0 if diagnose_data() else 1
        
        elif command == 'users':
            return 0 if show_users() else 1
        
        else:
            print("Использование:")
            print("  python utils.py check        - Проверка системы")
            print("  python utils.py find <ID>    - Найти заявку")
            print("  python utils.py diagnose     - Диагностика данных")
            print("  python utils.py users        - Показать пользователей")
            return 1
    
    # Интерактивный режим
    while True:
        show_menu()
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            check_system()
        elif choice == '2':
            dse_id = input("Введите ID заявки: ").strip()
            if dse_id:
                find_dse(dse_id)
        elif choice == '3':
            diagnose_data()
        elif choice == '4':
            show_users()
        elif choice == '0':
            print("\n👋 До свидания!\n")
            break
        else:
            print_warning("Неверный выбор!")
        
        input("\nНажмите Enter для продолжения...")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Прервано пользователем{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Ошибка: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
