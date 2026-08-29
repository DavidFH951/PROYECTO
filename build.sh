#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Crear superusuario automáticamente si no existe
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='davik951').exists() or User.objects.create_superuser('davik951', 'admin@galeno.com', 'davidfh159')"