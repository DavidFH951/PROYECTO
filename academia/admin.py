from django.contrib import admin
from .models import Curso, Material, Inscripcion, Nota

admin.site.register(Curso)
admin.site.register(Material)
admin.site.register(Inscripcion)
admin.site.register(Nota)