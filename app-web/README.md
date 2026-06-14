# App Web - LabFull

## Interfaz de Login Cyberpunk

### Características
- Diseño moderno estilo cyberpunk con efectos de neón
- Animaciones CSS3 (grid, glow, slide-in)
- Panel post-login con estado del último pipeline de Jenkins
- Fechas en formato `dd-mm-YY hh:mm:ss`
- Resumen por stage y estado del mensaje de OpenClaw
- Inventario clicable de containers con detalle de publicación
- Formulario de registro conectado al backend
- Efectos de scanlines retro

### Cómo ejecutar
```bash
# Usando Python HTTP server
python -m http.server 8080

# O servirlo detrás del reverse proxy que expone /api hacia FastAPI
```

### Acceder a la aplicación
- Local: http://localhost:8080
- Pública: https://labfull.maurocastro.cl
