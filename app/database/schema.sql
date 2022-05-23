CREATE SCHEMA wcs;

CREATE TABLE IF NOT EXISTS wcs.customers (
    customer_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    phone_number text NOT NULL UNIQUE,
    full_name text NOT NULL,
    short_name text NOT NULL, -- how to address the customer
    email_address citext UNIQUE -- email address is (in practice) case insensitive
);

CREATE TABLE IF NOT EXISTS wcs.guest_customers (
    guest_customer_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    -- guest_customer must enter phone_number or email_address when joining a room
    -- this info is stored to be able to contact guest_customer later

    phone_number text UNIQUE,
    email_address citext UNIQUE, -- email address is (in practice) case insensitive
    nickname text NOT NULL
);

CREATE TABLE IF NOT EXISTS wcs.representatives (
    representative_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    full_name text NOT NULL,
    short_name text NOT NULL,
    -- representatives login by entering email_address and password
    email_address citext NOT NULL UNIQUE,
    hashed_password text NOT NULL
);

CREATE TABLE IF NOT EXISTS wcs.call_logs (
    call_log_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    representative_id bigint NOT NULL,
    -- one of the customer_ids will be null
    customer_id bigint,
    guest_customer_id bigint,
    call_start_timestamp timestamp NOT NULL,
    call_length_secs integer NOT NULL,
    active_talked_secs integer,
    camera_on_secs integer
);

CREATE TABLE IF NOT EXISTS wcs.meeting_rooms (
    meeting_room_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    representative_id bigint,
    -- one of the customer_ids will be null
    customer_id bigint,
    guest_customer_id bigint
);

ALTER TABLE wcs.call_logs
    ADD FOREIGN KEY (representative_id) REFERENCES wcs.representatives (representative_id),
    ADD FOREIGN KEY (customer_id) REFERENCES wcs.customers (customer_id),
    ADD FOREIGN KEY (guest_customer_id) REFERENCES wcs.guest_customers (guest_customer_id);

ALTER TABLE wcs.meeting_rooms
    ADD FOREIGN KEY (representative_id) REFERENCES wcs.representatives (representative_id),
    ADD FOREIGN KEY (customer_id) REFERENCES wcs.customers (customer_id),
    ADD FOREIGN KEY (guest_customer_id) REFERENCES wcs.guest_customers (guest_customer_id);

