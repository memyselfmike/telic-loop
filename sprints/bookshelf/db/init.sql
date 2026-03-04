-- Bookshelf database initialization

CREATE TABLE IF NOT EXISTS books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(500) NOT NULL,
    genre VARCHAR(100),
    cover_url TEXT,
    status VARCHAR(20) DEFAULT 'want_to_read' CHECK(status IN ('want_to_read', 'reading', 'finished', 'abandoned')),
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    notes TEXT,
    date_added TIMESTAMPTZ DEFAULT NOW(),
    date_finished TIMESTAMPTZ
);

-- Create index on status for filtering performance
CREATE INDEX idx_books_status ON books(status);

-- Create index on genre for stats queries
CREATE INDEX idx_books_genre ON books(genre);
