from django.urls import path
from .views import (
    vista_chat,
    buscar_sesiones,
    nueva_sesion_chat,
    generar_respuesta,
    subir_documento_chat,
    eliminar_documento_chat,
    editar_chat,
    eliminar_chat,
    toggle_favorito,
    exportar_chat_csv,
    exportar_chat_pdf,
    lista_productos,
    crear_producto,
    editar_producto,
    eliminar_producto_logico,
    reactivar_producto,
    ajustar_stock,
    reportes_inventario,
    exportar_reporte_excel,
    exportar_reporte_pdf,
    catalogo_publico,
    api_chat_cliente,
)

urlpatterns = [
    # Módulo de Chat con IA (Ollama)
    path('', catalogo_publico, name='inicio'),
    path('api/chat-cliente/', api_chat_cliente, name='api-chat-cliente'),
    path('admin-chat/', vista_chat, name='admin-chat'),
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

    # Módulo de Inventario de Componentes de PC (CRUD)
    path('inventario/', lista_productos, name='lista-productos'),
    path('inventario/nuevo/', crear_producto, name='crear-producto'),
    path('inventario/<int:pk>/editar/', editar_producto, name='editar-producto'),
    path('inventario/<int:pk>/eliminar-logico/', eliminar_producto_logico, name='eliminar-producto-logico'),
    path('inventario/<int:pk>/reactivar/', reactivar_producto, name='reactivar-producto'),
    path('inventario/<int:pk>/ajustar-stock/', ajustar_stock, name='ajustar-stock'),

    # Módulo de Reportes Predefinidos (RF-06)
    path('inventario/reportes/', reportes_inventario, name='reportes-inventario'),
    path('inventario/reportes/exportar/excel/', exportar_reporte_excel, name='exportar-reporte-excel'),
    path('inventario/reportes/exportar/pdf/', exportar_reporte_pdf, name='exportar-reporte-pdf'),
]
