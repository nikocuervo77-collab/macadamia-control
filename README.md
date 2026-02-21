# Macadamia – Warehouse Control

Sistema de gestión de bodegas avanzado.

## Estado del Proyecto: Paso 1 - Base de Datos Inicial

Se ha configurado la base de datos inicial utilizando **SQLite** para facilitar el desarrollo local y la portabilidad.

### Modelos de Datos Implementados:

1. **Warehouses**: 
   - `id`: Autoincremental.
   - `name`: Nombre de la bodega.
   - `city`: Ciudad de ubicación.
   - `active`: Estado (Activo/Inactivo).

2. **Users & Roles**:
   - Autenticación mediante `email` y `password_hash`.
   - Roles definidos: `ADMIN` y `WAREHOUSE_USER`.
   - Relación con `Warehouses` para asignación de bodega (nullable para Admins).

3. **Products**:
   - `barcode`: Clave Primaria (Única y obligatoria).
   - `name`: Nombre del producto.
   - `description`: Descripción detallada.
   - `photo_url`: URL o ruta de la foto.

### Archivos Generados:
- `schema.sql`: Definiciones de tablas SQL.
- `init_db.py`: Script de inicialización y seeding.
- `macadamia.db`: Archivo de base de datos SQLite.

### Próximos Pasos (Paso 4):
- Implementación de reportes avanzados (PDF/Excel).
- Integración real con API Backend.
- Gestión de fotos y almacenamiento en la nube.

---

## 🚀 Despliegue y Ejecución

El sistema está listo para ser puesto en marcha. Sigue estos pasos para iniciar el servidor:

### 1. Requisitos de Entorno
Asegúrate de tener instaladas las dependencias necesarias:
```bash
pip install fastapi uvicorn reportlab openpyxl pandas
```

### 2. Iniciar el Servidor
Ejecuta el archivo principal para levantar la API y la interfaz:
```bash
python3 main.py
```
El sistema estará disponible en: `http://localhost:8000`

### 3. Funcionalidades de Producción
*   **API REST**: Documentación automática disponible en `http://localhost:8000/docs`.
*   **Reportes**: Los archivos PDF y Excel se generan automáticamente en la carpeta `reports/`.
*   **Trazabilidad**: Cada movimiento queda sellado con fecha, hora y usuario responsable.

---

## Paso 3: Interfaz de Usuario & Quick Movement (Implementado)

Se ha diseñado y prototipado la experiencia de usuario con un enfoque **Mobile-first** y estética premium.
... (continuación del contenido previo)

### Características de la UI:
1. **Quick Movement Mode**:
   - Una "Single Page" optimizada para terminales móviles y scanners.
   - **Escaneo**: Integración conceptual para disparo de cámara/scanner de código de barras.
   - **Selector de Movimiento**: Botones grandes y ergonómicos para Entrada, Salida y Transferencia.
   - **Teclado Numérico Custom**: Optimizado para ingreso rápido de cantidades sin depender del teclado nativo del sistema que a veces oculta elementos.
2. **Dashboards Diferenciados**:
   - **Admin View**: Métricas globales (Stock total, estados de todas las bodegas).
   - **Warehouse User View**: Enfocado exclusivamente en la bodega asignada al usuario, mostrando capacidad actual y estado de operaciones locales.
3. **Diseño Premium**:
   - Paleta de colores inspirada en la nuez de Macadamia (cremas, dorados y tonos oscuros).
   - Uso de **Glassmorphism** y tipografía moderna (`Outfit`).

### Archivos Nuevos:
- `index.html`: Prototipo funcional de la interfaz de usuario.
