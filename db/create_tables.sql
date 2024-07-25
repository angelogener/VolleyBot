-- Create sessions table
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    datetime TEXT NOT NULL,
    location TEXT NOT NULL,
    max_players INTEGER NOT NULL,
    rsvp_message_id BIGINT
);

-- Create rsvps table
CREATE TABLE rsvps (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    user_id BIGINT NOT NULL,
    status TEXT CHECK (status IN ('confirmed', 'waitlist')) NOT NULL,
    order_position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE rsvps ADD CONSTRAINT unique_order_per_session UNIQUE (session_id, order_position);

-- Create teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    team_number INTEGER NOT NULL
);

-- Create team_members table
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    user_id BIGINT NOT NULL
);

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    elo INTEGER DEFAULT 1000
);

-- Create matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    team1_id INTEGER REFERENCES teams(id),
    team2_id INTEGER REFERENCES teams(id),
    winner_id INTEGER REFERENCES teams(id)
);

-- Create player groups table
CREATE TABLE player_groups (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    group_name TEXT NOT NULL
);

-- Create player group members table
CREATE TABLE player_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES player_groups(id),
    user_id BIGINT NOT NULL
);
-- Create indexes for faster querying
CREATE INDEX idx_rsvps_session_id ON rsvps(session_id);
CREATE INDEX idx_rsvps_user_id ON rsvps(user_id);
CREATE INDEX idx_rsvps_session_order ON rsvps(session_id, order_position);
CREATE INDEX idx_teams_session_id ON teams(session_id);
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_users_discord_id ON users(discord_id);
CREATE INDEX idx_matches_session_id ON matches(session_id);
