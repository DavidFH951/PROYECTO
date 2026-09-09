import os
from django.core.exceptions import ValidationError

EXTENSIONES_PERMITIDAS_MATERIAL = [
    '.pdf', '.docx', '.doc', '.xlsx', '.xls', 
    '.pptx', '.ppt', '.zip', '.rar', '.jpg', '.jpeg', '.png'
    '.mp4', '.webm'  # Permitir videos
]

TAMANO_MAXIMO_MB = 15

def validar_archivo_material(archivo):
    # 1. Validar tamaño
    limite = TAMANO_MAXIMO_MB * 1024 * 1024
    if archivo.size > limite:
        raise ValidationError(f"El archivo supera el tamaño máximo permitido de {TAMANO_MAXIMO_MB} MB.")

    # 2. Validar extensión permitida
    ext = os.path.splitext(archivo.name)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS_MATERIAL:
        raise ValidationError(
            f"Formato no permitido ({ext}). Solo se admiten documentos (PDF, Office), comprimidos o imágenes."
        )