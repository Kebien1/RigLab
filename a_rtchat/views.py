from pathlib import Path
import os
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse

from .forms import FormularioCrearMensaje, ProductoForm, AjusteStockForm
from .models import SesionChat, MensajeChat, DocumentoSesion, Producto
from .rag import KnowledgeBaseEmpty, LocalRag, LocalRagConfigurationError, LocalRagError
from django.db.models import Q, Max, Min, Sum, F, ExpressionWrapper, DecimalField
from django.contrib import messages

NOMBRE_USUARIO_BOT = "venk"

@login_required
def vista_chat(request, id_sesion=None):
    q = request.GET.get('q', '')
    sesiones = SesionChat.objects.filter(propietario=request.user)
    if q:
        sesiones = sesiones.filter(titulo__icontains=q)
    
    if id_sesion:
        sesion_actual = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    else:
        sesion_actual = sesiones.first()
        if not sesion_actual:
            if not q:
                # Si no tiene sesiones y no está buscando, crear una por defecto
                sesion_actual = SesionChat.objects.create(propietario=request.user)
                return redirect("chat", id_sesion=sesion_actual.id_sesion)
            else:
                # Si está buscando y no hay resultados, intentar cargar la última sesión existente del usuario
                sesion_actual = SesionChat.objects.filter(propietario=request.user).first()
                if not sesion_actual:
                    sesion_actual = SesionChat.objects.create(propietario=request.user)
                    return redirect("chat", id_sesion=sesion_actual.id_sesion)

    # Limpiar sesiones vacías (sin mensajes ni documentos) que no sean la actual
    if sesion_actual:
        sesiones_vacias = SesionChat.objects.filter(
            propietario=request.user
        ).exclude(
            id_sesion=sesion_actual.id_sesion
        ).filter(
            mensajes__isnull=True,
            documentos__isnull=True,
        )
        sesiones_vacias.delete()
        # Refrescar el queryset de sesiones después de la limpieza
        sesiones = SesionChat.objects.filter(propietario=request.user)
        if q:
            sesiones = sesiones.filter(titulo__icontains=q)

    mensajes_chat = sesion_actual.mensajes.all()[:30] if sesion_actual else []
    formulario = FormularioCrearMensaje()
    documentos_sesion = sesion_actual.documentos.all() if sesion_actual else []

    if request.method == "POST":
        formulario = FormularioCrearMensaje(request.POST)
        if formulario.is_valid():
            mensaje = formulario.save(commit=False)
            mensaje.autor = request.user
            mensaje.sesion = sesion_actual
            mensaje.save()
            
            # Actualizar el título si es el primer mensaje
            if sesion_actual.mensajes.count() == 1 or sesion_actual.titulo == "Nuevo Chat":
                sesion_actual.titulo = mensaje.cuerpo[:30] + ("..." if len(mensaje.cuerpo) > 30 else "")
                sesion_actual.save()

            contexto = {
                "mensaje": mensaje,
                "sesion_actual": sesion_actual,
                "usuario": request.user,
            }
            if request.htmx:
                return render(request, "a_rtchat/partials/mensajes_chat_p.html", contexto)
            return redirect("chat", id_sesion=sesion_actual.id_sesion)

    contexto = {
        "sesiones": sesiones,
        "sesion_actual": sesion_actual,
        "mensajes_chat": mensajes_chat,
        "formulario": formulario,
        "documentos_sesion": documentos_sesion,
        "busqueda_q": q,
    }
    return render(request, "a_rtchat/chat.html", contexto)

@login_required
def buscar_sesiones(request):
    """Devuelve solo la lista de sesiones filtrada (para búsqueda en vivo con HTMX)."""
    q = request.GET.get('q', '')
    sesiones = SesionChat.objects.filter(propietario=request.user)
    if q:
        sesiones = sesiones.filter(titulo__icontains=q)
    # Obtener la sesión actual para resaltar en la lista
    sesion_actual = SesionChat.objects.filter(propietario=request.user).first()
    contexto = {
        "sesiones": sesiones,
        "sesion_actual": sesion_actual,
        "busqueda_q": q,
    }
    return render(request, "a_rtchat/partials/lista_sesiones_p.html", contexto)


@login_required
def generar_respuesta(request, id_sesion, mensaje_id):
    sesion_actual = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    mensaje_usuario = get_object_or_404(MensajeChat, id=mensaje_id, sesion=sesion_actual)
    
    mensaje2 = _crear_mensaje_bot(sesion_actual, mensaje_usuario.cuerpo)
    contexto = {
        "mensaje2": mensaje2,
    }
    return render(request, "a_rtchat/partials/mensaje_bot_p.html", contexto)

@login_required
def subir_documento_chat(request, id_sesion):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]
        nombre_orig = archivo.name
        
        # Guardar en base de datos
        doc = DocumentoSesion.objects.create(
            sesion=sesion,
            archivo=archivo,
            nombre_original=nombre_orig,
            tamano_bytes=archivo.size,
        )
        
        # Convertir a Markdown usando MarkItDown
        ruta_archivo = Path(doc.archivo.path)
        markdown_dir = Path(settings.RAG_MARKDOWN_DIR) / "sesiones" / str(sesion.id_sesion)
        markdown_dir.mkdir(parents=True, exist_ok=True)
        salida_md = markdown_dir / f"{doc.id}_{ruta_archivo.name}.md"
        
        texto_md = ""
        try:
            if ruta_archivo.suffix.lower() == ".md":
                texto_md = ruta_archivo.read_text(encoding="utf-8")
            else:
                from markitdown import MarkItDown
                md_conv = MarkItDown(enable_plugins=False)
                res = md_conv.convert(str(ruta_archivo))
                texto_md = res.text_content if hasattr(res, 'text_content') else str(res)
            
            salida_md.write_text(texto_md, encoding="utf-8")
            doc.ruta_markdown = str(salida_md)
            doc.save()
        except Exception as e:
            # Si falla la conversión con MarkItDown, intentar leer como texto plano
            try:
                texto_md = ruta_archivo.read_text(encoding="utf-8", errors="ignore")
                salida_md.write_text(texto_md, encoding="utf-8")
                doc.ruta_markdown = str(salida_md)
                doc.save()
            except Exception:
                pass

        # Crear un mensaje en el chat confirmando la integración del archivo
        MensajeChat.objects.create(
            sesion=sesion,
            autor=_obtener_usuario_bot(),
            cuerpo=f"📄 He procesado el documento **{nombre_orig}**. Ahora puedes hacerme cualquier pregunta sobre su contenido.",
        )
        
    return redirect("chat", id_sesion=sesion.id_sesion)

