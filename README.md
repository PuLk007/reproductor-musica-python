# Reproductor de música - Proyecto integrador Etapa 2

Aplicación de escritorio desarrollada en Python con `tkinter`, `pygame.mixer`,
`os` y `mutagen`. Permite cargar una carpeta de música, presentar la lista de
canciones, reproducir, pausar, detener, cambiar de pista, adelantar o
retroceder 10 segundos, controlar el volumen y visualizar el tiempo.

## Requisitos

- Python 3.10 a 3.13. Para Windows se recomienda Python 3.13 de 64 bits.
- Una salida de audio habilitada.
- Archivos MP3, WAV, OGG o FLAC sin protección DRM.

## Instalación

```bash
python -m venv .venv
```

En Windows:

```bash
py -V:3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python reproductor_musica.py
```

En macOS o Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python reproductor_musica.py
```

## Uso

1. Presiona **Cargar carpeta**.
2. Elige una carpeta que contenga archivos de audio compatibles.
3. Selecciona una canción en la lista.
4. Usa los controles de reproducción, pausa, detención, pista anterior,
   siguiente, salto de diez segundos y volumen.

## Archivos para GitHub

El repositorio incluye `reproductor_musica.py`, `requirements.txt`,
`requirements-dev.txt`, este `README.md`, `test_reproductor.py` y `.gitignore`.
No subas canciones comerciales al repositorio.

## Pruebas

Instala la dependencia de desarrollo y ejecuta las tres pruebas automatizadas:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest test_reproductor.py -v
```

El resultado esperado es `3 passed`.

## Consideraciones

El posicionamiento exacto con los botones -10 y +10 depende de las capacidades
del formato y del decodificador disponible en Pygame. Los formatos comprimidos
que permiten iniciar la reproducción desde una marca de tiempo ofrecen el
mejor resultado.
