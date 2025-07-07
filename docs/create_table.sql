-- Discord 메시지 저장 테이블 생성
CREATE TABLE IF NOT EXISTS discord_messages (
    id BIGINT PRIMARY KEY,  -- Discord 메시지 ID (unique)
    channel_id BIGINT NOT NULL,
    channel_name TEXT,
    server_id BIGINT,
    server_name TEXT,
    author_id BIGINT NOT NULL,
    author_name TEXT NOT NULL,
    author_discriminator TEXT,
    author_avatar TEXT,
    content TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    message_type TEXT DEFAULT 'Default',
    is_pinned BOOLEAN DEFAULT FALSE,
    reference_message_id BIGINT,
    attachments JSONB DEFAULT '[]'::jsonb,
    embeds JSONB DEFAULT '[]'::jsonb,
    reactions JSONB DEFAULT '[]'::jsonb,
    mentions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_discord_messages_channel_id ON discord_messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_discord_messages_server_id ON discord_messages(server_id);
CREATE INDEX IF NOT EXISTS idx_discord_messages_author_id ON discord_messages(author_id);
CREATE INDEX IF NOT EXISTS idx_discord_messages_timestamp ON discord_messages(timestamp);

-- RLS (Row Level Security) 비활성화 (API key로 접근하므로)
ALTER TABLE discord_messages DISABLE ROW LEVEL SECURITY;

-- 코멘트 추가
COMMENT ON TABLE discord_messages IS 'Discord 채팅 메시지 저장 테이블';
COMMENT ON COLUMN discord_messages.id IS 'Discord 메시지 고유 ID';
COMMENT ON COLUMN discord_messages.channel_id IS 'Discord 채널 ID';
COMMENT ON COLUMN discord_messages.server_id IS 'Discord 서버(길드) ID';
COMMENT ON COLUMN discord_messages.author_id IS '메시지 작성자 ID';
COMMENT ON COLUMN discord_messages.content IS '메시지 내용';
COMMENT ON COLUMN discord_messages.timestamp IS '메시지 작성 시간';
COMMENT ON COLUMN discord_messages.attachments IS '첨부파일 정보 (JSON)';
COMMENT ON COLUMN discord_messages.embeds IS '임베드 정보 (JSON)';
COMMENT ON COLUMN discord_messages.reactions IS '반응(이모지) 정보 (JSON)';
COMMENT ON COLUMN discord_messages.mentions IS '멘션 정보 (JSON)'; 