@login_required
def eliminar_documento_chat(request, id_sesion, id_documento):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    doc = get_object_or_404(DocumentoSesion, id=id_documento, sesion=sesion)
    
    # Eliminar archivo físico y su markdown
    try:
        if doc.ruta_markdown and os.path.exists(doc.ruta_markdown):
            os.remove(doc.ruta_markdown)
        if doc.archivo and os.path.exists(doc.archivo.path):
            os.remove(doc.archivo.path)
    except Exception:
        pass

    nombre = doc.nombre_original
    doc.delete()

    MensajeChat.objects.create(
        sesion=sesion,
        autor=_obtener_usuario_bot(),
        cuerpo=f"🗑️ Se ha desvinculado el documento **{nombre}** de este chat.",
    )
    return redirect("chat", id_sesion=sesion.id_sesion)

@login_required
def nueva_sesion_chat(request):
    # Reusar una sesión vacía existente en lugar de crear otra
    sesion_vacia = SesionChat.objects.filter(
        propietario=request.user,
        mensajes__isnull=True,
        documentos__isnull=True,
    ).first()
    if sesion_vacia:
        return redirect("chat", id_sesion=sesion_vacia.id_sesion)
    nueva_sesion = SesionChat.objects.create(propietario=request.user)
    return redirect("chat", id_sesion=nueva_sesion.id_sesion)

@login_required
def editar_chat(request, id_sesion):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    if request.method == "POST":
        nuevo_titulo = request.POST.get("titulo")
        if nuevo_titulo and nuevo_titulo.strip():
            sesion.titulo = nuevo_titulo.strip()
            sesion.save()
    return redirect("chat", id_sesion=sesion.id_sesion)

@login_required
def eliminar_chat(request, id_sesion):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    if request.method == "POST":
        sesion.delete()
        return redirect("admin-chat")
    return redirect("chat", id_sesion=sesion.id_sesion)

@login_required
def toggle_favorito(request, id_sesion):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    sesion.favorito = not sesion.favorito
    sesion.save()
    return redirect("chat", id_sesion=sesion.id_sesion)

def _obtener_usuario_bot() -> User:
    usuario_bot, creado = User.objects.get_or_create(
        username=NOMBRE_USUARIO_BOT,
        defaults={"email": "venk@ejemplo.local", "is_active": False},
    )
    if creado:
        usuario_bot.set_unusable_password()
        usuario_bot.save(update_fields=["password"])
    return usuario_bot

def _crear_mensaje_bot(sesion: SesionChat, pregunta: str) -> MensajeChat:
    cuerpo = _responder_pregunta(pregunta, sesion=sesion)
    return MensajeChat.objects.create(
        cuerpo=cuerpo,
        autor=_obtener_usuario_bot(),
        sesion=sesion,
    )

def _responder_pregunta(pregunta: str, sesion: SesionChat = None) -> str:
    # Primero intentar respuesta conversacional directa con Ollama (rápido y con contexto)
    try:
        return _respuesta_directa_ollama(pregunta, sesion=sesion)
    except Exception:
        pass

    # Fallback al sistema RAG si la respuesta directa falla
    try:
        respuesta = LocalRag.from_settings().answer(pregunta)
    except KnowledgeBaseEmpty as exc:
        return str(exc)
    except LocalRagConfigurationError as exc:
        return str(exc)
    except LocalRagError:
        return (
            "No pude consultar la base de conocimientos local. "
            "Verifica que Ollama esté en ejecución y los modelos configurados estén instalados."
        )

    if not respuesta.sources:
        return respuesta.text

    fuentes = ", ".join(respuesta.sources)
    return f"{respuesta.text}\n\nFuentes: {fuentes}"


import time as _time

_cache_inventario = {"cliente": "", "tienda": "", "ts": 0}
_CACHE_TTL = 60


def _inventario_compacto_cliente():
    """Formato ultra-compacto del inventario para el chat del cliente."""
    ahora = _time.time()
    if _cache_inventario["cliente"] and (ahora - _cache_inventario["ts"]) < _CACHE_TTL:
        return _cache_inventario["cliente"]

    productos = Producto.objects.filter(activo=True, cantidad__gt=0).order_by('categoria', 'nombre')
    if not productos.exists():
        return "No hay productos disponibles en este momento."

    lineas = ["SKU | Producto | Categoría | Precio | Disponible"]
    for p in productos:
        lineas.append(f"{p.sku} | {p.nombre} | {p.categoria} | Bs {p.precio:.0f} | {p.cantidad} uds")

    texto = "\n".join(lineas)
    _cache_inventario["cliente"] = texto
    _cache_inventario["ts"] = ahora
    return texto


