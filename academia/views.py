from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import Curso, Material, Inscripcion, Nota
from django.contrib.auth import logout
from django.shortcuts import redirect

# Vista para la Landing Page pública de la Academia
def inicio_publico(request):
    return render(request, 'inicio_publico.html')
# 1. Función para la pantalla principal (Redirige según el rol)
@login_required 
def dashboard(request):
    # Verificamos si pertenece al grupo Docentes o es staff
    es_docente = request.user.groups.filter(name='Docentes').exists() or request.user.is_staff
    
    # Si es docente, lo mandamos directo a su panel de gestión
    if es_docente:
        cursos = Curso.objects.all()
        return render(request, 'panel_docente.html', {'cursos': cursos, 'es_docente': True})
    
    # Si es un alumno, cargamos sus cursos inscritos normalmente
    mis_inscripciones = Inscripcion.objects.filter(alumno=request.user)
    context = {
        'inscripciones': mis_inscripciones,
        'es_docente': False
    }
    return render(request, 'dashboard.html', context)
# 2. Función para el detalle del curso y notas
@login_required
def detalle_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    
    esta_matriculado = Inscripcion.objects.filter(alumno=request.user, curso=curso).exists()
    
    if not esta_matriculado and not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para ver este curso.")
    
    materiales = curso.materiales.all()
    notas = Nota.objects.filter(alumno=request.user, curso=curso)
    
    context = {
        'curso': curso,
        'materiales': materiales,
        'notas': notas
    }
    return render(request, 'detalle_curso.html', context)

# ... (deja tus funciones dashboard y detalle_curso intactas arriba) ...

@login_required
def mis_notas(request):
    # Buscamos todas las notas que le pertenecen a este alumno en todos sus cursos
    notas = Nota.objects.filter(alumno=request.user)
    
    return render(request, 'notas.html', {'notas': notas})
# ... (tus otras funciones quedan igual arriba) ...

@login_required
def mi_perfil(request):
    return render(request, 'perfil.html')

def salir(request):
    logout(request) # Esto destruye la sesión del usuario
    return redirect('/cuentas/login/') # Esto lo empuja de vuelta al login

    # ... (tus otras funciones quedan arriba) ...

@login_required
def panel_docente(request):
    # Verificamos estrictamente que pertenezca al grupo Docentes (o sea administrador)
    es_docente = request.user.groups.filter(name='Docentes').exists()
    
    if not es_docente and not request.user.is_staff:
        return HttpResponseForbidden("Acceso denegado. Esta área es exclusiva para docentes.")
    
    # Traemos todos los cursos de la base de datos
    cursos = Curso.objects.all()
    
    return render(request, 'panel_docente.html', {'cursos': cursos})

@login_required
def subir_material(request, curso_id):
    # Verificamos que sea docente o staff
    es_docente = request.user.groups.filter(name='Docentes').exists() or request.user.is_staff
    if not es_docente:
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    curso = get_object_or_404(Curso, id=curso_id)
    
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
            return redirect('detalle_curso', curso_id=curso.id)
            
    return render(request, 'subir_material.html', {'curso': curso})