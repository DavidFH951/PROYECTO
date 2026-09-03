from django.contrib import admin
from .models import PeriodoAcademico, Curso, Material, Inscripcion, Calificacion, LogActividad,BannerCarrusel, ConfiguracionLanding,Examen, Pregunta, Opcion, IntentoExamen

# 1. Primero defines el Inline de las alternativas
class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 4

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

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    inlines = [OpcionInline]
    list_display = ('enunciado_corto', 'examen', 'puntaje')
    list_filter = ('examen__curso', 'examen')
    search_fields = ('enunciado',)

    def enunciado_corto(self, obj):
        return obj.enunciado[:80] + "..." if len(obj.enunciado) > 80 else obj.enunciado
    enunciado_corto.short_description = "Enunciado"

# 3. Resto de modelos
@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'duracion_minutos', 'activo', 'fecha_creacion')
    list_filter = ('curso', 'activo')
    search_fields = ('titulo',)

@admin.register(IntentoExamen)
class IntentoExamenAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'examen', 'nota', 'completado', 'fecha_fin')
    list_filter = ('examen', 'completado')