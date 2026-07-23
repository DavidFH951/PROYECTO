from django.db import models
from django.contrib.auth.models import User

class Curso(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título del Curso")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    estado = models.BooleanField(default=True, verbose_name="Curso Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def __str__(self):
        return self.titulo

class Material(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='materiales')
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, choices=[('CLASE', 'Clase'), ('EXAMEN', 'Examen'), ('TAREA', 'Tarea')])
    contenido = models.TextField(blank=True, help_text="Texto, enlaces a videos o instrucciones")
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"

    def __str__(self):
        return f"{self.curso.titulo} - {self.titulo}"

class Inscripcion(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha_matricula = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"

    def __str__(self):
        return f"{self.alumno.username} inscrito en {self.curso.titulo}"

class Nota(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Nota final")
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"

    def __str__(self):
        return f"Nota de {self.alumno.username} en {self.curso.titulo}: {self.calificacion}"