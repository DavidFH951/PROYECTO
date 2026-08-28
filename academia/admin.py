from django.contrib import admin
from .models import Curso, Material, Inscripcion, Calificacion, LogActividad

admin.site.register(Curso)
admin.site.register(Material)
admin.site.register(Inscripcion)
admin.site.register(Calificacion)
admin.site.register(LogActividad)