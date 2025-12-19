# -*- coding: utf-8 -*-
"""
PDF Generator для создания отчетов по заявкам ДСЕ
Использует шаблон таблицы как на изображении пользователя
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Image
import os
from datetime import datetime

# Регистрируем поддержку UTF-8
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class DSEPDFGenerator:
    def __init__(self):
        # Попробуем зарегистрировать русский шрифт
        try:
            # Попробуем разные пути к шрифтам
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf',
                '/System/Library/Fonts/Arial.ttf',
                'DejaVuSans.ttf'
            ]
            
            font_registered = False
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('RussianFont', font_path))
                        self.font_name = 'RussianFont'
                        self.font_bold = 'RussianFont'
                        font_registered = True
                        break
                except:
                    continue
            
            if not font_registered:
                raise Exception("No suitable font found")
                
        except:
            # Используем встроенные шрифты ReportLab с поддержкой UTF-8
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
                self.font_name = 'HeiseiKakuGo-W5'
                self.font_bold = 'HeiseiKakuGo-W5'
            except:
                # Последний вариант - стандартные шрифты
                self.font_name = 'Helvetica'
                self.font_bold = 'Helvetica-Bold'
        
        self.styles = getSampleStyleSheet()
        
        # Стиль для текста в ячейках таблицы
        self.cell_style = ParagraphStyle(
            'CellStyle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=7,
            leading=8,
            alignment=1,  # Центрирование
            wordWrap='CJK'
        )
        
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontName=self.font_bold,
            fontSize=7,
            leading=8,
            alignment=1,
            wordWrap='CJK'
        )
        
    def create_dse_report(self, record_data, output_filename):
        """
        Создать PDF отчет по заявке ДСЕ
        
        :param record_data: Словарь с данными заявки
        :param output_filename: Имя выходного файла
        :return: True если успешно, False если ошибка
        """
        try:
            from reportlab.lib.pagesizes import landscape
            
            # Создаем документ в альбомной ориентации
            doc = SimpleDocTemplate(
                output_filename,
                pagesize=landscape(A4),
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )
            
            story = []
            
            # Заголовок
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontName=self.font_bold,
                fontSize=16,
                alignment=1,  # Центрирование
                spaceAfter=20,
                encoding='utf-8'
            )
            
            title = Paragraph("ОТЧЕТ".encode('utf-8').decode('utf-8'), title_style)
            story.append(title)
            story.append(Spacer(1, 10*mm))
            
            # Создаем горизонтальную таблицу (заголовки сверху, данные снизу)
            table_data = []
            
            # Извлекаем дату из datetime
            date_str = record_data.get('datetime', '').split()[0] if record_data.get('datetime') else ''
            
            # Заголовки (первая строка) - используем Paragraph для автоматического переноса
            headers = [
                Paragraph('Дата', self.header_style),
                Paragraph('ДСЕ', self.header_style),
                Paragraph('Наименование ДСЕ', self.header_style),
                Paragraph('Вид проблемы', self.header_style),
                Paragraph('РЦ', self.header_style),
                Paragraph('Номер станка', self.header_style),
                Paragraph('ФИО Наладчика', self.header_style),
                Paragraph('ФИО Программиста', self.header_style)
            ]
            table_data.append(headers)
            
            # Данные (вторая строка) - используем Paragraph для автоматического переноса
            data_row = [
                Paragraph(str(date_str), self.cell_style),
                Paragraph(str(record_data.get('dse', '')), self.cell_style),
                Paragraph(str(record_data.get('dse_name', '')), self.cell_style),
                Paragraph(str(record_data.get('problem_type', '')), self.cell_style),
                Paragraph(str(record_data.get('rc', '')), self.cell_style),
                Paragraph(str(record_data.get('machine_number', '')), self.cell_style),
                Paragraph(str(record_data.get('installer_fio', '')), self.cell_style),
                Paragraph(str(record_data.get('programmer_name', '')), self.cell_style)
            ]
            table_data.append(data_row)
            
            # Создаем таблицу
            table = Table(table_data, colWidths=[
                22*mm,  # Дата
                18*mm,  # ДСЕ
                30*mm,  # Наименование ДСЕ
                28*mm,  # Вид проблемы
                18*mm,  # РЦ
                20*mm,  # Номер станка
                32*mm,  # ФИО Наладчика
                32*mm   # ФИО Программиста
            ])
             
            # Стиль таблицы
            table.setStyle(TableStyle([
                # Границы
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Заголовки (первая строка)
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Отступы
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                
                # Минимальная высота строк для многострочного текста
                ('ROWMINHEIGHT', (0, 0), (-1, -1), 15),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 10*mm))
            
            # Поле для описания проблемы
            desc_style = ParagraphStyle(
                'DescTitle',
                parent=self.styles['Normal'],
                fontName=self.font_bold,
                fontSize=12
            )
            desc_title = Paragraph("<b>Описание проблемы:</b>", desc_style)
            story.append(desc_title)
            story.append(Spacer(1, 5*mm))
            
            # Создаем рамку для описания
            desc_text = str(record_data.get('description', 'Описание не указано'))
            
            # Разбиваем описание на строки и создаем таблицу с линиями
            desc_lines = []
            max_chars = 80  # Максимум символов в строке
            
            # Разбиваем текст на строки
            words = desc_text.split()
            current_line = ""
            
            for word in words:
                if len(current_line + word) <= max_chars:
                    current_line += word + " "
                else:
                    desc_lines.append(current_line.strip())
                    current_line = word + " "
            
            if current_line:
                desc_lines.append(current_line.strip())
            
            # Добавляем пустые строки до минимума 10
            while len(desc_lines) < 10:
                desc_lines.append('')
            
            # Создаем таблицу для описания
            desc_table_data = []
            for line in desc_lines[:15]:  # Максимум 15 строк
                desc_table_data.append([line])
            
            desc_table = Table(desc_table_data, colWidths=[255*mm])
            desc_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(desc_table)
            
            # Информация о создании отчета
            story.append(Spacer(1, 15*mm))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontName=self.font_name,
                fontSize=8,
                alignment=2  # Правое выравнивание
            )
            
            creation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            footer_text = f"Отчет создан: {creation_time}"
            footer = Paragraph(footer_text, footer_style)
            story.append(footer)
            
            # Создаем PDF
            doc.build(story)
            
            return True
            
        except Exception as e:
            print(f"Ошибка создания PDF: {e}")
            return False


def create_dse_pdf_report(record_data, filename=None):
    """
    Удобная функция для создания PDF отчета
    
    :param record_data: Данные записи
    :param filename: Имя файла (опционально)
    :return: Имя созданного файла или None при ошибке
    """
    if not filename:
        dse = record_data.get('dse', 'unknown').replace('/', '_')
        date_str = record_data.get('datetime', '').split()[0].replace('-', '') if record_data.get('datetime') else 'unknown'
        filename = f"dse_report_{dse}_{date_str}.pdf"
    
    generator = DSEPDFGenerator()
    
    if generator.create_dse_report(record_data, filename):
        return filename
    else:
        return None


def create_single_dse_pdf_report(record_data, filename, options=None):
    """
    Создание PDF отчета для одной записи ДСЕ с расширенными опциями
    
    :param record_data: Данные записи
    :param filename: Путь к выходному файлу
    :param options: Словарь с опциями (include_photos, include_description, etc.)
    :return: True если успешно, False если ошибка
    """
    if options is None:
        options = {}
    
    try:
        from reportlab.lib.pagesizes import A4, A3, LETTER, landscape, portrait
        from reportlab.platypus import PageBreak, Image as RLImage
        
        print(f"Creating single DSE PDF: {filename} for {record_data.get('dse', 'N/A')}")
        
        # Определяем размер страницы
        page_format = options.get('page_format', 'A4')
        if page_format == 'A3':
            pagesize = A3
        elif page_format == 'Letter':
            pagesize = LETTER
        else:
            pagesize = A4
        
        # Определяем ориентацию
        if options.get('page_orientation') == 'landscape':
            pagesize = landscape(pagesize)
        else:
            pagesize = portrait(pagesize)
        
        # Создаем документ
        doc = SimpleDocTemplate(
            filename,
            pagesize=pagesize,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        generator = DSEPDFGenerator()
        story = []
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=generator.styles['Heading1'],
            fontName=generator.font_bold,
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )
        
        title = Paragraph("OTCHET PO ZAYAVKE DSE", title_style)
        story.append(title)
        story.append(Spacer(1, 10*mm))
        
        # Основная информация
        info_data = [
            ['Номер ДСЕ:', str(record_data.get('dse', 'N/A'))],
            ['Тип проблемы:', str(record_data.get('problem_type', 'N/A'))[:50]],
            ['РЦ:', str(record_data.get('rc', 'N/A'))],
        ]
        
        if options.get('include_timestamp', True):
            info_data.append(['Дата:', str(record_data.get('datetime', 'N/A'))])
        
        if options.get('include_user_info', True):
            info_data.append(['Автор:', f"ID: {record_data.get('user_id', 'N/A')}"])
        
        info_table = Table(info_data, colWidths=[50*mm, 120*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), generator.font_bold),
            ('FONTNAME', (1, 0), (1, -1), generator.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 10*mm))
        
        # Описание
        if options.get('include_description', True) and record_data.get('description'):
            desc_style = ParagraphStyle(
                'DescTitle',
                parent=generator.styles['Normal'],
                fontName=generator.font_bold,
                fontSize=12
            )
            desc_title = Paragraph("<b>Описание проблемы:</b>", desc_style)
            story.append(desc_title)
            story.append(Spacer(1, 3*mm))
            
            desc_text = str(record_data.get('description', ''))[:500]  # Ограничиваем длину
            desc_para = Paragraph(desc_text, generator.styles['Normal'])
            story.append(desc_para)
            story.append(Spacer(1, 10*mm))
        
        # Футер с информацией о создании
        if options.get('include_timestamp', True):
            footer_style = ParagraphStyle(
                'Footer',
                parent=generator.styles['Normal'],
                fontName=generator.font_name,
                fontSize=8,
                alignment=2
            )
            creation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            footer_text = f"Otchet sozdan: {creation_time}"
            footer = Paragraph(footer_text, footer_style)
            story.append(Spacer(1, 10*mm))
            story.append(footer)
        
        print(f"Building single PDF document...")
        doc.build(story)
        print(f"Single PDF created successfully: {filename}")
        
        # Проверяем что файл создан
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"PDF file size: {os.path.getsize(filename)} bytes")
            return True
        else:
            print(f"ERROR: PDF file not created or empty")
            return False
        
    except Exception as e:
        print(f"Ошибка создания PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_multi_dse_pdf_report(records_list, filename, options=None):
    """
    Создание PDF отчета с несколькими записями ДСЕ
    
    :param records_list: Список записей ДСЕ
    :param filename: Путь к выходному файлу
    :param options: Словарь с опциями
    :return: True если успешно, False если ошибка
    """
    if options is None:
        options = {}
    
    try:
        from reportlab.lib.pagesizes import A4, A3, LETTER, landscape, portrait
        from reportlab.platypus import PageBreak, Image as RLImage
        
        print(f"Creating multi-DSE PDF: {filename} with {len(records_list)} records")
        
        # Определяем размер страницы
        page_format = options.get('page_format', 'A4')
        if page_format == 'A3':
            pagesize = A3
        elif page_format == 'Letter':
            pagesize = LETTER
        else:
            pagesize = A4
        
        # Определяем ориентацию
        if options.get('page_orientation') == 'landscape':
            pagesize = landscape(pagesize)
        else:
            pagesize = portrait(pagesize)
        
        # Создаем документ
        doc = SimpleDocTemplate(
            filename,
            pagesize=pagesize,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        generator = DSEPDFGenerator()
        story = []
        
        # Титульная страница
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=generator.styles['Heading1'],
            fontName=generator.font_bold,
            fontSize=18,
            alignment=1,
            spaceAfter=20
        )
        
        # Используем безопасное кодирование
        title_text = "OTCHET PO ZAYAVKAM DSE"
        try:
            title_text = "ОТЧЕТ ПО ЗАЯВКАМ ДСЕ"
        except:
            pass
        
        title = Paragraph(title_text, title_style)
        story.append(title)
        story.append(Spacer(1, 5*mm))
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=generator.styles['Normal'],
            fontName=generator.font_name,
            fontSize=12,
            alignment=1
        )
        
        subtitle = Paragraph(f"Vsego zapisey: {len(records_list)}", subtitle_style)
        story.append(subtitle)
        
        if options.get('include_timestamp', True):
            date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            date_text = Paragraph(f"Data sozdaniya: {date_str}", subtitle_style)
            story.append(date_text)
        
        story.append(PageBreak())
        
        # Добавляем каждую запись
        for i, record_data in enumerate(records_list, 1):
            print(f"Processing record {i}/{len(records_list)}: {record_data.get('dse', 'N/A')}")
            
            # Заголовок записи
            record_title_style = ParagraphStyle(
                'RecordTitle',
                parent=generator.styles['Heading2'],
                fontName=generator.font_bold,
                fontSize=14,
                spaceAfter=10
            )
            
            dse_num = str(record_data.get('dse', 'N/A'))
            record_title = Paragraph(f"ДСЕ {i} из {len(records_list)}: {dse_num}", record_title_style)
            story.append(record_title)
            story.append(Spacer(1, 5*mm))
            
            # Основная информация
            info_data = [
                ['Номер ДСЕ:', str(record_data.get('dse', 'N/A'))],
                ['Тип проблемы:', str(record_data.get('problem_type', 'N/A'))[:50]],
                ['РЦ:', str(record_data.get('rc', 'N/A'))],
            ]
            
            if options.get('include_timestamp', True):
                info_data.append(['Дата:', str(record_data.get('datetime', 'N/A'))])
            
            if options.get('include_user_info', True):
                info_data.append(['Автор:', f"ID: {record_data.get('user_id', 'N/A')}"])
            
            info_table = Table(info_data, colWidths=[50*mm, 120*mm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), generator.font_bold),
                ('FONTNAME', (1, 0), (1, -1), generator.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 8*mm))
            
            # Описание
            if options.get('include_description', True) and record_data.get('description'):
                desc_style = ParagraphStyle(
                    'DescTitle',
                    parent=generator.styles['Normal'],
                    fontName=generator.font_bold,
                    fontSize=11
                )
                desc_title = Paragraph("<b>Описание:</b>", desc_style)
                story.append(desc_title)
                story.append(Spacer(1, 2*mm))
                
                # Транслитерация описания для безопасности
                desc_text = str(record_data.get('description', ''))[:500]  # Ограничиваем длину
                desc_para_style = ParagraphStyle(
                    'DescText',
                    parent=generator.styles['Normal'],
                    fontName=generator.font_name,
                    fontSize=10
                )
                desc_para = Paragraph(desc_text, desc_para_style)
                story.append(desc_para)
                story.append(Spacer(1, 8*mm))
            
            # Разделитель между записями
            if i < len(records_list):
                story.append(Spacer(1, 10*mm))
                story.append(PageBreak())
        
        print(f"Building PDF document...")
        doc.build(story)
        print(f"PDF created successfully: {filename}")
        
        # Проверяем что файл создан
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"PDF file size: {os.path.getsize(filename)} bytes")
            return True
        else:
            print(f"ERROR: PDF file not created or empty")
            return False
        
    except Exception as e:
        print(f"Ошибка создания мульти-PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


async def show_pdf_export_menu(update, context):
    """
    Показать меню экспорта PDF
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📄 Экспорт всех записей", callback_data='pdf_export_all')],
        [InlineKeyboardButton("📋 Выбрать записи", callback_data='pdf_export_select')],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data='back_to_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 *Экспорт в PDF*\n\n"
        "Выберите опцию экспорта:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_pdf_export_all(update, context):
    """Экспорт всех записей в PDF"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from .dse_manager import get_all_dse_records
    
    query = update.callback_query
    await query.answer("⏳ Загрузка всех записей...")
    
    try:
        # Получаем все записи
        records = get_all_dse_records()
        
        if not records:
            await query.edit_message_text(
                "❌ Нет записей для экспорта.\n\n"
                "Используйте /start для возврата в главное меню.",
                parse_mode='Markdown'
            )
            return
        
        await query.edit_message_text(
            f"⏳ Создаю PDF отчёт...\n"
            f"Всего записей: {len(records)}",
            parse_mode='Markdown'
        )
        
        # Создаём PDF для каждой записи
        from telegram import InputFile
        import os
        
        for i, record in enumerate(records[:10], 1):  # Ограничение 10 файлов за раз
            try:
                filename = f"dse_report_{record.get('dse', 'unknown').replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                pdf_file = create_dse_pdf_report(record, filename)
                
                if pdf_file and os.path.exists(pdf_file):
                    # Отправляем PDF файл
                    with open(pdf_file, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=query.message.chat_id,
                            document=f,
                            filename=filename,
                            caption=f"📄 Отчёт {i}/{len(records)}: {record.get('dse', 'N/A')}"
                        )
                    
                    # Удаляем временный файл
                    os.remove(pdf_file)
            except Exception as e:
                print(f"Ошибка создания PDF для записи {i}: {e}")
                continue
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ Экспорт завершён!\n"
                 f"Создано отчётов: {min(len(records), 10)}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Ошибка при экспорте: {str(e)}",
            reply_markup=reply_markup
        )


async def handle_pdf_export_select(update, context):
    """Выбор записей для экспорта в PDF"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from .dse_manager import get_all_dse_records
    
    query = update.callback_query
    await query.answer("⏳ Загрузка записей...")
    
    try:
        # Получаем все записи
        records = get_all_dse_records()
        
        if not records:
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Нет записей для экспорта.",
                reply_markup=reply_markup
            )
            return
        
        # Создаём кнопки выбора по ДСЕ (группируем одинаковые)
        dse_dict = {}
        for record in records:
            dse = record.get('dse', 'N/A')
            if dse not in dse_dict:
                dse_dict[dse] = []
            dse_dict[dse].append(record)
        
        keyboard = []
        
        # Показываем первые 10 ДСЕ
        for i, (dse, dse_records) in enumerate(list(dse_dict.items())[:10]):
            count = len(dse_records)
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 {dse} ({count} зап.)",
                    callback_data=f'pdf_select_dse_{dse.replace("/", "-")}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("📥 Экспорт выбранных", callback_data='pdf_export_selected')])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "� *Выборочный экспорт PDF*\n\n"
            "Выберите ДСЕ для экспорта:\n"
            f"(Доступно ДСЕ: {len(dse_dict)})\n\n"
            "💡 _Выберите один или несколько ДСЕ, затем нажмите 'Экспорт выбранных'_",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Сохраняем список ДСЕ в контексте
        user_id = str(query.from_user.id)
        if not hasattr(context, 'user_data'):
            context.user_data = {}
        context.user_data[user_id] = {
            'pdf_export_mode': 'select',
            'dse_dict': dse_dict,
            'selected_dse': []
        }
        
    except Exception as e:
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Ошибка при загрузке записей: {str(e)}",
            reply_markup=reply_markup
        )


