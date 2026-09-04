from datetime import date, datetime, timedelta
import math

from django.contrib.auth.models import User
from django.db import models
from django.utils.dateparse import parse_date
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


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


# ----------------------------------------------------
# 6. MODELOS DINÁMICOS DE LA PORTADA
# ----------------------------------------------------
class BannerCarrusel(models.Model):
    titulo = models.CharField(max_length=150, help_text="Descripción o referencia de la foto", default="Banner Médico")
    imagen = models.ImageField(upload_to='carrusel/', verbose_name="Imagen de Fondo (Horizontal)")
    orden = models.PositiveIntegerField(default=1, help_text="Orden de aparición: 1, 2, 3...")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Banner del Carrusel"
        verbose_name_plural = "Banners del Carrusel"
        ordering = ['orden']

    def __str__(self):
        return f"Slide #{self.orden} - {self.titulo}"


class ConfiguracionLanding(models.Model):
    # Textos del Hero Principal
    hero_badge = models.CharField(max_length=120, default="🩺 Especialistas en Formación y Ciencias de la Salud")
    hero_titulo = models.CharField(max_length=200, default="Formando a los Mejores Profesionales de la Salud")
    hero_subtitulo = models.TextField(default="Metodología de alto rendimiento, docentes médicos especializados y resolución de casos reales para potenciar tu nivel académico.")
    
    # Textos Institucionales
    sobre_nosotros_titulo = models.CharField(max_length=200, default="Comprometidos con la excelencia y el rigor científico")
    sobre_nosotros_texto_1 = models.TextField(default="En Academia Galeno nos dedicamos al fortalecimiento de competencias en estudiantes y profesionales de ciencias de la salud.")
    sobre_nosotros_texto_2 = models.TextField(default="Contamos con una infraestructura virtual moderna orientada a la resolución ágil de dudas y a la asimilación profunda de cada asignatura médica.")
    sobre_nosotros_imagen = models.ImageField(upload_to='institucional/', null=True, blank=True, verbose_name="Foto Sobre Nosotros")

    mision = models.TextField(default="Brindar una educación complementaria y de especialización médica accesible, estructurada y exigente que potencie el rendimiento y la capacidad de toma de decisiones clínicas.")
    vision = models.TextField(default="Ser la academia líder de formación y actualización en ciencias médicas a nivel nacional, reconocida por el rigor de sus programas y el éxito de sus egresados.")
    valores = models.TextField(default="Rigor científico, compromiso con la salud humana, integridad profesional, innovación pedagógica constante y vocación de servicio docente.")

    # Datos de Contacto Directo
    whatsapp_contacto = models.CharField(max_length=20, default="51999999999", help_text="Código de país seguido del número (ej. 51987654321)")
    correo_contacto = models.EmailField(default="informes@academiagaleno.pe")
    horario_atencion = models.CharField(max_length=100, default="Lun - Sáb: 8:00 AM - 8:00 PM")

    class Meta:
        verbose_name = "Configuración de la Portada"
        verbose_name_plural = "Configuración de la Portada"

    def __str__(self):
        return "Configuración General de la Portada"

