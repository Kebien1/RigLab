# Requerimiento base del Entregable Final Programación 4

## Sistema de aplicación web de inventario de componentes de PC con CRUD e inteligencia artificial local mediante Ollama

### 1. Descripción general

Desarrollar una aplicación web utilizando Django que permita administrar un inventario de componentes de computadora mediante operaciones CRUD y realizar consultas sobre la información registrada utilizando un modelo de inteligencia artificial local ejecutado con Ollama. 

El sistema permite consultar los componentes mediante reportes predefinidos y mediante un chat integrado, enviando a Ollama los datos del inventario en tiempo real. Además, la Inteligencia Artificial tiene la capacidad de ejecutar operaciones CRUD directamente sobre la base de datos a través de instrucciones en el chat.

## 2. Objetivo general

Implementar una aplicación Django que integre:

- Registro de componentes de PC.
- Consulta, actualización y eliminación lógica de componentes.
- Control de cantidades en stock.
- Menú de reportes basado en los datos del inventario.
- Chat con inteligencia artificial local (Ollama).
- Capacidad de la IA para realizar operaciones CRUD interpretando las peticiones del usuario.

## 3. Alcance del sistema

El sistema está compuesto por módulos principales integrados:

### Módulo de inventario (Productos)
Permitirá administrar los datos de los componentes mediante operaciones CRUD (Crear, Leer, Actualizar, Eliminar).

### Módulo de inteligencia artificial
Permitirá consultar y gestionar la información del inventario mediante:
- Reportes predefinidos.
- Preguntas en lenguaje natural escritas en el chat.
- Funciones de llamada (Function Calling) donde la IA interactúa directamente con el inventario para modificar, agregar o eliminar stock.

---

# 4. Requerimientos funcionales

## RF-01. Registro de componentes
El sistema permite registrar componentes con los siguientes datos:
- Código (SKU)
- Nombre del componente
- Descripción técnica
- Categoría (Procesadores, Placas Base, Memoria RAM, etc.)
- Precio
- Cantidad existente en stock
- Stock mínimo permitido
- Estado del producto (Nuevo, Reacondicionado, Usado)
- Fecha de registro

El código (SKU) debe ser único. Se validan los precios y cantidades para no permitir valores negativos.

## RF-02. Consulta de componentes
El sistema muestra una lista de los componentes registrados y permite buscar por:
- Código (SKU).
- Nombre.
- Categoría.

## RF-03. Actualización de componentes
Se permite modificar la información de un componente, validando que:
- El componente exista.
- El SKU no colisione.
- Precios y cantidades no sean negativos.

## RF-04. Eliminación de componentes
Se implementa la eliminación lógica (dando de baja el producto mediante un campo "activo"). Esto conserva el historial en la base de datos.

## RF-05. Control de existencia
El sistema permite:
- Aumentar o disminuir la cantidad disponible de un producto.
- Consultar componentes bajo stock o agotados.
- Evitar que el stock sea negativo.

## RF-06. Reportes predefinidos
El sistema incluye reportes para:
- Componente más caro y más barato.
- Productos con existencias menores o iguales al stock mínimo.
- Resumen general y valor total del inventario.

## RF-07. Chat con inteligencia artificial
El usuario puede hacer preguntas sobre los componentes o pedir que se realicen acciones. Ejemplos:
- "¿Qué procesadores tenemos en stock?"
- "Registra un nuevo teclado inalámbrico con SKU T001 por 50 dólares con 10 unidades."
- "¿Cuál es el componente más caro?"

## RF-08. Integración con Ollama y Function Calling
La aplicación se comunica con un modelo local (ej. qwen2.5:1.5b) enviando el contexto del inventario y las instrucciones (system prompt). Si el usuario pide modificar datos, la IA genera un JSON estructurado que el backend de Django intercepta y ejecuta en la base de datos.

## RF-09. Restricción de respuestas de la IA
La IA está restringida para responder únicamente con información del inventario de hardware y no inventar datos. Si se sale del contexto, debe notificarlo.

## RF-10. Historial de consultas
El sistema guarda las sesiones de chat, los mensajes enviados y las respuestas generadas (además de los documentos subidos).

---

# 5. Modelo de datos

## Entidad Producto (Componente)

| Campo | Tipo | Descripción |
|---|---|---|
| id | Entero | Identificador automático |
| sku | Texto | Código único del producto |
| nombre | Texto | Nombre del componente |
| descripcion | Texto | Descripción técnica |
| categoria | Texto | Categoría (Opciones predefinidas) |
| precio | Decimal | Precio unitario |
| cantidad | Entero | Cantidad en stock |
| stock_minimo | Entero | Nivel de alerta |
| estado | Texto | Nuevo, Usado, etc. |
| activo | Booleano | Eliminación lógica |
| fecha_registro | Fecha y hora | Timestamp |

## Entidad SesionChat y MensajeChat
Administran el historial del chat interactivo entre el usuario y el bot.

---

# 6. Requerimientos no funcionales

- Aplicación desarrollada en Django.
- Base de datos SQLite.
- Motor de IA local Ollama, conectado vía API REST desde el backend de Django.
- Interfaz web amigable y reactiva (HTMX/Bootstrap/Tailwind según corresponda).
- Validación robusta en formularios (Backend y Frontend).

---

# 7. Conclusión de la Evaluación

**Tu proyecto CUMPLE SATISFACTORIAMENTE con todos los requerimientos solicitados en el ejemplo.** 
De hecho, **supera las expectativas** al integrar capacidades de *Function Calling*, lo cual le permite a la Inteligencia Artificial no solo leer la base de datos, sino modificarla de forma autónoma a petición del usuario. Las validaciones de stock, la eliminación lógica y los filtros de reportes están perfectamente implementados en las vistas y el modelo.
