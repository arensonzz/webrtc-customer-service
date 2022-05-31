-- wcs.representative table
INSERT INTO wcs.representative (PASSWORD, email_address, full_name, short_name)
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', 'admin@admin.com', 'Admin_name Admin_surname', 'Admin_name');

INSERT INTO wcs.representative (PASSWORD, email_address, full_name, short_name)
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', 'irennebach0@cyberchimps.com', 'Illa Rennebach', 'Illa');

INSERT INTO wcs.representative (PASSWORD, email_address, full_name, short_name)
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', 'aluxen1@hao123.com', 'Arin Luxen', 'Arin');

INSERT INTO wcs.representative (PASSWORD, email_address, full_name, short_name)
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', 'sturmel2@issuu.com', 'Saundra Turmel', 'Saundra');

INSERT INTO wcs.representative (PASSWORD, email_address, full_name, short_name)
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', 'ghaliburton3@businessweek.com', 'Giustino Haliburton', 'Giustino');

-- wcs.customer table
INSERT INTO wcs.customer (email_address, full_name, short_name, phone_number)
    VALUES ('nyukhnevich4@cargocollective.com', 'Netty Yukhnevich', 'Netty', '+905350984700');

INSERT INTO wcs.customer (email_address, full_name, short_name, phone_number)
    VALUES ('ahavill5@etsy.com', 'Adelind Havill', 'Adelind', '+905382354700');

INSERT INTO wcs.customer (email_address, full_name, short_name, phone_number)
    VALUES ('soboyle6@businessweek.com', 'Sam O''Boyle', 'Sam', '+905324558588');

INSERT INTO wcs.customer (email_address, full_name, short_name, phone_number)
    VALUES ('epoxton7@state.gov', 'Edik Poxton', 'Edik', '+905354142020');

INSERT INTO wcs.customer (email_address, full_name, short_name, phone_number)
    VALUES ('gmcatamney8@tumblr.com', 'Garrett McAtamney', 'Garrett', '+905350984704');

-- wcs.guest_customer table
INSERT INTO wcs.guest_customer (email_address, short_name)
    VALUES ('mclerc9@cpanel.net', 'Marylin');

INSERT INTO wcs.guest_customer (email_address, short_name, phone_number)
    VALUES ('mganninga@biblegateway.com', 'Mathe', '+905350984705');

-- wcs.meeting_room table
INSERT INTO wcs.meeting_room ("password", "rep_id", "cust_id", "title", "description")
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', (
            SELECT
                rep_id
            FROM
                wcs.representative
            WHERE
                email_address = 'admin@admin.com'), (
                SELECT
                    cust_id
                FROM
                    wcs.customer
                WHERE
                    full_name = 'Netty Yukhnevich'), 'Room With Customer', 'Room description with customer');

INSERT INTO wcs.meeting_room ("password", "rep_id", "title", "description")
    VALUES ('pbkdf2:sha256:260000$3aIZDCHQLv5OgReF$49961503ad05d6a7d1eeba8f56e5b48c1940b1fd3efe1d8a806b1d6ce7935700', (
            SELECT
                rep_id
            FROM
                wcs.representative
            WHERE
                full_name = 'Illa Rennebach'), 'Room With Guest', 'Room description with guest');

