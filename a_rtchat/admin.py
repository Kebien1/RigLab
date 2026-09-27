from django.contrib import admin
from .models import SesionChat, MensajeChat, DocumentoSesion, Producto


admin.site.register(SesionChat)
admin.site.register(MensajeChat)
admin.site.register(DocumentoSesion)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'nombre',
        'categoria',
        'precio',
        'cantidad',
        'stock_minimo',
        'estado',
        'activo',
        'fecha_registro'
    )
    list_filter = ('activo', 'categoria', 'estado', 'fecha_registro')
    search_fields = ('sku', 'nombre', 'descripcion')
    list_editable = ('activo',)
    readonly_fields = ('fecha_registro',)
    actions = ['marcar_como_inactivo', 'marcar_como_activo']

    @admin.action(description="Dar de baja (Eliminación lógica) a los productos seleccionados")
    def marcar_como_inactivo(self, request, queryset):
        queryset.update(activo=False)

    @admin.action(description="Reactivar los productos seleccionados")
    def marcar_como_activo(self, request, queryset):
        queryset.update(activo=True)
