#!/bin/bash

cd ../code
echo "Running command makemigrations"
python manage.py makemigrations user_management
python manage.py makemigrations configuration
python manage.py makemigrations
echo "Running command migrate"
python manage.py migrate