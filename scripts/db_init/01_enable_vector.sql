-- This script runs automatically when the container starts for the first time
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify it works
SELECT * FROM pg_extension WHERE extname = 'vector';