-- Phase 4: Nonprofit Voice Amplification
-- Enables nonprofits to author impact stories, program descriptions, volunteer needs, leadership profiles

CREATE TABLE IF NOT EXISTS nonprofit_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('impact_story', 'program', 'volunteer_need', 'leadership')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    published_at TIMESTAMP,
    author_email TEXT NOT NULL,
    author_name TEXT,
    verified_at TIMESTAMP,
    verifier_notes TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, content_type, version)
);

CREATE TABLE IF NOT EXISTS nonprofit_content_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    body TEXT NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_by TEXT,
    FOREIGN KEY (content_id) REFERENCES nonprofit_content(id)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_nonprofit_content_ein_status ON nonprofit_content(ein, status);
CREATE INDEX IF NOT EXISTS idx_nonprofit_content_type ON nonprofit_content(content_type, status);
CREATE INDEX IF NOT EXISTS idx_nonprofit_content_published ON nonprofit_content(published_at DESC);
