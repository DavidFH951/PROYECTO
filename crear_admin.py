import os
import django

# Pega aquí dentro de las comillas tu External Database URL copiada de Render
os.environ['DATABASE_URL'] = 'postgresql://davik951:viT2t3HOylWrS207tOP5V9bFC7CGphVb@dpg-da963fp42hec73erm0qg-a.oregon-postgres.render.com/academiadb_4cn6'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'davik951'
password = 'davidfh159'
email = 'admin@galeno.com'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("¡Superusuario creado exitosamente!")
else:
    u = User.objects.get(username=username)
    u.set_password(password)
    u.save()
    print("¡Contraseña de davik951 actualizada exitosamente!")