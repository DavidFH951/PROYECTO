from django import forms
from django.contrib.auth.models import User, Group
from .models import Curso, Inscripcion,Examen, Pregunta, Opcion

# ----------------------------------------------------
# 1. REGISTRO DE USUARIOS
# ----------------------------------------------------
class RegistroUsuarioForm(forms.ModelForm):
    ROL_CHOICES = (
        ('Alumnos', 'Alumno'),
        ('Docentes', 'Docente'),
        ('Administrador', 'Administrador'),
    )

    username = forms.CharField(
        label='Nombre de Usuario',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. jflores'})
    )
    first_name = forms.CharField(
        label='Nombres',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. Juan Carlos'})
    )
    last_name = forms.CharField(
        label='Apellidos',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. Pérez Gómez'})
    )
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ejemplo@galeno.edu.pe'})
    )
    rol = forms.ChoiceField(
        choices=ROL_CHOICES,
        label='Rol en el Sistema',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    password = forms.CharField(
        label='Contraseña Provisional',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '••••••••'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        rol_seleccionado = self.cleaned_data['rol']
        user.is_staff = (rol_seleccionado == 'Administrador')

        if commit:
            user.save()
            grupo, _ = Group.objects.get_or_create(name=rol_seleccionado)
            user.groups.add(grupo)

        return user

# ----------------------------------------------------
# 2. EDICIÓN DE USUARIOS
# ----------------------------------------------------
class EditarUsuarioForm(forms.ModelForm):
    ROL_CHOICES = (
        ('Alumnos', 'Alumno'),
        ('Docentes', 'Docente'),
        ('Administrador', 'Administrador'),
    )

    first_name = forms.CharField(label='Nombres', max_length=150, required=True)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=True)
    email = forms.EmailField(label='Correo Electrónico', required=True)
    rol = forms.ChoiceField(choices=ROL_CHOICES, label='Rol del Usuario', required=True)
    password = forms.CharField(
        widget=forms.PasswordInput(),
        label='Nueva Contraseña (dejar en blanco para mantener la actual)',
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            if self.instance.is_superuser or self.instance.is_staff:
                self.fields['rol'].initial = 'Administrador'
            elif self.instance.groups.filter(name='Docentes').exists():
                self.fields['rol'].initial = 'Docentes'
            else:
                self.fields['rol'].initial = 'Alumnos'

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva_clave = self.cleaned_data.get('password')
        if nueva_clave:
            user.set_password(nueva_clave)

        rol_seleccionado = self.cleaned_data['rol']
        user.is_staff = (rol_seleccionado == 'Administrador')

        if commit:
            user.save()
            user.groups.clear()
            grupo, _ = Group.objects.get_or_create(name=rol_seleccionado)
            user.groups.add(grupo)

        return user


# ----------------------------------------------------
# 3. CREACIÓN DE CURSOS
# ----------------------------------------------------
class DocenteChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        nombre = obj.get_full_name()
        return f"{nombre} (@{obj.username})" if nombre else obj.username

class CursoForm(forms.ModelForm):
    docentes = DocenteChoiceField(
        queryset=User.objects.filter(groups__name='Docentes'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Docentes Asignados"
    )

    class Meta:
        model = Curso
        fields = ['titulo', 'descripcion', 'imagen_portada', 'periodo', 'docentes']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Anatomía Humana'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del curso...'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
        }

# ----------------------------------------------------
# 4. MATRÍCULA DE ALUMNOS
# ----------------------------------------------------
class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ['alumno', 'curso']
        widgets = {
            'alumno': forms.Select(attrs={'class': 'form-input'}),
            'curso': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra para que solo aparezcan usuarios del grupo Alumnos
        self.fields['alumno'].queryset = User.objects.filter(groups__name='Alumnos')

class PreguntaForm(forms.ModelForm):
    # Campos dinámicos para las 4 alternativas típicas (A, B, C, D)
    opcion_1 = forms.CharField(label="Alternativa A", max_length=255, widget=forms.TextInput(attrs={'class': 'hero-input-field', 'placeholder': 'Texto opción A'}))
    opcion_2 = forms.CharField(label="Alternativa B", max_length=255, widget=forms.TextInput(attrs={'class': 'hero-input-field', 'placeholder': 'Texto opción B'}))
    opcion_3 = forms.CharField(label="Alternativa C", max_length=255, widget=forms.TextInput(attrs={'class': 'hero-input-field', 'placeholder': 'Texto opción C'}))
    opcion_4 = forms.CharField(label="Alternativa D", max_length=255, widget=forms.TextInput(attrs={'class': 'hero-input-field', 'placeholder': 'Texto opción D'}))
    
    opcion_correcta = forms.ChoiceField(
        label="¿Cuál es la alternativa correcta?",
        choices=[('1', 'Opción A'), ('2', 'Opción B'), ('3', 'Opción C'), ('4', 'Opción D')],
        widget=forms.Select(attrs={'class': 'hero-input-field'})
    )

    class Meta:
        model = Pregunta
        fields = ['examen', 'enunciado', 'explicacion', 'puntaje']
        widgets = {
            'examen': forms.Select(attrs={'class': 'hero-input-field'}),
            'enunciado': forms.Textarea(attrs={'class': 'hero-input-field', 'rows': 3, 'placeholder': 'Enunciado clínico o teórico...'}),
            'explicacion': forms.Textarea(attrs={'class': 'hero-input-field', 'rows': 2, 'placeholder': 'Feedback médico o justificación (opcional)...'}),
            'puntaje': forms.NumberInput(attrs={'class': 'hero-input-field', 'step': '0.5'}),
        }

    def __init__(self, *args, **kwargs):
        curso = kwargs.pop('curso', None)
        super().__init__(*args, **kwargs)
        if curso:
            # Filtrar solo exámenes pertenecientes a este curso
            self.fields['examen'].queryset = Examen.objects.filter(curso=curso)

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['titulo', 'semana', 'duracion_minutos', 'descripcion', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'hero-input-field', 'placeholder': 'Ej: Examen Parcial / Test Rápido'}),
            'semana': forms.NumberInput(attrs={'class': 'hero-input-field', 'min': 1, 'max': 20}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'hero-input-field', 'placeholder': 'Minutos'}),
            'descripcion': forms.Textarea(attrs={'class': 'hero-input-field', 'rows': 2, 'placeholder': 'Instrucciones para el postulante...'}),
        }