import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


load_dotenv()

st.set_page_config(page_title="StudySprint AI", page_icon="⚡", layout="wide")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = DATA_DIR / "progress.json"

DEFAULT_FEATURES = ["plan_48h", "resumenes", "quiz"]
AGENTS = {
    "planificador": {
        "emoji": "🧭",
        "prompt": (
            "Eres Planificador. Diseñas estrategias de estudio ultra-prácticas para aprobar en 48h. "
            "Da planes accionables por bloques, prioridad, tiempo y descansos."
        ),
    },
    "tutor": {
        "emoji": "🧠",
        "prompt": (
            "Eres Tutor de ingeniería. Explicas conceptos difíciles simple y rápido, "
            "con ejemplos y fórmulas mínimas necesarias para aprobar."
        ),
    },
    "examinador": {
        "emoji": "📝",
        "prompt": (
            "Eres Examinador. Generas preguntas tipo examen, mini simulacros y retroalimentación "
            "corta basada en errores típicos."
        ),
    },
}


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "¡Vamos con todo! 💥 Soy tu copiloto para aprobar en 2 días. "
                    "Puedes hablar con 3 agentes: Planificador, Tutor y Examinador."
                ),
                "agent": "planificador",
            }
        ]
    if "features" not in st.session_state:
        st.session_state.features = DEFAULT_FEATURES.copy()
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "active_agent" not in st.session_state:
        st.session_state.active_agent = "planificador"


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
                "detail": f"Materia: {subjects}. 2h teoría + 1h problemas. Cierra con 10 preguntas.",
            }
        )

    review_start = exam_datetime - timedelta(hours=4)
    blocks.append(
        {
            "done": False,
            "title": "Repaso final + fórmula sheet",
            "time": f"{review_start.strftime('%d/%m %H:%M')} - {(review_start + timedelta(hours=2)).strftime('%H:%M')} UTC",
            "detail": "Revisa errores, fórmulas clave y 1 mini simulacro final.",
        }
    )
    return blocks


def local_assistant_reply(prompt: str, agent: str):
    text = prompt.lower()

    if "pomodoro" in text:
        if "pomodoro" not in st.session_state.features:
            st.session_state.features.append("pomodoro")
        return "✅ Añadido módulo Pomodoro: usa ciclos 50/10 y pausa larga cada 3 ciclos."

    if "flashcard" in text or "anki" in text:
        if "flashcards" not in st.session_state.features:
            st.session_state.features.append("flashcards")
        return "✅ Añadido módulo Flashcards: repasa en ventanas mañana/tarde/noche."

    if agent == "planificador":
        return (
            "🧭 Plan exprés recomendado:\n"
            "1) 3 bloques duros hoy (tema crítico + problemas).\n"
            "2) 3 bloques mañana (simulacro + corrección).\n"
            "3) Últimas 4h: sólo errores y fórmulas."
        )

    if agent == "tutor":
        return (
            "🧠 Método Tutor (rápido):\n"
            "- Definición corta\n- Fórmula clave\n- Ejemplo típico\n- Error común\n"
            "Dime el tema exacto y te lo explico en 2 minutos."
        )

    if agent == "examinador":
        return (
            "📝 Mini simulacro (5 preguntas):\n"
            "1) Concepto esencial.\n2) Ejercicio numérico.\n3) Caso mixto.\n"
            "4) Error típico.\n5) Pregunta de integración entre temas."
        )

    return "Perfecto. Dime materia + tema + tipo de examen y te lo convierto en acciones concretas."