def _inventario_compacto_tienda():
    """Formato compacto del inventario para el asistente de tienda."""
    ahora = _time.time()
    if _cache_inventario["tienda"] and (ahora - _cache_inventario["ts"]) < _CACHE_TTL:
        return _cache_inventario["tienda"]

    productos = Producto.objects.filter(activo=True).order_by('categoria', 'nombre')
    if not productos.exists():
        return "El inventario está vacío."

    lineas = ["SKU | Producto | Categoría | Precio | Stock | Mín | Estado"]
    for p in productos:
        lineas.append(f"{p.sku} | {p.nombre} | {p.categoria} | Bs {p.precio:.0f} | {p.cantidad} | {p.stock_minimo} | {p.estado}")

    texto = "\n".join(lineas)
    _cache_inventario["tienda"] = texto
    _cache_inventario["ts"] = ahora
    return texto


def _obtener_contexto_inventario():
    """Compatibilidad. Usa formato compacto de tienda."""
    return _inventario_compacto_tienda()


import json
import re

def _ejecutar_crud_ia(json_data: dict) -> str:
    """Ejecuta operaciones CRUD basadas en el JSON generado por la IA."""
    accion = json_data.get('accion', '').upper()
    try:
        if accion == 'CREAR':
            # Validaciones básicas
            sku = json_data.get('sku')
            nombre = json_data.get('nombre')
            precio = float(json_data.get('precio', 0))
            cantidad = int(json_data.get('cantidad', 0))
            
            if precio < 0 or cantidad < 0:
                return "Error: Precio y cantidad no pueden ser negativos."
            if not sku or not nombre:
                return "Error: SKU y nombre son obligatorios."
            if Producto.objects.filter(sku=sku).exists():
                return f"Error: Ya existe un producto con el SKU {sku}."
            
            Producto.objects.create(
                sku=sku,
                nombre=nombre,
                descripcion=json_data.get('descripcion', 'Sin descripción'),
                categoria=json_data.get('categoria', Producto.CategoriaChoices.OTROS),
                precio=precio,
                cantidad=cantidad,
                stock_minimo=int(json_data.get('stock_minimo', 5)),
                estado=json_data.get('estado', Producto.EstadoChoices.NUEVO),
            )
            return "Éxito: Producto creado correctamente."

        elif accion == 'ACTUALIZAR':
            sku = json_data.get('sku')
            if not sku:
                return "Error: Se requiere el SKU para actualizar."
            
            producto = Producto.objects.filter(sku=sku).first()
            if not producto:
                return f"Error: Producto con SKU {sku} no encontrado."
            
            if 'precio' in json_data:
                precio = float(json_data['precio'])
                if precio < 0: return "Error: El precio no puede ser negativo."
                producto.precio = precio
            
            if 'cantidad' in json_data:
                cantidad = int(json_data['cantidad'])
                if cantidad < 0: return "Error: La cantidad no puede ser negativa."
                producto.cantidad = cantidad
                
            if 'nombre' in json_data: producto.nombre = json_data['nombre']
            if 'descripcion' in json_data: producto.descripcion = json_data['descripcion']
            
            producto.save()
            return "Éxito: Producto actualizado correctamente."

        elif accion == 'ELIMINAR':
            sku = json_data.get('sku')
            if not sku:
                return "Error: Se requiere el SKU para eliminar."
            
            producto = Producto.objects.filter(sku=sku).first()
            if not producto:
                return f"Error: Producto con SKU {sku} no encontrado."
            
            producto.activo = False
            producto.save()
            return "Éxito: Producto eliminado (baja lógica) correctamente."
            
        return f"Error: Acción '{accion}' no reconocida."
        
    except Exception as e:
        return f"Error interno al procesar la base de datos: {str(e)}"


