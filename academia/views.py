import base64
import csv
from datetime import date
from functools import wraps
import io
import json
import os
from urllib.parse import quote
import uuid
import cloudinary.uploader

from axes.models import AccessAttempt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import qrcode

from .forms import (
    CursoForm,
    EditarUsuarioForm,
    InscripcionForm,
    PreguntaForm,
    RegistroUsuarioForm,
)
from .models import (
    Asistencia,
    BannerCarrusel,
    Calificacion,
    ConfiguracionLanding,
    Curso,
    GrupoCurso,
    Examen,
    HorarioCurso,
    Inscripcion,
    IntentoExamen,
    LogActividad,
    Material,
    Opcion,
    PeriodoAcademico,
    Pregunta,
    RespuestaEstudiante,
)
from .validators import validar_archivo_material


# ==============================================================================
# 1. DECORADORES, HELPERS Y AUDITORÍA (ANTI-IDOR Y 2FA)
# ==============================================================================

def requerir_2fa_si_esta_activo(view_func):
    """Verifica que el usuario haya completado el desafío 2FA si su cuenta lo tiene configurado."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            tiene_dispositivo = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            if tiene_dispositivo and not getattr(user, 'is_verified', lambda: False)():
                messages.warning(request, "Debes completar la verificación de dos pasos para acceder.")
                return redirect('verificar_2fa')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def registrar_log(request, accion, detalles=""):
    """Registra una acción en la tabla de auditoría con la IP del usuario."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    LogActividad.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        accion=accion,
        detalles=detalles,
        ip_origen=ip
    )


def es_administrador(user):
    """Verifica si el usuario tiene privilegios de administración."""
    return user.is_authenticated and (
        user.is_superuser or 
        user.is_staff or 
        user.groups.filter(name='Administrador').exists()
    )


def es_docente_valido(user):
    """Verifica si el usuario cuenta con el rol de docente o admin a nivel general."""
    return user.is_authenticated and (
        user.groups.filter(name='Docentes').exists() or 
        getattr(user, 'rol', None) == 'docente' or
        user.is_staff or 
        user.is_superuser
    )


def es_docente_del_curso(user, curso):
    """Valida si el usuario es docente asignado al curso específico o administrador del sistema."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return curso.docentes.filter(id=user.id).exists()


def es_alumno_del_curso(user, curso):
    """Valida si el estudiante está formalmente matriculado en el curso."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return Inscripcion.objects.filter(curso=curso, alumno=user).exists()


def _obtener_o_crear_token_sesion(request):
    """Gestiona un token UUID único por sesión para ofuscar las rutas del alumno."""
    token = request.session.get('dashboard_token')
    if not token:
        token = str(uuid.uuid4())
        request.session['dashboard_token'] = token
        request.session.modified = True
    return token


# ==============================================================================
# 2. AUTENTICACIÓN, LOGIN Y DOBLE FACTOR (2FA)
# ==============================================================================

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return redirect('verificar_2fa')
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        username = form.data.get('username', '').strip()
        limite = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
        
        intento = AccessAttempt.objects.filter(username=username).first()
        if intento:
            fallos = intento.failures_since_start
            restantes = max(0, limite - fallos)
            if restantes > 0:
                messages.error(
                    self.request,
                    f"Credenciales incorrectas. Te queda(n) {restantes} intento(s) antes del bloqueo temporal."
                )
        else:
            messages.error(
                self.request,
                f"Credenciales incorrectas. Te queda(n) {limite - 1} intento(s) antes del bloqueo temporal."
            )
        return response


def inicio_publico(request):
    """Landing page pública de la Academia."""
    periodo_activo = PeriodoAcademico.objects.filter(activo=True).first()
    cursos_qs = Curso.objects.select_related('periodo')

    if periodo_activo:
        cursos = cursos_qs.filter(periodo=periodo_activo)
        if not cursos.exists():
            cursos = cursos_qs.all()
    else:
        cursos = cursos_qs.all()

    banners = BannerCarrusel.objects.filter(activo=True).order_by('orden')
    config_landing, _ = ConfiguracionLanding.objects.get_or_create(id=1)

    context = {
        'periodo_activo': periodo_activo,
        'cursos_destacados': cursos,
        'banners': banners,
        'config': config_landing,
    }
    return render(request, 'inicio_publico.html', context)


def salir(request):
    """Cierra la sesión del usuario."""
    logout(request)
    return redirect('/cuentas/login/')


