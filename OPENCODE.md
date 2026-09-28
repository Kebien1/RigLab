# Evidencia de Interacciones con OpenCode

Para el desarrollo de este proyecto, el proceso de codificación no se hizo en un solo paso, sino a través de una serie de iteraciones complejas asistidas por el agente OpenCode. El desarrollo se guio principalmente utilizando el archivo `zDOCUMENTACION_MD/REQUERIMIENTOS_PROYECTO.md` como contexto base (Mega-Prompt), el cual se fue desglosando en diferentes fases para abordar la complejidad arquitectónica del sistema, la integración del LLM y la corrección de errores.

A continuación, se documenta el registro detallado de las sesiones clave de interacción con la inteligencia artificial.

---

## Sesión 1: Arquitectura de Base de Datos y Modelos

**Contexto:** Necesitábamos traducir los requerimientos del negocio (RF-01 a RF-05) a modelos reales de Django con validaciones estrictas.
**Prompt utilizado:**
> "OpenCode, toma como base el documento de `REQUERIMIENTOS_PROYECTO.md`. Empieza únicamente generando el archivo `models.py`. Necesito que el modelo `Producto` tenga validaciones a nivel de base de datos para que el precio y el stock nunca sean negativos usando `MinValueValidator`. Implementa un campo booleano `activo` para manejar la eliminación lógica (Soft Delete) y evitar perder el historial. Añade un método `__str__` para que en el admin se vea bien."

**Respuesta obtenida e Impacto:**
OpenCode redactó el modelo importando `django.core.validators`. Nos explicó cómo la eliminación lógica evitaría errores futuros en posibles tablas de facturación o reportes históricos. Al ejecutar `makemigrations` y `migrate`, la base de datos se estructuró a la perfección en el primer intento.

---

## Sesión 2: Generación del CRUD y Vistas Genéricas

**Contexto:** El sistema requería implementar todas las operaciones de inventario de forma segura.
**Prompt utilizado:**
> "Ahora necesitamos las vistas. En lugar de vistas basadas en funciones, genera Vistas Basadas en Clases (CBV) para `ListView`, `DetailView`, `CreateView`, `UpdateView` y una vista personalizada para el `DeleteView` que en lugar de borrar el registro de la DB, simplemente cambie `producto.activo = False`. Además, genera el archivo `urls.py` correspondiente y un archivo `forms.py` que aplique clases de Bootstrap ('form-control') a todos los inputs."

**Respuesta obtenida e Impacto:**
OpenCode entregó un código muy limpio para las vistas. Sobrescribió el método `delete()` en el `DeleteView` para lograr la eliminación lógica de manera nativa sin que el usuario note la diferencia. También inyectó clases CSS de Bootstrap dinámicamente en el método `__init__` del formulario en `forms.py`, ahorrándonos horas de diseño manual en HTML.

---

## Sesión 3: Integración Crítica con Ollama Local

**Contexto:** El requerimiento más exigente era conectar Django con un LLM local y prevenir alucinaciones (RF-07 y RF-09).
**Prompt utilizado:**
> "Pasa a la integración de inteligencia artificial. Crea un módulo `services/ollama_service.py`. Usa la librería `requests` para comunicarte con la API en `http://localhost:11434/api/generate` usando el modelo `qwen2.5:1.5b`. 
> 
> Es vital que el LLM no invente datos. Redacta un 'System Prompt' que inyecte un JSON con todos los productos activos de la base de datos. Dile explícitamente: 'Eres un asistente de inventario. Solo puedes responder basándote en los datos adjuntos. Si te preguntan algo que no está en el inventario, debes responder: No tengo información sobre eso'. Implementa el bloque `try/except` para el Timeout y ConnectionError."

**Respuesta obtenida e Impacto:**
Esta interacción fue crucial. OpenCode nos proporcionó un prompt sistémico impecable. En las primeras pruebas, el modelo a veces inventaba procesadores que no existían; sin embargo, al aplicar las restricciones estrictas generadas por OpenCode en el System Prompt, logramos limitar la respuesta del modelo `qwen2.5` estrictamente a los productos del JSON inyectado. El manejo de errores también evitó que la aplicación crasheara cuando Ollama no estaba ejecutándose.

---

## Sesión 4: Depuración (Debugging) del Formulario de Chat

