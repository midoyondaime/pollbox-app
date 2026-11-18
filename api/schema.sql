-- OVERVIEW
-- Database schema of pollbox: polls, their options, and the votes.
-- Safe to run several times (IF NOT EXISTS); the API runs it at startup.

-- A poll: one question.
CREATE TABLE IF NOT EXISTS polls (
    -- Auto-incremented identifier.
    id         SERIAL PRIMARY KEY,
    -- The question shown to voters; it cannot be empty.
    question   TEXT NOT NULL,
    -- When the poll was created; the database fills it in.
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- An option of a poll (one answer a voter can pick).
CREATE TABLE IF NOT EXISTS options (
    -- Auto-incremented identifier.
    id      SERIAL PRIMARY KEY,
    -- The poll this option belongs to; deleting the poll deletes its options.
    poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    -- The text of the option.
    label   TEXT NOT NULL
);

-- One vote = one row, pointing at the chosen option.
CREATE TABLE IF NOT EXISTS votes (
    -- BIGSERIAL because there can be many more votes than polls.
    id         BIGSERIAL PRIMARY KEY,
    -- The option that received the vote; deleting the option deletes its votes.
    option_id  INTEGER NOT NULL REFERENCES options(id) ON DELETE CASCADE,
    -- When the vote was recorded.
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
