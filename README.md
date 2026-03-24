# StudySprint AI (MVP para estudiar ingeniería en 2 días)

App en **Streamlit** con IA para estudiar de forma ultra-rápida antes de un examen.

## Qué incluye

- **Plan de 48 horas** con bloques priorizados.
- **Chat multi-agente**:
  - 🧭 **Planificador** (organiza bloques y estrategia)
  - 🧠 **Tutor** (explica temas difíciles de forma corta)
  - 📝 **Examinador** (simulacros y preguntas tipo examen)
- **Módulos ampliables por chat** (pomodoro, flashcards, quiz).
- **Persistencia de progreso** local (`data/progress.json`): guardar/cargar tareas, chat y módulos.
- Modo con OpenAI (si hay key) o modo local por reglas (sin key).

## Requisitos

- Python 3.10+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno (opcional)

Crea `.env`:

```bash
OPENAI_API_KEY=tu_api_key
OPENAI_MODEL=gpt-4o-mini
```

Sin API key, la app sigue funcionando con respuestas locales.

## Ejecutar

```bash
streamlit run app.py
```

## Uso rápido

1. Configura materias, temas y fecha del examen.
2. Genera el plan de 2 días.
3. Elige agente en la barra lateral según objetivo.
4. Usa el chat para pedir:
   - `organiza hoy en 3 bloques`
   - `explica transformada de Laplace fácil`
   - `simulacro de física nivel alto`
   - `añade pomodoro 50/10`
5. Guarda y carga tu progreso cuando quieras.

## Nota

Este MVP es ideal para arrancar rápido. Se puede extender con base de datos, exportación de reportes y analíticas de desempeño.