if __name__ == "__main__":
    # Тестовые данные
    test_record = {
        'dse': 'DSE-123/456',
        'problem_type': 'Проблема с настройкой',
        'rc': '11102',
        'description': 'Подробное описание проблемы, которая возникла при работе с данным ДСЕ. Необходимо настроить параметры и проверить работу системы.',
        'datetime': '2025-10-03 14:30:00',
        'user_display': 'Иванов И.И.'
    }
    
    filename = create_dse_pdf_report(test_record, 'test_report.pdf')
    if filename:
        print(f"PDF отчет создан: {filename}")
    else:
        print("Ошибка создания PDF отчета")


async def handle_pdf_select_dse(update, context, dse_name):
    """Обработка выбора ДСЕ для экспорта"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    # Получаем данные пользователя
    if not hasattr(context, 'user_data') or user_id not in context.user_data:
        await query.answer("❌ Сессия истекла. Начните заново.", show_alert=True)
        return
    
    user_context = context.user_data[user_id]
    selected = user_context.get('selected_dse', [])
    
    # Восстанавливаем оригинальное имя ДСЕ (с "/")
    dse_name = dse_name.replace("-", "/")
    
    # Переключаем выбор
    if dse_name in selected:
        selected.remove(dse_name)
        await query.answer(f"❌ {dse_name} удалён из выбора")
    else:
        selected.append(dse_name)
        await query.answer(f"✅ {dse_name} добавлен в выбор")
    
    user_context['selected_dse'] = selected
    
    # Обновляем меню с отметками
    dse_dict = user_context.get('dse_dict', {})
    keyboard = []
    
    for i, (dse, dse_records) in enumerate(list(dse_dict.items())[:10]):
        count = len(dse_records)
        mark = "✅ " if dse in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{mark}📄 {dse} ({count} зап.)",
                callback_data=f'pdf_select_dse_{dse.replace("/", "-")}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton(
        f"📥 Экспорт выбранных ({len(selected)})",
        callback_data='pdf_export_selected'
    )])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Выборочный экспорт PDF*\n\n"
        "Выберите ДСЕ для экспорта:\n"
        f"(Доступно ДСЕ: {len(dse_dict)})\n"
        f"(Выбрано: {len(selected)})\n\n"
        "💡 _Нажмите на ДСЕ для выбора, затем 'Экспорт выбранных'_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_pdf_export_selected(update, context):
    """Экспорт выбранных ДСЕ в PDF"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import os
    
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    # Получаем данные пользователя
    if not hasattr(context, 'user_data') or user_id not in context.user_data:
        await query.answer("❌ Сессия истекла. Начните заново.", show_alert=True)
        return
    
    user_context = context.user_data[user_id]
    selected_dse = user_context.get('selected_dse', [])
    dse_dict = user_context.get('dse_dict', {})
    
    if not selected_dse:
        await query.answer("❌ Не выбраны ДСЕ для экспорта", show_alert=True)
        return
    
    await query.answer()
    await query.edit_message_text("⏳ Генерация PDF файлов...")
    
    try:
        exported_count = 0
        total_records = sum(len(dse_dict[dse]) for dse in selected_dse if dse in dse_dict)
        
        for dse in selected_dse:
            if dse not in dse_dict:
                continue
            
            records = dse_dict[dse]
            
            for i, record in enumerate(records[:10]):  # Максимум 10 записей на ДСЕ
                try:
                    filename = create_dse_pdf_report(record)
                    
                    if filename and os.path.exists(filename):
                        with open(filename, 'rb') as pdf_file:
                            await context.bot.send_document(
                                chat_id=query.message.chat_id,
                                document=pdf_file,
                                filename=f"DSE_{record.get('dse', 'N/A')}_{record.get('num', i+1)}.pdf",
                                caption=f"📄 Отчёт ДСЕ: {record.get('dse', 'N/A')}"
                            )
                        
                        os.remove(filename)
                        exported_count += 1
                
                except Exception as e:
                    print(f"Ошибка экспорта записи: {e}")
                    continue
        
        # Возвращаемся в меню
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ *Экспорт завершён!*\n\n"
                 f"Выбрано ДСЕ: {len(selected_dse)}\n"
                 f"Всего записей: {total_records}\n"
                 f"Экспортировано PDF: {exported_count}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Очищаем контекст
        context.user_data[user_id] = {}
        
    except Exception as e:
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='pdf_export_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Ошибка экспорта: {str(e)}",
            reply_markup=reply_markup
        )