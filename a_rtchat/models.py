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