def _respuesta_directa_ollama(pregunta: str, sesion: SesionChat = None) -> str:
    """Llama a Ollama con qwen2.5:1.5b usando contexto compacto del inventario."""
    import ollama
    from django.conf import settings as django_settings

    chat_model = getattr(django_settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")
    inventario = _inventario_compacto_tienda()

    # Detectar si el usuario quiere hacer CRUD basado en palabras clave
    msg_lower = pregunta.lower()
    keywords_crud = ["crea", "agrega", "añade", "nuevo", "registra", "actualiza", "modifica", "cambia", "edita", "elimina", "borra", "quita"]
    es_crud = any(kw in msg_lower for kw in keywords_crud)

    if es_crud:
        instrucciones_extra = (
            "El usuario quiere MODIFICAR el inventario. Responde ÚNICAMENTE con un bloque JSON así:\n"
            "Crear: ```json\n{\"accion\":\"CREAR\",\"sku\":\"...\",\"nombre\":\"...\",\"precio\":0,\"cantidad\":0,\"descripcion\":\"...\",\"categoria\":\"...\"}\n```\n"
            "Actualizar: ```json\n{\"accion\":\"ACTUALIZAR\",\"sku\":\"SKU_EXISTENTE\",\"precio\":0,\"cantidad\":0}\n```\n"
            "Eliminar: ```json\n{\"accion\":\"ELIMINAR\",\"sku\":\"SKU_EXISTENTE\"}\n```\n"
        )
    else:
        instrucciones_extra = "El usuario está haciendo una PREGUNTA. Responde normalmente en español con un texto breve. NO uses JSON."

    # System prompt dinámico
    system_prompt = (
        "Eres el asistente de inventario de RigLab.\n"
        "REGLAS:\n"
        "- Nunca inventes datos. Usa SOLO SKUs reales del inventario si te los piden.\n"
        f"{instrucciones_extra}\n\n"
        f"INVENTARIO:\n{inventario}"
    )

    historial_mensajes = []
    if sesion:
        mensajes_recientes = list(sesion.mensajes.order_by("-creado_en")[:4])
        mensajes_recientes.reverse()
        for m in mensajes_recientes:
            rol = "assistant" if m.autor.username == NOMBRE_USUARIO_BOT else "user"
            historial_mensajes.append({"role": rol, "content": m.cuerpo})

    if not historial_mensajes or historial_mensajes[-1].get("content") != pregunta:
        historial_mensajes.append({"role": "user", "content": pregunta})

    messages = [{"role": "system", "content": system_prompt}] + historial_mensajes
    client = ollama.Client(host=django_settings.OLLAMA_BASE_URL)

    response = client.chat(
        model=chat_model,
        messages=messages,
        options={"temperature": 0.1, "top_p": 0.7, "num_predict": 200, "repeat_penalty": 1.15},
    )

    text = response.get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("Respuesta vacía de Ollama")

    # Detectar si la IA intentó una operación CRUD
    match_json = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    json_str = None
    if match_json:
        json_str = match_json.group(1)
    else:
        # Intentar buscar JSON sin formato markdown
        match_raw = re.search(r'(\{.*?\"accion\".*?\})', text, re.DOTALL)
        if match_raw:
            json_str = match_raw.group(1)

    if json_str:
        try:
            json_data = json.loads(json_str)
            if 'accion' in json_data:
                resultado_crud = _ejecutar_crud_ia(json_data)
                # Invalidar caché tras operación CRUD
                _cache_inventario["ts"] = 0
                # Respuesta directa sin segunda llamada a Ollama
                if resultado_crud.startswith("Éxito"):
                    accion = json_data.get('accion', '').upper()
                    sku = json_data.get('sku', '')
                    nombre = json_data.get('nombre', sku)
                    if accion == 'CREAR':
                        return f"✅ Producto **{nombre}** (SKU: {sku}) registrado correctamente en el inventario."
                    elif accion == 'ACTUALIZAR':
                        campos = [k for k in json_data if k not in ('accion', 'sku')]
                        return f"✅ Producto **{sku}** actualizado. Campos modificados: {', '.join(campos)}."
                    elif accion == 'ELIMINAR':
                        return f"✅ Producto **{sku}** dado de baja (eliminación lógica) correctamente."
                    return f"✅ {resultado_crud}"
                else:
                    return f"⚠️ {resultado_crud}"
        except json.JSONDecodeError:
            pass

    return text


def _buscar_fragmentos_relevantes(pregunta: str, sesion: SesionChat = None, max_chars: int = 3500) -> str:
    """Busca los fragmentos más relevantes a la pregunta.
    
    Si la sesión tiene documentos subidos (Opción A), busca de forma exclusiva en ellos.
    Si no tiene documentos propios, busca en la base general knowledge_markdown.
    """
    from django.conf import settings as django_settings

    archivos_a_leer = []

    # 1. Si la sesión tiene documentos subidos, usarlos exclusivamente
    if sesion and sesion.documentos.exists():
        for doc in sesion.documentos.all():
            if doc.ruta_markdown and Path(doc.ruta_markdown).exists():
                archivos_a_leer.append(Path(doc.ruta_markdown))
    
    # 2. Si no hay documentos de sesión, usar los de la base general
    if not archivos_a_leer:
        markdown_dir = Path(django_settings.RAG_MARKDOWN_DIR)
        if markdown_dir.exists():
            for archivo in sorted(markdown_dir.glob("*.md")):
                if archivo.is_file():
                    archivos_a_leer.append(archivo)

    if not archivos_a_leer:
        return ""

    # Leer todo el texto
    todo_el_texto = ""
    for archivo in archivos_a_leer:
        try:
            todo_el_texto += archivo.read_text(encoding="utf-8") + "\n\n"
        except Exception:
            continue

    if not todo_el_texto.strip():
        return ""

    # Dividir en párrafos/secciones
    parrafos = [p.strip() for p in todo_el_texto.split("\n\n") if p.strip() and len(p.strip()) > 20]

    # Palabras clave de la pregunta (quitar palabras muy comunes)
    palabras_ignorar = {
        "que", "es", "la", "el", "un", "una", "los", "las", "de", "del", "en",
        "y", "o", "a", "al", "por", "para", "con", "se", "su", "como", "son",
        "cual", "cuales", "me", "te", "lo", "le", "nos", "qué", "cómo",
        "dime", "explica", "explicame", "puedes", "decir", "hablar", "hay",
        "sobre", "acerca", "tiene", "tienen", "fue", "ser", "esta", "estan",
        "hola", "gracias", "favor", "ejemplo", "ejemplos",
    }
    palabras_clave = [
        _quitar_acentos(p.lower().strip("¿?¡!.,;:"))
        for p in pregunta.split()
        if _quitar_acentos(p.lower().strip("¿?¡!.,;:")) not in palabras_ignorar and len(p) > 2
    ]

    # Si el texto total es corto (ej. documento de tamaño moderado subido por el usuario), retornarlo completo
    if len(todo_el_texto) <= max_chars:
        return todo_el_texto.strip()

    if not palabras_clave:
        # Si no hay palabras clave específicas, devolver los primeros párrafos del documento
        return todo_el_texto[:max_chars].strip()

    # Puntuar cada párrafo según cuántas palabras clave contiene
    puntuados = []
    for parrafo in parrafos:
        parrafo_normalizado = _quitar_acentos(parrafo.lower())
        puntaje = sum(1 for palabra in palabras_clave if palabra in parrafo_normalizado)
        if puntaje > 0:
            puntuados.append((puntaje, parrafo))

    if not puntuados:
        # Fallback a los primeros párrafos
        return todo_el_texto[:max_chars].strip()

    # Ordenar por relevancia y tomar los mejores
    puntuados.sort(key=lambda x: x[0], reverse=True)

    resultado = ""
    for _, parrafo in puntuados:
        if len(resultado) + len(parrafo) > max_chars:
            break
        resultado += parrafo + "\n\n"

    return resultado.strip()


def _quitar_acentos(texto: str) -> str:
    """Quita tildes y acentos para comparaciones de búsqueda."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

@login_required
def exportar_chat_csv(request, id_sesion):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="chat_{sesion.id_sesion}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Autor', 'Mensaje'])
    
    # Exportar mensajes en orden cronológico ascendente (el más viejo primero)
    for mensaje in sesion.mensajes.all().order_by('creado_en'):
        writer.writerow([
            mensaje.creado_en.strftime("%Y-%m-%d %H:%M:%S"),
            mensaje.autor.username,
            mensaje.cuerpo
        ])
        
    return response

@login_required
def exportar_chat_pdf(request, id_sesion):
    sesion = get_object_or_404(SesionChat, id_sesion=id_sesion, propietario=request.user)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="chat_{sesion.id_sesion}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []
    
    titulo = f"Historial de Chat: {sesion.titulo}"
    Story.append(Paragraph(titulo, styles['Title']))
    Story.append(Spacer(1, 12))
    
    for mensaje in sesion.mensajes.all().order_by('creado_en'):
        fecha_str = mensaje.creado_en.strftime("%Y-%m-%d %H:%M:%S")
        autor_str = mensaje.autor.username
        
        encabezado = f"<b>{autor_str}</b> ({fecha_str}):"
        Story.append(Paragraph(encabezado, styles['Normal']))
        
        # Convertir saltos de línea de texto a saltos de HTML para platypus
        cuerpo = mensaje.cuerpo.replace('\n', '<br />')
        Story.append(Paragraph(cuerpo, styles['Normal']))
        Story.append(Spacer(1, 6))
        
    doc.build(Story)
    return response


# ==============================================================================
# VISTAS DE INVENTARIO DE COMPONENTES DE PC (CRUD Y CONTROL DE EXISTENCIAS)
# ==============================================================================

@login_required
def lista_productos(request):
    """
    RF-02: Consulta de productos con búsqueda filtrada por Código (SKU), Nombre o Categoría.
    Muestra productos y permite filtrar entre todos, solo activos o solo dados de baja.
    """
    query = request.GET.get('q', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    estado_filtro = request.GET.get('estado_filtro', 'activos').strip()

    productos = Producto.objects.all()

    # Filtro de estado lógico
    if estado_filtro == 'activos':
        productos = productos.filter(activo=True)
    elif estado_filtro == 'inactivos':
        productos = productos.filter(activo=False)

    # Filtro por categoría
    if categoria_filtro:
        productos = productos.filter(categoria=categoria_filtro)

    # Búsqueda por SKU, nombre o categoría
    if query:
        productos = productos.filter(
            Q(sku__icontains=query) |
            Q(nombre__icontains=query) |
            Q(categoria__icontains=query)
        )

    categorias = Producto.CategoriaChoices.choices

    # Estadísticas rápidas para tarjetas del encabezado
    total_registrados = Producto.objects.filter(activo=True).count()
    bajo_stock_count = sum(1 for p in Producto.objects.filter(activo=True) if p.bajo_stock)
    agotados_count = Producto.objects.filter(activo=True, cantidad=0).count()

    contexto = {
        'productos': productos,
        'query': query,
        'categoria_filtro': categoria_filtro,
        'estado_filtro': estado_filtro,
        'categorias': categorias,
        'total_registrados': total_registrados,
        'bajo_stock_count': bajo_stock_count,
        'agotados_count': agotados_count,
    }
    return render(request, 'a_rtchat/inventario/lista_productos.html', contexto)


@login_required
def crear_producto(request):
    """RF-01: Registro de nuevos componentes de PC."""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f"Componente [{producto.sku}] {producto.nombre} registrado con éxito.")
            return redirect('lista-productos')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ProductoForm()

    return render(request, 'a_rtchat/inventario/formulario_producto.html', {
        'form': form,
        'titulo_accion': 'Registrar Componente de PC',
        'boton_texto': 'Guardar Producto'
    })


@login_required
def editar_producto(request, pk):
    """RF-03: Actualización de datos de un componente existente."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Componente [{producto.sku}] actualizado con éxito.")
            return redirect('lista-productos')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'a_rtchat/inventario/formulario_producto.html', {
        'form': form,
        'producto': producto,
        'titulo_accion': f"Modificar: {producto.nombre}",
        'boton_texto': 'Guardar Cambios'
    })


