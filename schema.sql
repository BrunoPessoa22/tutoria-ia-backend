-- Tutoria IA - PostgreSQL Schema
-- Phase 3: User Management & Progress Persistence

-- Users table (synced with Clerk)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP DEFAULT NOW()
);

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    current_level INTEGER DEFAULT 0,
    current_module INTEGER DEFAULT 0,
    current_lesson INTEGER DEFAULT 1,
    completed_lessons JSONB DEFAULT '[]',
    total_lessons_completed INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Conversation history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    lesson_number INTEGER NOT NULL,
    messages JSONB NOT NULL,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Student questions & responses (analytics)
CREATE TABLE IF NOT EXISTS student_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    student_level TEXT,
    lesson_number INTEGER,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    module TEXT,
    lesson_name TEXT
);

-- User achievements & badges
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,
    level_earned INTEGER,
    earned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, achievement_type, level_earned)
);

-- Learning streaks
CREATE TABLE IF NOT EXISTS learning_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_activity_date DATE DEFAULT CURRENT_DATE,
    UNIQUE(user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_clerk_id ON users(clerk_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_student_questions_user_id ON student_questions(user_id);
CREATE INDEX IF NOT EXISTS idx_student_questions_timestamp ON student_questions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_streaks_user_id ON learning_streaks(user_id);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_user_progress_updated_at BEFORE UPDATE ON user_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id,
    u.name,
    u.email,
    up.current_level,
    up.total_lessons_completed,
    ls.current_streak,
    ls.longest_streak,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT sq.id) as total_questions,
    COUNT(DISTINCT a.id) as total_achievements
FROM users u
LEFT JOIN user_progress up ON u.id = up.user_id
LEFT JOIN learning_streaks ls ON u.id = ls.user_id
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN student_questions sq ON u.id = sq.user_id
LEFT JOIN achievements a ON u.id = a.user_id
GROUP BY u.id, u.name, u.email, up.current_level, up.total_lessons_completed,
         ls.current_streak, ls.longest_streak;
