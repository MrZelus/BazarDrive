CREATE TABLE IF NOT EXISTS guest_feed_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    guest_profile_id TEXT NOT NULL,
    reaction_type TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES guest_feed_posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, guest_profile_id)
);

CREATE INDEX IF NOT EXISTS idx_guest_feed_reactions_post_id
    ON guest_feed_reactions(post_id);

CREATE INDEX IF NOT EXISTS idx_guest_feed_reactions_post_reaction_type
    ON guest_feed_reactions(post_id, reaction_type);
