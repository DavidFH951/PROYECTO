import csv
import io

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Curso, Material, Inscripcion, Calificacion, LogActividad
from .forms import RegistroUsuarioForm, EditarUsuarioForm, CursoForm, InscripcionForm


# ----------------------------------------------------
# UTILIDAD DE AUDITORÍA (LOGS)
# ----------------------------------------------------
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


# ----------------------------------------------------
# VALIDACIÓN DE ACCESOS
# ----------------------------------------------------
def es_administrador(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.groups.filter(name='Administrador').exists())


def es_docente_valido(user):
    return user.is_authenticated and (user.groups.filter(name='Docentes').exists() or user.is_staff or user.is_superuser)


# ----------------------------------------------------
# VISTAS PÚBLICAS Y GENERALES
# ----------------------------------------------------
def inicio_publico(request):
    return render(request, 'inicio_publico.html')


def salir(request):
    logout(request)
    return redirect('/cuentas/login/')


# ----------------------------------------------------
# CONTROLADOR PRINCIPAL SEGÚN ROL
# ----------------------------------------------------
@login_required 
def dashboard(request):
    # 1. Administrador -> Panel de administración
    if es_administrador(request.user):
        return redirect('admin_dashboard')
    
    # 2. Docente -> Panel de gestión docente
    if request.user.groups.filter(name='Docentes').exists():
        return redirect('panel_docente')
    
    # 3. Alumno -> Dashboard con sus cursos
    mis_inscripciones = Inscripcion.objects.filter(alumno=request.user).select_related('curso')
    context = {
        'inscripciones': mis_inscripciones,
        'es_docente': False
    }
    return render(request, 'dashboard.html', context)


