-- Логируем начало выполнения скрипта
DO $$ BEGIN RAISE NOTICE 'Starting database initialization'; END $$;

-- Создаём схему, если нужно
CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS "User" (
    user_id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255)
);
DO $$ BEGIN RAISE NOTICE 'Table "User" created'; END $$;

CREATE TABLE IF NOT EXISTS "Operator" (
    operator_id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS "Chat" (
    chat_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    status VARCHAR(20) DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "User"(user_id)
);

DO $$ BEGIN RAISE NOTICE 'Table "Chat" created'; END $$;

CREATE TABLE IF NOT EXISTS "Message" (
    message_id SERIAL PRIMARY KEY,
    chat_id INTEGER,
    sender_type VARCHAR(10) CHECK (sender_type IN ('USER', 'BOT', 'OPERATOR')),
    responder_id INTEGER,
    text TEXT,
    send_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES "Chat"(chat_id),
    FOREIGN KEY (responder_id) REFERENCES "Operator"(operator_id)
);

DO $$ BEGIN RAISE NOTICE 'Table "Message" created'; END $$;
