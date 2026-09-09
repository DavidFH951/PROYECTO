from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from academia import views

urlpatterns = [
    # ==============================================================================
    # 1. CORE, AUTENTICACIÓN Y SEGURIDAD
    # ==============================================================================
    path('panel-k8f9a2b71c4e90d/', admin.site.urls),
    path('', views.inicio_publico, name='inicio_publico'),
    path('salir/', views.salir, name='salir'),
    path('seguridad/2fa/configurar/', views.configurar_2fa, name='configurar_2fa'),
    path('seguridad/2fa/verificar/', views.verificar_2fa, name='verificar_2fa'),

    # Autenticación
    path('cuentas/login/', views.CustomLoginView.as_view(), name='login'),
    path('cuentas/', include('django.contrib.auth.urls')),

    # ==============================================================================
    # 2. PORTAL ESTUDIANTIL CON TOKEN DINÁMICO (UUID)
    # ==============================================================================
    # Rutas protegidas con UUID en la URL
    path('dashboard/<uuid:token>/', views.dashboard, name='dashboard_token'),
    path('aula-virtual/mis-cursos/<uuid:token>/', views.mis_cursos, name='mis_cursos_token'),
    path('intranet/mis-notas/<uuid:token>/', views.mis_notas, name='mis_notas_token'),
    path('intranet/mis-asistencias/<uuid:token>/', views.mis_asistencias, name='mis_asistencias_token'),
    path('intranet/mi-perfil/<uuid:token>/', views.mi_perfil, name='mi_perfil_token'),

    # Redirecciones transparentes (si entran a la ruta base sin token, los envía a su URL con UUID)
    path('dashboard/', views.redirigir_dashboard, name='dashboard'),
    path('aula-virtual/mis-cursos/', views.redirigir_mis_cursos, name='mis_cursos'),
    path('intranet/mis-notas/', views.redirigir_mis_notas, name='mis_notas'),
    path('intranet/mis-asistencias/', views.redirigir_mis_asistencias, name='mis_asistencias'),
    path('intranet/mi-perfil/', views.redirigir_mi_perfil, name='mi_perfil'),
    path('perfil/', views.redirigir_mi_perfil),

    # Contenido académico del estudiante
    path('aula-virtual/curso/<uuid:token>/<int:curso_id>/', views.detalle_curso, name='detalle_curso_token'),
    path('aula-virtual/curso/<int:curso_id>/', views.redirigir_detalle_curso, name='detalle_curso'),
    path('examen/<int:examen_id>/rendir/', views.rendir_examen, name='rendir_examen'),
    path('examen/<int:examen_id>/revision/', views.revision_examen, name='revision_examen'),
    path('examen/<int:examen_id>/verificar-estado/', views.verificar_estado_examen, name='verificar_estado_examen'),

    # ==============================================================================
    # 3. GESTIÓN DOCENTE (AULA, CALIFICACIONES Y ASISTENCIA)
    # ==============================================================================
    path('panel-docente/', views.panel_docente, name='panel_docente'),
    path('docente/mis-calificaciones/', views.docente_mis_calificaciones, name='docente_mis_calificaciones'),
    path('docente/curso/<int:curso_id>/calificar/', views.docente_calificar_curso, name='docente_calificar_curso'),
    path('docente/asistencias/', views.docente_mis_asistencias, name='docente_mis_asistencias'),
    path('docente/curso/<int:curso_id>/asistencia/', views.docente_asistencia_curso, name='docente_asistencia_curso'),

    # Recursos y material del curso
    path('curso/<int:curso_id>/subir-material/', views.subir_material, name='subir_material'),
    path('material/<int:material_id>/eliminar/', views.eliminar_material, name='eliminar_material'),

    # Exámenes y Banco de Preguntas
    path('curso/<int:curso_id>/crear-examen/', views.crear_examen_curso, name='crear_examen_curso'),
    path('examen/<int:examen_id>/toggle/', views.toggle_examen, name='toggle_examen'),
    path('examen/<int:examen_id>/eliminar/', views.eliminar_examen, name='eliminar_examen'),
    path('examen/<int:examen_id>/finalizar-docente/', views.finalizar_examen_docente, name='finalizar_examen_docente'),
    path('curso/<int:curso_id>/banco-preguntas/', views.banco_preguntas_curso, name='banco_preguntas_curso'),
    path('curso/<int:curso_id>/importar-preguntas/', views.importar_preguntas_curso, name='importar_preguntas_curso'),
    path('preguntas/descargar-plantilla/', views.descargar_plantilla_preguntas, name='descargar_plantilla_preguntas'),
    path('pregunta/<int:pregunta_id>/eliminar/', views.eliminar_pregunta, name='eliminar_pregunta'),
    path('examen/<int:examen_id>/entregas/', views.ver_intentos_examen, name='ver_intentos_examen'),
    path('intento/<int:intento_id>/detalle/', views.ver_detalle_intento, name='ver_detalle_intento'),

    # ==============================================================================
    # 4. PANEL DE ADMINISTRACIÓN
    # ==============================================================================
    path('panel-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('panel-admin/auditoria/', views.admin_logs_actividad, name='admin_logs_actividad'),
    path('admin-panel/gestionar-temporada/', views.gestionar_temporada, name='gestionar_temporada'),
    path('admin/usuarios/<int:user_id>/reset-2fa/', views.admin_resetear_2fa, name='admin_resetear_2fa'),

    # Gestión de usuarios
    path('panel-admin/registrar-usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('panel-admin/usuario/<int:user_id>/', views.admin_detalle_usuario, name='admin_detalle_usuario'),
    path('panel-admin/usuario/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('panel-admin/usuario/<int:user_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('panel-admin/usuarios/eliminar-masivo/', views.eliminar_usuarios_masivo, name='eliminar_usuarios_masivo'),
    path('panel-admin/carga-masiva/', views.admin_carga_masiva_usuarios, name='admin_carga_masiva_usuarios'),
    path('panel-admin/descargar-plantilla/', views.descargar_plantilla_usuarios, name='descargar_plantilla_usuarios'),
    path('panel-admin/exportar/usuarios-csv/', views.exportar_usuarios_csv, name='exportar_usuarios_csv'),

    # Cursos y matrículas
    path('panel-admin/cursos/', views.admin_cursos_lista, name='admin_cursos_lista'),
    path('panel-admin/crear-curso/', views.admin_crear_curso, name='admin_crear_curso'),
    path('panel-admin/curso/<int:curso_id>/editar/', views.admin_editar_curso, name='admin_editar_curso'),
    path('panel-admin/curso/<int:curso_id>/eliminar/', views.admin_eliminar_curso, name='admin_eliminar_curso'),
    path('panel-admin/matricular/', views.admin_matricular, name='admin_matricular'),
    path('panel-admin/matricular/<int:curso_id>/', views.admin_matricular, name='admin_matricular_curso'),
    path('panel-admin/curso/<int:curso_id>/alumnos/', views.admin_curso_alumnos, name='admin_curso_alumnos'),
    path('panel-admin/inscripcion/<int:inscripcion_id>/eliminar/', views.admin_desmatricular_alumno, name='admin_desmatricular_alumno'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'academia.views.error_403_view'
handler404 = 'academia.views.error_404_view'
handler500 = 'academia.views.error_500_view'