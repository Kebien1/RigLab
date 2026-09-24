# 📋 CAMBIOS — Registro de Modificaciones del Proyecto

> **Proyecto:** Django Chat con RAG Local  
> **Fecha de actualización:** 20 de septiembre de 2026  
> **Base original:** [dilancroos/django_chat](https://github.com/dilancroos/django_chat) (commit `bf57413`)

---

## 📑 Tabla de Contenidos

- [1. Traducciones (Inglés → Español)](#1-traducciones-inglés--español)
- [2. Ajustes de Prompt del Bot](#2-ajustes-de-prompt-del-bot)
- [3. Funcionalidades Añadidas](#3-funcionalidades-añadidas)
- [4. Archivos Modificados](#4-archivos-modificados)
- [5. Archivos Nuevos](#5-archivos-nuevos)
- [6. Archivos Eliminados](#6-archivos-eliminados)
- [7. Cambios en Modelos de Datos](#7-cambios-en-modelos-de-datos)
- [8. Cambios en URLs](#8-cambios-en-urls)
- [9. Comandos de Instalación](#9-comandos-de-instalación)

---

## 1. Traducciones (Inglés → Español)

Se tradujo toda la interfaz de usuario y la lógica interna del proyecto del inglés al español.

### 1.1 Modelos (`a_rtchat/models.py`)

| Original (inglés)   | Traducido (español)   |
|----------------------|-----------------------|
| `ChatGroup`          | `SesionChat`          |
| `GroupMessage`       | `MensajeChat`         |
| `group_name`         | `titulo`              |
| `body`               | `cuerpo`              |
| `author`             | `autor`               |
| `created`            | `creado_en`           |
| `group`              | `sesion`              |
| `chat_messages`      | `mensajes`            |

### 1.2 Formularios (`a_rtchat/forms.py`)

| Original               | Traducido                  |
|-------------------------|----------------------------|
| `ChatmessageCreateForm` | `FormularioCrearMensaje`   |
| `fields = ['body']`     | `fields = ['cuerpo']`      |
| `'Type a message...'`   | `'Escribe un mensaje...'`  |

### 1.3 Vistas (`a_rtchat/views.py`)

| Original                | Traducido                    |
|-------------------------|------------------------------|
| `BOT_USERNAME`          | `NOMBRE_USUARIO_BOT`         |
| `chat_view`             | `vista_chat`                 |
| `_get_chat_group()`     | *(eliminada)*                |
| `_get_bot_user()`       | `_obtener_usuario_bot()`     |
| `_create_bot_message()` | `_crear_mensaje_bot()`       |
| `_answer_question()`    | `_responder_pregunta()`      |
| Nombre del bot: `botty` | Nombre del bot: `venk`       |

### 1.4 URLs (`a_rtchat/urls.py`)

| Original             | Traducido               |
|----------------------|--------------------------|
| `name='home'`        | `name='inicio'`          |
| *(no existía)*       | `name='nuevo-chat'`      |
| *(no existía)*       | `name='chat'`            |
| *(no existía)*       | `name='generar-respuesta'`|
| *(no existía)*       | `name='editar-chat'`     |
| *(no existía)*       | `name='eliminar-chat'`   |
| *(no existía)*       | `name='toggle-favorito'` |

### 1.5 Plantillas HTML

| Elemento                       | Original         | Traducido         |
|--------------------------------|------------------|-------------------|
| Nombre del sitio (header)      | `Chatbot`        | `Venk`            |
| Link de navegación             | `Home`           | `Inicio`          |
| Menú de perfil                 | `My Profile`     | `Mi perfil`       |
| Menú editar perfil             | `Edit Profile`   | `Editar Perfil`   |
| Menú configuración             | `Settings`       | `Ajustes`         |
| Menú cerrar sesión             | `Log Out`        | `cerrar sesion`   |
| Botón de enviar                | `Send`           | `Enviar`          |
| Fuentes en respuestas          | `Sources:`       | `Fuentes:`        |

### 1.6 Configuración (`a_core/settings.py`)

| Configuración    | Original   | Traducido  |
|------------------|------------|------------|
| `LANGUAGE_CODE`  | `'en-us'`  | `'es'`     |

### 1.7 README.md

El `README.md` fue traducido completamente del inglés al español, incluyendo:
- Tabla de contenidos
- Sección "About the Project" → "Acerca del proyecto"
- Sección "Getting Started" → "Primeros pasos"
- Todos los encabezados y descripciones

### 1.8 Mensajes de error

| Original                                                   | Traducido                                                                |
|------------------------------------------------------------|--------------------------------------------------------------------------|
| `I could not query the local knowledge base...`            | `No pude consultar la base de conocimientos local...`                    |
| `Check that Ollama is running and the configured models...`| `Verifica que Ollama esté en ejecución y los modelos configurados...`    |

---

## 2. Ajustes de Prompt del Bot

### 2.1 System Prompt completo

Se añadió un **nuevo system prompt en español** para las respuestas directas de Ollama (`_respuesta_directa_ollama()`):

```
Eres un asistente virtual amigable para un proyecto de Chat con RAG Local en Django.
Puedes responder cordialmente a saludos (ej: hola, buenos días) y preguntas básicas
sobre quién eres. Sin embargo, para cualquier pregunta técnica o específica, DEBES
basarte EXCLUSIVAMENTE en la información del TEXTO proporcionado abajo.
Si te hacen una pregunta técnica o de conocimiento que NO está en el TEXTO,
debes indicar amablemente que no tienes esa información en tus documentos y que
solo puedes responder preguntas basadas en el material proporcionado.
```

### 2.2 Formato del mensaje de usuario

```
TEXTO:
"""<fragmentos relevantes del knowledge_base>"""

PREGUNTA: <pregunta del usuario>

Responde en español siguiendo estrictamente tus instrucciones.
```

### 2.3 Parámetros de generación

| Parámetro       | Valor  |
|-----------------|--------|
| `num_predict`   | `300`  |
| `temperature`   | `0.1`  |

### 2.4 Modelo cambiado

| Original         | Actual           |
|------------------|------------------|
| `llama3.2`       | `qwen2.5:1.5b`  |

---

## 3. Funcionalidades Añadidas

### 3.1 Sistema de Sesiones de Chat (Multi-chat)

Se reemplazó el modelo de chat único (`ChatGroup`) por un sistema de **sesiones individuales por usuario**:

- Cada usuario tiene sus propias sesiones de chat
- Cada sesión usa un **UUID** como identificador primario (`id_sesion`)
- Las sesiones pertenecen a un usuario (`propietario`)
- Auto-naming: el título se actualiza automáticamente con los primeros 30 caracteres del primer mensaje

### 3.2 Sidebar lateral con lista de chats

- Panel lateral (1/3 del ancho) con lista de todas las sesiones
- Buscador de chats (`q` query parameter)
- Botón "Nuevo Chat" para crear sesiones
- Indicador visual de la sesión activa
- Sesiones fijadas (favoritas) aparecen primero

### 3.3 Menú contextual por sesión

Cada sesión en el sidebar tiene un **menú desplegable** (tres puntos) con las opciones:
- **Fijar / Desfijar** — marca la sesión como favorita
- **Renombrar** — permite cambiar el título de la sesión
- **Eliminar** — elimina la sesión y todos sus mensajes

### 3.4 Respuesta directa con Ollama

Se añadió la función `_respuesta_directa_ollama()` que:
1. Busca fragmentos relevantes del `knowledge_base` usando búsqueda por palabras clave
2. Llama directamente a Ollama con contexto + system prompt
3. Funciona como método **primario** de respuesta (RAG original queda como fallback)

### 3.5 Búsqueda de fragmentos relevantes

Nueva función `_buscar_fragmentos_relevantes()`:
- Lee todos los archivos `.md` del directorio `knowledge_markdown/`
- Divide el texto en párrafos (mínimo 20 caracteres)
- Filtra stop words en español (40+ palabras comunes)
- Puntúa párrafos según coincidencias de palabras clave
- Normaliza acentos con `_quitar_acentos()` para mejores coincidencias
- Retorna los fragmentos más relevantes hasta un máximo de 3000 caracteres

### 3.6 Indicador de "pensando" (thinking)

Cuando el usuario envía un mensaje:
- Se muestra una animación de **tres puntos rebotando** (bounce) mientras la IA genera la respuesta
- Se usa `hx-get` con `hx-trigger="load"` para solicitar la respuesta del bot asincrónicamente
- El indicador se reemplaza automáticamente con la respuesta real

### 3.7 Bloqueo del botón "Enviar"

- El botón "Enviar" se **deshabilita** mientras la IA procesa la respuesta
- Cambia de color verde a gris con cursor `not-allowed`
- Se reactiva automáticamente cuando la respuesta aparece (evento `htmx:afterSettle`)

### 3.8 Animaciones de entrada

- Los mensajes nuevos aparecen con una animación **fade-in-up** (0.6s ease)

### 3.9 Título automático de sesiones

- Cuando se envía el primer mensaje o el título es "Nuevo Chat", el título se actualiza automáticamente con los primeros 30 caracteres del mensaje + "..."

---

## 4. Archivos Modificados

| # | Archivo | Descripción del cambio |
|---|---------|------------------------|
| 1 | [`a_core/settings.py`](a_core/settings.py) | `LANGUAGE_CODE` cambiado a `'es'`, `ALLOWED_HOSTS` actualizado |
| 2 | [`a_rtchat/models.py`](a_rtchat/models.py) | Modelos renombrados y reestructurados (`SesionChat`, `MensajeChat`), campo UUID, campo `favorito` |
| 3 | [`a_rtchat/views.py`](a_rtchat/views.py) | Reescritura completa: vistas traducidas, 5 nuevas vistas, respuesta directa Ollama, búsqueda de fragmentos |
| 4 | [`a_rtchat/forms.py`](a_rtchat/forms.py) | Formulario renombrado a `FormularioCrearMensaje`, campos traducidos |
| 5 | [`a_rtchat/admin.py`](a_rtchat/admin.py) | Registros actualizados a los nuevos modelos |
| 6 | [`a_rtchat/urls.py`](a_rtchat/urls.py) | 7 rutas nuevas reemplazando la ruta única original |
| 7 | [`a_rtchat/rag.py`](a_rtchat/rag.py) | Modelo por defecto cambiado de `llama3.2` a `qwen2.5:1.5b` |
| 8 | [`a_rtchat/templates/a_rtchat/chat.html`](a_rtchat/templates/a_rtchat/chat.html) | Reescritura completa: layout con sidebar, lista de sesiones, menú contextual, JS interactivo |
| 9 | [`a_rtchat/migrations/0001_initial.py`](a_rtchat/migrations/0001_initial.py) | Migración reescrita para los nuevos modelos |
| 10 | [`templates/includes/header.html`](templates/includes/header.html) | Nombre del sitio y menú de navegación traducidos |
| 11 | [`a_users/templates/a_users/profile_edit.html`](a_users/templates/a_users/profile_edit.html) | URL `'home'` cambiada a `'inicio'` |
| 12 | [`README.md`](README.md) | Traducción completa al español |

---

## 5. Archivos Nuevos

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | [`a_rtchat/templates/a_rtchat/mensaje_chat.html`](a_rtchat/templates/a_rtchat/mensaje_chat.html) | Plantilla de un mensaje individual (reemplaza `chat_message.html`) |
| 2 | [`a_rtchat/templates/a_rtchat/partials/mensajes_chat_p.html`](a_rtchat/templates/a_rtchat/partials/mensajes_chat_p.html) | Partial HTMX que muestra el mensaje del usuario + indicador de "pensando" del bot |
| 3 | [`a_rtchat/templates/a_rtchat/partials/mensaje_bot_p.html`](a_rtchat/templates/a_rtchat/partials/mensaje_bot_p.html) | Partial HTMX que muestra la respuesta del bot (reemplaza el indicador de pensando) |

---

## 6. Archivos Eliminados

| # | Archivo | Motivo |
|---|---------|--------|
| 1 | `a_rtchat/templates/a_rtchat/chat_message.html` | Reemplazado por `mensaje_chat.html` |
| 2 | `a_rtchat/templates/a_rtchat/partials/chat_messages_p.html` | Reemplazado por `mensajes_chat_p.html` |
| 3 | `a_rtchat/migrations/0002_alter_groupmessage_body.py` | Ya no es necesaria (migración consolidada en `0001`) |
| 4 | `knowledge_markdown/.gitkeep` | Archivo de marcador eliminado |

---

## 7. Cambios en Modelos de Datos

### Modelo `SesionChat` (antes `ChatGroup`)

```python
class SesionChat(models.Model):
    id_sesion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # NUEVO
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)                      # NUEVO
    titulo = models.CharField(max_length=128, default="Nuevo Chat")                      # antes: group_name
    fecha_creacion = models.DateTimeField(auto_now_add=True)                              # NUEVO
    favorito = models.BooleanField(default=False)                                         # NUEVO

    class Meta:
        ordering = ['-favorito', '-fecha_creacion']
```

### Modelo `MensajeChat` (antes `GroupMessage`)

```python
class MensajeChat(models.Model):
    sesion = models.ForeignKey(SesionChat, related_name='mensajes', on_delete=models.CASCADE)  # antes: group
    autor = models.ForeignKey(User, on_delete=models.CASCADE)                                   # antes: author
    cuerpo = models.TextField()                                                                  # antes: body (CharField max_length=300)
    creado_en = models.DateTimeField(auto_now_add=True)                                          # antes: created

    class Meta:
        ordering = ['-creado_en']
```

> **Nota importante:** El campo `cuerpo` cambió de `CharField(max_length=300)` a `TextField()`, permitiendo mensajes de longitud ilimitada.

---

## 8. Cambios en URLs

### Antes (1 ruta):
```python
urlpatterns = [
    path('', chat_view, name='home'),
]
```

### Después (7 rutas):
```python
urlpatterns = [
    path('', vista_chat, name='inicio'),
    path('chat/nuevo/', nueva_sesion_chat, name='nuevo-chat'),
    path('chat/<uuid:id_sesion>/', vista_chat, name='chat'),
    path('chat/<uuid:id_sesion>/generar/<int:mensaje_id>/', generar_respuesta, name='generar-respuesta'),
    path('chat/<uuid:id_sesion>/editar/', editar_chat, name='editar-chat'),
    path('chat/<uuid:id_sesion>/eliminar/', eliminar_chat, name='eliminar-chat'),
    path('chat/<uuid:id_sesion>/favorito/', toggle_favorito, name='toggle-favorito'),
]
```

---

## 9. Comandos de Instalación

### Requisitos previos

- **Python** 3.10+
- **Ollama** instalado y en ejecución (`http://localhost:11434`)
- Modelos de Ollama descargados:
  ```bash
  ollama pull qwen2.5:1.5b
  ollama pull nomic-embed-text
  ```

### Instalación paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/dilancroos/django_chat.git
cd django_chat

# 2. Crear y activar entorno virtual
python -m venv env
source env/bin/activate        # Linux/Mac
# env\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Copiar el archivo de ejemplo y ajustar según sea necesario
cp envtemp .env
# Editar .env con tus valores:
#   DJANGO_SECRET_KEY=<tu-clave-secreta>
#   OLLAMA_BASE_URL=http://localhost:11434
#   OLLAMA_CHAT_MODEL=qwen2.5:1.5b
#   OLLAMA_EMBED_MODEL=nomic-embed-text
#   RAG_SOURCE_DIR=knowledge_base
#   RAG_MARKDOWN_DIR=knowledge_markdown
#   RAG_STORAGE_DIR=rag_storage

# 5. Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# 6. Crear superusuario (opcional)
python manage.py createsuperuser

# 7. Agregar documentos a la base de conocimiento
# Colocar archivos (.pdf, .docx, .txt, .md, etc.) en la carpeta:
#   knowledge_base/

# 8. Iniciar el servidor
python manage.py runserver 0.0.0.0:8000
```

### Dependencias principales (`requirements.txt`)

```
Django>=5.2,<5.3
django-allauth>=65.0,<66.0
django-cleanup>=9.0,<10.0
django-htmx>=1.20,<2.0

llama-index-core>=0.14,<0.15
llama-index-embeddings-ollama>=0.8,<0.9
llama-index-llms-ollama>=0.7,<0.8
llama-index-readers-file>=0.5,<0.6
markitdown[pdf,docx,pptx,xlsx,xls]>=0.1,<0.2
ollama>=0.5,<1.0

python-dotenv>=1.0,<2.0
```

---