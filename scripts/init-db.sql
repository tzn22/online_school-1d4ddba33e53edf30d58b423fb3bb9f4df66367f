-- init-db.sql
-- Скрипт инициализации базы данных PostgreSQL

-- Создание базы данных
CREATE DATABASE online_school OWNER online_school_user;

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- Настройка прав доступа
GRANT ALL PRIVILEGES ON DATABASE online_school TO online_school_user;

-- Создание дополнительных схем (если нужно)
-- CREATE SCHEMA IF NOT EXISTS analytics;
-- GRANT USAGE ON SCHEMA analytics TO online_school_user;
-- GRANT CREATE ON SCHEMA analytics TO online_school_user;

-- Настройка параметров базы данных
ALTER DATABASE online_school SET timezone TO 'Europe/Moscow';
ALTER DATABASE online_school SET client_encoding TO 'UTF8';
ALTER DATABASE online_school SET default_transaction_isolation TO 'read committed';

-- Создание ролей для различных типов пользователей
-- CREATE ROLE readonly_user;
-- GRANT CONNECT ON DATABASE online_school TO readonly_user;
-- GRANT USAGE ON SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Создание индексов для часто используемых полей
-- Эти индексы будут созданы через миграции Django, но здесь пример:
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON accounts_user(email);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_courses_level ON courses_course(level);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lessons_start_time ON courses_lesson(start_time);

-- Создание функций для обслуживания
-- CREATE OR REPLACE FUNCTION cleanup_old_sessions()
-- RETURNS void AS $$
-- BEGIN
--     DELETE FROM django_session WHERE expire_date < NOW();
-- END;
-- $$ LANGUAGE plpgsql;

-- Создание заданий для регулярного обслуживания
-- SELECT cron.schedule('cleanup-sessions', '0 2 * * *', $$SELECT cleanup_old_sessions()$$);

-- Вывод информации о создании
SELECT 'Database online_school created successfully' as message;