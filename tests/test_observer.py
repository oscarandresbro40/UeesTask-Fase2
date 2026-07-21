def test_tarea_tiene_observador_registrado(
    gestor,
    docente,
    curso,
    notificador,
):
    from datetime import datetime, timedelta

    tarea = gestor.crear_tarea(
        docente=docente,
        curso_id=curso.id_curso,
        titulo="Observer",
        descripcion="Validar patrón Observer.",
        fecha_entrega=datetime.now() + timedelta(days=1),
        ponderacion=10,
    )

    assert notificador in tarea.observadores


def test_servicio_observer_recibe_evento_personalizado(notificador):
    notificador.actualizar(
        "EVENTO_PERSONALIZADO",
        {
            "destinatario": "usuario@uees.edu.ec",
            "detalle": "Evento de prueba",
        },
    )

    assert len(notificador.notificaciones) == 1
    assert notificador.notificaciones[0].destinatario == "usuario@uees.edu.ec"
