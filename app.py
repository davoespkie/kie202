import os
from datetime import datetime, timedelta
import json

import streamlit as st
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


load_dotenv()

st.set_page_config(page_title="StudySprint AI", page_icon="⚡", layout="wide")

DEFAULT_FEATURES = ["plan_48h", "resumenes", "quiz"]


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "¡Vamos con todo! 💥 Soy tu copiloto para preparar el examen en 2 días. "
                    "Dime qué materia te preocupa y te monto un plan exprés."
                ),
            }
        ]
    if "features" not in st.session_state:
        st.session_state.features = DEFAULT_FEATURES.copy()
    if "tasks" not in st.session_state:
        st.session_state.tasks = []


def maybe_build_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def build_48h_plan(subjects: str, topics: str, exam_datetime: datetime):
    now = datetime.utcnow()
    blocks = []

    t_list = [t.strip() for t in topics.split(",") if t.strip()]
    if not t_list:
        t_list = ["Repaso general", "Problemas tipo examen", "Errores frecuentes"]

    total_blocks = 8
    for i in range(total_blocks):
        start = now + timedelta(hours=i * 5)
        end = start + timedelta(hours=3)
        topic = t_list[i % len(t_list)]
        blocks.append(
            {
                "done": False,
                "title": f"Bloque {i+1}: {topic}",
                "time": f"{start.strftime('%d/%m %H:%M')} - {end.strftime('%H:%M')} UTC",
                "detail": (
                    f"Materia: {subjects}. 2h teoría + 1h problemas. "
                    "Cierra con 10 preguntas rápidas."
                ),
            }
        )

    review_start = exam_datetime - timedelta(hours=4)
    blocks.append(
        {
            "done": False,
            "title": "Repaso final + fórmula sheet",
            "time": f"{review_start.strftime('%d/%m %H:%M')} - {(review_start + timedelta(hours=2)).strftime('%H:%M')} UTC",
            "detail": "Revisa errores marcados, fórmulas clave y 1 mini simulacro final.",
        }
    )
    return blocks


def local_assistant_reply(prompt: str):
    text = prompt.lower()

    if "pomodoro" in text:
        if "pomodoro" not in st.session_state.features:
            st.session_state.features.append("pomodoro")
        return "✅ Listo, añadí Pomodoro. Recomendación para 2 días: ciclos 50/10 en bloques intensos."

    if "flashcard" in text or "anki" in text:
        if "flashcards" not in st.session_state.features:
            st.session_state.features.append("flashcards")
        return "✅ Activé flashcards. Te conviene repasar en tandas cortas: mañana/tarde/noche."

    if "simulacro" in text:
        return (
            "🎯 Mini simulacro rápido (5 preguntas):\n"
            "1) Explica el concepto clave del tema 1.\n"
            "2) Resuelve un ejercicio típico del tema 2.\n"
            "3) ¿Qué error común te haría perder puntos?\n"
            "4) Relaciona dos temas del examen en un solo problema.\n"
            "5) Resume todo en 5 fórmulas imprescindibles."
        )

    if "resumen" in text:
        return (
            "🧠 Plantilla de resumen exprés:\n"
            "- Definición en 1 línea\n"
            "- 3 ideas clave\n"
            "- 2 fórmulas\n"
            "- 1 ejemplo resuelto\n"
            "- 1 error típico"
        )

    if "preguntas" in text or "quiz" in text:
        return "📚 Te propongo 15 preguntas: 5 conceptuales, 5 numéricas y 5 mixtas de nivel examen."

    if "añade" in text or "agrega" in text:
        return "✅ Hecho. Dime exactamente qué módulo quieres (pomodoro, flashcards, simulacros, repasos espaciados)."

    return (
        "Perfecto. Para avanzar súper rápido, dime:\n"
        "1) materia exacta\n2) temas más difíciles\n3) tipo de examen (teórico/problemas/mixto)."
    )


