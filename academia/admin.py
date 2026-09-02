from django.contrib import admin
from .models import PeriodoAcademico, Curso, Material, Inscripcion, Calificacion, LogActividad,BannerCarrusel, ConfiguracionLanding

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'fecha_inicio', 'fecha_fin', 'activo')
    list_editable = ('activo',)
    search_fields = ('nombre', 'codigo')

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'periodo')
    search_fields = ('titulo',)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'semana', 'fecha_subida')
    list_filter = ('semana',)

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'curso', 'fecha_inscripcion')

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'curso')

@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'fecha')
    list_filter = ('accion',)

@admin.register(BannerCarrusel)
class BannerCarruselAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'orden', 'activo')
    list_editable = ('orden', 'activo')

@admin.register(ConfiguracionLanding)
class ConfiguracionLandingAdmin(admin.ModelAdmin):
    # Evita crear múltiples registros: solo debe existir una configuración general
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)