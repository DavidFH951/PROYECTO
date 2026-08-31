from datetime import date, datetime, timedelta
import math

from django.contrib.auth.models import User
from django.db import models
from django.utils.dateparse import parse_date

# ----------------------------------------------------
# 0. MODELO PERÍODO ACADÉMICO / TEMPORADA
# ----------------------------------------------------
class PeriodoAcademico(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(max_length=20, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Período Académico"
        verbose_name_plural = "Períodos Académicos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def obtener_cronograma_semanas(self):
        inicio = self.fecha_inicio
        fin = self.fecha_fin

        # Normalizar a objeto date por seguridad
        if isinstance(inicio, str):
            inicio = parse_date(inicio)
        elif isinstance(inicio, datetime):
            inicio = inicio.date()

        if isinstance(fin, str):
            fin = parse_date(fin)
        elif isinstance(fin, datetime):
            fin = fin.date()

        if not inicio or not fin or inicio > fin:
            return [{'numero': i, 'inicio': None, 'fin': None, 'etiqueta': f"Semana {i}"} for i in range(1, 11)]

        semanas = []
        fecha_actual = inicio
        num = 1

        while fecha_actual <= fin:
            fin_semana = fecha_actual + timedelta(days=6)
            if fin_semana > fin:
                fin_semana = fin

            semanas.append({
                'numero': num,
                'inicio': fecha_actual,
                'fin': fin_semana,
                'etiqueta': f"Semana {num} ({fecha_actual.strftime('%d/%m')} - {fin_semana.strftime('%d/%m')})"
            })
            fecha_actual = fin_semana + timedelta(days=1)
            num += 1

        return semanas
# ----------------------------------------------------
# 1. MODELO CURSO
# ----------------------------------------------------
class Curso(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    imagen_portada = models.ImageField(upload_to='cursos_portadas/', blank=True, null=True)
    docentes = models.ManyToManyField(User, related_name='cursos_asignados', blank=True)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.SET_NULL, related_name='cursos', null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

    @property
    def docentes_nombres(self):
        nombres = [d.get_full_name() or d.username for d in self.docentes.all()]
        return ", ".join(nombres) if nombres else "Sin asignar"


# ----------------------------------------------------
# 2. MODELO MATERIAL DE CLASE
# ----------------------------------------------------
class Material(models.Model):
    TIPO_OPCIONES = [
        ('CLASE', 'Clase Grabada / Diapositivas'),
        ('LECTURA', 'Lectura / PDF'),
        ('EXAMEN', 'Examen / Simulacro'),
        ('TAREA', 'Tarea Práctica'),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='materiales')
    titulo = models.CharField(max_length=200, verbose_name="Título del Material")
    tipo = models.CharField(max_length=50, choices=TIPO_OPCIONES, default='CLASE')
    semana = models.PositiveSmallIntegerField(default=1, verbose_name="Semana / Sesión")
    archivo = models.FileField(upload_to='materiales/%Y/%m/', null=True, blank=True, verbose_name="Archivo Adjunto (PDF, ZIP, etc.)")
    enlace = models.URLField(max_length=500, null=True, blank=True, verbose_name="Enlace Externo (Video, Meet, Drive)")
    enlace_web = models.URLField(max_length=500, null=True, blank=True, verbose_name="Enlace Web Alternativo")
    contenido = models.TextField(blank=True, verbose_name="Instrucciones o Detalles Adicionales")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['semana', '-fecha_subida']

    def __str__(self):
        return f"[Semana {self.semana}] {self.titulo}"


# ----------------------------------------------------
# 3. MODELO INSCRIPCIÓN / MATRÍCULA
# ----------------------------------------------------
class Inscripcion(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscripciones')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='inscripciones')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        unique_together = ('alumno', 'curso')

    def __str__(self):
        return f"{self.alumno.username} en {self.curso.titulo}"


# ----------------------------------------------------
# 4. MODELO NOTAS Y CALIFICACIONES
# ----------------------------------------------------
class Calificacion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='calificaciones')
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones')
    nota1 = models.FloatField(null=True, blank=True, verbose_name="Examen Parcial")
    nota2 = models.FloatField(null=True, blank=True, verbose_name="Evaluación Continua")
    nota3 = models.FloatField(null=True, blank=True, verbose_name="Examen Final")

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        unique_together = ('curso', 'alumno')

    def __str__(self):
        return f"{self.alumno.username} - {self.curso.titulo}"


# ----------------------------------------------------
# 5. MODELO LOG DE ACTIVIDAD
# ----------------------------------------------------
class LogActividad(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255)
    detalles = models.TextField(blank=True, null=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Actividad'
        verbose_name_plural = 'Logs de Actividad'

    def __str__(self):
        return f"[{self.fecha.strftime('%d/%m/%Y %H:%M')}] {self.usuario}: {self.accion}"