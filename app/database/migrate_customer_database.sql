-- DEMONSTRATION OF DATABASE MIGRATION PROCESS
CREATE SCHEMA main;

-- firm's main database schema
CREATE TABLE IF NOT EXISTS main.customer (
    m_customer_id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    m_phone_number text NOT NULL UNIQUE, -- phone numbers are stored in E.164 standard
    m_full_name text NOT NULL,
    m_short_name text NOT NULL, -- how to address the customer
    m_email_address citext UNIQUE -- email address is (in practice) case insensitive
);

-- webrtc-customer-service (wcs)
CREATE SCHEMA wcs;

DROP TABLE IF EXISTS wcs.customer;

CREATE OR REPLACE VIEW wcs.customer AS
SELECT
    m_customer_id AS cust_id,
    m_phone_number AS phone_number,
    m_full_name AS full_name,
    m_short_name AS short_name,
    m_email_address AS email_address
FROM
    main.customer;

