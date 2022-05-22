-- drop existing tables
DROP TABLE IF EXISTS USER;

DROP TABLE IF EXISTS chat_room;

DROP TABLE IF EXISTS room_history;

-- configure sqlite
PRAGMA foreign_keys = ON;

-- create new tables
CREATE TABLE USER (
    user_id integer NOT NULL PRIMARY KEY,
    password text NOT NULL,
    email_address text UNIQUE, -- email address is (in practice) case insensitive
    full_name text,
    short_name text NOT NULL -- nickname for users
);

CREATE TABLE chat_room (
    chat_room_id integer NOT NULL PRIMARY KEY,
    created_by_user integer NOT NULL,
    name text NOT NULL UNIQUE, -- room name is case insensitive
    password text NOT NULL,
    description text NOT NULL,
    FOREIGN KEY (created_by_user) REFERENCES USER (user_id)
);

CREATE TABLE room_history (
    chat_room_id integer NOT NULL,
    user_id integer NOT NULL,
    date_joined text NOT NULL,
    PRIMARY KEY (chat_room_id, user_id)
);

