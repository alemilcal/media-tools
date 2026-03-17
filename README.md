# VideoTools

Colección de herramientas en Python para la optimización de archivos de video y conversión avanzada de subtítulos.

## Scripts Incluidos

### 1. Subtitle Converter (`subtitle-converter.py`)
Un conversor de subtítulos de formato ASS a SRT avanzado enfocado en la limpieza y legibilidad del texto.
- **Limpieza de etiquetas:** Elimina etiquetas de formato ASS complejas (posicionamiento, colores, efectos de dibujo).
- **Balanceo de texto:** Ajusta automáticamente la longitud de las líneas para una mejor lectura (límite de 40 caracteres por línea).
- **Tratamiento de estilos:** Soporta la detección de cursivas tanto por etiquetas (`\i1`) como por definición de estilo en el archivo.
- **Unificación y Clipping:** Une automáticamente subtítulos contiguos con el mismo texto y resuelve solapamientos temporales.

### 2. Video Optimizer (`video-optimizer.py`)
Herramienta integral basada en FFmpeg para procesar archivos de video y gestionar pistas de audio/subtítulos de forma automatizada.
- **Optimización de Video:** Transcodificación eficiente para mejorar la compatibilidad y reducir el tamaño de los archivos.
- **Gestión de Pistas:** Permite extraer, convertir y filtrar pistas de audio y subtítulos de forma selectiva.
- **Modo Cartoon:** Incluye configuraciones de codificación optimizadas específicamente para contenido de animación.
- **Quemado de Subtítulos:** Opción para integrar (hardcode) subtítulos directamente en la imagen del video.

## Requisitos
- Python 3.8+
- NumPy
- FFmpeg (requerido para el procesamiento de video, debe estar disponible en el PATH del sistema)
