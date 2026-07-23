from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from academia import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.inicio_publico, name='inicio_publico'),

    path('dashboard/', views.dashboard, name='dashboard'),
    # Login limpio usando nuestra plantilla personalizada
    path('cuentas/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # El resto de nuestras rutas protegidas
    path('cuentas/', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('curso/<int:curso_id>/', views.detalle_curso, name='detalle_curso'),
    path('curso/<int:curso_id>/subir-material/', views.subir_material, name='subir_material'),
    path('notas/', views.mis_notas, name='mis_notas'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('salir/', views.salir, name='salir'),
    path('panel-docente/', views.panel_docente, name='panel_docente'),
]