def call_ai(prompt: str, context: dict, agent: str):
    client = maybe_build_openai_client()
    if client is None:
        return local_assistant_reply(prompt, agent)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    agent_prompt = AGENTS[agent]["prompt"]

    messages = [
        {
            "role": "system",
            "content": (
                f"{agent_prompt} Responde en español, directo y orientado a aprobar en 48 horas."
            ),
        },
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


def save_progress(subjects: str, topics: str, exam_dt: datetime):
    payload = {
        "subjects": subjects,
        "topics": topics,
        "exam_dt": exam_dt.strftime("%Y-%m-%d %H:%M"),
        "features": st.session_state.features,
        "tasks": st.session_state.tasks,
        "messages": st.session_state.messages[-30:],
        "active_agent": st.session_state.active_agent,
        "saved_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    PROGRESS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_progress():
    if not PROGRESS_FILE.exists():
        return None
    try:
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def sidebar_controls():
    with st.sidebar:
        st.header("⚙️ Configuración exprés")
        subjects = st.text_input("Materias", "Cálculo, Física, Álgebra lineal")
        topics = st.text_area(
            "Temas clave (separados por coma)",
            "Integrales, EDO, Transformadas, Mecánica, Matrices",
        )
        exam_str = st.text_input("Examen (UTC) YYYY-MM-DD HH:MM", "2026-03-26 14:00")

        st.markdown("---")
        st.subheader("🧑‍🏫 Agente activo")
        st.session_state.active_agent = st.selectbox(
            "Selecciona",
            options=list(AGENTS.keys()),
            format_func=lambda a: f"{AGENTS[a]['emoji']} {a.title()}",
            index=list(AGENTS.keys()).index(st.session_state.active_agent),
        )

        try:
            exam_dt = datetime.strptime(exam_str, "%Y-%m-%d %H:%M")
        except ValueError:
            st.error("Formato inválido. Usa YYYY-MM-DD HH:MM")
            exam_dt = datetime.utcnow() + timedelta(days=2)

        if st.button("Generar plan de 2 días", use_container_width=True):
            st.session_state.tasks = build_48h_plan(subjects, topics, exam_dt)
            st.success("Plan generado ✅")

        c1, c2 = st.columns(2)
        if c1.button("Guardar progreso", use_container_width=True):
            save_progress(subjects, topics, exam_dt)
            st.success("Progreso guardado")

        if c2.button("Cargar progreso", use_container_width=True):
            data = load_progress()
            if data:
                st.session_state.features = data.get("features", DEFAULT_FEATURES.copy())
                st.session_state.tasks = data.get("tasks", [])
                st.session_state.messages = data.get("messages", st.session_state.messages)
                st.session_state.active_agent = data.get("active_agent", "planificador")
                st.success(f"Progreso cargado ({data.get('saved_at', 'sin fecha')})")
            else:
                st.warning("No se encontró progreso guardado.")

        st.caption("Tip: con API key usa IA real; sin key funciona en modo local.")

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
            st.markdown(f"**{task['title']}**")
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
    st.subheader("🤖 Chat multi-agente")
    st.caption("Tip: cambia de agente en la barra lateral según lo que necesites.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            badge = ""
            if msg["role"] == "assistant":
                ag = msg.get("agent", st.session_state.active_agent)
                badge = f"**{AGENTS[ag]['emoji']} {ag.title()}**\n\n"
            st.markdown(f"{badge}{msg['content']}")

    prompt = st.chat_input("Ej: 'hazme simulacro de física', 'explica Laplace fácil', 'organiza hoy en 3 bloques'")
    if not prompt:
        return

    active_agent = st.session_state.active_agent
    st.session_state.messages.append({"role": "user", "content": prompt, "agent": active_agent})
    with st.chat_message("user"):
        st.markdown(prompt)

    context = {
        "subjects": subjects,
        "topics": topics,
        "exam_datetime_utc": exam_dt.strftime("%Y-%m-%d %H:%M"),
        "features": st.session_state.features,
        "tasks_count": len(st.session_state.tasks),
        "active_agent": active_agent,
    }
    reply = call_ai(prompt, context, active_agent)
    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "agent": active_agent}
    )

    with st.chat_message("assistant"):
        st.markdown(f"**{AGENTS[active_agent]['emoji']} {active_agent.title()}**\n\n{reply}")


def main():
    init_state()
    st.title("⚡ StudySprint AI")
    st.caption("Prepárate para tu examen de ingeniería en 2 días con ayuda de IA multi-agente.")

    subjects, topics, exam_dt = sidebar_controls()

    col1, col2 = st.columns([1.15, 1])
    with col1:
        render_tasks()
        render_chat(subjects, topics, exam_dt)
    with col2:
        render_features()
        st.subheader("🎯 Estrategia recomendada")
        st.markdown(
            """
            1. **Prioriza 20% de temas = 80% puntos**.
            2. **Bloques 50/10** y problemas antes que teoría si el examen es práctico.
            3. **Cierra cada bloque con 5-10 preguntas**.
            4. **Haz un simulacro y corrígelo**.
            5. **Últimas 4h: errores + fórmulas**.
            """
        )


if __name__ == "__main__":
    main()