class Prospecto(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    dni = models.CharField(max_length=12)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField()
    curso_interes = models.CharField(max_length=150)
    fecha_contacto = models.DateTimeField(auto_now_add=True)
    contactado = models.BooleanField(default=False)

class Examen(models.Model):
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='examenes')
    titulo = models.CharField(max_length=200, verbose_name="Título de la Evaluación")
    semana = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Semana del Ciclo",
        help_text="Semana donde se mostrará la evaluación"
    )
    descripcion = models.TextField(blank=True, verbose_name="Instrucciones")
    duracion_minutos = models.PositiveIntegerField(default=60, help_text="Tiempo límite en minutos")
    fecha_apertura = models.DateTimeField(null=True, blank=True, verbose_name="Fecha y hora de inicio")
    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name="Fecha y hora de cierre")
    activo = models.BooleanField(default=True, verbose_name="Habilitado")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    cantidad_preguntas_aleatorias = models.PositiveIntegerField(
        default=0,
        help_text="0 para mostrar todas las preguntas registradas, o un número (ej. 10) para extraer aleatoriamente solo esa cantidad del banco."
    )
    intentos_permitidos = models.PositiveIntegerField(
        default=1,
        verbose_name="Intentos Permitidos",
        help_text="Número máximo de veces que un estudiante puede rendir esta prueba."
    )
    cerrado_manualmente = models.BooleanField(
        default=False,
        verbose_name="Cerrado Manualmente por Docente",
        help_text="Si está activo, fuerza el autoenvío de las evaluaciones en curso."
    )
    @property
    def revision_disponible(self):
        """Permite ver el solucionario si venció la fecha límite o si el docente forzó el cierre."""
        if self.cerrado_manualmente:
           return True
        if not self.fecha_cierre:
           return True
        return timezone.now() > self.fecha_cierre

    class Meta:
        verbose_name = "Examen / Evaluación"
        verbose_name_plural = "Exámenes y Evaluaciones"

    def __str__(self):
        return f"[Semana {self.semana}] {self.titulo} - {self.curso.titulo}"

    @property
    def esta_disponible(self):
        """Determina si un alumno puede ingresar a rendir la prueba."""
        if not self.activo:
            return False
        ahora = timezone.now()
        if self.fecha_apertura and ahora < self.fecha_apertura:
            return False
        if self.fecha_cierre and ahora > self.fecha_cierre:
            return False
        return True

    @property
    def estado_texto(self):
        """Mensaje legible para mostrar al alumno en la interfaz."""
        if not self.activo:
            return "Evaluación pausada"
        ahora = timezone.now()
        if self.fecha_apertura and ahora < self.fecha_apertura:
            return f"Disponible desde {self.fecha_apertura.strftime('%d/%m %H:%M')}"
        if self.fecha_cierre and ahora > self.fecha_cierre:
            return "Evaluación finalizada"
        return "Disponible ahora"

class Pregunta(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='preguntas')
    enunciado = models.TextField(verbose_name="Enunciado de la Pregunta")
    explicacion = models.TextField(blank=True, verbose_name="Explicación / Justificación (Feedback médico)")
    puntaje = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Puntaje asignado")

    class Meta:
        verbose_name = "Pregunta de Examen"
        verbose_name_plural = "Banco de Preguntas"

    def __str__(self):
        return f"[{self.examen.titulo}] {self.enunciado[:60]}..."

class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones')
    texto = models.CharField(max_length=255, verbose_name="Opción de Respuesta")
    es_correcta = models.BooleanField(default=False, verbose_name="¿Es la respuesta correcta?")

    class Meta:
        verbose_name = "Opción de Respuesta"
        verbose_name_plural = "Opciones de Respuesta"

    def __str__(self):
        return f"{self.texto} ({'Correcta' if self.es_correcta else 'Incorrecta'})"

class IntentoExamen(models.Model):
    alumno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='intentos_examen')
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='intentos')
    nota = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    completado = models.BooleanField(default=False)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Intento de Examen"
        verbose_name_plural = "Resultados de Alumnos"

    def __str__(self):
        return f"{self.alumno.get_full_name()} - {self.examen.titulo} (Nota: {self.nota})"

class IntentoExamen(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='intentos_examen'
    )
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='intentos')
    nota = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    completado = models.BooleanField(default=False)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.alumno.username} - {self.examen.titulo} ({self.nota} pts)"

class RespuestaEstudiante(models.Model):
    """Guarda la alternativa que marcó el alumno para la revisión diferida."""
    intento = models.ForeignKey(IntentoExamen, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey('Pregunta', on_delete=models.CASCADE)
    opcion_seleccionada = models.ForeignKey('Opcion', on_delete=models.SET_NULL, null=True, blank=True)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Respuesta de Estudiante"
        verbose_name_plural = "Respuestas de Estudiantes"