# ----------------------------------------------------
# SECCIÓN ADMINISTRACIÓN: USUARIOS
# ----------------------------------------------------
@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_dashboard(request):
    total_alumnos = User.objects.filter(groups__name='Alumnos').count()
    total_docentes = User.objects.filter(groups__name='Docentes').count()
    total_cursos = Curso.objects.count()
    
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
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    context = {
        'total_alumnos': total_alumnos,
        'total_docentes': total_docentes,
        'total_cursos': total_cursos,
        'usuarios': usuarios,
        'query': query,
        'rol_filtro': rol_filtro,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_detalle_usuario(request, user_id):
    usuario_detalle = get_object_or_404(User, id=user_id)
    
    # Cursos matriculados como alumno
    inscripciones = Inscripcion.objects.filter(alumno=usuario_detalle).select_related('curso')
    
    # Cursos asignados como docente (relación ManyToMany con Curso)
    cursos_docente = Curso.objects.filter(docentes=usuario_detalle)
    
    context = {
        'usuario_detalle': usuario_detalle,
        'inscripciones': inscripciones,
        'cursos_docente': cursos_docente,
    }
    return render(request, 'admin_detalle_usuario.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()
            rol_nombre = form.cleaned_data.get('rol', 'Sin rol')
            registrar_log(request, "Creación de Usuario", f"Creó al usuario '{nuevo_usuario.username}' con rol '{rol_nombre}'")
            messages.success(request, f"Usuario '{nuevo_usuario.username}' registrado correctamente.")
            return redirect('admin_dashboard')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'registro_usuario.html', {'form': form})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def editar_usuario(request, user_id):
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
            grupo_docentes, _ = Group.objects.get_or_create(name='Docentes')
            usuario_editar.groups.add(grupo_docentes)
        else:  # Alumno
            usuario_editar.is_staff = False
            usuario_editar.is_superuser = False
            grupo_alumnos, _ = Group.objects.get_or_create(name='Alumnos')
            usuario_editar.groups.add(grupo_alumnos)

        usuario_editar.save()
        messages.success(request, f"Usuario @{usuario_editar.username} actualizado correctamente.")
        return redirect('admin_dashboard')

    context = {
        'usuario_editar': usuario_editar,
        'rol_actual': rol_actual,
    }
    return render(request, 'editar_usuario.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_matricular(request, curso_id=None):
    cursos = Curso.objects.filter(estado=True).order_by('titulo')
    curso_seleccionado = None
    alumnos_matriculados_ids = []
    
    grupo_alumnos = Group.objects.filter(name='Alumnos').first()
    alumnos = User.objects.filter(groups=grupo_alumnos).order_by('last_name', 'first_name') if grupo_alumnos else User.objects.none()

    if curso_id:
        curso_seleccionado = get_object_or_404(Curso, id=curso_id)
        alumnos_matriculados_ids = list(Inscripcion.objects.filter(curso=curso_seleccionado).values_list('alumno_id', flat=True))

    if request.method == 'POST':
        curso_post_id = request.POST.get('curso_id')
        curso_actual = get_object_or_404(Curso, id=curso_post_id)
        seleccionados_ids = request.POST.getlist('alumnos_seleccionados')
        seleccionados_ids = [int(i) for i in seleccionados_ids]

        Inscripcion.objects.filter(curso=curso_actual).exclude(alumno_id__in=seleccionados_ids).delete()

        nuevos_matriculados = 0
        for a_id in seleccionados_ids:
            obj, created = Inscripcion.objects.get_or_create(curso=curso_actual, alumno_id=a_id)
            if created:
                nuevos_matriculados += 1

        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Actualizó matrícula del curso '{curso_actual.titulo}' ({len(seleccionados_ids)} alumnos activos)"
        )

        messages.success(request, f"Matrícula actualizada exitosamente para '{curso_actual.titulo}'.")
        return redirect('admin_matricular_curso', curso_id=curso_actual.id)

    context = {
        'cursos': cursos,
        'curso_seleccionado': curso_seleccionado,
        'alumnos': alumnos,
        'alumnos_matriculados_ids': alumnos_matriculados_ids,
    }
    return render(request, 'admin_matricular.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta de administrador.")
        return redirect('admin_dashboard')
    
    nombre = usuario.username
    registrar_log(request, "Eliminación de Usuario", f"Eliminó la cuenta del usuario '{nombre}'")
    usuario.delete()
    messages.success(request, f"El usuario '{nombre}' fue eliminado correctamente.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def eliminar_usuarios_masivo(request):
    if request.method == 'POST':
        user_ids = request.POST.getlist('usuarios_seleccionados')
        
        if not user_ids:
            messages.error(request, "No seleccionaste ningún usuario para eliminar.")
            return redirect('admin_dashboard')
        
        usuarios_a_borrar = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        cantidad = usuarios_a_borrar.count()
        nombres = ", ".join(usuarios_a_borrar.values_list('username', flat=True))
        usuarios_a_borrar.delete()
        
        registrar_log(request, "Eliminación Masiva", f"Eliminó {cantidad} usuario(s): {nombres}")
        messages.success(request, f"Se eliminaron {cantidad} usuario(s) correctamente.")
    
    return redirect('admin_dashboard')


# ----------------------------------------------------
# SECCIÓN ADMINISTRACIÓN: CURSOS Y MATRÍCULAS
# ----------------------------------------------------
@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_cursos_lista(request):
    cursos = Curso.objects.prefetch_related('docentes').all()
    
    total_alumnos = User.objects.filter(groups__name='Alumnos').count()
    total_docentes = User.objects.filter(groups__name='Docentes').count()
    total_cursos = Curso.objects.filter(estado=True).count()

    context = {
        'cursos': cursos,
        'total_alumnos': total_alumnos,
        'total_docentes': total_docentes,
        'total_cursos': total_cursos,
    }
    return render(request, 'admin_cursos_lista.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_crear_curso(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        estado = True if request.POST.get('estado') else False
        imagen = request.FILES.get('imagen_portada')
        
        curso = Curso.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            estado=estado,
            imagen_portada=imagen
        )
        
        docentes_ids = request.POST.getlist('docentes')
        if docentes_ids:
            curso.docentes.set(docentes_ids)
            
        messages.success(request, f"Curso '{curso.titulo}' creado exitosamente.")
        return redirect('admin_cursos_lista')

    docentes = User.objects.filter(groups__name='Docentes')
    return render(request, 'admin_crear_curso.html', {'docentes': docentes})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_editar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    
    if request.method == 'POST':
        curso.titulo = request.POST.get('titulo')
        curso.descripcion = request.POST.get('descripcion')
        curso.estado = True if request.POST.get('estado') else False
        
        if 'imagen_portada' in request.FILES:
            curso.imagen_portada = request.FILES['imagen_portada']
            
        docentes_ids = request.POST.getlist('docentes')
        curso.docentes.set(docentes_ids)
        curso.save()
        
        messages.success(request, f"Curso '{curso.titulo}' actualizado.")
        return redirect('admin_cursos_lista')

    docentes = User.objects.filter(groups__name='Docentes')
    return render(request, 'editar_curso.html', {'curso': curso, 'docentes': docentes})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    titulo = curso.titulo
    registrar_log(request, "Eliminación de Curso", f"Eliminó el curso '{titulo}'")
    curso.delete()
    messages.success(request, f"El curso '{titulo}' fue eliminado correctamente.")
    return redirect('admin_cursos_lista')


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_matricular_alumno(request):
    if request.method == 'POST':
        form = InscripcionForm(request.POST)
        if form.is_valid():
            inscripcion = form.save()
            registrar_log(request, "Matrícula de Alumno", f"Matriculó a '{inscripcion.alumno.username}' en '{inscripcion.curso.titulo}'")
            messages.success(request, f"Alumno '{inscripcion.alumno.username}' matriculado en '{inscripcion.curso.titulo}'.")
            return redirect('admin_cursos_lista')
    else:
        form = InscripcionForm()
    return render(request, 'admin_matricular.html', {'form': form})


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_curso_alumnos(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscripciones = Inscripcion.objects.filter(curso=curso).select_related('alumno').order_by('alumno__last_name', 'alumno__first_name')
    
    context = {
        'curso': curso,
        'inscripciones': inscripciones,
    }
    return render(request, 'admin_curso_alumnos.html', context)


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_desmatricular_alumno(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    curso_id = inscripcion.curso.id
    nombre_alumno = inscripcion.alumno.get_full_name() or inscripcion.alumno.username
    titulo_curso = inscripcion.curso.titulo
    
    registrar_log(request, "Desmatriculación", f"Desmatriculó a '{nombre_alumno}' del curso '{titulo_curso}'")
    inscripcion.delete()
    messages.success(request, f"Se desmatriculó al alumno '{nombre_alumno}' del curso '{titulo_curso}'.")
    return redirect('admin_curso_alumnos', curso_id=curso_id)


# ----------------------------------------------------
# SECCIÓN ADMINISTRACIÓN: CARGA MASIVA, REPORTES Y LOGS
# ----------------------------------------------------
@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_carga_masiva_usuarios(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        
        if not archivo.name.endswith('.csv'):
            messages.error(request, "El archivo seleccionado debe tener extensión .csv")
            return redirect('admin_carga_masiva_usuarios')

        try:
            contenido = archivo.read().decode('utf-8-sig')
            lector = csv.DictReader(io.StringIO(contenido))
            
            creados = 0
            omitidos = 0

            for fila in lector:
                username = fila.get('username', '').strip()
                email = fila.get('email', '').strip()
                first_name = fila.get('first_name', '').strip()
                last_name = fila.get('last_name', '').strip()
                password = fila.get('password', '').strip()
                rol = fila.get('rol', 'Alumnos').strip()

                if username and password and not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    if rol == 'Administrador':
                        user.is_staff = True
                        user.save()
                    
                    grupo, _ = Group.objects.get_or_create(name=rol)
                    user.groups.add(grupo)
                    creados += 1
                else:
                    omitidos += 1

            registrar_log(request, "Carga Masiva", f"Creó {creados} usuarios vía CSV ({omitidos} omitidos)")
            messages.success(request, f"Carga masiva completada: {creados} usuarios creados con éxito ({omitidos} omitidos o duplicados).")
            return redirect('admin_dashboard')

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo CSV: {str(e)}")
            return redirect('admin_carga_masiva_usuarios')

    return render(request, 'admin_carga_masiva.html')


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def exportar_usuarios_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reporte_usuarios_galeno.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Usuario', 'Nombres', 'Apellidos', 'Correo', 'Rol', 'Fecha de Registro'])

    for u in User.objects.all().prefetch_related('groups').order_by('last_name', 'first_name'):
        if u.is_superuser or u.is_staff:
            rol = 'Administrador'
        elif u.groups.filter(name='Docentes').exists():
            rol = 'Docente'
        else:
            rol = 'Alumno'

        writer.writerow([
            u.username,
            u.first_name,
            u.last_name,
            u.email or 'Sin correo',
            rol,
            u.date_joined.strftime('%d/%m/%Y %H:%M')
        ])

    registrar_log(request, "Exportación de Datos", "Descargó el listado general de usuarios en CSV")
    return response


@login_required
@user_passes_test(es_administrador, login_url='/cuentas/login/')
def admin_logs_actividad(request):
    total_alumnos = User.objects.filter(groups__name='Alumnos').count()
    total_docentes = User.objects.filter(groups__name='Docentes').count()
    total_cursos = Curso.objects.count()

    query = request.GET.get('q', '').strip()
    logs_qs = LogActividad.objects.all().select_related('usuario').order_by('-fecha')

    if query:
        logs_qs = logs_qs.filter(
            Q(accion__icontains=query) |
            Q(detalles__icontains=query) |
            Q(usuario__username__icontains=query)
        )

    paginator = Paginator(logs_qs, 20)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    context = {
        'total_alumnos': total_alumnos,
        'total_docentes': total_docentes,
        'total_cursos': total_cursos,
        'logs': logs,
        'query': query,
    }
    return render(request, 'admin_logs.html', context)


# ----------------------------------------------------
# SECCIÓN DOCENTE
# ----------------------------------------------------
@login_required
def panel_docente(request):
    if not es_docente_valido(request.user):
        return HttpResponseForbidden("Acceso exclusivo para docentes.")

    if request.user.is_superuser or request.user.is_staff:
        cursos = Curso.objects.prefetch_related('docentes', 'inscripciones', 'materiales').all()
    else:
        cursos = Curso.objects.filter(docentes=request.user).prefetch_related('docentes', 'inscripciones', 'materiales').distinct()

    return render(request, 'panel_docente.html', {'cursos': cursos})


@login_required
def subir_material(request, curso_id):
    if not es_docente_valido(request.user):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    curso = get_object_or_404(Curso, id=curso_id)

    if not (request.user.is_staff or request.user.is_superuser) and not curso.docentes.filter(id=request.user.id).exists():
        return HttpResponseForbidden("No estás asignado como docente en este curso.")
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        archivo = request.FILES.get('archivo')
        enlace = request.POST.get('enlace')
        
        if titulo:
            Material.objects.create(
                curso=curso,
                titulo=titulo,
                archivo=archivo,
                enlace=enlace
            )
            registrar_log(request, "Subida de Material", f"Subió '{titulo}' al curso '{curso.titulo}'")
            messages.success(request, f"Material '{titulo}' publicado exitosamente.")
            return redirect('detalle_curso', curso_id=curso.id)
            
    return render(request, 'subir_material.html', {'curso': curso})


@login_required
def eliminar_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    curso = material.curso
    es_autorizado = request.user.is_staff or request.user.is_superuser or curso.docentes.filter(id=request.user.id).exists()

    if not es_autorizado:
        return HttpResponseForbidden("No tienes permiso para eliminar este material.")

    titulo_mat = material.titulo
    material.delete()
    registrar_log(request, "Eliminación de Material", f"Eliminó el material '{titulo_mat}' del curso '{curso.titulo}'")
    messages.success(request, f"Material '{titulo_mat}' eliminado correctamente.")
    return redirect('detalle_curso', curso_id=curso.id)


@login_required
def docente_calificar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    es_docente = curso.docentes.filter(id=request.user.id).exists()
    es_admin = request.user.is_superuser or request.user.groups.filter(name='Administrador').exists()
    
    if not (es_docente or es_admin):
        messages.error(request, "No tienes permisos para calificar en este curso.")
        return redirect('panel_docente')

    inscripciones = Inscripcion.objects.filter(curso=curso).select_related('alumno')

    def parsear_nota(valor):
        if valor is not None and str(valor).strip() != '':
            try:
                return float(valor)
            except ValueError:
                return None
        return None

    if request.method == 'POST':
        for insc in inscripciones:
            alumno_id = str(insc.alumno.id)
            n1 = request.POST.get(f'nota1_{alumno_id}')
            n2 = request.POST.get(f'nota2_{alumno_id}')
            n3 = request.POST.get(f'nota3_{alumno_id}')

            calificacion, _ = Calificacion.objects.get_or_create(curso=curso, alumno=insc.alumno)
            calificacion.nota1 = parsear_nota(n1)
            calificacion.nota2 = parsear_nota(n2)
            calificacion.nota3 = parsear_nota(n3)
            calificacion.save()

        registrar_log(request, "Registro de Calificaciones", f"Actualizó notas del curso '{curso.titulo}'")
        messages.success(request, "Las calificaciones se guardaron correctamente.")
        return redirect('docente_calificar_curso', curso_id=curso.id)

    calificaciones_dict = {c.alumno_id: c for c in Calificacion.objects.filter(curso=curso)}
    filas_calificaciones = []
    for insc in inscripciones:
        calif = calificaciones_dict.get(insc.alumno.id)
        filas_calificaciones.append({
            'alumno': insc.alumno,
            'nota1': calif.nota1 if calif and calif.nota1 is not None else '',
            'nota2': calif.nota2 if calif and calif.nota2 is not None else '',
            'nota3': calif.nota3 if calif and calif.nota3 is not None else '',
            'promedio': calif.promedio if calif and hasattr(calif, 'promedio') else None
        })

    return render(request, 'docente_calificar.html', {
        'curso': curso,
        'filas_calificaciones': filas_calificaciones
    })


# ----------------------------------------------------
# VISTAS GENERALES DE ALUMNO Y CURSOS
# ----------------------------------------------------
@login_required
def detalle_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    es_docente_curso = curso.docentes.filter(id=request.user.id).exists()
    esta_matriculado = Inscripcion.objects.filter(alumno=request.user, curso=curso).exists()
    
    if not (esta_matriculado or es_docente_curso or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("No tienes permiso para ver este curso.")
    
    materiales = curso.materiales.all()
    notas = Calificacion.objects.filter(alumno=request.user, curso=curso)
    
    context = {
        'curso': curso,
        'materiales': materiales,
        'notas': notas,
        'es_docente_curso': es_docente_curso or request.user.is_staff or request.user.is_superuser,
    }
    return render(request, 'detalle_curso.html', context)


@login_required
def mis_notas(request):
    notas = Calificacion.objects.filter(alumno=request.user).select_related('curso')
    return render(request, 'notas.html', {'notas': notas})


@login_required
def mi_perfil(request):
    return render(request, 'perfil.html')