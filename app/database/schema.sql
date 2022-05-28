-- drop existing tables
DROP SCHEMA IF EXISTS wcs CASCADE;

-- create schema and its tables
CREATE SCHEMA wcs;

-- case insensitive text
CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA wcs;

CREATE TABLE IF NOT EXISTS wcs.customer (
    cust_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    phone_country_code text NOT NULL,
    phone_number text NOT NULL,
    full_name text NOT NULL,
    short_name text NOT NULL, -- how to address the customer
    email_address citext UNIQUE, -- email address is (in practice) case insensitive
    UNIQUE (phone_country_code, phone_number)
);

CREATE TABLE IF NOT EXISTS wcs.guest_customer (
    g_cust_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    -- guest_customer must enter phone_number or email_address when joining a room
    -- this info is stored to be able to contact guest_customer later

    phone_country_code text,
    phone_number text,
    email_address citext UNIQUE, -- email address is (in practice) case insensitive
    short_name text NOT NULL, -- how to address the customer
    UNIQUE (phone_country_code, phone_number)
);

CREATE TABLE IF NOT EXISTS wcs.representative (
    rep_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    full_name text NOT NULL,
    short_name text NOT NULL,
    -- representatives login by entering email_address and password
    email_address citext NOT NULL UNIQUE,
    password text NOT NULL
);

CREATE TABLE IF NOT EXISTS wcs.call_log (
    call_log_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    rep_id bigint NOT NULL,
    -- one of the cust_ids will be null
    cust_id bigint,
    g_cust_id bigint,
    call_start_timestamp timestamp NOT NULL,
    call_length_secs integer NOT NULL,
    active_talked_secs integer,
    camera_on_secs integer
);

CREATE TABLE IF NOT EXISTS wcs.meeting_room (
    room_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    password text NOT NULL,
    rep_id bigint UNIQUE, -- representative can create at most one room simultaneously
    -- one of the cust_ids will be null

    cust_id bigint,
    g_cust_id bigint,
    title text not null,
    description text not null
);

ALTER TABLE wcs.call_log
    ADD FOREIGN KEY (rep_id) REFERENCES wcs.representative (rep_id),
    ADD FOREIGN KEY (cust_id) REFERENCES wcs.customer (cust_id),
    ADD FOREIGN KEY (g_cust_id) REFERENCES wcs.guest_customer (g_cust_id);

ALTER TABLE wcs.meeting_room
    ADD FOREIGN KEY (rep_id) REFERENCES wcs.representative (rep_id),
    ADD FOREIGN KEY (cust_id) REFERENCES wcs.customer (cust_id),
    ADD FOREIGN KEY (g_cust_id) REFERENCES wcs.guest_customer (g_cust_id);

