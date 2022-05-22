# WebRTC Customer Service

We aim to provide free and open-source web conferencing application to be used in the customer service domain.

## Requirements

* Python 3
* Pip 3

## Running Server Locally

1. Install Python dependencies
    ```sh
    pip3 install -r requirements.txt
    ```
1. Initiate the PostgreSQL database with Flask CLI command
    ```sh
    flask init-db
    ```
1. [OPTIONAL] Insert mock data to database for test purposes. All mock passwords are `1234`.
    ```sh
    flask import-mock-data
    ```
1. Start the Flask server
    ```sh
    python app.py
    ```
1. Access the application from browser
    ```sh
    http://localhost:5000
    ```

## Routes

| Route | Description | Methods |
|:---:|---|:---:|
| /auth/register | Interface where user creates an account. | GET, POST |
| /auth/login | Interface where user enters the application with his account. | GET, POST |
| /auth/logout | Logouts from the user's account and clears the session. | GET |

## Application Interface

TODO

## Technologies

* [Python Flask](https://flask.palletsprojects.com/en/2.1.x/quickstart/) back-end
* [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/templates/) template engine for Flask
* HTML, CSS, JS front-end
* [Bootstrap 5.1](https://getbootstrap.com/docs/5.1/getting-started/introduction/) CSS framework
* [Socket.io](https://socket.io/docs/v4/client-api/) JS client API and [flask-socketio](https://flask-socketio.readthedocs.io/en/latest/getting_started.html) library
* [PostgreSQL](https://www.postgresql.org/about/) database