@login_required
def configurar_2fa(request):
    """Permite vincular 2FA exclusivamente a Administradores y Docentes."""
    user = request.user
    
    # Bloqueo para alumnos
    if not (user.is_staff or user.is_superuser or es_docente_valido(user)):
        messages.error(request, "Esta opción de seguridad no está habilitada para cuentas de estudiantes.")
        return redirect('mi_perfil')

    dispositivo_confirmado = TOTPDevice.objects.filter(user=user, confirmed=True).first()

    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        dispositivo_temp = TOTPDevice.objects.filter(user=user, confirmed=False).last()

        if dispositivo_temp and dispositivo_temp.verify_token(token):
            dispositivo_temp.confirmed = True
            dispositivo_temp.save()
            TOTPDevice.objects.filter(user=user, confirmed=True).exclude(id=dispositivo_temp.id).delete()
            registrar_log(request, "Seguridad 2FA", "Activó el doble factor de autenticación")
            messages.success(request, "Doble factor de autenticación (2FA) activado correctamente.")
            return redirect('mi_perfil')
        else:
            messages.error(request, "Código incorrecto o expirado. Inténtalo nuevamente.")

    dispositivo_temp = TOTPDevice.objects.filter(user=user, confirmed=False).last()
    if not dispositivo_temp:
        dispositivo_temp = TOTPDevice.objects.create(
            user=user, 
            name="Academia Galeno", 
            confirmed=False
        )

    secret_b32 = base64.b32encode(dispositivo_temp.bin_key).decode('ascii').replace('=', '')
    identificador = user.email if user.email else user.username
    emisor = "Academia Galeno"

    otp_url = (
        f"otpauth://totp/{quote(emisor)}:{quote(identificador)}"
        f"?secret={secret_b32}&issuer={quote(emisor)}&digits=6&period=30"
    )

    qr = qrcode.make(otp_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('ascii')

    context = {
        'tiene_2fa': dispositivo_confirmado is not None,
        'qr_b64': qr_b64,
        'secret_key': secret_b32,
        'emisor': emisor,
        'identificador': identificador,
    }
    return render(request, 'configurar_2fa.html', context)


@login_required
def verificar_2fa(request):
    """Valida el código OTP de 6 dígitos."""
    user = request.user
    tiene_dispositivo = TOTPDevice.objects.filter(user=user, confirmed=True).exists()

    if getattr(user, 'is_verified', lambda: False)() or not tiene_dispositivo:
        return redirect('dashboard')

    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        dispositivo = TOTPDevice.objects.filter(user=user, confirmed=True).first()

        if dispositivo and dispositivo.verify_token(token):
            otp_login(request, dispositivo)
            registrar_log(request, "Inicio de Sesión 2FA", "Verificación TOTP exitosa")
            return redirect('dashboard')
        else:
            messages.error(request, "Código de 6 dígitos inválido. Revisa tu aplicación Authenticator.")

    return render(request, 'verificar_2fa.html')


# ==============================================================================
# 3. REDIRECCIONES TRANSPARENTES A RUTAS CON UUID (PORTAL ESTUDIANTIL)
# ==============================================================================

@login_required
def redirigir_dashboard(request):
    token = _obtener_o_crear_token_sesion(request)
    return redirect('dashboard_token', token=token)


@login_required
def redirigir_mis_cursos(request):
    token = _obtener_o_crear_token_sesion(request)
    return redirect('mis_cursos_token', token=token)


@login_required
def redirigir_mis_notas(request):
    token = _obtener_o_crear_token_sesion(request)
    return redirect('mis_notas_token', token=token)


@login_required
def redirigir_mis_asistencias(request):
    token = _obtener_o_crear_token_sesion(request)
    return redirect('mis_asistencias_token', token=token)


@login_required
def redirigir_mi_perfil(request):
    token = _obtener_o_crear_token_sesion(request)
    return redirect('mi_perfil_token', token=token)

@login_required
def redirigir_detalle_curso(request, curso_id):
    token = _obtener_o_crear_token_sesion(request)
    return redirect('detalle_curso_token', token=token, curso_id=curso_id)


# ==============================================================================
# 4. PORTAL ESTUDIANTIL (DASHBOARD, CURSOS, NOTAS, ASISTENCIAS Y PERFIL)
# ==============================================================================

@login_required
def dashboard(request, token=None):
    usuario = request.user
    es_docente = usuario.groups.filter(name__iexact='Docentes').exists() or usuario.cursos_asignados.exists() or GrupoCurso.objects.filter(docente=usuario).exists()

    if es_docente:
        # 1. Cursos y Grupos asignados al Docente
        grupos_docente = GrupoCurso.objects.filter(docente=usuario, activo=True).select_related('curso')
        cursos_directos = usuario.cursos_asignados.filter(estado=True)
        cursos_grupos = [g.curso for g in grupos_docente if g.curso.estado]
        cursos = list({c.id: c for c in (list(cursos_directos) + cursos_grupos)}.values())

        # Horarios específicos que dicta este docente
        horarios = HorarioCurso.objects.filter(
            Q(grupo__in=grupos_docente) | Q(curso__in=cursos_directos, grupo__isnull=True)
        ).select_related('curso', 'grupo', 'grupo__docente').order_by('dia', 'hora_inicio')

        total_cursos = len(cursos)
        porcentaje_asistencia = 100.0

    else:
        # 2. Inscripciones del Estudiante (por Grupo o Curso General)
        inscripciones = Inscripcion.objects.filter(alumno=usuario).select_related('curso', 'grupo', 'grupo__docente')
        cursos = [ins.curso for ins in inscripciones if ins.curso.estado]
        
        # Obtenemos los grupos a los que pertenece el alumno
        grupos_inscritos = [ins.grupo for ins in inscripciones if ins.grupo is not None]
        cursos_sin_grupo = [ins.curso for ins in inscripciones if ins.grupo is None]

        # Solo traer los horarios de su grupo; si el curso no tiene grupos aún, trae el horario general
        horarios = HorarioCurso.objects.filter(
            Q(grupo__in=grupos_inscritos) | Q(curso__in=cursos_sin_grupo, grupo__isnull=True)
        ).select_related('curso', 'grupo', 'grupo__docente').order_by('dia', 'hora_inicio')

        total_cursos = len(cursos)
        
        # Cálculo de Asistencia Global del Alumno
        total_asist = Asistencia.objects.filter(alumno=usuario).count()
        if total_asist > 0:
            asistidas = Asistencia.objects.filter(alumno=usuario, estado__in=['P', 'T']).count()
            porcentaje_asistencia = round((asistidas / total_asist) * 100, 1)
        else:
            porcentaje_asistencia = 100.0

    context = {
        'cursos': cursos,
        'horarios': horarios,
        'total_cursos': total_cursos,
        'porcentaje_asistencia': porcentaje_asistencia,
        'es_docente': es_docente,
        'token': token,
    }
    return render(request, 'intranet_dashboard.html', context)


@login_required
def mis_cursos(request, token=None):
    """Aula Virtual: Redirige al docente a su panel o muestra materias al estudiante."""
    # 1. Si es docente, lo enviamos a su catálogo oficial
    if es_docente_valido(request.user):
        return redirect('panel_docente')

    # 2. Control de token para estudiantes
    if not token:
        return redirigir_mis_cursos(request)

    token_sesion = _obtener_o_crear_token_sesion(request)
    if str(token) != token_sesion:
        return redirect('mis_cursos_token', token=token_sesion)

    # 3. Consulta exclusiva de asignaturas matriculadas del estudiante
    inscripciones = Inscripcion.objects.filter(alumno=request.user).select_related('curso', 'curso__periodo')

    context = {
        'inscripciones': inscripciones,
        'token': token_sesion,
        'es_docente': False,
    }
    return render(request, 'mis_cursos.html', context)

@login_required
def mis_notas(request, token=None):
    """Consulta consolidada de calificaciones del estudiante."""
    user = request.user
    if es_docente_valido(user) and not user.groups.filter(name='Alumnos').exists():
        return redirect('docente_mis_calificaciones')

    if not token:
        return redirigir_mis_notas(request)

    token_sesion = _obtener_o_crear_token_sesion(request)
    if str(token) != token_sesion:
        return redirect('mis_notas_token', token=token_sesion)

    periodos = PeriodoAcademico.objects.all().order_by('-fecha_inicio')
    periodo_id = request.GET.get('periodo')

    if periodo_id:
        periodo_actual = PeriodoAcademico.objects.filter(id=periodo_id).first()
    else:
        periodo_actual = PeriodoAcademico.objects.filter(activo=True).first() or periodos.first()

    inscripciones = Inscripcion.objects.filter(alumno=user).select_related('curso', 'curso__periodo')

    if periodo_actual:
        inscripciones_periodo = inscripciones.filter(curso__periodo=periodo_actual)
        if inscripciones_periodo.exists():
            inscripciones = inscripciones_periodo

    calificaciones_dict = {
        c.curso_id: c for c in Calificacion.objects.filter(alumno=user)
    }

    reporte_cursos = []
    for insc in inscripciones:
        curso = insc.curso
        if not curso:
            continue

        calif = calificaciones_dict.get(curso.id)
        criterios = curso.obtener_criterios() if hasattr(curso, 'obtener_criterios') else []
        notas_map = calif.notas_detalle if (calif and calif.notas_detalle) else {}

        evaluaciones = []
        for crit in criterios:
            cod = crit.get("codigo")
            evaluaciones.append({
                'nombre': crit.get("nombre"),
                'codigo': cod,
                'nota': notas_map.get(cod)
            })

        reporte_cursos.append({
            'curso': curso,
            'evaluaciones': evaluaciones,
            'evaluaciones_json': json.dumps(evaluaciones),
            'formula': getattr(curso, 'formula_evaluacion', ''),
            'promedio': calif.promedio if (calif and calif.promedio is not None) else None
        })

    context = {
        'periodos': periodos,
        'periodo_actual': periodo_actual,
        'reporte_cursos': reporte_cursos,
        'token': token_sesion,
        'es_docente': False,
    }
    return render(request, 'notas.html', context)


@login_required
def mis_asistencias(request, token=None):
    """Consulta detallada de asistencias por curso."""
    user = request.user
    if user.groups.filter(name='Docentes').exists() and not user.is_staff:
        return redirect('docente_mis_asistencias')

    if not token:
        return redirigir_mis_asistencias(request)

    token_sesion = _obtener_o_crear_token_sesion(request)
    if str(token) != token_sesion:
        return redirect('mis_asistencias_token', token=token_sesion)

    inscripciones = Inscripcion.objects.filter(alumno=user).select_related('curso', 'curso__periodo')

    resumen_asistencias = []
    for insc in inscripciones:
        curso = insc.curso
        if not curso:
            continue

        registros = Asistencia.objects.filter(curso=curso, alumno=user).order_by('-fecha')
        total_sesiones = registros.count()
        presentes = registros.filter(estado='P').count()
        tardanzas = registros.filter(estado='T').count()
        faltas = registros.filter(estado='F').count()
        justificadas = registros.filter(estado='J').count()

        asistencias_validas = presentes + tardanzas + justificadas
        porcentaje = round((asistencias_validas / total_sesiones) * 100, 1) if total_sesiones > 0 else 100.0

        resumen_asistencias.append({
            'curso': curso,
            'porcentaje': porcentaje,
            'total_sesiones': total_sesiones,
            'presentes': presentes,
            'tardanzas': tardanzas,
            'faltas': faltas,
            'justificadas': justificadas,
            'detalles': registros,
        })

    context = {
        'resumen_asistencias': resumen_asistencias,
        'token': token_sesion,
        'es_docente': False,
    }
    return render(request, 'alumno_mis_asistencias.html', context)


@login_required
def mi_perfil(request, token=None):
    """Vista de perfil con datos del usuario y seguridad 2FA."""
    if not token:
        return redirigir_mi_perfil(request)

    token_sesion = _obtener_o_crear_token_sesion(request)
    if str(token) != token_sesion:
        return redirect('mi_perfil_token', token=token_sesion)

    es_docente = request.user.groups.filter(name='Docentes').exists()
    return render(request, 'perfil.html', {
        'token': token_sesion,
        'es_docente': es_docente,
    })


# ==============================================================================
# 5. AULA VIRTUAL, MATERIALES Y EVALUACIONES (ALUMNOS Y DOCENTES)
# ==============================================================================

@login_required
def detalle_curso(request, curso_id, token=None):
    """Detalle de contenidos, semanas y cronograma de una asignatura."""
    if not token:
        return redirigir_detalle_curso(request, curso_id)

    token_sesion = _obtener_o_crear_token_sesion(request)
    if str(token) != token_sesion:
        return redirect('detalle_curso_token', token=token_sesion, curso_id=curso_id)

    curso = get_object_or_404(Curso, id=curso_id)
    es_docente = es_docente_del_curso(request.user, curso)
    es_alumno = es_alumno_del_curso(request.user, curso)

    if not (es_docente or es_alumno):
        messages.error(request, "No tienes autorización para acceder a los contenidos de este curso.")
        return redirect('dashboard')

    periodo = curso.periodo or PeriodoAcademico.objects.filter(activo=True).first()
    if periodo:
        cronograma = periodo.obtener_cronograma_semanas()
    else:
        cronograma = [{'numero': i, 'inicio': None, 'fin': None, 'etiqueta': f"Semana {i}"} for i in range(1, 11)]

    materiales = list(curso.materiales.all().order_by('semana', '-fecha_subida'))
    examenes = list(curso.examenes.all().prefetch_related('preguntas'))

    bloques_semanas = []
    for sem in cronograma:
        mats_semana = [m for m in materiales if m.semana == sem['numero']]
        exams_semana = [e for e in examenes if e.semana == sem['numero']]
        bloques_semanas.append({
            'info': sem,
            'materiales': mats_semana,
            'examenes': exams_semana,
            'total_materiales': len(mats_semana),
            'total_recursos': len(mats_semana) + len(exams_semana)
        })

    notas = Calificacion.objects.filter(alumno=request.user, curso=curso) if not es_docente else None

    context = {
        'curso': curso,
        'materiales': materiales,
        'bloques_semanas': bloques_semanas,
        'cronograma': cronograma,
        'notas': notas,
        'periodo': periodo,
        'es_docente_curso': es_docente,
        'token': token_sesion,
    }
    return render(request, 'detalle_curso.html', context)

@login_required
def detalle_recurso(request, curso_id=None, material_id=None, token=None):
    if token:
        curso = get_object_or_404(Curso, token=token)
    else:
        curso = get_object_or_404(Curso, id=curso_id)
        
    recurso = get_object_or_404(Material, id=material_id, curso=curso)
    
    context = {
        'recurso': recurso,
        'curso': curso,
        'token': token,
    }
    es_docente = (
        request.user in curso.docentes.all() or
        request.user.is_staff or
        request.user.is_superuser
    )
    return render(request, 'detalle_recurso.html', {
        'curso': curso,
        'recurso': recurso,
        'es_docente': request.user == curso.docente or request.user.is_staff
    })

@login_required
def rendir_examen(request, examen_id):
    """Toma de evaluación para el estudiante con barajado dinámico."""
    examen = get_object_or_404(Examen, id=examen_id)
    es_docente = es_docente_del_curso(request.user, examen.curso)
    es_alumno = es_alumno_del_curso(request.user, examen.curso)

    if not (es_docente or es_alumno):
        messages.error(request, "No estás matriculado en el curso correspondiente a este examen.")
        return redirect('dashboard')

    if not es_docente:
        if not examen.esta_disponible:
            messages.error(request, f"Acceso restringido: {examen.estado_texto}.")
            return redirect('detalle_curso', curso_id=examen.curso.id)

        intentos_hechos = IntentoExamen.objects.filter(
            alumno=request.user, 
            examen=examen, 
            completado=True
        ).count()

        if intentos_hechos >= examen.intentos_permitidos:
            messages.warning(request, f"Has alcanzado el límite de intentos permitidos ({examen.intentos_permitidos}).")
            return redirect('revision_examen', examen_id=examen.id)

    queryset_preguntas = examen.preguntas.order_by('?')
    if getattr(examen, 'cantidad_preguntas_aleatorias', 0) > 0:
        preguntas = list(queryset_preguntas[:examen.cantidad_preguntas_aleatorias])
    else:
        preguntas = list(queryset_preguntas)

    for p in preguntas:
        p.opciones_aleatorias = list(p.opciones.order_by('?'))

    if request.method == 'POST':
        puntaje_total = 0.0
        intento = IntentoExamen.objects.create(
            alumno=request.user,
            examen=examen,
            completado=True,
            fecha_fin=timezone.now()
        )

        for pregunta in examen.preguntas.all():
            opcion_id = request.POST.get(f'pregunta_{pregunta.id}')
            if opcion_id:
                try:
                    opcion = Opcion.objects.get(id=opcion_id, pregunta=pregunta)
                    es_correcta = opcion.es_correcta
                    if es_correcta:
                        puntaje_total += float(pregunta.puntaje)
                    RespuestaEstudiante.objects.create(
                        intento=intento,
                        pregunta=pregunta,
                        opcion_seleccionada=opcion,
                        es_correcta=es_correcta
                    )
                except Opcion.DoesNotExist:
                    pass

        intento.nota = puntaje_total
        intento.save()

        registrar_log(request, "Rendición de Examen", f"Completó '{examen.titulo}' con nota {puntaje_total}")
        messages.success(request, f"Evaluación finalizada. Tu nota es: {puntaje_total} puntos.")
        return redirect('revision_examen', examen_id=examen.id)

    context = {
        'examen': examen,
        'preguntas': preguntas,
        'tiempo_segundos': examen.duracion_minutos * 60,
    }
    return render(request, 'rendir_examen.html', context)


@login_required
def revision_examen(request, examen_id):
    """Revisión de respuestas y retroalimentación del examen."""
    examen = get_object_or_404(Examen, id=examen_id)
    es_docente = es_docente_del_curso(request.user, examen.curso)
    es_alumno = es_alumno_del_curso(request.user, examen.curso)

    if not (es_docente or es_alumno):
        messages.error(request, "No estás autorizado a ver revisiones de este examen.")
        return redirect('dashboard')
    
    ultimo_intento = IntentoExamen.objects.filter(
        alumno=request.user, 
        examen=examen, 
        completado=True
    ).order_by('-fecha_fin').first()

    if not ultimo_intento and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No has realizado ningún intento en esta evaluación.")
        return redirect('detalle_curso', curso_id=examen.curso.id)

    respuestas = ultimo_intento.respuestas.select_related('pregunta', 'opcion_seleccionada').all() if ultimo_intento else []

    context = {
        'examen': examen,
        'intento': ultimo_intento,
        'respuestas': respuestas,
        'puede_ver_solucionario': examen.revision_disponible or request.user.is_staff,
    }
    return render(request, 'revision_examen.html', context)


@login_required
def verificar_estado_examen(request, examen_id):
    """Endpoint JSON para sincronizar cierres en tiempo real desde el cliente."""
    examen = get_object_or_404(Examen, id=examen_id)
    return JsonResponse({
        'cerrado': examen.cerrado_manualmente or not examen.activo
    })


# ==============================================================================
# 6. GESTIÓN DOCENTE (CALIFICACIONES, ASISTENCIAS Y CONTENIDOS)
# ==============================================================================

@login_required
def panel_docente(request):
    """Panel oficial del docente con sus asignaturas asignadas."""
    if not es_docente_valido(request.user):
        messages.error(request, "Acceso restringido a docentes.")
        return redirect('dashboard')

    if request.user.is_superuser or request.user.is_staff:
        cursos_qs = Curso.objects.all()
    else:
        cursos_qs = Curso.objects.filter(docentes=request.user)

    cursos = cursos_qs.select_related('periodo').prefetch_related('inscripciones').distinct()

    return render(request, 'panel_docente.html', {
        'cursos': cursos,
        'es_docente': True,
    })


@login_required
def subir_material(request, curso_id):
    """Subida de material didáctico validado con soporte para videos MP4/WebM y enlaces."""
    curso = get_object_or_404(Curso, id=curso_id)

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permiso para subir material a este curso.")
        return redirect('dashboard')

    periodo = curso.periodo or PeriodoAcademico.objects.filter(activo=True).first()
    cronograma = periodo.obtener_cronograma_semanas() if periodo else []

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        semana = request.POST.get('semana', 1)
        archivo = request.FILES.get('archivo')
        enlace = request.POST.get('enlace') or request.POST.get('enlace_web')

        if not titulo:
            messages.error(request, "El título del contenido es obligatorio.")
            return render(request, 'subir_material.html', {'curso': curso, 'cronograma': cronograma})

        if not archivo and not enlace:
            messages.error(request, "Debes adjuntar un archivo o ingresar un enlace web.")
            return render(request, 'subir_material.html', {'curso': curso, 'cronograma': cronograma})

        if archivo:
            # Límite ampliado a 60 MB para videos y documentos pesados
            max_bytes = 60 * 1024 * 1024
            if archivo.size > max_bytes:
                messages.error(request, "El archivo excede el tamaño máximo permitido de 60 MB.")
                return render(request, 'subir_material.html', {'curso': curso, 'cronograma': cronograma})

            extensiones_permitidas = {
                '.pdf', '.docx', '.doc', '.xlsx', '.xls', 
                '.pptx', '.ppt', '.zip', '.rar', '.jpg', '.jpeg', '.png',
                '.mp4', '.webm'
            }
            _, ext = os.path.splitext(archivo.name)
            ext = ext.lower()
            if ext not in extensiones_permitidas:
                messages.error(
                    request, 
                    f"Tipo de archivo no permitido ({ext}). Formatos admitidos: PDF, Office, comprimidos, imágenes y video MP4/WebM."
                )
                return render(request, 'subir_material.html', {'curso': curso, 'cronograma': cronograma})

            # Asignar el resource_type adecuado para Cloudinary
            if ext in ['.mp4', '.webm']:
                res_type = 'video'
            elif ext in ['.jpg', '.jpeg', '.png']:
                res_type = 'image'
            else:
                res_type = 'raw'

            try:
                # Subir directamente a Cloudinary con el tipo de recurso correcto
                resultado = cloudinary.uploader.upload(
                    archivo,
                    resource_type=res_type,
                    folder="academia_galeno/materiales/"
                )
                # Si el campo en la base de datos almacena el archivo/CloudinaryField:
                archivo = resultado.get('public_id') or resultado.get('secure_url')
            except Exception as e:
                # Si no usa el uploader manual o falla, continuar con fallback
                pass

        # Normalización automática de videos embebidos de YouTube
        if enlace and 'youtube.com/watch?v=' in enlace:
            video_id = enlace.split('v=')[-1].split('&')[0]
            enlace = f"https://www.youtube-nocookie.com/embed/{video_id}"
        elif enlace and 'youtu.be/' in enlace:
            video_id = enlace.split('youtu.be/')[-1].split('?')[0]
            enlace = f"https://www.youtube-nocookie.com/embed/{video_id}"

        Material.objects.create(
            curso=curso,
            titulo=titulo,
            semana=semana,
            archivo=archivo,
            enlace_web=enlace
        )
        registrar_log(request, "Subida de Contenido", f"Publicó '{titulo}' en la semana {semana} del curso '{curso.titulo}'")
        messages.success(request, f"Contenido '{titulo}' publicado exitosamente.")
        return redirect('detalle_curso', curso_id=curso.id)

    return render(request, 'subir_material.html', {'curso': curso, 'cronograma': cronograma})


@login_required
def eliminar_material(request, material_id):    
    """Elimina un material con control Anti-IDOR."""
    material = get_object_or_404(Material, id=material_id)
    curso = material.curso

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permiso para eliminar este material.")
        return redirect('dashboard')

    titulo_mat = material.titulo
    material.delete()
    registrar_log(request, "Eliminación de Material", f"Eliminó '{titulo_mat}' de '{curso.titulo}'")
    messages.success(request, f"Material '{titulo_mat}' eliminado.")
    return redirect('detalle_curso', curso_id=curso.id)


@login_required
def docente_mis_calificaciones(request):
    """Catálogo de cursos para registro de notas."""
    if not es_docente_valido(request.user):
        messages.error(request, "Acceso restringido a docentes.")
        return redirect('dashboard')

    cursos = Curso.objects.all() if (request.user.is_superuser or request.user.is_staff) else Curso.objects.filter(docentes=request.user)
    cursos_data = [
        {'curso': c, 'total_alumnos': Inscripcion.objects.filter(curso=c).count()}
        for c in cursos.select_related('periodo').distinct()
    ]
    return render(request, 'docente_mis_calificaciones.html', {'cursos_data': cursos_data})


@login_required
def docente_calificar_curso(request, curso_id):
    """Planilla dinámica de notas y cálculo de promedios."""
    curso = get_object_or_404(Curso, id=curso_id)

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes autorización para calificar esta materia.")
        return redirect('docente_mis_calificaciones')
    
    inscripciones = Inscripcion.objects.filter(curso=curso).select_related('alumno').order_by('alumno__last_name', 'alumno__first_name')
    criterios = curso.obtener_criterios()

    def parsear_nota(valor):
        if valor is not None and str(valor).strip() != '':
            try:
                val = round(float(str(valor).replace(',', '.')), 2)
                return max(0.0, min(20.0, val))
            except ValueError:
                return None
        return None

    if request.method == 'POST':
        accion = request.POST.get('accion', 'guardar_promediar')

        for insc in inscripciones:
            alumno_id = str(insc.alumno.id)
            detalle = {
                crit["codigo"]: parsear_nota(request.POST.get(f'nota_{crit["codigo"]}_{alumno_id}'))
                for crit in criterios
            }
            calificacion, _ = Calificacion.objects.get_or_create(curso=curso, alumno=insc.alumno)
            calificacion.notas_detalle = detalle

            if accion == 'guardar_promediar':
                calificacion.save()
            else:
                calificacion.save(update_fields=['notas_detalle'])

        messages.success(request, "Notas guardadas exitosamente.")
        return redirect('docente_calificar_curso', curso_id=curso.id)

    calificaciones_dict = {c.alumno_id: c for c in Calificacion.objects.filter(curso=curso)}
    filas = []

    for insc in inscripciones:
        calif = calificaciones_dict.get(insc.alumno.id)
        notas_map = calif.notas_detalle if (calif and calif.notas_detalle) else {}
        columnas_alumno = [
            {
                'codigo': crit["codigo"],
                'valor': f"{notas_map[crit['codigo']]:.2f}" if isinstance(notas_map.get(crit["codigo"]), (int, float)) else (notas_map.get(crit["codigo"]) or '')
            }
            for crit in criterios
        ]
        filas.append({
            'alumno': insc.alumno,
            'columnas': columnas_alumno,
            'promedio': calif.promedio if (calif and calif.promedio is not None) else None
        })

    context = {
        'curso': curso,
        'criterios': criterios,
        'filas_calificaciones': filas,
        'formula_evaluacion': curso.formula_evaluacion,
    }
    return render(request, 'docente_calificar.html', context)


@login_required
def docente_mis_asistencias(request):
    """Catálogo de materias del docente para toma de asistencia."""
    if not es_docente_valido(request.user):
        messages.error(request, "Acceso restringido a docentes.")
        return redirect('dashboard')

    cursos = Curso.objects.all() if (request.user.is_superuser or request.user.is_staff) else Curso.objects.filter(docentes=request.user)
    cursos_data = [
        {'curso': c, 'total_alumnos': Inscripcion.objects.filter(curso=c).count()}
        for c in cursos.select_related('periodo').distinct()
    ]
    return render(request, 'docente_mis_asistencias.html', {
        'cursos_data': cursos_data,
        'hoy': date.today().strftime('%Y-%m-%d'),
    })


@login_required
def docente_asistencia_curso(request, curso_id):
    """Toma de asistencia y gestión de sesiones."""
    curso = get_object_or_404(Curso, id=curso_id)

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permisos para gestionar este curso.")
        return redirect('panel_docente')

    fechas_qs = (
        Asistencia.objects.filter(curso=curso)
        .values_list('fecha', flat=True)
        .distinct()
        .order_by('fecha')
    )
    
    sesiones_existentes = [
        {
            'numero': idx,
            'fecha': f,
            'fecha_str': f.strftime('%Y-%m-%d'),
            'fecha_formateada': f.strftime('%d/%m/%Y'),
        }
        for idx, f in enumerate(fechas_qs, start=1)
    ]

    fecha_param = request.GET.get('fecha')
    if fecha_param:
        try:
            fecha_sesion = date.fromisoformat(fecha_param)
        except ValueError:
            fecha_sesion = date.today()
    elif sesiones_existentes:
        fecha_sesion = sesiones_existentes[-1]['fecha']
    else:
        fecha_sesion = date.today()

    sesion_actual_num = next((s['numero'] for s in sesiones_existentes if s['fecha'] == fecha_sesion), len(sesiones_existentes) + 1)
    semana = int(request.GET.get('semana', sesion_actual_num))

    inscripciones = (
        Inscripcion.objects.filter(curso=curso)
        .select_related('alumno')
        .order_by('alumno__last_name', 'alumno__first_name')
    )

    if request.method == 'POST':
        semana_post = int(request.POST.get('semana', semana))
        try:
            fecha_guardar = date.fromisoformat(request.POST.get('fecha', str(fecha_sesion)))
        except ValueError:
            fecha_guardar = date.today()

        total_marcados = 0
        for insc in inscripciones:
            if not insc.alumno:
                continue
            estado = request.POST.get(f'asistencia_{insc.alumno.id}', 'P')
            Asistencia.objects.update_or_create(
                curso=curso,
                alumno=insc.alumno,
                fecha=fecha_guardar,
                defaults={'semana': semana_post, 'estado': estado}
            )
            total_marcados += 1

        registrar_log(request, "Control Asistencia", f"Sesión {sesion_actual_num} ({fecha_guardar}) en '{curso.titulo}'")
        messages.success(request, f"Asistencia guardada para la Sesión {sesion_actual_num}.")
        return redirect(f"{request.path}?fecha={fecha_guardar}&semana={semana_post}")

    asistencias_existentes = {
        a.alumno_id: a.estado
        for a in Asistencia.objects.filter(curso=curso, fecha=fecha_sesion)
    }

    filas = [
        {
            'alumno': insc.alumno,
            'inscripcion': insc,
            'estado': asistencias_existentes.get(insc.alumno.id, 'P')
        }
        for insc in inscripciones if insc.alumno
    ]

    context = {
        'curso': curso,
        'semana': semana,
        'fecha_sesion': fecha_sesion.strftime('%Y-%m-%d'),
        'sesiones_existentes': sesiones_existentes,
        'sesion_actual_num': sesion_actual_num,
        'filas': filas,
        'hoy_str': date.today().strftime('%Y-%m-%d'),
        'es_docente': True,  # <-- ESTA LÍNEA SINCRONIZA EL ROL
    }
    return render(request, 'docente_asistencia.html', context)


@login_required
def crear_examen_curso(request, curso_id):
    """Creación de exámenes por el docente."""
    curso = get_object_or_404(Curso, id=curso_id)

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permisos para programar evaluaciones.")
        return redirect('detalle_curso', curso_id=curso.id)

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        semana = request.POST.get('semana', 1)
        duracion = request.POST.get('duracion_minutos', 60)
        intentos = request.POST.get('intentos_permitidos', 1)
        cant_aleatorias = request.POST.get('cantidad_preguntas_aleatorias', 0)
        fecha_apertura = request.POST.get('fecha_apertura') or None
        fecha_cierre = request.POST.get('fecha_cierre') or None
        descripcion = request.POST.get('descripcion', '')

        if titulo:
            Examen.objects.create(
                curso=curso,
                titulo=titulo,
                semana=int(semana),
                duracion_minutos=int(duracion),
                intentos_permitidos=int(intentos),
                cantidad_preguntas_aleatorias=int(cant_aleatorias) if str(cant_aleatorias).isdigit() else 0,
                fecha_apertura=fecha_apertura,
                fecha_cierre=fecha_cierre,
                descripcion=descripcion,
                activo=True
            )
            registrar_log(request, "Creación de Examen", f"Creó examen '{titulo}' para '{curso.titulo}'")
            messages.success(request, f"Evaluación '{titulo}' programada exitosamente.")
        else:
            messages.error(request, "El título de la evaluación es obligatorio.")

    return redirect('detalle_curso', curso_id=curso.id)


@login_required
def toggle_examen(request, examen_id):
    """Habilita o pausa un examen."""
    examen = get_object_or_404(Examen, id=examen_id)
    if not es_docente_del_curso(request.user, examen.curso):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('dashboard')

    examen.activo = not examen.activo
    examen.save()
    messages.success(request, f"Evaluación '{examen.titulo}' {'habilitada' if examen.activo else 'pausada'}.")
    return redirect('detalle_curso', curso_id=examen.curso.id)


@login_required
def eliminar_examen(request, examen_id):
    """Eliminación de un examen."""
    examen = get_object_or_404(Examen, id=examen_id)
    curso_id = examen.curso.id

    if not es_docente_del_curso(request.user, examen.curso):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('dashboard')

    titulo = examen.titulo
    examen.delete()
    registrar_log(request, "Eliminación de Examen", f"Eliminó '{titulo}' de curso ID {curso_id}")
    messages.success(request, f"Evaluación '{titulo}' eliminada.")
    return redirect('detalle_curso', curso_id=curso_id)


@login_required
def banco_preguntas_curso(request, curso_id):
    """Gestión de banco de preguntas reactivas."""
    curso = get_object_or_404(Curso, id=curso_id)

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permisos para gestionar este banco de preguntas.")
        return redirect('detalle_curso', curso_id=curso.id)

    examenes_curso = Examen.objects.filter(curso=curso)

    if request.method == 'POST':
        form = PreguntaForm(request.POST, curso=curso)
        if form.is_valid():
            pregunta = form.save()
            correcta = form.cleaned_data['opcion_correcta']
            for idx in ['1', '2', '3', '4']:
                Opcion.objects.create(
                    pregunta=pregunta, 
                    texto=form.cleaned_data[f'opcion_{idx}'], 
                    es_correcta=(correcta == idx)
                )
            messages.success(request, "Pregunta agregada con éxito al banco.")
            return redirect('banco_preguntas_curso', curso_id=curso.id)
    else:
        form = PreguntaForm(curso=curso)

    preguntas = Pregunta.objects.filter(examen__curso=curso).prefetch_related('opciones').order_by('-id')

    context = {
        'curso': curso,
        'form': form,
        'preguntas': preguntas,
        'examenes_curso': examenes_curso,
    }
    return render(request, 'banco_preguntas.html', context)


@login_required
def eliminar_pregunta(request, pregunta_id):
    """Elimina una pregunta del banco."""
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    curso = pregunta.examen.curso

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permisos para eliminar preguntas de este curso.")
        return redirect('dashboard')

    pregunta.delete()
    messages.success(request, "Pregunta eliminada correctamente.")
    return redirect('banco_preguntas_curso', curso_id=curso.id)


@login_required
def descargar_plantilla_preguntas(request):
    """Descarga de plantilla Excel (.xlsx) para banco de preguntas."""
    if not es_docente_valido(request.user):
        messages.error(request, "Acceso restringido a docentes.")
        return redirect('dashboard')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BancoPreguntas"

    headers = [
        "Enunciado de la Pregunta",
        "Alternativa A",
        "Alternativa B",
        "Alternativa C",
        "Alternativa D",
        "Respuesta Correcta (A, B, C o D)",
        "Puntaje",
        "Explicación Clínica (Opcional)"
    ]
    ws.append(headers)

    header_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    ejemplo = [
        "¿Cuál es el agente causal más frecuente de la infección del tracto urinario?",
        "Escherichia coli", "Staphylococcus aureus", "Klebsiella pneumoniae", "Pseudomonas aeruginosa",
        "A", 2.0, "E. coli representa más del 80% de los casos comunitarios."
    ]
    ws.append(ejemplo)

    for col_idx in range(1, len(ejemplo) + 1):
        cell = ws.cell(row=2, column=col_idx)
        cell.border = thin_border
        cell.alignment = Alignment(vertical="center")

    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 25
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 45

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_preguntas_galeno.xlsx"'
    return response


@login_required
def importar_preguntas_curso(request, curso_id):
    """Importación masiva de preguntas desde Excel."""
    curso = get_object_or_404(Curso, id=curso_id)

    if not es_docente_del_curso(request.user, curso):
        messages.error(request, "No tienes permisos para esta acción.")
        return redirect('detalle_curso', curso_id=curso.id)

    if request.method == 'POST' and request.FILES.get('archivo_preguntas'):
        examen_id = request.POST.get('examen_id')
        archivo = request.FILES['archivo_preguntas']

        if not examen_id:
            messages.error(request, "Debes seleccionar una evaluación de destino.")
            return redirect('banco_preguntas_curso', curso_id=curso.id)

        examen = get_object_or_404(Examen, id=examen_id, curso=curso)

        try:
            wb = openpyxl.load_workbook(archivo, data_only=True)
            ws = wb.active
            creadas = 0

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue

                enunciado = str(row[0]).strip()
                op_a = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
                op_b = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
                op_c = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
                op_d = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
                correcta = str(row[5]).strip().upper() if len(row) > 5 and row[5] is not None else "A"

                try:
                    puntaje = float(row[6]) if len(row) > 6 and row[6] is not None else 1.0
                except (ValueError, TypeError):
                    puntaje = 1.0

                explicacion = str(row[7]).strip() if len(row) > 7 and row[7] is not None else ""

                if not enunciado or not op_a:
                    continue

                pregunta = Pregunta.objects.create(
                    examen=examen,
                    enunciado=enunciado,
                    explicacion=explicacion,
                    puntaje=puntaje
                )
                Opcion.objects.create(pregunta=pregunta, texto=op_a, es_correcta=(correcta == 'A'))
                Opcion.objects.create(pregunta=pregunta, texto=op_b, es_correcta=(correcta == 'B'))
                Opcion.objects.create(pregunta=pregunta, texto=op_c, es_correcta=(correcta == 'C'))
                Opcion.objects.create(pregunta=pregunta, texto=op_d, es_correcta=(correcta == 'D'))
                creadas += 1

            registrar_log(request, "Importación Masiva", f"Cargó {creadas} preguntas en '{examen.titulo}'")
            messages.success(request, f"Se importaron {creadas} preguntas con éxito.")
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo Excel: {str(e)}")
    else:
        messages.error(request, "Adjunta un archivo Excel (.xlsx) válido.")

    return redirect('banco_preguntas_curso', curso_id=curso.id)


@login_required
def ver_intentos_examen(request, examen_id):
    """Lista intentos rendidos para revisión docente."""
    examen = get_object_or_404(Examen, id=examen_id)
    if not es_docente_del_curso(request.user, examen.curso):
        messages.error(request, "No tienes permiso para ver estos resultados.")
        return redirect('dashboard')

    intentos = IntentoExamen.objects.filter(
        examen=examen, 
        completado=True
    ).select_related('alumno').order_by('-nota', 'fecha_fin')

    return render(request, 'docente_intentos_examen.html', {'examen': examen, 'intentos': intentos})


@login_required
def ver_detalle_intento(request, intento_id):
    """Auditoría de respuestas enviadas por un estudiante."""
    intento = get_object_or_404(IntentoExamen, id=intento_id)
    if not es_docente_del_curso(request.user, intento.examen.curso):
        messages.error(request, "No tienes permiso para auditar este intento.")
        return redirect('dashboard')

    respuestas = intento.respuestas.select_related('pregunta', 'opcion_seleccionada').all()
    return render(request, 'revision_examen.html', {
        'examen': intento.examen,
        'intento': intento,
        'respuestas': respuestas,
        'puede_ver_solucionario': True,
    })


@login_required
def finalizar_examen_docente(request, examen_id):
    """Cierre manual de la evaluación por el docente."""
    examen = get_object_or_404(Examen, id=examen_id)
    if not es_docente_del_curso(request.user, examen.curso):
        messages.error(request, "No tienes permisos para cerrar este examen.")
        return redirect('dashboard')

    examen.cerrado_manualmente = True
    examen.activo = False
    examen.save()

    registrar_log(request, "Cierre de Examen", f"Cerró manualmente '{examen.titulo}'")
    messages.warning(request, f"La evaluación '{examen.titulo}' fue cerrada definitivamente.")
    return redirect('detalle_curso', curso_id=examen.curso.id)


# ==============================================================================
# 7. PANEL DE ADMINISTRACIÓN GENERAL
# ==============================================================================

@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
@requerir_2fa_si_esta_activo
def admin_dashboard(request):
    """Panel de administración con búsqueda y paginación."""
    total_alumnos = User.objects.filter(groups__name='Alumnos').count()
    total_docentes = User.objects.filter(groups__name='Docentes').count()
    total_cursos = Curso.objects.count()
    periodo_activo = PeriodoAcademico.objects.filter(activo=True).first()
    
    query = request.GET.get('q', '').strip()
    rol_filtro = request.GET.get('rol', '').strip()
    
    usuarios_qs = User.objects.all().prefetch_related('groups').order_by('-date_joined')

    if query:
        usuarios_qs = usuarios_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if rol_filtro == 'admin':
        usuarios_qs = usuarios_qs.filter(Q(is_superuser=True) | Q(is_staff=True))
    elif rol_filtro == 'docente':
        usuarios_qs = usuarios_qs.filter(groups__name='Docentes')
    elif rol_filtro == 'alumno':
        usuarios_qs = usuarios_qs.filter(groups__name='Alumnos')

    paginator = Paginator(usuarios_qs, 15)
    usuarios = paginator.get_page(request.GET.get('page'))

    context = {
        'total_alumnos': total_alumnos,
        'total_docentes': total_docentes,
        'total_cursos': total_cursos,
        'usuarios': usuarios,
        'query': query,
        'rol_filtro': rol_filtro,
        'periodo_activo': periodo_activo,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_detalle_usuario(request, user_id):
    """Ficha informativa de matrículas y asignaciones de un usuario."""
    usuario_detalle = get_object_or_404(User, id=user_id)
    return render(request, 'admin_detalle_usuario.html', {
        'usuario_detalle': usuario_detalle,
        'inscripciones': Inscripcion.objects.filter(alumno=usuario_detalle).select_related('curso'),
        'cursos_docente': Curso.objects.filter(docentes=usuario_detalle),
    })


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def registrar_usuario(request):
    """Creación individual de usuario."""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()
            rol = form.cleaned_data.get('rol', 'Sin rol')
            registrar_log(request, "Creación de Usuario", f"Creó usuario '{nuevo_usuario.username}' ({rol})")
            messages.success(request, f"Usuario @{nuevo_usuario.username} registrado con éxito.")
            return redirect('admin_dashboard')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registro_usuario.html', {'form': form})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def editar_usuario(request, user_id):
    """Edición de credenciales y roles por el administrador."""
    usuario_editar = get_object_or_404(User, id=user_id)
    rol_actual = 'Alumno'
    if usuario_editar.is_superuser or usuario_editar.is_staff:
        rol_actual = 'Administrador'
    elif usuario_editar.groups.filter(name='Docentes').exists():
        rol_actual = 'Docente'

    if request.method == 'POST':
        usuario_editar.username = request.POST.get('username')
        usuario_editar.first_name = request.POST.get('first_name')
        usuario_editar.last_name = request.POST.get('last_name')
        usuario_editar.email = request.POST.get('email')

        nuevo_password = request.POST.get('password')
        if nuevo_password:
            usuario_editar.set_password(nuevo_password)

        nuevo_rol = request.POST.get('rol')
        usuario_editar.groups.clear()
        if nuevo_rol == 'Administrador':
            usuario_editar.is_staff = True
            usuario_editar.is_superuser = True
        elif nuevo_rol == 'Docente':
            usuario_editar.is_staff = False
            usuario_editar.is_superuser = False
            grupo, _ = Group.objects.get_or_create(name='Docentes')
            usuario_editar.groups.add(grupo)
        else:
            usuario_editar.is_staff = False
            usuario_editar.is_superuser = False
            grupo, _ = Group.objects.get_or_create(name='Alumnos')
            usuario_editar.groups.add(grupo)

        usuario_editar.save()
        registrar_log(request, "Edición de Usuario", f"Actualizó datos de '{usuario_editar.username}'")
        messages.success(request, f"Usuario @{usuario_editar.username} actualizado.")
        return redirect('admin_dashboard')

    return render(request, 'editar_usuario.html', {
        'usuario_editar': usuario_editar,
        'rol_actual': rol_actual,
        'tiene_2fa': TOTPDevice.objects.filter(user=usuario_editar, confirmed=True).exists(),
        'es_alumno': rol_actual == 'Alumno',
        'es_docente': rol_actual == 'Docente',
        'es_admin': rol_actual == 'Administrador',
    })


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def eliminar_usuario(request, user_id):
    """Elimina una cuenta de usuario."""
    usuario = get_object_or_404(User, id=user_id)
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta de administrador.")
        return redirect('admin_dashboard')

    nombre = usuario.username
    usuario.delete()
    registrar_log(request, "Eliminación de Usuario", f"Eliminó al usuario '{nombre}'")
    messages.success(request, f"Usuario '{nombre}' eliminado.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def eliminar_usuarios_masivo(request):
    """Elimina múltiples usuarios seleccionados."""
    if request.method == 'POST':
        user_ids = request.POST.getlist('usuarios_seleccionados')
        if not user_ids:
            messages.error(request, "No seleccionaste ningún usuario.")
            return redirect('admin_dashboard')

        a_borrar = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        cantidad = a_borrar.count()
        a_borrar.delete()

        registrar_log(request, "Eliminación Masiva", f"Eliminó {cantidad} usuario(s)")
        messages.success(request, f"Se eliminaron {cantidad} usuario(s) correctamente.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_cursos_lista(request):
    """Listado general de asignaturas activas e inactivas."""
    return render(request, 'admin_cursos_lista.html', {
        'cursos': Curso.objects.prefetch_related('docentes').all(),
        'total_alumnos': User.objects.filter(groups__name='Alumnos').count(),
        'total_docentes': User.objects.filter(groups__name='Docentes').count(),
        'total_cursos': Curso.objects.filter(estado=True).count(),
    })


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_crear_curso(request):
    """Crea una asignatura y sus horarios de clase."""
    if request.method == 'POST':
        curso = Curso.objects.create(
            titulo=request.POST.get('titulo'),
            descripcion=request.POST.get('descripcion'),
            estado=bool(request.POST.get('estado')),
            imagen_portada=request.FILES.get('imagen_portada'),
            formula_evaluacion=request.POST.get('formula_evaluacion', '(N1 + N2 + N3) / 3')
        )
        docentes_ids = request.POST.getlist('docentes')
        if docentes_ids:
            curso.docentes.set(docentes_ids)

        dias = request.POST.getlist('horario_dia[]')
        inicios = request.POST.getlist('horario_inicio[]')
        fines = request.POST.getlist('horario_fin[]')
        aulas = request.POST.getlist('horario_aula[]')

        for d, ini, fin, aula in zip(dias, inicios, fines, aulas):
            if d and ini and fin:
                HorarioCurso.objects.create(
                    curso=curso, dia=d, hora_inicio=ini, hora_fin=fin, aula=aula.strip() if aula else "Aula Virtual"
                )

        registrar_log(request, "Creación de Curso", f"Creó '{curso.titulo}'")
        messages.success(request, f"Curso '{curso.titulo}' creado exitosamente.")
        return redirect('admin_cursos_lista')

    return render(request, 'admin_crear_curso.html', {'docentes': User.objects.filter(groups__name='Docentes')})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_editar_curso(request, curso_id):
    """Edición integral de asignatura y ponderaciones."""
    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        curso.titulo = request.POST.get('titulo')
        curso.descripcion = request.POST.get('descripcion')
        curso.estado = bool(request.POST.get('estado'))

        if 'imagen_portada' in request.FILES:
            curso.imagen_portada = request.FILES['imagen_portada']

        curso.docentes.set(request.POST.getlist('docentes'))

        criterios_raw = request.POST.getlist('criterio_nombre')
        curso.criterios_evaluacion = [
            {"codigo": f"N{idx}", "nombre": nombre.strip()}
            for idx, nombre in enumerate(criterios_raw, start=1) if nombre.strip()
        ]
        curso.formula_evaluacion = request.POST.get('formula_evaluacion', '(N1 + N2 + N3) / 3').strip()
        curso.save()

        curso.horarios.all().delete()
        dias = request.POST.getlist('horario_dia[]')
        inicios = request.POST.getlist('horario_inicio[]')
        fines = request.POST.getlist('horario_fin[]')
        aulas = request.POST.getlist('horario_aula[]')

        for d, ini, fin, aula in zip(dias, inicios, fines, aulas):
            if d and ini and fin:
                HorarioCurso.objects.create(
                    curso=curso, dia=d, hora_inicio=ini, hora_fin=fin, aula=aula.strip() if aula else "Aula Virtual"
                )

        registrar_log(request, "Edición de Curso", f"Actualizó '{curso.titulo}'")
        messages.success(request, f"Curso '{curso.titulo}' actualizado.")
        return redirect('admin_cursos_lista')

    return render(request, 'editar_curso.html', {
        'curso': curso,
        'docentes': User.objects.filter(groups__name='Docentes'),
        'docentes_asignados_ids': list(curso.docentes.values_list('id', flat=True)),
        'criterios': curso.obtener_criterios(),
        'horarios': curso.horarios.all().order_by('dia', 'hora_inicio'),
    })


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_eliminar_curso(request, curso_id):
    """Eliminación de asignatura."""
    curso = get_object_or_404(Curso, id=curso_id)
    titulo = curso.titulo
    curso.delete()
    registrar_log(request, "Eliminación de Curso", f"Eliminó '{titulo}'")
    messages.success(request, f"Curso '{titulo}' eliminado correctamente.")
    return redirect('admin_cursos_lista')


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_matricular(request, curso_id=None):
    """Matrícula masiva de estudiantes."""
    cursos = Curso.objects.filter(estado=True).order_by('titulo')
    curso_seleccionado = None
    alumnos_matriculados_ids = []
    
    grupo_alumnos = Group.objects.filter(name='Alumnos').first()
    alumnos = User.objects.filter(groups=grupo_alumnos).order_by('last_name', 'first_name') if grupo_alumnos else User.objects.none()

    if curso_id:
        curso_seleccionado = get_object_or_404(Curso, id=curso_id)
        alumnos_matriculados_ids = list(Inscripcion.objects.filter(curso=curso_seleccionado).values_list('alumno_id', flat=True))

    if request.method == 'POST':
        curso_actual = get_object_or_404(Curso, id=request.POST.get('curso_id'))
        seleccionados_ids = [int(i) for i in request.POST.getlist('alumnos_seleccionados')]

        Inscripcion.objects.filter(curso=curso_actual).exclude(alumno_id__in=seleccionados_ids).delete()
        for a_id in seleccionados_ids:
            Inscripcion.objects.get_or_create(curso=curso_actual, alumno_id=a_id)

        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Matrícula actualizada en '{curso_actual.titulo}' ({len(seleccionados_ids)} inscritos)"
        )
        messages.success(request, f"Matrícula actualizada para '{curso_actual.titulo}'.")
        return redirect('admin_matricular_curso', curso_id=curso_actual.id)

    return render(request, 'admin_matricular.html', {
        'cursos': cursos,
        'curso_seleccionado': curso_seleccionado,
        'alumnos': alumnos,
        'alumnos_matriculados_ids': alumnos_matriculados_ids,
    })


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_curso_alumnos(request, curso_id):
    """Lista de alumnos inscritos en un curso."""
    curso = get_object_or_404(Curso, id=curso_id)
    inscripciones = Inscripcion.objects.filter(curso=curso).select_related('alumno').order_by('alumno__last_name', 'alumno__first_name')
    return render(request, 'admin_curso_alumnos.html', {'curso': curso, 'inscripciones': inscripciones})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_desmatricular_alumno(request, inscripcion_id):
    """Retira la matrícula de un alumno."""
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    curso_id = inscripcion.curso.id
    nombre = inscripcion.alumno.get_full_name() or inscripcion.alumno.username
    titulo = inscripcion.curso.titulo
    inscripcion.delete()
    registrar_log(request, "Desmatriculación", f"Retiró a '{nombre}' de '{titulo}'")
    messages.success(request, f"Alumno '{nombre}' retirado de '{titulo}'.")
    return redirect('admin_curso_alumnos', curso_id=curso_id)


# ==============================================================================
# 8. GESTIÓN DE CICLOS, REPORTES, IMPORTACIÓN Y REVOCACIÓN 2FA
# ==============================================================================

@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_carga_masiva_usuarios(request):
    """Importación masiva de usuarios vía archivo CSV."""
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        if not archivo.name.lower().endswith('.csv'):
            messages.error(request, "El archivo debe tener extensión .csv")
            return redirect('admin_carga_masiva_usuarios')

        try:
            raw_data = archivo.read()
            try:
                contenido = raw_data.decode('utf-8-sig')
            except UnicodeDecodeError:
                contenido = raw_data.decode('latin-1')

            delimitador = ';' if ';' in contenido.split('\n')[0] else ','
            lector = csv.DictReader(io.StringIO(contenido), delimiter=delimitador)
            if lector.fieldnames:
                lector.fieldnames = [f.strip().lower() for f in lector.fieldnames if f]

            creados, omitidos = 0, 0
            for fila in lector:
                username = fila.get('username', '').strip()
                email = fila.get('email', '').strip()
                password = fila.get('password', '').strip()
                rol = fila.get('rol', 'Alumnos').strip() or 'Alumnos'

                if username and password and not User.objects.filter(username__iexact=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=fila.get('first_name', '').strip(),
                        last_name=fila.get('last_name', '').strip()
                    )
                    if rol.lower() in ['administrador', 'admin']:
                        user.is_staff = True
                        user.save()
                    grupo, _ = Group.objects.get_or_create(name=rol)
                    user.groups.add(grupo)
                    creados += 1
                else:
                    omitidos += 1

            registrar_log(request, "Carga Masiva", f"Creó {creados} usuarios ({omitidos} omitidos)")
            messages.success(request, f"Se crearon {creados} usuarios correctamente ({omitidos} omitidos).")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo CSV: {str(e)}")
            return redirect('admin_carga_masiva_usuarios')

    return render(request, 'admin_carga_masiva.html')


@login_required
def descargar_plantilla_usuarios_csv(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_usuarios_galeno.csv"'

    writer = csv.writer(response)
    writer.writerow(['username', 'first_name', 'last_name', 'email', 'password', 'rol'])
    writer.writerow(['jperez', 'Juan', 'Perez Garcia', 'jperez@galeno.pe', 'Temporal123*', 'Alumnos'])
    writer.writerow(['mrodriguez', 'Maria', 'Rodriguez Soto', 'mrodriguez@galeno.pe', 'Temporal123*', 'Docentes'])

    return response


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def exportar_usuarios_csv(request):
    """Exportación completa de usuarios a CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reporte_usuarios_galeno.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Usuario', 'Nombres', 'Apellidos', 'Correo', 'Rol', 'Fecha de Registro'])

    for u in User.objects.all().prefetch_related('groups').order_by('last_name', 'first_name'):
        rol = 'Administrador' if (u.is_superuser or u.is_staff) else ('Docente' if u.groups.filter(name='Docentes').exists() else 'Alumno')
        writer.writerow([u.username, u.first_name, u.last_name, u.email or 'Sin correo', rol, u.date_joined.strftime('%d/%m/%Y %H:%M')])

    registrar_log(request, "Exportación de Datos", "Descargó listado de usuarios")
    return response


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_logs_actividad(request):
    """Registro de logs y auditoría."""
    query = request.GET.get('q', '').strip()
    logs_qs = LogActividad.objects.all().select_related('usuario').order_by('-fecha')

    if query:
        logs_qs = logs_qs.filter(
            Q(accion__icontains=query) | Q(detalles__icontains=query) | Q(usuario__username__icontains=query)
        )

    paginator = Paginator(logs_qs, 20)
    return render(request, 'admin_logs.html', {
        'total_alumnos': User.objects.filter(groups__name='Alumnos').count(),
        'total_docentes': User.objects.filter(groups__name='Docentes').count(),
        'total_cursos': Curso.objects.count(),
        'logs': paginator.get_page(request.GET.get('page')),
        'query': query,
    })


@login_required
def gestionar_temporada(request):
    """Apertura, cierre y reactivación de ciclos académicos."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Acceso restringido.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            codigo = request.POST.get('codigo', '').strip()

            if PeriodoAcademico.objects.filter(codigo=codigo).exists():
                messages.error(request, f"El código '{codigo}' ya existe.")
                return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

            activar = request.POST.get('activo') == 'on'
            if activar:
                PeriodoAcademico.objects.update(activo=False)

            PeriodoAcademico.objects.create(
                nombre=nombre,
                codigo=codigo,
                fecha_inicio=request.POST.get('fecha_inicio'),
                fecha_fin=request.POST.get('fecha_fin'),
                activo=activar
            )
            registrar_log(request, "Gestión de Ciclo", f"Creó ciclo '{nombre}'")
            messages.success(request, f"Temporada '{nombre}' creada con éxito.")

        elif accion == 'culminar':
            periodo = PeriodoAcademico.objects.filter(id=request.POST.get('periodo_id')).first()
            if periodo:
                periodo.activo = False
                periodo.save()
                registrar_log(request, "Gestión de Ciclo", f"Culminó ciclo '{periodo.nombre}'")
                messages.warning(request, f"Temporada '{periodo.nombre}' culminada.")

        elif accion == 'reactivar':
            periodo_id = request.POST.get('periodo_id')
            PeriodoAcademico.objects.update(activo=False)
            periodo = PeriodoAcademico.objects.filter(id=periodo_id).first()
            if periodo:
                periodo.activo = True
                periodo.save()
                registrar_log(request, "Gestión de Ciclo", f"Reactivó ciclo '{periodo.nombre}'")
                messages.success(request, f"Temporada '{periodo.nombre}' activada como ciclo vigente.")

    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_resetear_2fa(request, user_id):
    """Revocación de 2FA por parte del administrador."""
    usuario_objetivo = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        total = TOTPDevice.objects.filter(user=usuario_objetivo).delete()[0]
        registrar_log(request, "Reseteo 2FA", f"Revocó 2FA a '{usuario_objetivo.username}'")
        if total > 0:
            messages.success(request, f"Se desactivó el 2FA para @{usuario_objetivo.username}.")
        else:
            messages.info(request, f"El usuario @{usuario_objetivo.username} no tenía 2FA activo.")
    return redirect('editar_usuario', user_id=usuario_objetivo.id)


# ==============================================================================
# 9. MANEJADORES DE ERROR HTTP
# ==============================================================================

def error_403_view(request, exception=None):
    return render(request, 'errores/403.html', status=403)


def error_404_view(request, exception=None):
    return render(request, 'errores/404.html', status=404)


def error_500_view(request):
    return render(request, 'errores/500.html', status=500)