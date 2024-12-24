#!/bin/bash

# This script serves as the entrypoint for the Docker container, ensuring that all necessary services and configurations are started when the container runs.
# It starts the MariaDB service, initializes the database and user with the necessary permissions, and runs Django migrations to set up the application's database schema.
# Finally, it starts the Django development server to make the application accessible.
# The Docker container uses this script to automate setup and ensure the environment is ready for the application to run seamlessly.

# Start MariaDB service
service mariadb start

# Initialize the database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS magic_db2 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'my_user'@'%' IDENTIFIED BY 'my_password';"
mysql -u root -e "GRANT ALL PRIVILEGES ON magic_db2.* TO 'my_user'@'%';"
mysql -u root -e "FLUSH PRIVILEGES;"

# Run Django migrations
python manage.py makemigrations a_rtchat
python manage.py makemigrations a_users
python manage.py migrate

# Start Django server
exec python manage.py runserver 0.0.0.0:8000
