from pathlib import Path
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse

from .forms import FormularioCrearMensaje
from .models import SesionChat, MensajeChat, DocumentoSesion
from .rag import KnowledgeBaseEmpty, LocalRag, LocalRagConfigurationError, LocalRagError

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
        return redirect("inicio")
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


def _respuesta_directa_ollama(pregunta: str, sesion: SesionChat = None) -> str:
    """Llama directamente a Ollama con historial de la conversación y fragmentos relevantes."""
    import ollama
    from django.conf import settings as django_settings

    # Buscar fragmentos relevantes en los documentos de la sesión (o en su defecto, en knowledge_markdown)
    contexto_docs = _buscar_fragmentos_relevantes(pregunta, sesion=sesion)

    chat_model = getattr(django_settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")

    system_prompt = (
        f"Eres Venk (o botty), un asistente virtual inteligente basado en el modelo {chat_model}, desarrollado para un sistema de chat con RAG en Django.\n\n"
        "REGLAS OBLIGATORIAS DE COMPORTAMIENTO:\n"
        "1. SALUDOS, CORTESÍA Y DESPEDIDAS:\n"
        "   - Si el usuario te saluda (ej: 'hola', 'buenos días'), responde amablemente y con calidez.\n"
        "   - Si el usuario te agradece (ej: 'gracias', 'muchas gracias', 'te lo agradezco'), responde de forma acorde como en una conversación en curso (por ejemplo: '¡De nada!', '¡Con mucho gusto!', 'Un placer ayudarte. Si necesitas algo más, dime'). NUNCA reinicies la conversación diciendo 'buenas en qué te puedo ayudar' cuando el usuario solo te está dando las gracias o despidiéndose.\n"
        "2. PREGUNTAS SOBRE TU IDENTIDAD O MODELO:\n"
        f"   - Si el usuario pregunta qué modelo eres, quién eres o cómo estás hecho, responde cordialmente indicando que tu nombre es Venk y que estás impulsado por el modelo {chat_model} ejecutado localmente con Ollama y RAG.\n"
        "3. PREGUNTAS TÉCNICAS O CONSULTAS DE CONTENIDO:\n"
        "   - Cuando haya información en el 'TEXTO DE DOCUMENTOS', responde con base en esa información con claridad y precisión citando los datos del archivo subido.\n"
        "   - Si te hacen una pregunta técnica o específica que no está en el 'TEXTO DE DOCUMENTOS' ni en el historial de la conversación, responde de manera cortés indicando que dicha información no figura en los documentos proporcionados.\n"
        "4. TONO Y FORMATO:\n"
        "   - Responde siempre en español, de manera concisa, fluida, natural y humana."
    )

    # Construir historial de mensajes recientes (últimos 8 mensajes previos para contexto)
    historial_mensajes = []
    if sesion:
        # Obtener los últimos mensajes excluyendo el que se acaba de crear si ya existe
        mensajes_recientes = list(sesion.mensajes.order_by("-creado_en")[:8])
        mensajes_recientes.reverse()
        for m in mensajes_recientes:
            rol = "assistant" if m.autor.username == NOMBRE_USUARIO_BOT else "user"
            historial_mensajes.append({"role": rol, "content": m.cuerpo})

    # Si el último mensaje del historial ya es la pregunta actual, no duplicarlo
    if not historial_mensajes or historial_mensajes[-1].get("content") != pregunta:
        if contexto_docs:
            contenido_pregunta = f"TEXTO DE DOCUMENTOS:\n\"\"\"{contexto_docs}\"\"\"\n\nPREGUNTA DEL USUARIO:\n{pregunta}"
        else:
            contenido_pregunta = pregunta
        historial_mensajes.append({"role": "user", "content": contenido_pregunta})
    else:
        # Reemplazar el último mensaje para incluir el contexto de documentos si existe
        if contexto_docs:
            historial_mensajes[-1]["content"] = f"TEXTO DE DOCUMENTOS:\n\"\"\"{contexto_docs}\"\"\"\n\nPREGUNTA DEL USUARIO:\n{pregunta}"

    messages = [{"role": "system", "content": system_prompt}] + historial_mensajes

    client = ollama.Client(host=django_settings.OLLAMA_BASE_URL)
    response = client.chat(
        model=chat_model,
        messages=messages,
        options={
            "num_predict": 350,
            "temperature": 0.3,
        },
    )
    text = response.get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("Respuesta vacía de Ollama")
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
