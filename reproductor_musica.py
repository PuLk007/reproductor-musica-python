"""Reproductor de música con Tkinter y pygame.

Proyecto integrador - Etapa 2
Asignatura: Algoritmos y Complejidad Computacional

La aplicación permite cargar una carpeta, mostrar su lista de archivos de
audio, reproducir, pausar, detener, cambiar de canción, adelantar o retroceder
10 segundos y modificar el volumen. También muestra el título, el tiempo
transcurrido y la duración total.
"""

from __future__ import annotations

import os
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from mutagen import File as MutagenFile
from pygame import mixer


SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")


def format_seconds(seconds: float) -> str:
    """Convierte segundos a una cadena MM:SS."""
    safe_seconds = max(0, int(seconds))
    minutes, remaining_seconds = divmod(safe_seconds, 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Limita un valor al intervalo cerrado [minimum, maximum]."""
    return max(minimum, min(value, maximum))


def discover_audio_files(folder: str) -> list[str]:
    """Devuelve los archivos de audio de una carpeta, ordenados por nombre."""
    if not folder or not os.path.isdir(folder):
        return []
    return sorted(
        filename
        for filename in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, filename))
        and filename.lower().endswith(SUPPORTED_EXTENSIONS)
    )


def get_audio_duration(path: str) -> float:
    """Obtiene la duración mediante metadatos; devuelve 0 si no está disponible."""
    try:
        metadata = MutagenFile(path)
        if metadata is not None and metadata.info is not None:
            return float(metadata.info.length)
    except Exception:
        pass
    return 0.0


class MusicPlayer:
    """Interfaz y lógica principal del reproductor."""

    BG = "#0f172a"
    PANEL = "#18243a"
    PANEL_LIGHT = "#23324d"
    ACCENT = "#2dd4bf"
    ACCENT_DARK = "#0f766e"
    TEXT = "#f8fafc"
    MUTED = "#94a3b8"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Reproductor de música - Proyecto integrador")
        self.root.geometry("980x620")
        self.root.minsize(860, 540)
        self.root.configure(bg=self.BG)

        try:
            mixer.init()
        except Exception as exc:
            messagebox.showerror(
                "No se pudo iniciar el audio",
                "Verifica que el equipo tenga una salida de audio disponible.\n\n"
                f"Detalle: {exc}",
            )
            raise

        self.folder = ""
        self.playlist: list[str] = []
        self.current_index = -1
        self.duration = 0.0
        self.position_base = 0.0
        self.started_at = 0.0
        self.is_paused = False
        self.is_stopped = True
        self.user_is_seeking = False

        self.title_var = tk.StringVar(value="Ninguna canción seleccionada")
        self.status_var = tk.StringVar(value="Selecciona una carpeta para comenzar")
        self.time_var = tk.StringVar(value="00:00 / 00:00")
        self.folder_var = tk.StringVar(value="Carpeta: sin seleccionar")
        self.volume_var = tk.DoubleVar(value=70)
        self.progress_var = tk.DoubleVar(value=0)

        self._build_ui()
        mixer.music.set_volume(0.70)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(400, self._update_playback_ui)

    def _build_ui(self) -> None:
        """Construye todos los controles visuales de la aplicación."""
        header = tk.Frame(self.root, bg=self.BG, padx=28, pady=22)
        header.pack(fill="x")

        tk.Label(
            header,
            text="REPRODUCTOR DE MÚSICA",
            bg=self.BG,
            fg=self.ACCENT,
            font=("Arial", 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Proyecto integrador · Etapa 2",
            bg=self.BG,
            fg=self.TEXT,
            font=("Arial", 26, "bold"),
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            header,
            textvariable=self.folder_var,
            bg=self.BG,
            fg=self.MUTED,
            font=("Arial", 10),
        ).pack(anchor="w", pady=(7, 0))

        body = tk.Frame(self.root, bg=self.BG, padx=28, pady=0)
        body.pack(fill="both", expand=True)

        playlist_panel = tk.Frame(body, bg=self.PANEL, padx=18, pady=18)
        playlist_panel.pack(side="left", fill="both", expand=True, padx=(0, 14))

        playlist_top = tk.Frame(playlist_panel, bg=self.PANEL)
        playlist_top.pack(fill="x", pady=(0, 12))
        tk.Label(
            playlist_top,
            text="Lista de reproducción",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 14, "bold"),
        ).pack(side="left")
        self.load_button = self._button(
            playlist_top, "Cargar carpeta", self.load_folder, primary=True
        )
        self.load_button.pack(side="right")

        list_container = tk.Frame(playlist_panel, bg=self.PANEL)
        list_container.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.song_list = tk.Listbox(
            list_container,
            bg=self.PANEL_LIGHT,
            fg=self.TEXT,
            selectbackground=self.ACCENT_DARK,
            selectforeground=self.TEXT,
            activestyle="none",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 11),
            yscrollcommand=scrollbar.set,
        )
        self.song_list.pack(side="left", fill="both", expand=True)
        self.song_list.bind("<<ListboxSelect>>", self.select_song)
        self.song_list.bind("<Double-Button-1>", lambda _event: self.play())
        scrollbar.config(command=self.song_list.yview)

        control_panel = tk.Frame(body, bg=self.PANEL, width=370, padx=22, pady=22)
        control_panel.pack(side="right", fill="y")
        control_panel.pack_propagate(False)

        tk.Label(
            control_panel,
            text="REPRODUCIENDO AHORA",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            control_panel,
            textvariable=self.title_var,
            wraplength=320,
            justify="left",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 17, "bold"),
        ).pack(anchor="w", pady=(7, 4))
        tk.Label(
            control_panel,
            textvariable=self.status_var,
            bg=self.PANEL,
            fg=self.ACCENT,
            font=("Arial", 10),
        ).pack(anchor="w", pady=(0, 20))

        self.progress = tk.Scale(
            control_panel,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.progress_var,
            command=self._preview_seek,
            bg=self.PANEL,
            fg=self.MUTED,
            troughcolor=self.PANEL_LIGHT,
            activebackground=self.ACCENT,
            highlightthickness=0,
            borderwidth=0,
            showvalue=False,
            length=320,
        )
        self.progress.pack(fill="x")
        self.progress.bind("<ButtonPress-1>", self._begin_seek)
        self.progress.bind("<ButtonRelease-1>", self._commit_seek)
        tk.Label(
            control_panel,
            textvariable=self.time_var,
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Arial", 10),
        ).pack(anchor="e", pady=(0, 18))

        transport = tk.Frame(control_panel, bg=self.PANEL)
        transport.pack(fill="x")
        for text, command in (
            ("⏮", self.previous_song),
            ("−10", lambda: self.seek_relative(-10)),
            ("▶", self.play),
            ("⏸", self.pause),
            ("+10", lambda: self.seek_relative(10)),
            ("⏭", self.next_song),
        ):
            button = self._button(transport, text, command, primary=(text == "▶"), width=4)
            button.pack(side="left", expand=True, padx=2)

        stop_button = self._button(control_panel, "■  Detener", self.stop)
        stop_button.pack(fill="x", pady=(12, 22))

        volume_row = tk.Frame(control_panel, bg=self.PANEL)
        volume_row.pack(fill="x")
        tk.Label(
            volume_row,
            text="Volumen",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 10, "bold"),
        ).pack(side="left")
        self.volume_label = tk.Label(
            volume_row,
            text="70%",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Arial", 10),
        )
        self.volume_label.pack(side="right")

        tk.Scale(
            control_panel,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.volume_var,
            command=self.set_volume,
            bg=self.PANEL,
            fg=self.MUTED,
            troughcolor=self.PANEL_LIGHT,
            activebackground=self.ACCENT,
            highlightthickness=0,
            borderwidth=0,
            showvalue=False,
            length=320,
        ).pack(fill="x")

        tk.Label(
            control_panel,
            text="Formatos admitidos: MP3, WAV, OGG y FLAC",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Arial", 9),
        ).pack(anchor="w", pady=(20, 0))

    def _button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        *,
        primary: bool = False,
        width: int | None = None,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=self.ACCENT if primary else self.PANEL_LIGHT,
            fg=self.BG if primary else self.TEXT,
            activebackground="#5eead4" if primary else "#334155",
            activeforeground=self.BG if primary else self.TEXT,
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            cursor="hand2",
            font=("Arial", 10, "bold"),
        )

    def load_folder(self, folder: str | None = None) -> None:
        """Carga y presenta las canciones encontradas en una carpeta."""
        selected_folder = folder or filedialog.askdirectory(title="Selecciona una carpeta con música")
        if not selected_folder:
            return

        songs = discover_audio_files(selected_folder)
        if not songs:
            messagebox.showwarning(
                "Carpeta sin canciones",
                "No se encontraron archivos MP3, WAV, OGG o FLAC.",
            )
            return

        self.stop()
        self.folder = selected_folder
        self.playlist = songs
        self.song_list.delete(0, tk.END)
        for number, filename in enumerate(self.playlist, start=1):
            self.song_list.insert(tk.END, f"{number:02d}.  {Path(filename).stem}")

        self.current_index = 0
        self.song_list.selection_set(0)
        self.song_list.activate(0)
        self.folder_var.set(f"Carpeta: {self.folder}")
        self._set_current_song(load_audio=False)
        self.status_var.set(f"{len(self.playlist)} canciones disponibles")

    def select_song(self, _event=None) -> None:
        """Actualiza la canción seleccionada en la lista."""
        selection = self.song_list.curselection()
        if not selection:
            return
        new_index = int(selection[0])
        if new_index != self.current_index:
            self.stop()
            self.current_index = new_index
            self._set_current_song(load_audio=False)

    def _current_path(self) -> str:
        if self.current_index < 0 or self.current_index >= len(self.playlist):
            return ""
        return os.path.join(self.folder, self.playlist[self.current_index])

    def _set_current_song(self, *, load_audio: bool) -> bool:
        path = self._current_path()
        if not path:
            return False
        if load_audio:
            try:
                mixer.music.load(path)
            except Exception as exc:
                messagebox.showerror("No se pudo cargar la canción", str(exc))
                return False
        self.duration = get_audio_duration(path)
        self.title_var.set(Path(path).stem)
        self.time_var.set(f"00:00 / {format_seconds(self.duration)}")
        self.progress.configure(to=max(self.duration, 1))
        self.progress_var.set(0)
        return True

    def play(self) -> None:
        """Inicia o reanuda la reproducción."""
        if not self.playlist:
            messagebox.showinfo("Lista vacía", "Primero carga una carpeta con canciones.")
            return

        if self.is_paused:
            mixer.music.unpause()
            self.started_at = time.monotonic() - self.position_base
            self.is_paused = False
            self.is_stopped = False
            self.status_var.set("Reproduciendo")
            return

        if not self._set_current_song(load_audio=True):
            return
        mixer.music.play()
        self.position_base = 0.0
        self.started_at = time.monotonic()
        self.is_paused = False
        self.is_stopped = False
        self.status_var.set("Reproduciendo")

    def pause(self) -> None:
        """Pausa la canción actual conservando su posición."""
        if self.is_stopped or self.is_paused:
            return
        self.position_base = self.current_position()
        mixer.music.pause()
        self.is_paused = True
        self.status_var.set("En pausa")

    def stop(self) -> None:
        """Detiene la reproducción y regresa al inicio."""
        mixer.music.stop()
        self.is_paused = False
        self.is_stopped = True
        self.position_base = 0.0
        self.progress_var.set(0)
        self.time_var.set(f"00:00 / {format_seconds(self.duration)}")
        if self.playlist:
            self.status_var.set("Detenida")

    def _select_index(self, index: int, *, autoplay: bool = True) -> None:
        if not self.playlist:
            return
        self.stop()
        self.current_index = index % len(self.playlist)
        self.song_list.selection_clear(0, tk.END)
        self.song_list.selection_set(self.current_index)
        self.song_list.activate(self.current_index)
        self.song_list.see(self.current_index)
        self._set_current_song(load_audio=False)
        if autoplay:
            self.play()

    def next_song(self) -> None:
        """Selecciona y reproduce la siguiente canción."""
        self._select_index(self.current_index + 1)

    def previous_song(self) -> None:
        """Selecciona y reproduce la canción anterior."""
        self._select_index(self.current_index - 1)

    def current_position(self) -> float:
        """Calcula la posición actual sin exceder la duración."""
        if self.is_stopped:
            return 0.0
        if self.is_paused:
            return self.position_base
        elapsed = max(0.0, time.monotonic() - self.started_at)
        return clamp(elapsed, 0.0, self.duration if self.duration > 0 else elapsed)

    def seek_relative(self, seconds: float) -> None:
        """Adelanta o retrocede la canción una cantidad de segundos."""
        if self.is_stopped or not self._current_path():
            return
        self.seek_to(self.current_position() + seconds)

    def seek_to(self, seconds: float) -> None:
        """Reinicia la reproducción desde la posición indicada."""
        if not self._current_path():
            return
        target = clamp(seconds, 0.0, self.duration if self.duration > 0 else seconds)
        try:
            mixer.music.play(start=target)
        except Exception:
            # Algunos formatos no permiten posicionamiento exacto. En ese caso
            # se conserva la aplicación estable y se informa al usuario.
            self.status_var.set("El formato no admite salto preciso")
            return
        self.position_base = target
        self.started_at = time.monotonic() - target
        self.is_stopped = False
        if self.is_paused:
            mixer.music.pause()
        self.progress_var.set(target)
        self.time_var.set(f"{format_seconds(target)} / {format_seconds(self.duration)}")

    def _begin_seek(self, _event=None) -> None:
        self.user_is_seeking = True

    def _preview_seek(self, value: str) -> None:
        if self.user_is_seeking:
            self.time_var.set(
                f"{format_seconds(float(value))} / {format_seconds(self.duration)}"
            )

    def _commit_seek(self, _event=None) -> None:
        if not self.user_is_seeking:
            return
        self.user_is_seeking = False
        if not self.is_stopped:
            self.seek_to(float(self.progress_var.get()))

    def set_volume(self, value: str) -> None:
        """Ajusta el volumen entre 0 y 100 por ciento."""
        percent = clamp(float(value), 0.0, 100.0)
        mixer.music.set_volume(percent / 100.0)
        self.volume_label.configure(text=f"{int(percent)}%")

    def _update_playback_ui(self) -> None:
        """Actualiza periódicamente tiempo, duración y fin de pista."""
        if not self.is_stopped and not self.user_is_seeking:
            position = self.current_position()
            self.progress_var.set(position)
            self.time_var.set(
                f"{format_seconds(position)} / {format_seconds(self.duration)}"
            )
            if (
                self.duration > 0
                and position >= self.duration - 0.25
                and not self.is_paused
            ):
                self.next_song()
        self.root.after(400, self._update_playback_ui)

    def close(self) -> None:
        """Libera el mezclador y cierra la ventana."""
        mixer.music.stop()
        mixer.quit()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    MusicPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
