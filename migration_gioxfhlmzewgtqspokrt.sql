-- Migration: Create userbot-orders tables for project gioxfhlmzewgtqspokrt
-- Execute this in Supabase Dashboard → SQL Editor

-- Create chats table (userbot-orders specific)
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(50) UNIQUE NOT NULL,
    chat_name VARCHAR(255) NOT NULL,
    chat_type VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_chats_chat_id ON chats(chat_id);
CREATE INDEX IF NOT EXISTS ix_chats_active_type ON chats(is_active, chat_type);

-- Create messages table (userbot-orders specific)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(50) NOT NULL,
    chat_id VARCHAR(50) NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    author_id VARCHAR(50) NOT NULL,
    author_name VARCHAR(255),
    text TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_messages_id_chat UNIQUE(message_id, chat_id)
);

CREATE INDEX IF NOT EXISTS ix_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS ix_messages_author_id ON messages(author_id);
CREATE INDEX IF NOT EXISTS ix_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS ix_messages_chat_timestamp ON messages(chat_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_messages_processed ON messages(processed);

-- Create orders table (userbot-orders specific)
CREATE TABLE IF NOT EXISTS userbot_orders (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(50) UNIQUE NOT NULL,
    chat_id VARCHAR(50) NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    author_id VARCHAR(50) NOT NULL,
    author_name VARCHAR(255),
    text TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    detected_by VARCHAR(20) NOT NULL,
    telegram_link VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exported BOOLEAN NOT NULL DEFAULT FALSE,
    feedback VARCHAR(20),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_userbot_orders_chat_id ON userbot_orders(chat_id);
CREATE INDEX IF NOT EXISTS ix_userbot_orders_author_id ON userbot_orders(author_id);
CREATE INDEX IF NOT EXISTS ix_userbot_orders_category ON userbot_orders(category);
CREATE INDEX IF NOT EXISTS ix_userbot_orders_created_at ON userbot_orders(created_at);
CREATE INDEX IF NOT EXISTS ix_userbot_orders_category_created ON userbot_orders(category, created_at);
CREATE INDEX IF NOT EXISTS ix_userbot_orders_exported_created ON userbot_orders(exported, created_at);
CREATE INDEX IF NOT EXISTS ix_userbot_orders_relevance ON userbot_orders(relevance_score);

-- Create stats table
CREATE TABLE IF NOT EXISTS stats (
    id SERIAL PRIMARY KEY,
    date VARCHAR(10) UNIQUE NOT NULL,
    total_messages INTEGER NOT NULL DEFAULT 0,
    detected_orders INTEGER NOT NULL DEFAULT 0,
    regex_detections INTEGER NOT NULL DEFAULT 0,
    llm_detections INTEGER NOT NULL DEFAULT 0,
    llm_tokens_used INTEGER NOT NULL DEFAULT 0,
    llm_cost FLOAT NOT NULL DEFAULT 0.0,
    avg_response_time_ms INTEGER NOT NULL DEFAULT 0,
    false_positive_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stats_date ON stats(date);

-- Create chat_stats table
CREATE TABLE IF NOT EXISTS chat_stats (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(50) NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    date VARCHAR(10) NOT NULL,
    messages_count INTEGER NOT NULL DEFAULT 0,
    orders_count INTEGER NOT NULL DEFAULT 0,
    order_percentage FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chat_stats_date UNIQUE(chat_id, date)
);

CREATE INDEX IF NOT EXISTS ix_chat_stats_chat_id ON chat_stats(chat_id);
CREATE INDEX IF NOT EXISTS ix_chat_stats_date ON chat_stats(date);

-- Create feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES userbot_orders(id) ON DELETE CASCADE,
    feedback_type VARCHAR(20) NOT NULL,
    reason VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_feedback_order_id ON feedback(order_id);
CREATE INDEX IF NOT EXISTS ix_feedback_order_type ON feedback(order_id, feedback_type);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for stats.updated_at
DROP TRIGGER IF EXISTS update_stats_updated_at ON stats;
CREATE TRIGGER update_stats_updated_at 
    BEFORE UPDATE ON stats
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Verify tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('chats', 'messages', 'userbot_orders', 'stats', 'chat_stats', 'feedback')
ORDER BY table_name;

