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
                '/System/Library/Fonts/Arial.ttf',  # macOS
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
        
    def create_dse_report(self, record_data, output_filename):
        """
        Создать PDF отчет по заявке ДСЕ
        
        :param record_data: Словарь с данными заявки
        :param output_filename: Имя выходного файла
        :return: True если успешно, False если ошибка
        """
        try:
            # Создаем документ
            doc = SimpleDocTemplate(
                output_filename,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
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
            
            title = Paragraph("ОТЧЕТ ПО ЗАЯВКЕ ДСЕ".encode('utf-8').decode('utf-8'), title_style)
            story.append(title)
            story.append(Spacer(1, 10*mm))
            
            # Создаем таблицу как на изображении
            # Верхняя часть таблицы
            table_data = []
            
            # Заголовки
            headers = ['№ п/п', 'Дата', 'Деталь', 'Наименование ДСЕ', 'Номер УП', 'ФИО Наладчика', 'ФИО Программиста']
            # Убеждаемся, что все заголовки в правильной кодировке
            headers = [str(header) for header in headers]
            table_data.append(headers)
            
            # Строка с данными
            row_data = [
                '1',  # № п/п
                record_data.get('datetime', '').split()[0] if record_data.get('datetime') else '',  # Дата
                str(record_data.get('dse', '')),  # Деталь (ДСЕ)
                str(record_data.get('problem_type', '')),  # Наименование ДСЕ (Тип проблемы)
                str(record_data.get('rc', '')),  # Номер УП (РЦ)
                str(record_data.get('user_display', '')),  # ФИО Наладчика
                ''  # ФИО Программиста (пустое)
            ]
            # Убеждаемся, что все данные в правильной кодировке
            row_data = [str(item) for item in row_data]
            table_data.append(row_data)
            
            # Создаем таблицу
            table = Table(table_data, colWidths=[
                15*mm,  # № п/п
                25*mm,  # Дата
                25*mm,  # Деталь
                50*mm,  # Наименование ДСЕ
                25*mm,  # Номер УП
                35*mm,  # ФИО Наладчика
                35*mm   # ФИО Программиста
            ])
            
            # Стиль таблицы
            table.setStyle(TableStyle([
                # Границы
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Заголовки
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Данные
                ('FONTNAME', (0, 1), (-1, -1), self.font_name),
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
            
            desc_table = Table(desc_table_data, colWidths=[170*mm])
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