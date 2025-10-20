#!/usr/bin/env python3
"""
🔍 ПРОВЕРКА ЗАВИСИМОСТЕЙ И ИМПОРТОВ
Проверяет все Python файлы на корректность импортов после реорганизации
"""
import os
import ast
import sys
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def get_imports(file_path):
    """Извлекает все импорты из Python файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                for alias in node.names:
                    imports.append({
                        'type': 'from',
                        'module': module,
                        'name': alias.name,
                        'line': node.lineno
                    })
        
        return imports
    except SyntaxError as e:
        print_error(f"Синтаксическая ошибка в {file_path}: {e}")
        return None
    except Exception as e:
        print_warning(f"Не удалось прочитать {file_path}: {e}")
        return None

def check_local_imports(file_path, imports, all_files):
    """Проверяет локальные импорты (из проекта)"""
    issues = []
    file_dir = os.path.dirname(file_path)
    
    for imp in imports:
        module = imp.get('module', '')
        
        # Проверяем локальные импорты
        local_modules = [
            'bot', 'config', 'data', 'web', 'scripts',
            'commands', 'user_manager', 'dse_manager', 'chat_manager',
            'email_manager', 'gui_manager', 'pdf_generator', 'dse_watcher'
        ]
        
        # Если это локальный модуль
        if any(module.startswith(lm) or module == lm for lm in local_modules):
            # Проверяем что файл существует
            possible_paths = [
                os.path.join(file_dir, f"{module}.py"),
                os.path.join(file_dir, module, "__init__.py"),
                os.path.join('bot', f"{module}.py"),
                os.path.join('web', f"{module}.py"),
                os.path.join('config', f"{module}.py"),
            ]
            
            exists = any(os.path.exists(p) for p in possible_paths)
            
            if not exists:
                issues.append({
                    'line': imp['line'],
                    'module': module,
                    'type': 'missing_module'
                })
    
    return issues

def scan_directory(directory, all_files):
    """Сканирует директорию на Python файлы"""
    print_header(f"📁 Сканирование: {directory}")
    
    py_files = []
    for root, dirs, files in os.walk(directory):
        # Пропускаем виртуальное окружение и кэш
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', '.idea', 'archive', 'backup_20251020_160203', '.docs_backup_20251016_083213']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                py_files.append(file_path)
    
    return py_files

def analyze_file(file_path, all_files):
    """Анализирует один файл"""
    imports = get_imports(file_path)
    
    if imports is None:
        return None
    
    issues = check_local_imports(file_path, imports, all_files)
    
    return {
        'path': file_path,
        'imports': imports,
        'issues': issues
    }

def main():
    print("\n" + "="*70)
    print("🔍 ПРОВЕРКА ЗАВИСИМОСТЕЙ ПОСЛЕ РЕОРГАНИЗАЦИИ")
    print("="*70)
    
    # Получаем все Python файлы
    all_files = []
    directories = ['bot', 'web', 'config', 'scripts']
    
    for directory in directories:
        if os.path.exists(directory):
            all_files.extend(scan_directory(directory, all_files))
    
    # Добавляем корневые файлы
    root_py = [f for f in os.listdir('.') if f.endswith('.py')]
    all_files.extend(root_py)
    
    print(f"\n📊 Найдено Python файлов: {len(all_files)}\n")
    
    # Анализируем каждый файл
    results = []
    total_issues = 0
    
    for file_path in all_files:
        result = analyze_file(file_path, all_files)
        if result:
            results.append(result)
            
            # Выводим информацию
            rel_path = os.path.relpath(file_path)
            if result['issues']:
                print_error(f"{rel_path}")
                total_issues += len(result['issues'])
                for issue in result['issues']:
                    print(f"    Строка {issue['line']}: модуль '{issue['module']}' не найден")
            else:
                print_success(f"{rel_path} - импорты OK ({len(result['imports'])} импортов)")
    
    # Итоги
    print_header("📊 ИТОГИ")
    
    print(f"Проверено файлов: {len(results)}")
    print(f"Всего импортов: {sum(len(r['imports']) for r in results)}")
    print(f"Найдено проблем: {total_issues}")
    
    if total_issues == 0:
        print(f"\n{Colors.GREEN}✅ ВСЕ ЗАВИСИМОСТИ КОРРЕКТНЫ!{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠️  НАЙДЕНЫ ПРОБЛЕМЫ С ИМПОРТАМИ{Colors.END}")
        print("\n🔧 Рекомендации:")
        print("  1. Обновите импорты в проблемных файлах")
        print("  2. Используйте относительные импорты внутри пакета")
        print("  3. Или добавьте путь к sys.path в начале файла")
        print("\nПримеры исправлений:")
        print("  # БЫЛО:")
        print("  import user_manager")
        print("\n  # СТАЛО (если в bot/):")
        print("  from bot import user_manager")
        print("\n  # ИЛИ (относительный импорт):")
        print("  from . import user_manager")
        print()
    
    # Детальная статистика по директориям
    print("\n📁 Статистика по директориям:")
    for directory in directories:
        dir_files = [r for r in results if directory in r['path']]
        dir_issues = sum(len(r['issues']) for r in dir_files)
        
        if dir_files:
            status = f"{Colors.GREEN}✓{Colors.END}" if dir_issues == 0 else f"{Colors.RED}✗{Colors.END}"
            print(f"  {status} {directory}/: {len(dir_files)} файлов, {dir_issues} проблем")
    
    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
