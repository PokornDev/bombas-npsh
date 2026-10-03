import os
import base64
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# CONFIGURACIÓN
# =========================================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("No se encontró OPENAI_API_KEY en el archivo .env")
    st.stop()

client = OpenAI(api_key=api_key)

MODELO = "gpt-5.6-luna"

# Máximo que permitiremos enviar por consulta
MAX_ARCHIVOS = 5
MAX_TOTAL_MB = 20


st.set_page_config(
    page_title="Mi IA",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FUNCIONES PARA ARCHIVOS
# =========================================================

def obtener_mime(nombre):

    extension = nombre.lower().split(".")[-1]

    tipos = {
        "pdf": "application/pdf",

        "doc": "application/msword",
        "docx": (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),

        "xls": "application/vnd.ms-excel",
        "xlsx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),

        "csv": "text/csv",
        "txt": "text/plain",
        "md": "text/markdown",

        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }

    return tipos.get(extension, "application/octet-stream")


def convertir_a_data_url(archivo):

    datos = archivo.getvalue()

    mime = obtener_mime(archivo.name)

    codificado = base64.b64encode(datos).decode("utf-8")

    return f"data:{mime};base64,{codificado}"


def es_imagen(nombre):

    extension = nombre.lower().split(".")[-1]

    return extension in ["png", "jpg", "jpeg", "webp"]


def es_pdf(nombre):

    return nombre.lower().endswith(".pdf")


# =========================================================
# MEMORIA
# =========================================================

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:

    st.header("🤖 Mi IA")

    if st.button(
        "➕ Nuevo chat",
        use_container_width=True
    ):
        st.session_state.mensajes = []
        st.rerun()

    st.divider()

    st.subheader("📎 Adjuntar archivos")

    archivos = st.file_uploader(
        "PDF, Word, Excel, texto o imagen",
        type=[
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "csv",
            "txt",
            "md",
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        accept_multiple_files=True
    )

    if archivos:

        total_mb = sum(
            len(archivo.getvalue())
            for archivo in archivos
        ) / (1024 * 1024)

        st.caption(
            f"{len(archivos)} archivo(s) — "
            f"{total_mb:.2f} MB"
        )

        for archivo in archivos:
            st.write(f"📄 {archivo.name}")

        st.info(
            "Mientras estos archivos estén adjuntos, "
            "se enviarán junto con tu próxima pregunta."
        )

    st.divider()

    st.write("Modelo:")
    st.code("GPT-5.6 Luna")

    st.write("Motor:")
    st.write("OpenAI API")

    st.caption(
        "Tu clave API permanece en el archivo .env"
    )


# =========================================================
# ENCABEZADO
# =========================================================

st.title("🤖 Mi IA")

st.caption(
    "Pregunta, calcula o analiza documentos e imágenes"
)


# =========================================================
# MOSTRAR HISTORIAL
# =========================================================

for mensaje in st.session_state.mensajes:

    with st.chat_message(mensaje["role"]):

        st.markdown(
            mensaje["content"]
        )

        if mensaje.get("files"):

            st.caption(
                "📎 "
                + ", ".join(mensaje["files"])
            )


# =========================================================
# ENTRADA DEL USUARIO
# =========================================================

pregunta = st.chat_input(
    "Escribe un mensaje..."
)


if pregunta:

    # -----------------------------------------------------
    # VALIDAR ARCHIVOS
    # -----------------------------------------------------

    nombres_archivos = []

    if archivos:

        if len(archivos) > MAX_ARCHIVOS:

            st.error(
                f"Puedes adjuntar máximo "
                f"{MAX_ARCHIVOS} archivos."
            )

            st.stop()

        total_bytes = sum(
            len(archivo.getvalue())
            for archivo in archivos
        )

        total_mb = total_bytes / (1024 * 1024)

        if total_mb > MAX_TOTAL_MB:

            st.error(
                f"Los archivos pesan {total_mb:.1f} MB. "
                f"El máximo configurado es "
                f"{MAX_TOTAL_MB} MB."
            )

            st.stop()

        nombres_archivos = [
            archivo.name
            for archivo in archivos
        ]


    # -----------------------------------------------------
    # GUARDAR PREGUNTA
    # -----------------------------------------------------

    st.session_state.mensajes.append(
        {
            "role": "user",
            "content": pregunta,
            "files": nombres_archivos,
        }
    )


    # -----------------------------------------------------
    # MOSTRAR PREGUNTA
    # -----------------------------------------------------

    with st.chat_message("user"):

        st.markdown(pregunta)

        if nombres_archivos:

            st.caption(
                "📎 "
                + ", ".join(nombres_archivos)
            )


    # -----------------------------------------------------
    # HISTORIAL DE TEXTO
    # -----------------------------------------------------

    historial_anterior = (
        st.session_state.mensajes[:-1][-8:]
    )

    entrada_api = []

    for mensaje in historial_anterior:

        entrada_api.append(
            {
                "role": mensaje["role"],
                "content": mensaje["content"],
            }
        )


    # -----------------------------------------------------
    # MENSAJE ACTUAL
    # -----------------------------------------------------

    contenido_actual = [
        {
            "type": "input_text",
            "text": pregunta,
        }
    ]


    # -----------------------------------------------------
    # ADJUNTAR ARCHIVOS
    # -----------------------------------------------------

    if archivos:

        for archivo in archivos:

            data_url = convertir_a_data_url(
                archivo
            )

            # IMÁGENES
            if es_imagen(archivo.name):

                contenido_actual.append(
                    {
                        "type": "input_image",
                        "image_url": data_url,

                        # Bajo consumo
                        "detail": "low",
                    }
                )

            # PDF
            elif es_pdf(archivo.name):

                contenido_actual.append(
                    {
                        "type": "input_file",
                        "filename": archivo.name,
                        "file_data": data_url,

                        # Reduce consumo visual
                        "detail": "low",
                    }
                )

            # WORD, EXCEL, TXT, CSV...
            else:

                contenido_actual.append(
                    {
                        "type": "input_file",
                        "filename": archivo.name,
                        "file_data": data_url,
                    }
                )


    entrada_api.append(
        {
            "role": "user",
            "content": contenido_actual,
        }
    )


    # =====================================================
    # RESPUESTA DE OPENAI
    # =====================================================

    with st.chat_message("assistant"):

        contenedor = st.empty()

        texto = ""

        try:

            stream = client.responses.create(

                model=MODELO,

                instructions=(
                    "Responde siempre en español. "
                    "Sé claro, preciso y útil. "
                    "Si el usuario adjunta documentos, "
                    "analízalos cuidadosamente y basa "
                    "tu respuesta en su contenido. "
                    "Si analiza ingeniería, muestra "
                    "procedimientos, fórmulas, unidades "
                    "y resultados cuando corresponda. "
                    "Para fórmulas matemáticas utiliza "
                    "LaTeX compatible con Markdown: "
                    "$...$ para fórmulas cortas y "
                    "$$...$$ para ecuaciones separadas. "
                    "No inventes datos que no aparezcan "
                    "en los archivos."
                ),

                input=entrada_api,

                max_output_tokens=1200,

                stream=True,
            )


            # ------------------------------------------------
            # RESPUESTA PROGRESIVA
            # ------------------------------------------------

            for evento in stream:

                if (
                    evento.type
                    == "response.output_text.delta"
                ):

                    texto += evento.delta

                    contenedor.markdown(
                        texto + "▌"
                    )


            contenedor.markdown(texto)


        except Exception as error:

            st.error(
                f"Ocurrió un error:\n\n{error}"
            )

            st.stop()


    # =====================================================
    # GUARDAR RESPUESTA
    # =====================================================

    st.session_state.mensajes.append(
        {
            "role": "assistant",
            "content": texto,
        }
    )