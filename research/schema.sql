-- RhymeTextVQA SQLite schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS licenses (
    license_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS rhymes (
    rhyme_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    full_text TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    license_id INTEGER REFERENCES licenses(license_id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pages (
    page_id TEXT PRIMARY KEY,
    rhyme_id TEXT NOT NULL REFERENCES rhymes(rhyme_id) ON DELETE CASCADE,
    page_index INTEGER NOT NULL DEFAULT 0,
    image_path TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    split TEXT NOT NULL CHECK (split IN ('train', 'val', 'test')),
    illustration_prompt TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (rhyme_id, page_index)
);

CREATE TABLE IF NOT EXISTS ocr_tokens (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id TEXT NOT NULL REFERENCES pages(page_id) ON DELETE CASCADE,
    token_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    x1 REAL NOT NULL,
    y1 REAL NOT NULL,
    x2 REAL NOT NULL,
    y2 REAL NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    line_index INTEGER,
    UNIQUE (page_id, token_index)
);

CREATE TABLE IF NOT EXISTS objects (
    object_id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id TEXT NOT NULL REFERENCES pages(page_id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    x1 REAL NOT NULL,
    y1 REAL NOT NULL,
    x2 REAL NOT NULL,
    y2 REAL NOT NULL,
    attributes_json TEXT NOT NULL DEFAULT '{}',
    relation_hint TEXT
);

CREATE TABLE IF NOT EXISTS qa_pairs (
    qa_id TEXT PRIMARY KEY,
    page_id TEXT NOT NULL REFERENCES pages(page_id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answers_json TEXT NOT NULL,
    answer_type TEXT NOT NULL CHECK (answer_type IN ('text', 'object', 'relation')),
    reviewed INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pages_split ON pages(split);
CREATE INDEX IF NOT EXISTS idx_ocr_page ON ocr_tokens(page_id);
CREATE INDEX IF NOT EXISTS idx_objects_page ON objects(page_id);
CREATE INDEX IF NOT EXISTS idx_qa_page ON qa_pairs(page_id);
