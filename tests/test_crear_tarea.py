from datetime import datetime, timedelta
import pytest


def test_crear_tarea_correctamente(gestor, docente, curso, repositorio):
    tarea = gestor.crear_tarea(
        docente=docente,
        curso_id=curso.id_curso,
        titulo="Patrón Observer",
        descripcion="Implementar notificaciones automáticas.",
        fecha_entrega=datetime.now() + timedelta(days=3),
        ponderacion=20,
        recursos=["observer.pdf"],
    )

    assert tarea.id_tarea == 1
    assert tarea.titulo == "Patrón Observer"
    assert tarea.ponderacion == 20
    assert repositorio.obtener_tarea(tarea.id_tarea) is tarea


def test_crear_tarea_sin_titulo_falla(gestor, docente, curso):
    with pytest.raises(ValueError, match="título"):
        gestor.crear_tarea(
            docente=docente,
            curso_id=curso.id_curso,
            titulo="   ",
            descripcion="Descripción válida",
            fecha_entrega=datetime.now() + timedelta(days=2),
            ponderacion=15,
        )


def test_crear_tarea_con_fecha_pasada_falla(gestor, docente, curso):
    with pytest.raises(ValueError, match="fecha de entrega"):
        gestor.crear_tarea(
            docente=docente,
            curso_id=curso.id_curso,
            titulo="Tarea vencida",
            descripcion="No debe crearse",
            fecha_entrega=datetime.now() - timedelta(days=1),
            ponderacion=15,
        )


def test_crear_tarea_con_ponderacion_invalida_falla(gestor, docente, curso):
    with pytest.raises(ValueError, match="ponderación"):
        gestor.crear_tarea(
            docente=docente,
            curso_id=curso.id_curso,
            titulo="Tarea inválida",
            descripcion="Ponderación incorrecta",
            fecha_entrega=datetime.now() + timedelta(days=1),
            ponderacion=120,
        )


def test_docente_no_asignado_no_puede_crear_tarea(
    gestor,
    otro_docente,
    curso,
):
    with pytest.raises(PermissionError, match="asignado"):
        gestor.crear_tarea(
            docente=otro_docente,
            curso_id=curso.id_curso,
            titulo="Tarea no autorizada",
            descripcion="No debe guardarse",
            fecha_entrega=datetime.now() + timedelta(days=1),
            ponderacion=10,
        )


def test_crear_tarea_genera_notificacion(
    gestor,
    docente,
    curso,
    notificador,
):
    gestor.crear_tarea(
        docente=docente,
        curso_id=curso.id_curso,
        titulo="Nueva actividad",
        descripcion="Actividad de prueba",
        fecha_entrega=datetime.now() + timedelta(days=2),
        ponderacion=10,
    )

    assert len(notificador.notificaciones) == 1
    assert notificador.notificaciones[0].asunto == "Nueva tarea académica"
    assert "Nueva actividad" in notificador.notificaciones[0].mensaje
