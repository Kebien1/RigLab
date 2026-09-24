from django.urls import path
from .views import *

urlpatterns = [
    path('', vista_chat, name='inicio'),
    path('chat/buscar/', buscar_sesiones, name='buscar-sesiones'),
    path('chat/nuevo/', nueva_sesion_chat, name='nuevo-chat'),
    path('chat/<uuid:id_sesion>/', vista_chat, name='chat'),
    path('chat/<uuid:id_sesion>/generar/<int:mensaje_id>/', generar_respuesta, name='generar-respuesta'),
    path('chat/<uuid:id_sesion>/subir-archivo/', subir_documento_chat, name='subir-documento-chat'),
    path('chat/<uuid:id_sesion>/eliminar-archivo/<int:id_documento>/', eliminar_documento_chat, name='eliminar-documento-chat'),
    path('chat/<uuid:id_sesion>/editar/', editar_chat, name='editar-chat'),
    path('chat/<uuid:id_sesion>/eliminar/', eliminar_chat, name='eliminar-chat'),
    path('chat/<uuid:id_sesion>/favorito/', toggle_favorito, name='toggle-favorito'),
    path('chat/<uuid:id_sesion>/exportar-csv/', exportar_chat_csv, name='exportar-csv'),
    path('chat/<uuid:id_sesion>/exportar-pdf/', exportar_chat_pdf, name='exportar-pdf'),
]
