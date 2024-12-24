# Isaac's Magic Site

README last updated by Griffin Clark on Dec 23 2024

## Setup

### Using Docker

Note that we're using one Dockerfile for both the Django server and Mysql database because it's simpler initially. This will probably be split up in future versions.

0. Ensure that you have Docker Desktop installed and running
1. Build the container with `docker build -t isaac-magic-app .`
2. Run the container with `docker run --env-file .env -p 8000:8000 isaac-magic-app`

### Manual

1. Make sure you have Python 3.13 and mysql installed on your computer
   1. If you set up on a Mac and installed mysql with brew, you can use `brew services start mysql` to ensure that the database is started.
2. Create a .env from the sample.env and enter the correct values. Then go into Settings.py and edit the root password for mysql to be equal to what it is on your machine.
3. Build the database by going into your mysql shell and running `CREATE DATABASE magic_db2 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;`
4. Create and activate your virtual environment
5. Install pipenv with `python3 -m pip install pipenv`
6. Run `pipenv install` to install all packages from the Pipfile
7. Activate pipenv with `pipenv shell`
8. Run `python manage.py makemigrations a_rtchat` and `python manage.py makemigrations a_users` to... do stuff. Idk mysql
9. Run `python manage.py migrate` to set up the database
10. Run `python django-starter-main/manage.py runserver` to build the application

## Potential Errors

### Mac

If you encounter an SSL certificate verification error, use the command `python3 -m pip install certifi && /Applications/Python\ 3.13/Install\ Certificates.command` to install and fix the certificates. Then, verify it with `python -m ssl`