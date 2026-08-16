"""Pruebas unitarias de las funciones que no requieren interfaz gráfica."""

from pathlib import Path

from reproductor_musica import clamp, discover_audio_files, format_seconds


def test_format_seconds() -> None:
    assert format_seconds(0) == "00:00"
    assert format_seconds(65.9) == "01:05"
    assert format_seconds(-3) == "00:00"


def test_clamp() -> None:
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_discover_audio_files(tmp_path: Path) -> None:
    for name in ("b.wav", "a.MP3", "nota.txt", "c.ogg"):
        (tmp_path / name).write_bytes(b"")
    assert discover_audio_files(str(tmp_path)) == ["a.MP3", "b.wav", "c.ogg"]