**Contexto:** Al probar el chat integrado, la página se recargaba y se perdía el contexto visual del historial.
**Prompt utilizado:**
> "El servicio de Ollama funciona, pero en la vista del chat en Django, cuando el usuario envía el formulario, la página hace un refresh completo. ¿Cómo puedo hacer que la consulta se envíe por AJAX usando Javascript puro o fetch, y que el mensaje aparezca dinámicamente en el DOM con un indicador de 'Escribiendo...' mientras Ollama responde?"

**Respuesta obtenida e Impacto:**
OpenCode generó un script en Vanilla JS con la función `fetch()`. Añadió el token CSRF (`X-CSRFToken`) en las cabeceras para evitar bloqueos de seguridad de Django. Además, proporcionó el código HTML/CSS para un pequeño spinner de carga. Esto transformó por completo la experiencia de usuario, haciéndola sentir como una aplicación web moderna e interactiva.

---

## Sesión 5: Refactorización y Patrones de Diseño (Calidad de Código)

**Contexto:** Para cumplir con el nivel "Estratégico" de la rúbrica, debíamos aplicar patrones de diseño formales.
**Prompt utilizado:**
> "Para terminar, el profesor pide aplicar dos patrones de diseño. Actualmente, en la vista de reportes, tengo muchos 'if/elif' para calcular los distintos escenarios (productos más caros, stock crítico, total). Ayúdame a refactorizar esto aplicando el patrón **Strategy** creando clases separadas. Además, usa las Signals de Django para aplicar el patrón **Observer**: cada vez que el stock de un producto baje del límite permitido (`stock_minimo`), imprime una alerta de terminal advirtiendo que se necesita reabastecer."

**Respuesta obtenida e Impacto:**
OpenCode reestructuró la carpeta creando un módulo `strategies.py` donde cada reporte (ReporteCaro, ReporteStockCritico) implementa una interfaz común `ReportStrategy`. Luego, configuró el archivo `signals.py` atado al evento `post_save` del modelo Producto. Al guardar un producto, si `cantidad <= stock_minimo`, el patrón Observer notifica automáticamente por consola. Esto demostró un uso avanzado de patrones estructurales y de comportamiento, elevando drásticamente la calidad técnica de la entrega.

---

## Sesión 6: Pruebas Unitarias Exhaustivas

**Contexto:** Asegurar la robustez del aplicativo previniendo regresiones.
**Prompt utilizado:**
> "Genera pruebas unitarias en `tests.py` usando `django.test.TestCase`. Necesito probar:
> 1. Que no se pueda guardar un Producto con precio negativo.
> 2. Que el reporte de Stock Crítico (Strategy) funcione correctamente con datos falsos.
> 3. Que el servicio de Ollama arroje nuestra excepción personalizada cuando recibe un error 500 simulado (usa `unittest.mock.patch`)."

**Respuesta obtenida e Impacto:**
El agente construyó tests sólidos. Nos introdujo al uso de `@patch` de la librería `mock` de Python para simular que Ollama fallaba sin tener que apagar el servidor de verdad. Ejecutamos `python manage.py test` y conseguimos validar la lógica de negocio sin depender de servicios externos, logrando un código completamente resiliente.

---

## Sesión 7: Corrección de Observaciones de Evaluación (Chat Visual)

**Contexto:** En la evaluación de la actividad, el ingeniero observó que solo se mostraba una *"respuesta_directa_ollama pegada; sin la vista completa ni formulario"*. 
**Análisis:** Al revisar el repositorio, descubrimos que la vista completa del chat (con formulario, historial, subida de documentos y carga interactiva mediante HTMX) **sí estaba desarrollada y funcional** en la ruta `/admin-chat/`. El problema real no era de código backend ni falta de vistas, sino de **Experiencia de Usuario (UX)**: el evaluador no encontró cómo llegar a esa ruta porque el enlace en el menú de navegación (Header) pasaba desapercibido y, en la versión móvil, apuntaba erróneamente al catálogo.
**Acción y Resultado:**
1. Se refactorizó el menú superior (`templates/includes/header.html`).
2. Se cambió el enlace estándar por un botón destacado de color índigo sólido con el texto **"Chat IA"** e icono de mensaje.
3. Se corrigió el menú hamburguesa (móvil) para que apunte directamente a `{% url 'admin-chat' %}`.

Con este cambio, el formulario de chat y su interfaz gráfica completa (Requisito 2.3) quedan total y fácilmente visibles para la evaluación.
