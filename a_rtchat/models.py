import uuid
from django.db import models
from django.contrib.auth.models import User

class SesionChat(models.Model):
    id_sesion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=128, default="Nuevo Chat")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    favorito = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.propietario.username}"

    class Meta:
        ordering = ['-favorito', '-fecha_creacion']

class MensajeChat(models.Model):
    sesion = models.ForeignKey(
        SesionChat, related_name='mensajes', on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    cuerpo = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.autor.username} : {self.cuerpo[:20]}'

    class Meta:
        ordering = ['-creado_en']



class DocumentoSesion(models.Model):
    sesion = models.ForeignKey(
        SesionChat, related_name='documentos', on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='documentos_chat/')
    nombre_original = models.CharField(max_length=255)
    tamano_bytes = models.BigIntegerField(default=0)
    ruta_markdown = models.CharField(max_length=512, blank=True, default='')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_original} ({self.sesion.titulo})"

    class Meta:
        ordering = ['-creado_en']


from django.core.validators import MinValueValidator
from decimal import Decimal


class Producto(models.Model):
    """
    Modelo de Componentes de PC para Inventario.
    Cumple con RF-01, RF-04 y validaciones para evitar números negativos.
    """
    class EstadoChoices(models.TextChoices):
        NUEVO = 'Nuevo', 'Nuevo'
        REACONDICIONADO = 'Reacondicionado', 'Reacondicionado'
        USADO = 'Usado', 'Usado'

    class CategoriaChoices(models.TextChoices):
        PROCESADORES = 'Procesadores', 'Procesadores'
        PLACAS_BASE = 'Placas Base', 'Placas Base'
        MEMORIA_RAM = 'Memoria RAM', 'Memoria RAM'
        TARJETAS_GRAFICAS = 'Tarjetas Gráficas', 'Tarjetas Gráficas'
        ALMACENAMIENTO = 'Almacenamiento', 'Almacenamiento'
        FUENTES_PODER = 'Fuentes de Poder', 'Fuentes de Poder'
        CHASIS_GABINETES = 'Gabinetes/Chasis', 'Gabinetes/Chasis'
        REFRIGERACION = 'Refrigeración', 'Refrigeración'
        MONITORES = 'Monitores', 'Monitores'
        TECLADOS = 'Teclados', 'Teclados'
        RATONES = 'Ratones', 'Ratones'
        AUDIO = 'Audio', 'Audio'
        OTROS = 'Otros', 'Otros'

    # Atributos obligatorios
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código (SKU)",
        help_text="Identificador único del producto"
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del componente"
    )
    descripcion = models.TextField(
        verbose_name="Descripción técnica"
    )
    categoria = models.CharField(
        max_length=50,
        choices=CategoriaChoices.choices,
        default=CategoriaChoices.OTROS,
        verbose_name="Categoría"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Precio ($)",
        help_text="No se permiten valores negativos"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Cantidad existente en stock"
    )
    stock_minimo = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=5,
        verbose_name="Stock mínimo permitido"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.NUEVO,
        verbose_name="Estado del producto"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )

    # Eliminación lógica (RF-04)
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desmarcar para realizar eliminación lógica del producto"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"[{self.sku}] {self.nombre} (Stock: {self.cantidad})"

    @property
    def bajo_stock(self):
        return self.cantidad <= self.stock_minimo

    @property
    def agotado(self):
        return self.cantidad == 0

    @property
    def valor_total_stock(self):
        return self.precio * self.cantidad
