-- Active: 1753569113741@@ssc-postree.postgres.database.azure.com@5432@connect@public

-- Table: companies
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    selection TEXT NOT NULL,
    selection_hash TEXT,
    selection_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL
);

CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    card_data TEXT NOT NULL,
    combination_name TEXT,
    combination_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    like_count INT DEFAULT 0,
    times_shown INT DEFAULT 0,
    last_time_shown TIMESTAMP NULL
);

CREATE TABLE prompt_templates (
    id SERIAL PRIMARY KEY,
    selection_key TEXT NOT NULL,
    selection_value TEXT,
    prompt TEXT,
    template_order INT
);

CREATE TABLE dynamics (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE session_cards (
    id SERIAL PRIMARY KEY,
    session_id  int,
    card_id int,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL
);

