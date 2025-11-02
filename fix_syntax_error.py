#!/usr/bin/env python3
import re

with open('final_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим и исправляем проблемную строку
problem_line = '''        message = f"✅ Выбрано часов: {selected_count}
Часы: {hours_text}
Нажмите '✅ Подтвердить выбор лотов' когда закончите"'''

fixed_line = '''        message = f"✅ Выбрано часов: {selected_count}\\nЧасы: {hours_text}\\n\\nНажмите '✅ Подтвердить выбор лотов' когда закончите"'''

content = content.replace(problem_line, fixed_line)

with open('final_bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print "✅ Синтаксическая ошибка исправлена!"