@login_required
def eliminar_producto_logico(request, pk):
    """
    RF-04: Eliminación lógica cambiando el campo activo a False.
    Conserva el historial en la base de datos SQLite.
    """
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        messages.warning(request, f"Componente [{producto.sku}] ha sido dado de baja (Eliminación lógica realizada).")
        return redirect('lista-productos')

    return render(request, 'a_rtchat/inventario/confirmar_baja.html', {'producto': producto})


@login_required
def reactivar_producto(request, pk):
    """Permite reactivar un producto previamente dado de baja."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = True
        producto.save()
        messages.success(request, f"Componente [{producto.sku}] reactivado exitosamente en el inventario.")
    return redirect('lista-productos')


@login_required
def ajustar_stock(request, pk):
    """
    RF-05: Control de existencias (incrementar/decrementar).
    Impide que la existencia caiga en valores negativos.
    """
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = AjusteStockForm(request.POST)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            cant = form.cleaned_data['cantidad']

            if accion == 'sumar':
                producto.cantidad += cant
                producto.save()
                messages.success(request, f"Se agregaron {cant} unidades a {producto.nombre}. Stock actual: {producto.cantidad}")
                return redirect('lista-productos')
            elif accion == 'restar':
                if producto.cantidad < cant:
                    messages.error(
                        request,
                        f"Operación denegada: No se puede decrementar en {cant} unidades. Stock disponible: {producto.cantidad} (Evita valores negativos)."
                    )
                else:
                    producto.cantidad -= cant
                    producto.save()
                    messages.info(request, f"Se descontaron {cant} unidades a {producto.nombre}. Stock actual: {producto.cantidad}")
                    return redirect('lista-productos')
    else:
        form = AjusteStockForm()

    return render(request, 'a_rtchat/inventario/ajustar_stock.html', {
        'producto': producto,
        'form': form
    })


# ==============================================================================
# VISTAS DE REPORTES PREDEFINIDOS (RF-06)
# ==============================================================================

def _obtener_datos_reporte(tipo_reporte):
    """Retorna (titulo_reporte, productos_qs, valor_total_inventario, mas_caro, mas_barato)"""
    qs_activos = Producto.objects.filter(activo=True)
    inventario_con_valor = qs_activos.annotate(
        valor_acumulado=ExpressionWrapper(F('precio') * F('cantidad'), output_field=DecimalField(max_digits=12, decimal_places=2))
    )
    valor_total_inventario = inventario_con_valor.aggregate(total=Sum('valor_acumulado'))['total'] or 0
    mas_caro = qs_activos.order_by('-precio').first()
    mas_barato = qs_activos.order_by('precio').first()

    if tipo_reporte == 'extremos':
        titulo = "2. Componente Más Caro y Más Barato"
        ids = [p.id for p in [mas_caro, mas_barato] if p is not None]
        productos = qs_activos.filter(id__in=ids).order_by('-precio')
    elif tipo_reporte == 'bajo_stock':
        titulo = "3. Productos con Existencias Menores o Iguales al Stock Mínimo"
        productos = qs_activos.filter(cantidad__lte=F('stock_minimo'), cantidad__gt=0).order_by('cantidad')
    elif tipo_reporte == 'agotados':
        titulo = "4. Productos Agotados (Stock Cero)"
        productos = qs_activos.filter(cantidad=0)
    elif tipo_reporte == 'eliminados':
        titulo = "5. Productos Eliminados Lógicamente (Inactivos)"
        productos = Producto.objects.filter(activo=False).order_by('-fecha_registro')
    else:
        tipo_reporte = 'todos'
        titulo = "1. Listado General de Componentes Activos"
        productos = qs_activos.order_by('categoria', 'nombre')

    return tipo_reporte, titulo, productos, valor_total_inventario, mas_caro, mas_barato


@login_required
def reportes_inventario(request):
    """
    RF-06: Menú de reportes con opciones predefinidas.
    """
    tipo_reporte = request.GET.get('tipo', 'todos')
    tipo_reporte, titulo_reporte, productos_reporte, valor_total_inventario, mas_caro, mas_barato = _obtener_datos_reporte(tipo_reporte)

    contexto = {
        'tipo_reporte': tipo_reporte,
        'titulo_reporte': titulo_reporte,
        'productos_reporte': productos_reporte,
        'mas_caro': mas_caro,
        'mas_barato': mas_barato,
        'valor_total_inventario': valor_total_inventario,
        'total_productos': Producto.objects.filter(activo=True).count(),
        'total_eliminados': Producto.objects.filter(activo=False).count(),
    }
    return render(request, 'a_rtchat/inventario/reportes.html', contexto)


@login_required
def exportar_reporte_excel(request):
    """Exporta el reporte seleccionado a formato Excel (.xlsx)."""
    tipo_reporte = request.GET.get('tipo', 'todos')
    _, titulo_reporte, productos, valor_total_inventario, _, _ = _obtener_datos_reporte(tipo_reporte)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Inventario"

    # Estilos
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="0F172A")
    subtitle_font = Font(name="Calibri", size=10, italic=True, color="475569")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Título del Reporte
    ws.merge_cells("A1:J1")
    ws["A1"] = f"RIGLAB — {titulo_reporte.upper()}"
    ws["A1"].font = title_font

    ws.merge_cells("A2:J2")
    fecha_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws["A2"] = f"Generado el: {fecha_generacion} | Generado por: {request.user.username} | Total Registros: {productos.count()}"
    ws["A2"].font = subtitle_font

    # Encabezados de Tabla (Fila 4)
    columnas = [
        "SKU",
        "Nombre del Componente",
        "Categoría",
        "Precio Unitario (Bs)",
        "Existencia",
        "Stock Mínimo",
        "Subtotal Invertido (Bs)",
        "Condición",
        "Estado / Visibilidad",
        "Fecha Registro"
    ]

    for col_idx, col_name in enumerate(columnas, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.row_dimensions[4].height = 24

    # Llenado de Filas
    fila_actual = 5
    for p in productos:
        subtotal = float(p.valor_total_stock)
        estado_vis = "Activo" if p.activo else "Eliminado Lógico"

        ws.cell(row=fila_actual, column=1, value=p.sku).alignment = Alignment(horizontal="center")
        ws.cell(row=fila_actual, column=2, value=p.nombre)
        ws.cell(row=fila_actual, column=3, value=p.categoria)
        
        celda_precio = ws.cell(row=fila_actual, column=4, value=float(p.precio))
        celda_precio.number_format = '#,##0.00'
        celda_precio.alignment = Alignment(horizontal="right")

        ws.cell(row=fila_actual, column=5, value=p.cantidad).alignment = Alignment(horizontal="center")
        ws.cell(row=fila_actual, column=6, value=p.stock_minimo).alignment = Alignment(horizontal="center")

        celda_subtotal = ws.cell(row=fila_actual, column=7, value=subtotal)
        celda_subtotal.number_format = '#,##0.00'
        celda_subtotal.alignment = Alignment(horizontal="right")

        ws.cell(row=fila_actual, column=8, value=p.estado).alignment = Alignment(horizontal="center")
        ws.cell(row=fila_actual, column=9, value=estado_vis).alignment = Alignment(horizontal="center")
        ws.cell(row=fila_actual, column=10, value=p.fecha_registro.strftime("%Y-%m-%d")).alignment = Alignment(horizontal="center")

        for col_idx in range(1, 11):
            cell = ws.cell(row=fila_actual, column=col_idx)
            cell.border = thin_border
            cell.font = regular_font

        fila_actual += 1

    # Fila de Totales si aplica
    ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=6)
    celda_tot_label = ws.cell(row=fila_actual, column=1, value="TOTAL VALORIZADO")
    celda_tot_label.font = bold_font
    celda_tot_label.alignment = Alignment(horizontal="right")

    celda_tot = ws.cell(row=fila_actual, column=7, value=f"=SUM(G5:G{fila_actual-1})")
    celda_tot.font = bold_font
    celda_tot.number_format = '#,##0.00'
    celda_tot.alignment = Alignment(horizontal="right")

    for col_idx in range(1, 11):
        c = ws.cell(row=fila_actual, column=col_idx)
        c.border = thin_border
        c.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    # Ajuste automático del ancho de columnas
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in [1, 2]:
                continue
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    nombre_archivo = f"reporte_riglab_{tipo_reporte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    wb.save(response)
    return response


@login_required
def exportar_reporte_pdf(request):
    """Exporta el reporte seleccionado a documento PDF con formato apaisado."""
    tipo_reporte = request.GET.get('tipo', 'todos')
    _, titulo_reporte, productos, valor_total_inventario, _, _ = _obtener_datos_reporte(tipo_reporte)

    response = HttpResponse(content_type='application/pdf')
    nombre_archivo = f"reporte_riglab_{tipo_reporte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'RepSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    th_style = ParagraphStyle(
        'RepTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )
    td_style = ParagraphStyle(
        'RepTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    td_center = ParagraphStyle('RepTDC', parent=td_style, alignment=1)
    td_right = ParagraphStyle('RepTDR', parent=td_style, alignment=2)
    td_bold_right = ParagraphStyle('RepTDBR', parent=td_style, fontName='Helvetica-Bold', alignment=2)

    story = []

    # Encabezado
    story.append(Paragraph(f"<b>RigLab</b> — {titulo_reporte}", title_style))
    fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Fecha de emisión: {fecha_str} | Generado por: {request.user.username} | Total registros: {productos.count()}", sub_style))

    # Construcción de la tabla
    tabla_datos = [[
        Paragraph("SKU", th_style),
        Paragraph("Nombre del Componente", th_style),
        Paragraph("Categoría", th_style),
        Paragraph("Precio (Bs)", th_style),
        Paragraph("Stock", th_style),
        Paragraph("Mín.", th_style),
        Paragraph("Subtotal (Bs)", th_style),
        Paragraph("Condición", th_style),
        Paragraph("Estado", th_style),
        Paragraph("Fecha Reg.", th_style),
    ]]

    total_subtotal = 0
    for p in productos:
        subtotal = p.valor_total_stock
        total_subtotal += subtotal
        estado_vis = "Activo" if p.activo else "Eliminado"
        
        # Color suave para eliminados
        fila = [
            Paragraph(p.sku, td_center),
            Paragraph(p.nombre[:38], td_style),
            Paragraph(p.categoria, td_center),
            Paragraph(f"Bs {p.precio:,.2f}", td_right),
            Paragraph(str(p.cantidad), td_center),
            Paragraph(str(p.stock_minimo), td_center),
            Paragraph(f"Bs {subtotal:,.2f}", td_right),
            Paragraph(p.estado, td_center),
            Paragraph(estado_vis, td_center),
            Paragraph(p.fecha_registro.strftime("%Y-%m-%d"), td_center),
        ]
        tabla_datos.append(fila)

    # Fila total
    tabla_datos.append([
        Paragraph("<b>TOTAL GENERAL</b>", td_bold_right),
        "", "", "", "", "",
        Paragraph(f"<b>Bs {total_subtotal:,.2f}</b>", td_bold_right),
        "", "", ""
    ])

    # Anchos de columnas (Landscape letter es 792 pt, menos márgenes = ~732 pt disponible)
    col_widths = [60, 172, 90, 65, 40, 35, 75, 65, 65, 65]
    tabla = Table(tabla_datos, colWidths=col_widths, repeatRows=1)

    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('SPAN', (0, -1), (5, -1)),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
    ]

    # Alternar colores de fila
    for i in range(1, len(tabla_datos) - 1):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F8FAFC')))

    tabla.setStyle(TableStyle(t_style))
    story.append(tabla)

    doc.build(story)
    return response

def catalogo_publico(request):
    """
    Vista pública (Landing Page) para los clientes.
    Muestra los productos activos en un catálogo estilo vitrina con filtrado dinámico por categoría.
    """
    categoria_sel = request.GET.get('categoria', '').strip()
    productos_base = Producto.objects.filter(activo=True)
    
    # Extraer categorías activas con recuento
    from django.db.models import Count
    categorias_disponibles = (
        productos_base.values('categoria')
        .annotate(total=Count('id'))
        .order_by('categoria')
    )

    if categoria_sel:
        productos = productos_base.filter(categoria=categoria_sel).order_by('nombre')
    else:
        productos = productos_base.order_by('categoria', 'nombre')
    
    contexto = {
        'productos': productos,
        'categorias_disponibles': categorias_disponibles,
        'categoria_sel': categoria_sel,
        'total_productos': productos_base.count(),
    }
    return render(request, 'a_rtchat/publico/catalogo.html', contexto)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

def _obtener_knowledge_base() -> str:
    """Lee todos los archivos de la carpeta knowledge_base y extrae su contenido."""
    from django.conf import settings as django_settings
    kb_path = os.path.join(django_settings.BASE_DIR, 'knowledge_base')
    if not os.path.exists(kb_path):
        return ""
    
    contenido_total = []
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        
        for filename in os.listdir(kb_path):
            if filename == '.gitkeep': continue
            filepath = os.path.join(kb_path, filename)
            
            if os.path.isfile(filepath):
                try:
                    if filename.endswith('.md') or filename.endswith('.txt'):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contenido_total.append(f"--- ARCHIVO: {filename} ---\n{f.read()}\n")
                    else:
                        # Intentar convertir con MarkItDown
                        resultado = md.convert(filepath)
                        contenido_total.append(f"--- ARCHIVO: {filename} ---\n{resultado.text_content}\n")
                except Exception as e:
                    print(f"Error procesando {filename}: {e}")
                    
    except Exception as e:
        print(f"Error inicializando knowledge base: {e}")
        
    return "\n".join(contenido_total)


@csrf_exempt
def api_chat_cliente(request):
    """
    Endpoint para el chat flotante de clientes.
    Usa inventario compacto y prompt reducido para respuestas rápidas y precisas.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo POST permitido'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        historial = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)

        import ollama
        from django.conf import settings as django_settings
        chat_model = getattr(django_settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")

        # Pre-filtrado por categoría para reducir contexto
        MAPA_CATEGORIAS = {
            'procesador': 'Procesadores', 'cpu': 'Procesadores', 'ryzen': 'Procesadores', 'intel': 'Procesadores',
            'placa base': 'Placas Base', 'placa madre': 'Placas Base', 'motherboard': 'Placas Base', 'tarjeta madre': 'Placas Base',
            'ram': 'Memoria RAM', 'memoria': 'Memoria RAM', 'ddr': 'Memoria RAM',
            'tarjeta gráfica': 'Tarjetas Gráficas', 'gpu': 'Tarjetas Gráficas', 'gráfica': 'Tarjetas Gráficas',
            'rtx': 'Tarjetas Gráficas', 'radeon': 'Tarjetas Gráficas', 'rx': 'Tarjetas Gráficas',
            'ssd': 'Almacenamiento', 'disco': 'Almacenamiento', 'almacenamiento': 'Almacenamiento', 'nvme': 'Almacenamiento',
            'fuente': 'Fuentes de Poder', 'psu': 'Fuentes de Poder', 'fuente de poder': 'Fuentes de Poder',
            'gabinete': 'Gabinetes/Chasis', 'chasis': 'Gabinetes/Chasis', 'case': 'Gabinetes/Chasis', 'torre': 'Gabinetes/Chasis',
            'refrigeración': 'Refrigeración', 'cooler': 'Refrigeración', 'disipador': 'Refrigeración', 'ventilador': 'Refrigeración',
            'monitor': 'Monitores', 'pantalla': 'Monitores',
            'teclado': 'Teclados', 'keyboard': 'Teclados',
            'ratón': 'Ratones', 'raton': 'Ratones', 'mouse': 'Ratones',
            'auricular': 'Audio', 'audífono': 'Audio', 'headset': 'Audio', 'audio': 'Audio',
        }

        msg_lower = user_message.lower()
        categorias_detectadas = set()
        for keyword, categoria in MAPA_CATEGORIAS.items():
            if keyword in msg_lower:
                categorias_detectadas.add(categoria)

        # Construir inventario filtrado en formato compacto
        productos_q = Producto.objects.filter(activo=True, cantidad__gt=0)
        if categorias_detectadas:
            productos_q = productos_q.filter(categoria__in=categorias_detectadas)
        productos_q = productos_q.order_by('categoria', 'nombre')

        if not productos_q.exists():
            if categorias_detectadas:
                inventario_texto = f"No tenemos productos en: {', '.join(categorias_detectadas)}."
            else:
                inventario_texto = _inventario_compacto_cliente()
        else:
            lineas = []
            for p in productos_q:
                lineas.append(f"{p.sku} | {p.nombre} | {p.categoria} | Bs {p.precio:.0f} | {p.cantidad} uds")
            inventario_texto = "\n".join(lineas)

        system_prompt = (
            "Eres Venk, asesor de ventas de RigLab (tienda de componentes de PC).\n"
            "Responde SOLO con los datos de abajo. NUNCA inventes productos ni precios.\n"
            "Precios en Bolivianos (Bs). Si no existe el producto, dilo.\n"
            "Sé breve, amable y responde en español.\n\n"
            f"PRODUCTOS:\n{inventario_texto}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        # Solo últimos 3 mensajes de historial para reducir contexto
        for msg in historial[-3:]:
            if msg.get('role') in ['user', 'assistant']:
                messages.append({"role": msg['role'], "content": msg.get('content', '')})

        messages.append({"role": "user", "content": user_message})

        client = ollama.Client(host=django_settings.OLLAMA_BASE_URL)
        response = client.chat(
            model=chat_model,
            messages=messages,
            options={"temperature": 0.0, "top_p": 0.5, "num_predict": 250},
        )

        text = response.get("message", {}).get("content", "").strip()
        return JsonResponse({'response': text})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

