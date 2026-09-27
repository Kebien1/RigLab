<div align="center">
    <h2 align="center">RigLab (RAG Local Chat)</h2>
</div>

##  Acerca de este repositorio

Este repositorio contiene el proyecto **RigLab**, una aplicación de chat local desarrollado en Django que aplica técnicas de RAG (Retrieval-Augmented Generation). 

El propósito es responder preguntas basándose en documentos locales, utilizando modelos de Inteligencia Artificial locales a través de **Ollama**. Recientemente se ha incorporado la capacidad de procesar diversos formatos mediante `markitdown` y realizar scraping web para extender la base de conocimientos.

---

##  Cómo ejecutar el proyecto

Sigue estos pasos para levantar el entorno de manera rápida y sencilla.

### 1. Requisitos previos

- **Python 3.11** o superior.
- **Ollama** instalado y corriendo en tu computadora. Puedes descargarlo en [ollama.com](https://ollama.com/download).

Una vez instalado Ollama, debes descargar los modelos que usa la aplicación ejecutando estos comandos en tu terminal:
```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### 2. Preparar el entorno

Clona este repositorio e ingresa a la carpeta del proyecto:
```bash
git clone https://github.com/Kebien1/RigLab.git
cd RigLab
```

Crea y activa un entorno virtual (recomendado):
```bash
python3 -m venv env
source env/bin/activate
```
*(Nota: Si usas Windows, el comando de activación es `env\Scripts\activate`)*

Instala los paquetes necesarios:
```bash
pip install -r requirements.txt
```

Crea tu archivo de variables de entorno copiando la plantilla:
```bash
cp .env.example .env
```

### 3. Base de datos

Genera la base de datos local y crea tu cuenta de administrador:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Inicio el Local

Inicia el servidor local de Django:
```bash
python manage.py runserver
```

Entra a tu navegador web y visita: [http://127.0.0.1:8000](http://127.0.0.1:8000). 
Para alimentar la inteligencia de la aplicación, puedes colocar tus documentos o generar información a partir del módulo de scraping. Los documentos son procesados y almacenados internamente (en formatos markdown) para ser utilizados por el modelo RAG.

---

##  Créditos y Agradecimientos

Este proyecto es únicamente una modificación para fines académicos. Todo el crédito arquitectónico y conceptual pertenece a los autores originales:

- **Proyecto Original:** [Django Local RAG Chat](https://github.com/dilancroos/django_chat) creado por **Dilan Croos**.
- **Institución Académica:** Université Paris Cité - M2 - Digital Science (AIRE).
- **Diseño del Chat:** Plantilla original de chat en Django por [Andreas Jud](https://www.youtube.com/@ajudmeister).
