# UeesTask — Fase 2

Implementación funcional mínima de los tres casos de uso definidos en la Fase 1:

- CU-04 Crear tarea
- CU-07 Entregar tarea
- CU-08 Calificar entrega

## Tecnologías

- Python 3.10 o superior
- Programación orientada a objetos
- Arquitectura por capas
- Patrón Observer
- Persistencia temporal en memoria

## Instalación

```bash
python -m pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Pruebas

```bash
python -m pytest
```

## Estructura

```text
UeesTask_Fase2/
├── app/
│   ├── controllers/
│   ├── models/
│   ├── notifications/
│   ├── repositories/
│   ├── services/
│   └── utils/
├── database/
├── docs/
├── tests/
├── main.py
├── requirements.txt
└── pytest.ini
```

## Nota académica

Esta versión corresponde al código base de la Fase 2. Incluye algunos malos olores controlados que serán documentados en el informe de diagnóstico y corregidos en la siguiente fase de refactorización.
