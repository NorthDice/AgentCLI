#!/bin/bash
# Скрипт для установки зависимостей

# Проверка наличия pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3 не установлен. Установка pip..."
    sudo apt update
    sudo apt install python3-pip -y
fi

# Проверка наличия venv модуля
if ! python3 -m venv --help &> /dev/null; then
    echo "python3-venv не установлен. Установка..."
    sudo apt install python3-venv -y
fi

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv .venv

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source "$(pwd)/.venv/bin/activate"

# Установка зависимостей
echo "Установка зависимостей..."
pip install -e .

echo "Настройка завершена. Активируйте виртуальное окружение командой:"
echo "source \"$(pwd)/.venv/bin/activate\""
