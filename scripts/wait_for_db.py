#!/usr/bin/env python
"""
Скрипт для ожидания доступности базы данных
"""

import time
import psycopg2
import sys
import os
from decouple import config

def wait_for_db():
    """Ожидание доступности базы данных"""
    db_config = {
        'dbname': config('DB_NAME', default='online_school'),
        'user': config('DB_USER', default='online_school_user'),
        'password': config('DB_PASSWORD', default='online_school_pass'),
        'host': config('DB_HOST', default='localhost'),
        'port': config('DB_PORT', default='5432'),
    }
    
    max_attempts = 30
    attempt = 0
    
    print("Ожидание доступности базы данных...")
    
    while attempt < max_attempts:
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            print("✅ База данных доступна!")
            return True
        except psycopg2.OperationalError as e:
            attempt += 1
            print(f"Попытка {attempt}/{max_attempts}: База данных недоступна, ждем...")
            time.sleep(2)
        except Exception as e:
            attempt += 1
            print(f"Попытка {attempt}/{max_attempts}: Ошибка подключения: {e}")
            time.sleep(2)
    
    print("❌ Не удалось подключиться к базе данных")
    return False

if __name__ == '__main__':
    if wait_for_db():
        sys.exit(0)
    else:
        sys.exit(1)