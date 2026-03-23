CREATE TABLE IF NOT EXISTS guest_feed_post_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    url TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES guest_feed_posts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_guest_feed_post_media_post_id
    ON guest_feed_post_media(post_id);

CREATE INDEX IF NOT EXISTS idx_guest_feed_post_media_post_position
    ON guest_feed_post_media(post_id, position);
