from django.db import models
from django.contrib.auth.models import User

# ----------------------------------------------------
# 1. MODELO CURSO
# ----------------------------------------------------
class Curso(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    imagen_portada = models.ImageField(upload_to='cursos_portadas/', blank=True, null=True)
    docentes = models.ManyToManyField(User, related_name='cursos_asignados', blank=True)
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
    archivo = models.FileField(upload_to='materiales/%Y/%m/', null=True, blank=True, verbose_name="Archivo Adjunto (PDF, ZIP, etc.)")
    enlace = models.URLField(max_length=500, null=True, blank=True, verbose_name="Enlace Externo (Video, Meet, Drive)")
    contenido = models.TextField(blank=True, verbose_name="Instrucciones o Detalles Adicionales")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"[{self.curso.titulo}] {self.titulo} ({self.get_tipo_display()})"


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


class Material(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='materiales')
    titulo = models.CharField(max_length=200)
    semana = models.PositiveSmallIntegerField(default=1, verbose_name="Semana / Sesión")  # <-- AGREGAR ESTA LÍNEA
    archivo = models.FileField(upload_to='materiales/', blank=True, null=True)
    enlace_web = models.URLField(blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['semana', '-fecha_subida']

    def __str__(self):
        return f"Semana {self.semana}: {self.titulo}"

# ----------------------------------------------------
# 4. MODELO NOTAS Y CALIFICACIONES
# ----------------------------------------------------
class Calificacion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='calificaciones')
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones')
    nota1 = models.FloatField(null=True, blank=True)
    nota2 = models.FloatField(null=True, blank=True)
    nota3 = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('curso', 'alumno')

    def __str__(self):
        return f"{self.alumno.username} - {self.curso.titulo}"

class LogActividad(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255)
    detalles = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Actividad'
        verbose_name_plural = 'Logs de Actividad'

    def __str__(self):
        return f"[{self.fecha.strftime('%d/%m/%Y %H:%M')}] {self.usuario}: {self.accion}"

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