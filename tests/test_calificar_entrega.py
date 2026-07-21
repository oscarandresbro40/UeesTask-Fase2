import pytest


def test_calificar_entrega_correctamente(
    gestor,
    docente,
    entrega_valida,
):
    resultado = gestor.calificar_entrega(
        docente=docente,
        entrega_id=entrega_valida.id_entrega,
        nota=95,
        retroalimentacion="Excelente trabajo.",
    )

    assert resultado.calificacion == 95
    assert resultado.estado.value == "CALIFICADA"
    assert resultado.retroalimentacion == "Excelente trabajo."


def test_calificar_con_nota_fuera_de_rango_falla(
    gestor,
    docente,
    entrega_valida,
):
    with pytest.raises(ValueError, match="entre 0 y 100"):
        gestor.calificar_entrega(
            docente=docente,
            entrega_id=entrega_valida.id_entrega,
            nota=105,
            retroalimentacion="Nota inválida.",
        )


def test_docente_no_autorizado_no_puede_calificar(
    gestor,
    otro_docente,
    entrega_valida,
):
    with pytest.raises(PermissionError, match="no puede calificar"):
        gestor.calificar_entrega(
            docente=otro_docente,
            entrega_id=entrega_valida.id_entrega,
            nota=80,
            retroalimentacion="Evaluación no autorizada.",
        )


def test_no_permite_calificar_dos_veces(
    gestor,
    docente,
    entrega_valida,
):
    gestor.calificar_entrega(
        docente=docente,
        entrega_id=entrega_valida.id_entrega,
        nota=90,
        retroalimentacion="Primera calificación.",
    )

    with pytest.raises(ValueError, match="ya fue calificada"):
        gestor.calificar_entrega(
            docente=docente,
            entrega_id=entrega_valida.id_entrega,
            nota=95,
            retroalimentacion="Segunda calificación.",
        )


def test_calificar_entrega_genera_notificacion(
    gestor,
    docente,
    entrega_valida,
    notificador,
    estudiante,
):
    cantidad_inicial = len(notificador.notificaciones)

    gestor.calificar_entrega(
        docente=docente,
        entrega_id=entrega_valida.id_entrega,
        nota=88,
        retroalimentacion="Buen trabajo.",
    )

    assert len(notificador.notificaciones) == cantidad_inicial + 1
    notificacion = notificador.notificaciones[-1]
    assert notificacion.asunto == "Actividad calificada"
    assert notificacion.destinatario == estudiante.email
    assert "88/100" in notificacion.mensaje
