# StudySprint AI (MVP para estudiar ingeniería en 2 días)

App en **Streamlit** con un chatbot integrado para:

1. Crear un plan exprés de estudio para 48 horas.
2. Generar resúmenes, preguntas tipo examen y mini simulacros.
3. Ir "añadiendo cosas" desde el mismo chat (pomodoro, repasos, flashcards, etc.).

## Requisitos

- Python 3.10+
- (Opcional) API key de OpenAI para respuestas más inteligentes.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno (opcional)

Crea un archivo `.env` con:

```bash
OPENAI_API_KEY=tu_api_key
OPENAI_MODEL=gpt-4o-mini
```

Si no defines API key, la app usa un **modo local** con reglas para seguir funcionando.

## Ejecutar

```bash
streamlit run app.py
```

## Cómo usarla rápido

1. Pon tu examen, materias y temas en la barra lateral.
2. Pulsa **"Generar plan de 2 días"**.
3. Usa el chat para pedir cosas como:
   - `añade pomodoro 50/10`
   - `hazme 15 preguntas de ecuaciones diferenciales`
   - `simulacro de física con dificultad alta`
   - `resumen de transformada de Laplace`
4. Marca tareas como completadas y revisa tu avance.

## Nota

Este MVP está pensado para máxima velocidad de uso; puedes extenderlo con más herramientas, memoria persistente o exportación a PDF.
