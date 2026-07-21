from datetime import datetime, timedelta
import pytest


def test_entregar_tarea_correctamente(
    gestor,
    estudiante,
    tarea_valida,
    repositorio,
):
    entrega = gestor.entregar_tarea(
        estudiante=estudiante,
        tarea_id=tarea_valida.id_tarea,
        archivo="actividad.pdf",
        comentario="Trabajo terminado.",
    )

    assert entrega.estado.value == "ENVIADA"
    assert entrega.archivo == "actividad.pdf"
    assert repositorio.obtener_entrega(entrega.id_entrega) is entrega


def test_entregar_tarea_sin_archivo_falla(
    gestor,
    estudiante,
    tarea_valida,
):
    with pytest.raises(ValueError, match="archivo"):
        gestor.entregar_tarea(
            estudiante=estudiante,
            tarea_id=tarea_valida.id_tarea,
            archivo="",
            comentario="Sin archivo.",
        )


def test_entregar_tarea_vencida_falla(
    gestor,
    estudiante,
    tarea_valida,
):
    tarea_valida.fecha_entrega = datetime.now() - timedelta(minutes=1)

    with pytest.raises(ValueError, match="vencida"):
        gestor.entregar_tarea(
            estudiante=estudiante,
            tarea_id=tarea_valida.id_tarea,
            archivo="entrega_tardia.pdf",
            comentario="Entrega fuera de fecha.",
        )


def test_estudiante_no_matriculado_no_puede_entregar(
    gestor,
    otro_estudiante,
    tarea_valida,
):
    with pytest.raises(PermissionError, match="matriculado"):
        gestor.entregar_tarea(
            estudiante=otro_estudiante,
            tarea_id=tarea_valida.id_tarea,
            archivo="actividad.pdf",
            comentario="Intento no autorizado.",
        )


def test_no_permite_entrega_duplicada(
    gestor,
    estudiante,
    tarea_valida,
):
    gestor.entregar_tarea(
        estudiante=estudiante,
        tarea_id=tarea_valida.id_tarea,
        archivo="primera.zip",
        comentario="Primera entrega.",
    )

    with pytest.raises(ValueError, match="ya registró"):
        gestor.entregar_tarea(
            estudiante=estudiante,
            tarea_id=tarea_valida.id_tarea,
            archivo="segunda.zip",
            comentario="Segunda entrega.",
        )


def test_entregar_tarea_genera_notificacion(
    gestor,
    estudiante,
    tarea_valida,
    notificador,
):
    cantidad_inicial = len(notificador.notificaciones)

    gestor.entregar_tarea(
        estudiante=estudiante,
        tarea_id=tarea_valida.id_tarea,
        archivo="actividad.pdf",
        comentario="Entrega correcta.",
    )

    assert len(notificador.notificaciones) == cantidad_inicial + 1
    assert notificador.notificaciones[-1].asunto == "Entrega registrada"
    assert notificador.notificaciones[-1].destinatario == estudiante.email
