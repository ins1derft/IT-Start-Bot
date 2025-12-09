-- ITStart schema (synced with models on 2025-12-09)
-- Requires pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'publication_type') THEN
        CREATE TYPE publication_type AS ENUM ('job', 'internship', 'conference', 'contest');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'publication_status') THEN
        CREATE TYPE publication_status AS ENUM ('new', 'declined', 'ready', 'sent');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tag_category') THEN
        CREATE TYPE tag_category AS ENUM ('format', 'occupation', 'platform', 'language', 'location', 'technology', 'duration');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'admin_role') THEN
        CREATE TYPE admin_role AS ENUM ('admin', 'moderator');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'parser_type') THEN
        CREATE TYPE parser_type AS ENUM ('api_client', 'website_parser', 'tg_channel_parser');
    END IF;
END$$;

-- Tables
CREATE TABLE IF NOT EXISTS publication (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    type publication_type NOT NULL,
    company TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_id UUID,
    created_at TIMESTAMP NOT NULL,
    vacancy_created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    editor_id UUID,
    is_edited BOOLEAN NOT NULL DEFAULT false,
    is_declined BOOLEAN NOT NULL DEFAULT false,
    deadline_at TIMESTAMP,
    contact_info TEXT,
    contact_info_encrypted BYTEA,
    deadline_notified BOOLEAN NOT NULL DEFAULT false,
    status publication_status NOT NULL DEFAULT 'new',
    decline_reason TEXT
);

CREATE TABLE IF NOT EXISTS tag (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category tag_category NOT NULL,
    CONSTRAINT uq_tag_name_category UNIQUE (name, category)
);

CREATE TABLE IF NOT EXISTS publication_tags (
    publication_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    PRIMARY KEY (publication_id, tag_id),
    CONSTRAINT fk_pubtag_publication FOREIGN KEY (publication_id) REFERENCES publication(id) ON DELETE CASCADE,
    CONSTRAINT fk_pubtag_tag FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tg_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tg_id BIGINT NOT NULL UNIQUE,
    register_at TIMESTAMP NOT NULL,
    refused_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS tg_user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    publication_type publication_type NOT NULL,
    deadline_reminder BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT uq_sub_user_type UNIQUE (user_id, publication_type),
    CONSTRAINT fk_sub_user FOREIGN KEY (user_id) REFERENCES tg_user(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tg_user_subscription_tags (
    subscription_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    PRIMARY KEY (subscription_id, tag_id),
    CONSTRAINT fk_subtag_subscription FOREIGN KEY (subscription_id) REFERENCES tg_user_subscriptions(id) ON DELETE CASCADE,
    CONSTRAINT fk_subtag_tag FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    PRIMARY KEY (user_id, tag_id),
    CONSTRAINT fk_pref_user FOREIGN KEY (user_id) REFERENCES tg_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_pref_tag FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS parser (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,
    executable_file_path TEXT NOT NULL,
    type parser_type NOT NULL,
    parsing_interval INTEGER NOT NULL,
    parsing_start_time TIMESTAMP NOT NULL,
    last_parsed_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS parsing_result (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date TIMESTAMP NOT NULL,
    parser_id UUID NOT NULL,
    success BOOLEAN NOT NULL,
    received_amount INTEGER NOT NULL,
    CONSTRAINT fk_parsing_result_parser FOREIGN KEY (parser_id) REFERENCES parser(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS admin_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role admin_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    otp_secret TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_admin_username UNIQUE (username)
);

CREATE TABLE IF NOT EXISTS admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id UUID,
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS publication_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publication_type publication_type NOT NULL,
    interval_minutes INTEGER NOT NULL,
    start_time TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_publication_schedule_type UNIQUE (publication_type)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_publication_type_created_at ON publication (type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_publication_tags_tag ON publication_tags (tag_id);
CREATE INDEX IF NOT EXISTS idx_parsing_result_parser_date ON parsing_result (parser_id, date);
CREATE INDEX IF NOT EXISTS idx_tg_user_refused_at ON tg_user (refused_at);
CREATE INDEX IF NOT EXISTS idx_tg_user_subscriptions_user_type ON tg_user_subscriptions (user_id, publication_type);
