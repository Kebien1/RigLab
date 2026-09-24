[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url1]

<!-- PROJECT LOGO -->
<br />
<div align="center">
    <h2 align="center">Django Local RAG Chat</h2>
    <h5 align="center">Université Paris Cité - M2 - Digital Science (AIRE)</h5>

  <p align="center">
    Dilan Croos
    <br />
    <a href="https://github.com/dilancroos/django_chat"><strong>Explorar la documentación »</strong></a>
    <br />
    <br />
    ·
    <a href="https://github.com/dilancroos/django_chat/issues">Reportar un error</a>
    ·
    <a href="https://github.com/dilancroos/django_chat/issues">Solicitar una función</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Tabla de contenidos</summary>
  <ol>
    <li><a href="#acerca-del-proyecto">Acerca del proyecto</a></li>
    <li><a href="#primeros-pasos">Primeros pasos</a></li>
    <ul>
        <li><a href="#requisitos">Requisitos</a></li>
        <li><a href="#instalación">Instalación</a></li>
        <li><a href="#base-de-conocimiento">Base de conocimiento</a></li>
        <li><a href="#ejecución">Ejecución</a></li>
        <li><a href="#configuración">Configuración</a></li>
        <li><a href="#pruebas">Pruebas</a></li>
    </ul>
    <li><a href="#contacto">Contacto</a></li>
    <li><a href="#agradecimientos">Agradecimientos</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## Acerca del proyecto

Una aplicación de chat local en Django que responde preguntas a partir de los
archivos que colocas en una carpeta local de base de conocimiento. Los archivos
fuente se convierten primero a Markdown con MarkItDown de Microsoft, y luego la
aplicación indexa únicamente los archivos Markdown generados. La aplicación usa
Ollama para los modelos locales de chat y de embeddings, por lo que no necesita
una API de pago de LLM después de la instalación.

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

<!-- GETTING STARTED -->

## Primeros pasos

Para tener una copia local funcionando, sigue estos sencillos pasos.

## Requisitos

- Python 3.11 o superior
- Ollama ejecutándose localmente

Instala Ollama desde <https://ollama.com/download> y luego descarga los modelos por defecto:

```sh
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Instalación

Clona el repositorio

```sh
 git clone git@github.com:dilancroos/django_chat.git
 cd django_chat
```

Crea y activa un entorno virtual:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Instala las dependencias:

```sh
pip install -r requirements.txt
```

Crea un archivo de entorno:

```sh
cp envtemp .env
```

Ejecuta las migraciones de la base de datos y crea un usuario:

```sh
python manage.py migrate
python manage.py makemigrations
```

de nuevo

```sh
python manage.py migrate
```

```sh
python manage.py createsuperuser
```

## Base de conocimiento

Coloca los archivos fuente en `knowledge_base/`. La aplicación los convierte a
Markdown en `knowledge_markdown/` y luego indexa únicamente esos archivos `.md`
generados.

Los tipos de archivo fuente compatibles en la primera versión son:

- PDF
- Word
- PowerPoint
- XLS y XLSX
- CSV
- Markdown
- TXT
- HTML
- JSON y XML
- ZIP

La aplicación revisa esta carpeta cuando envías un mensaje de chat. Si los
archivos cambiaron, los convierte a Markdown y luego reconstruye el índice local
en `rag_storage/` antes de responder.

Puedes reconstruir el índice manualmente:

```sh
python manage.py rebuild_rag_index
```

Para omitir la reconstrucción cuando el manifiesto almacenado está actualizado:

```sh
python manage.py rebuild_rag_index --skip-unchanged
```

## Ejecución

Inicia Ollama y luego inicia Django:

```sh
python manage.py runserver
```

Abre <http://127.0.0.1:8000>, inicia sesión y haz preguntas sobre los archivos
en `knowledge_base/`. No edites `knowledge_markdown/` manualmente; se genera a
partir de la carpeta fuente.

La aplicación crea automáticamente el grupo de chat `ai-chat` y el usuario bot
`botty` la primera vez que se envía un mensaje de chat.

## Configuración

Estos ajustes se pueden cambiar en `.env`:

```sh
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
RAG_SOURCE_DIR=knowledge_base
RAG_MARKDOWN_DIR=knowledge_markdown
RAG_STORAGE_DIR=rag_storage
```

## Pruebas

```sh
python manage.py test
```

<!-- CONTACT -->

## Contacto

Dilan Croos - mail@dilancroos.com

Enlace del proyecto: [https://github.com/dilancroos/django_chat](https://github.com/dilancroos/django_chat)

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Agradecimientos

- Plantilla de chat en Django de [Andreas Jud](https://www.youtube.com/@ajudmeister)

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/dilancroos/django_chat.svg?style=for-the-badge
[contributors-url]: https://github.com/dilancroos/django_chat/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/dilancroos/django_chat.svg?style=for-the-badge
[forks-url]: https://github.com/dilancroos/django_chat/network/members
[stars-shield]: https://img.shields.io/github/stars/dilancroos/django_chat.svg?style=for-the-badge
[stars-url]: https://github.com/dilancroos/django_chat/stargazers
[issues-shield]: https://img.shields.io/github/issues/dilancroos/django_chat.svg?style=for-the-badge
[issues-url]: https://github.com/dilancroos/django_chat/issues
[license-shield]: https://img.shields.io/github/license/dilancroos/django_chat.svg?style=for-the-badge
[license-url]: https://github.com/dilancroos/django_chat/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url1]: https://linkedin.com/in/antondilancrooswarnakulasuriya
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com
