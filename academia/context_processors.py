# academia/context_processors.py
from .models import Curso , PeriodoAcademico # o tu función es_docente_valido

def roles_intranet(request):
    if not request.user.is_authenticated:
        return {'es_docente_global': False}
    
    # Comprobación directa si es docente
    es_doc = (
        request.user.is_superuser or 
        request.user.is_staff or 
        Curso.objects.filter(docentes=request.user).exists()
    )
    return {
        'es_docente_global': es_doc
    }
def periodo_context(request):
    periodo_activo = PeriodoAcademico.objects.filter(activo=True).first()
    return {
        'periodo_activo': periodo_activo
    }