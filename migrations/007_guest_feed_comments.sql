CREATE TABLE IF NOT EXISTS guest_feed_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    guest_profile_id TEXT,
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES guest_feed_posts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_guest_feed_comments_post_id
    ON guest_feed_comments(post_id);

CREATE INDEX IF NOT EXISTS idx_guest_feed_comments_created_at
    ON guest_feed_comments(created_at);