def call_ai(prompt: str, context: dict):
    client = maybe_build_openai_client()
    if client is None:
        return local_assistant_reply(prompt)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system = (
        "Eres un tutor ultra-práctico para universitarios de ingeniería con poco tiempo. "
        "Responde en español, directo, orientado a aprobar en 48h. "
        "Si el usuario pide añadir una funcionalidad, sugiere cómo usarla desde esta app."
    )

    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Contexto app: {json.dumps(context, ensure_ascii=False)}\n"
                f"Solicitud usuario: {prompt}"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.4,
    )
    return response.choices[0].message.content


def sidebar_controls():
    with st.sidebar:
        st.header("⚙️ Configuración exprés")
        subjects = st.text_input("Materias", "Cálculo, Física, Álgebra lineal")
        topics = st.text_area(
            "Temas clave (separados por coma)",
            "Integrales, EDO, Transformadas, Mecánica, Matrices",
        )
        exam_str = st.text_input("Examen (UTC) YYYY-MM-DD HH:MM", "2026-03-26 14:00")

        try:
            exam_dt = datetime.strptime(exam_str, "%Y-%m-%d %H:%M")
        except ValueError:
            st.error("Formato inválido. Usa YYYY-MM-DD HH:MM")
            exam_dt = datetime.utcnow() + timedelta(days=2)

        if st.button("Generar plan de 2 días", use_container_width=True):
            st.session_state.tasks = build_48h_plan(subjects, topics, exam_dt)
            st.success("Plan generado ✅")

        st.caption("Tip: sin API key funciona en modo local (reglas).")

    return subjects, topics, exam_dt


def render_tasks():
    st.subheader("🗓️ Plan de estudio (48h)")
    if not st.session_state.tasks:
        st.info("Genera el plan desde la barra lateral.")
        return

    for i, task in enumerate(st.session_state.tasks):
        cols = st.columns([0.08, 0.92])
        with cols[0]:
            done = st.checkbox("", key=f"task_{i}", value=task["done"])
        with cols[1]:
            st.markdown(f"**{task['title']}**  ")
            st.caption(f"{task['time']} · {task['detail']}")
        st.session_state.tasks[i]["done"] = done

    total = len(st.session_state.tasks)
    completed = sum(1 for t in st.session_state.tasks if t["done"])
    st.progress(completed / total if total else 0)
    st.write(f"Avance: **{completed}/{total}** bloques.")


def render_features():
    st.subheader("🧩 Módulos activos")
    labels = {
        "plan_48h": "Plan 48h",
        "resumenes": "Resúmenes",
        "quiz": "Quiz",
        "pomodoro": "Pomodoro",
        "flashcards": "Flashcards",
    }
    active = [labels.get(f, f) for f in st.session_state.features]
    st.write(" · ".join(active))


def render_chat(subjects, topics, exam_dt):
    st.subheader("🤖 Chatbot entrenador")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Pide algo: 'añade pomodoro 50/10', 'haz simulacro', 'resumen de ...'")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context = {
        "subjects": subjects,
        "topics": topics,
        "exam_datetime_utc": exam_dt.strftime("%Y-%m-%d %H:%M"),
        "features": st.session_state.features,
        "tasks_count": len(st.session_state.tasks),
    }
    reply = call_ai(prompt, context)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)


def main():
    init_state()
    st.title("⚡ StudySprint AI")
    st.caption("Prepárate para tu examen de ingeniería en 2 días con ayuda de IA.")

    subjects, topics, exam_dt = sidebar_controls()

    col1, col2 = st.columns([1.15, 1])
    with col1:
        render_tasks()
        render_chat(subjects, topics, exam_dt)
    with col2:
        render_features()
        st.subheader("🎯 Recomendación de estrategia")
        st.markdown(
            """
            1. **Prioriza 20% de temas que dan 80% de puntos**.
            2. **Bloques 50/10** para enfoque máximo.
            3. **Problemas primero, teoría después** si el examen es práctico.
            4. **Cierra cada bloque con autoevaluación** (5-10 preguntas).
            5. **Últimas 4 horas:** solo repaso de errores + fórmulas.
            """
        )


if __name__ == "__main__":
    main()
