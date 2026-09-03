from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from academia import views

urlpatterns = [
    # Panel Django por defecto
    path('admin/', admin.site.urls),

    # Portada pública
    path('', views.inicio_publico, name='inicio_publico'),

    # Autenticación y Cuentas
    path('cuentas/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('cuentas/', include('django.contrib.auth.urls')),
    path('salir/', views.salir, name='salir'),

    # Dashboard principal (Redirige automáticamente según el rol)
    path('dashboard/', views.dashboard, name='dashboard'),

    # ====================================================
    # RUTAS EXCLUSIVAS DEL ADMINISTRADOR
    # ====================================================
    path('panel-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('panel-admin/registrar-usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('panel-admin/usuario/<int:user_id>/', views.admin_detalle_usuario, name='admin_detalle_usuario'),
    path('panel-admin/usuario/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('panel-admin/usuario/<int:user_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('panel-admin/usuarios/eliminar-masivo/', views.eliminar_usuarios_masivo, name='eliminar_usuarios_masivo'),
    path('panel-admin/carga-masiva/', views.admin_carga_masiva_usuarios, name='admin_carga_masiva_usuarios'),
    path('panel-admin/descargar-plantilla/', views.descargar_plantilla_usuarios, name='descargar_plantilla_usuarios'),  
    path('panel-admin/exportar/usuarios-csv/', views.exportar_usuarios_csv, name='exportar_usuarios_csv'),
    path('panel-admin/auditoria/', views.admin_logs_actividad, name='admin_logs_actividad'),

    # Cursos y Matrículas (Admin)
    path('panel-admin/cursos/', views.admin_cursos_lista, name='admin_cursos_lista'),
    path('panel-admin/crear-curso/', views.admin_crear_curso, name='admin_crear_curso'),
    path('panel-admin/curso/<int:curso_id>/editar/', views.admin_editar_curso, name='admin_editar_curso'),
    path('panel-admin/curso/<int:curso_id>/eliminar/', views.admin_eliminar_curso, name='admin_eliminar_curso'),
    path('admin-panel/gestionar-temporada/', views.gestionar_temporada, name='gestionar_temporada'),
    
    # Matrículas
    path('panel-admin/matricular/', views.admin_matricular, name='admin_matricular'),
    path('panel-admin/matricular/<int:curso_id>/', views.admin_matricular, name='admin_matricular_curso'),
    path('panel-admin/curso/<int:curso_id>/alumnos/', views.admin_curso_alumnos, name='admin_curso_alumnos'),
    path('panel-admin/inscripcion/<int:inscripcion_id>/eliminar/', views.admin_desmatricular_alumno, name='admin_desmatricular_alumno'),

    # ====================================================
    # RUTAS DEL DOCENTE (AULA Y CALIFICACIONES)
    # ====================================================
    path('panel-docente/', views.panel_docente, name='panel_docente'),
    path('docente/curso/<int:curso_id>/calificar/', views.docente_calificar_curso, name='docente_calificar_curso'),
    path('curso/<int:curso_id>/subir-material/', views.subir_material, name='subir_material'),
    path('material/<int:material_id>/eliminar/', views.eliminar_material, name='eliminar_material'),
    path('curso/<int:curso_id>/banco-preguntas/', views.banco_preguntas_curso, name='banco_preguntas_curso'),

    # ====================================================
    # RUTAS DEL ALUMNO Y CURSOS EN GENERAL
    # ====================================================
    path('curso/<int:curso_id>/', views.detalle_curso, name='detalle_curso'),
    path('notas/', views.mis_notas, name='mis_notas'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),


    path('examen/<int:examen_id>/rendir/', views.rendir_examen, name='rendir_examen'),
    path('curso/<int:curso_id>/importar-preguntas/', views.importar_preguntas_curso, name='importar_preguntas_curso'),
    path('preguntas/descargar-plantilla/', views.descargar_plantilla_preguntas, name='descargar_plantilla_preguntas'),
]

# Servir archivos multimedia subidos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)