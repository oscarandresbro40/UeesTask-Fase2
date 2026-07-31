from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(
    title="UeesTask",
    description="Sistema web para la gestión académica de tareas.",
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse)
def inicio() -> str:
    return """
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>UeesTask</title>
        <style>
          body {
            align-items: center;
            background: #f4f6fb;
            color: #172033;
            display: flex;
            font-family: Arial, sans-serif;
            justify-content: center;
            margin: 0;
            min-height: 100vh;
          }
          main {
            background: white;
            border-radius: 18px;
            box-shadow: 0 18px 50px rgba(23, 32, 51, .12);
            max-width: 620px;
            padding: 48px;
            text-align: center;
          }
          h1 { color: #45277d; font-size: 42px; margin: 0 0 12px; }
          p { color: #5e6677; font-size: 18px; line-height: 1.6; }
          .estado {
            background: #e9f8ef;
            border-radius: 999px;
            color: #18723b;
            display: inline-block;
            font-weight: bold;
            margin-top: 18px;
            padding: 10px 18px;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>UeesTask</h1>
          <p>Sistema web de gestión de tareas académicas.</p>
          <p>La base de FastAPI está instalada y lista para comenzar el desarrollo.</p>
          <span class="estado">Servidor funcionando correctamente</span>
        </main>
      </body>
    </html>
    """


@app.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok", "aplicacion": "UeesTask"}
