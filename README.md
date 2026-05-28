# Sistema de Punto de Venta — Consultorio Naturista

Aplicación de escritorio desarrollada en Python para gestionar el 
inventario y ventas de un consultorio naturista. Conecta en tiempo 
real con Google Sheets como base de datos en la nube y genera 
tickets de venta en PDF.

> Este proyecto fue desarrollado para uso real en un negocio local.

## Funcionalidades

**Módulo de Inventario**
- Registrar nuevos productos con cantidad inicial
- Agregar stock existente con un clic
- Editar nombre o cantidad de cualquier producto
- Eliminar productos con opción de **deshacer** la última acción
- Filtro A-Z y buscador en tiempo real
- Alertas visuales automáticas para productos con poco stock (≤ 4 unidades)
- Exportar reporte PDF del inventario (completo o solo poco stock)

**Módulo de Ventas**
- Carrito de compras con control de cantidad por producto
- Validación automática contra el stock disponible
- Descuento automático del inventario al confirmar venta
- Generación de ticket PDF con nombre del paciente, productos y fecha
- Dos categorías de productos: Pastillas y Varios

## Tecnologías

- Python 3
- CustomTkinter — interfaz gráfica moderna
- gspread + oauth2client — conexión con Google Sheets API
- ReportLab — generación de PDFs
- Pillow — manejo de imágenes y logo

## Arquitectura

La app usa Google Sheets como base de datos compartida en la nube, 
lo que permite que el inventario se actualice en tiempo real desde 
cualquier dispositivo con acceso a la hoja de cálculo. 
