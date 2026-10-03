import os
import base64
import numpy as np
import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    st.error(
        "No se encontró OPENAI_API_KEY en el archivo .env"
    )
    st.stop()

client = OpenAI(api_key=API_KEY)

# Modelo que ya probaste y te funciona
MODELO = "gpt-5.6-luna"

# Gravedad
G = 9.81

# Límites para archivos
MAX_ARCHIVOS = 5
MAX_TOTAL_MB = 20


st.set_page_config(
    page_title="Bombas y NPSH",
    page_icon="💧",
    layout="wide"
)


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.25);
        padding: 15px;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNCIONES HIDRÁULICAS
# ============================================================

def presion_atmosferica(altura_m):
    """
    Presión atmosférica aproximada según
    atmósfera estándar.

    Entrada:
        altura_m -> metros sobre el nivel del mar

    Salida:
        presión atmosférica en kPa
    """

    return (
        101.325
        * (1 - 2.25577e-5 * altura_m) ** 5.25588
    )


def presion_vapor_agua(temperatura_c):
    """
    Presión de vapor del agua mediante
    ecuación de Antoine.

    Devuelve kPa.
    """

    A = 8.07131
    B = 1730.63
    C = 233.426

    p_mmhg = 10 ** (
        A
        - B / (C + temperatura_c)
    )

    p_kpa = (
        p_mmhg
        * 0.133322
    )

    return p_kpa


# ============================================================
# FUNCIONES PARA ARCHIVOS
# ============================================================

def obtener_mime(nombre):

    extension = (
        nombre
        .lower()
        .split(".")[-1]
    )

    tipos = {

        "pdf":
            "application/pdf",

        "doc":
            "application/msword",

        "docx":
            (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),

        "xls":
            "application/vnd.ms-excel",

        "xlsx":
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),

        "csv":
            "text/csv",

        "txt":
            "text/plain",

        "md":
            "text/markdown",

        "png":
            "image/png",

        "jpg":
            "image/jpeg",

        "jpeg":
            "image/jpeg",

        "webp":
            "image/webp"
    }

    return tipos.get(
        extension,
        "application/octet-stream"
    )


def convertir_data_url(archivo):

    datos = archivo.getvalue()

    codificado = (
        base64
        .b64encode(datos)
        .decode("utf-8")
    )

    mime = obtener_mime(
        archivo.name
    )

    return (
        f"data:{mime};base64,{codificado}"
    )


def es_imagen(nombre):

    extension = (
        nombre
        .lower()
        .split(".")[-1]
    )

    return extension in [
        "png",
        "jpg",
        "jpeg",
        "webp"
    ]


# ============================================================
# SESSION STATE
# ============================================================

if "mensajes" not in st.session_state:

    st.session_state.mensajes = []


if "uploader_key" not in st.session_state:

    st.session_state.uploader_key = 0


# ============================================================
# BARRA LATERAL
# ============================================================

with st.sidebar:

    st.title(
        "💧 Bombas & NPSH"
    )

    st.caption(
        "Ingeniería hidráulica y sanitaria"
    )

    # --------------------------------------------------------
    # NUEVO CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ Nuevo chat",
        use_container_width=True
    ):

        st.session_state.mensajes = []

        st.rerun()


    st.divider()


    # --------------------------------------------------------
    # ARCHIVOS
    # --------------------------------------------------------

    st.subheader(
        "📎 Archivo técnico"
    )

    archivos = st.file_uploader(

        "PDF, Word, Excel, TXT o imagen",

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
            "webp"
        ],

        accept_multiple_files=True,

        key=(
            f"uploader_"
            f"{st.session_state.uploader_key}"
        )
    )


    usar_archivos = False


    if archivos:

        total_mb = sum(
            len(a.getvalue())
            for a in archivos
        ) / (1024 * 1024)


        st.caption(
            f"{len(archivos)} archivo(s) — "
            f"{total_mb:.2f} MB"
        )


        for archivo in archivos:

            st.write(
                f"📄 {archivo.name}"
            )


        usar_archivos = st.checkbox(
            "Enviar archivos en la próxima pregunta",
            value=True
        )


        st.warning(
            "Si mantienes los archivos adjuntos, "
            "pueden volver a enviarse a la API en "
            "otra consulta y generar consumo adicional."
        )


        if st.button(
            "❌ Quitar archivos",
            use_container_width=True
        ):

            st.session_state.uploader_key += 1

            st.rerun()


    st.divider()


    st.write(
        "**Modelo IA**"
    )

    st.code(
        "GPT-5.6 Luna"
    )


    st.write(
        "**Funcionamiento**"
    )

    st.write(
        "OpenAI API"
    )


    st.success(
        "🧮 Las calculadoras hidráulicas "
        "son locales y NO consumen API."
    )


# ============================================================
# ENCABEZADO
# ============================================================

st.title(
    "💧 Bombas Centrífugas y NPSH"
)

st.caption(
    "Asistente técnico, cálculos hidráulicos "
    "y análisis de curvas de bombas."
)


# ============================================================
# PESTAÑAS
# ============================================================

(
    tab_chat,
    tab_npsh,
    tab_potencia,
    tab_curvas

) = st.tabs(
    [
        "🤖 Asistente IA",
        "🧮 NPSH",
        "⚙️ Potencia",
        "📈 Curvas de bomba"
    ]
)


# ============================================================
# 1. ASISTENTE IA
# ============================================================

with tab_chat:

    st.subheader(
        "🤖 Asistente técnico"
    )

    st.caption(
        "Bombas centrífugas, cavitación, "
        "NPSH, rendimiento, potencia, "
        "curvas y sistemas de bombeo."
    )


    # --------------------------------------------------------
    # MOSTRAR HISTORIAL
    # --------------------------------------------------------

    for mensaje in st.session_state.mensajes:

        with st.chat_message(
            mensaje["role"]
        ):

            st.markdown(
                mensaje["content"]
            )


    # --------------------------------------------------------
    # ENTRADA
    # --------------------------------------------------------

    pregunta = st.chat_input(
        "Pregunta sobre bombas o NPSH..."
    )


    if pregunta:

        # ----------------------------------------------------
        # VALIDAR ARCHIVOS
        # ----------------------------------------------------

        archivos_enviar = []


        if (
            archivos
            and usar_archivos
        ):

            archivos_enviar = archivos


            if (
                len(archivos_enviar)
                > MAX_ARCHIVOS
            ):

                st.error(
                    f"Máximo permitido: "
                    f"{MAX_ARCHIVOS} archivos."
                )

                st.stop()


            total_mb = sum(
                len(a.getvalue())
                for a in archivos_enviar
            ) / (1024 * 1024)


            if (
                total_mb
                > MAX_TOTAL_MB
            ):

                st.error(
                    f"Los archivos pesan "
                    f"{total_mb:.1f} MB. "
                    f"Máximo configurado: "
                    f"{MAX_TOTAL_MB} MB."
                )

                st.stop()


        # ----------------------------------------------------
        # GUARDAR PREGUNTA
        # ----------------------------------------------------

        st.session_state.mensajes.append(
            {
                "role": "user",
                "content": pregunta
            }
        )


        # ----------------------------------------------------
        # MOSTRAR PREGUNTA
        # ----------------------------------------------------

        with st.chat_message("user"):

            st.markdown(
                pregunta
            )


            if archivos_enviar:

                st.caption(
                    "📎 "
                    + ", ".join(
                        a.name
                        for a
                        in archivos_enviar
                    )
                )


        # ----------------------------------------------------
        # HISTORIAL RECIENTE
        # ----------------------------------------------------

        entrada = []


        for mensaje in (
            st.session_state
            .mensajes[-8:-1]
        ):

            entrada.append(
                {
                    "role":
                        mensaje["role"],

                    "content":
                        mensaje["content"]
                }
            )


        # ----------------------------------------------------
        # MENSAJE ACTUAL
        # ----------------------------------------------------

        contenido_actual = [
            {
                "type":
                    "input_text",

                "text":
                    pregunta
            }
        ]


        # ----------------------------------------------------
        # ARCHIVOS
        # ----------------------------------------------------

        for archivo in archivos_enviar:

            data_url = convertir_data_url(
                archivo
            )


            if es_imagen(
                archivo.name
            ):

                contenido_actual.append(
                    {
                        "type":
                            "input_image",

                        "image_url":
                            data_url,

                        "detail":
                            "low"
                    }
                )


            else:

                contenido_actual.append(
                    {
                        "type":
                            "input_file",

                        "filename":
                            archivo.name,

                        "file_data":
                            data_url
                    }
                )


        entrada.append(
            {
                "role":
                    "user",

                "content":
                    contenido_actual
            }
        )


        # ----------------------------------------------------
        # OPENAI
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            contenedor = st.empty()

            texto = ""


            try:

                stream = (
                    client
                    .responses
                    .create(

                        model=MODELO,

                        instructions=(
                            "Eres un especialista en "
                            "ingeniería hidráulica, "
                            "ingeniería sanitaria y "
                            "bombas centrífugas. "

                            "Responde siempre en español. "

                            "Explica de manera técnica "
                            "pero fácil de entender. "

                            "Diferencia claramente "
                            "NPSH disponible (NPSHa) "
                            "de NPSH requerido (NPSHr). "

                            "Cuando hagas un cálculo "
                            "muestra: datos, fórmula, "
                            "sustitución, unidades y "
                            "resultado final. "

                            "Trabaja preferentemente "
                            "con unidades del Sistema "
                            "Internacional. "

                            "Usa LaTeX para fórmulas. "

                            "Cuando analices una curva "
                            "de bomba, identifica cuando "
                            "sea posible caudal, altura, "
                            "rendimiento, potencia, "
                            "NPSHr y BEP. "

                            "Si el usuario proporciona "
                            "un documento, basa la "
                            "respuesta en ese documento. "

                            "No inventes información "
                            "que no esté disponible."
                        ),

                        input=entrada,

                        max_output_tokens=1200,

                        stream=True
                    )
                )


                for evento in stream:

                    if (
                        evento.type
                        == "response.output_text.delta"
                    ):

                        texto += evento.delta

                        contenedor.markdown(
                            texto + "▌"
                        )


                contenedor.markdown(
                    texto
                )


            except Exception as error:

                st.error(
                    "Ocurrió un error:\n\n"
                    f"{error}"
                )

                st.stop()


        # ----------------------------------------------------
        # GUARDAR RESPUESTA
        # ----------------------------------------------------

        st.session_state.mensajes.append(
            {
                "role":
                    "assistant",

                "content":
                    texto
            }
        )


# ============================================================
# 2. CALCULADORA NPSH
# ============================================================

with tab_npsh:

    st.subheader(
        "🧮 NPSH disponible"
    )

    st.success(
        "Este cálculo es local y "
        "NO consume tu saldo API."
    )


    st.write(
        "Para un depósito cuya superficie "
        "se encuentra a una presión conocida:"
    )


    st.latex(
        r"NPSH_a="
        r"\frac{P_{atm}+P_g-P_v}{\rho g}"
        r"+H_s-h_f"
    )


    st.caption(
        "Hs es positiva cuando la superficie "
        "del líquido está sobre el eje de la bomba "
        "y negativa cuando la bomba está por encima "
        "del nivel del líquido."
    )


    col1, col2 = st.columns(2)


    # --------------------------------------------------------
    # DATOS AMBIENTALES
    # --------------------------------------------------------

    with col1:

        st.markdown(
            "### Condiciones del líquido"
        )


        altitud = st.number_input(

            "Altitud sobre el nivel del mar (m)",

            min_value=0.0,
            max_value=6000.0,

            value=0.0,

            step=50.0
        )


        temperatura = st.number_input(

            "Temperatura del agua (°C)",

            min_value=1.0,
            max_value=100.0,

            value=20.0,

            step=1.0
        )


        densidad = st.number_input(

            "Densidad del líquido (kg/m³)",

            min_value=500.0,
            max_value=1500.0,

            value=998.0,

            step=1.0
        )


        presion_deposito = st.number_input(

            "Presión manométrica "
            "sobre el líquido (kPa)",

            value=0.0,

            step=1.0,

            help=(
                "Para un depósito abierto "
                "a la atmósfera utiliza 0 kPa."
            )
        )


    # --------------------------------------------------------
    # SISTEMA DE SUCCIÓN
    # --------------------------------------------------------

    with col2:

        st.markdown(
            "### Sistema de succión"
        )


        altura_succion = st.number_input(

            "Altura estática Hs (m)",

            value=2.0,

            step=0.1,

            help=(
                "Positiva si el nivel del líquido "
                "está sobre la bomba. "
                "Negativa si la bomba está sobre "
                "el nivel del líquido."
            )
        )


        perdidas_succion = st.number_input(

            "Pérdidas en succión hf (m)",

            min_value=0.0,

            value=1.0,

            step=0.1
        )


        npshr = st.number_input(

            "NPSH requerido NPSHr (m)",

            min_value=0.0,

            value=3.0,

            step=0.1
        )


        margen_seguridad = st.number_input(

            "Margen adicional (m)",

            min_value=0.0,

            value=0.5,

            step=0.1
        )


    # --------------------------------------------------------
    # CALCULAR
    # --------------------------------------------------------

    if st.button(
        "💧 Calcular NPSH",
        type="primary",
        use_container_width=True
    ):

        patm = (
            presion_atmosferica(
                altitud
            )
        )


        pv = (
            presion_vapor_agua(
                temperatura
            )
        )


        cabeza_presiones = (
            (
                patm
                + presion_deposito
                - pv
            )
            * 1000
            / (
                densidad
                * G
            )
        )


        npsha = (
            cabeza_presiones
            + altura_succion
            - perdidas_succion
        )


        margen_real = (
            npsha
            - npshr
        )


        minimo_requerido = (
            npshr
            + margen_seguridad
        )


        # ----------------------------------------------------
        # RESULTADOS
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "Resultados"
        )


        r1, r2, r3 = st.columns(3)


        r1.metric(
            "NPSHa",
            f"{npsha:.2f} m"
        )


        r2.metric(
            "NPSHr",
            f"{npshr:.2f} m"
        )


        r3.metric(
            "Margen NPSHa - NPSHr",
            f"{margen_real:.2f} m"
        )


        st.write(
            "Presión atmosférica estimada: "
            f"**{patm:.2f} kPa**"
        )


        st.write(
            "Presión de vapor: "
            f"**{pv:.3f} kPa**"
        )


        st.write(
            "Carga disponible por presiones: "
            f"**{cabeza_presiones:.2f} m**"
        )


        # ----------------------------------------------------
        # VERIFICACIÓN
        # ----------------------------------------------------

        if (
            npsha
            >= minimo_requerido
        ):

            st.success(
                "✅ CUMPLE\n\n"
                "El NPSH disponible es "
                "suficiente considerando "
                "el margen establecido."
            )


        else:

            deficit = (
                minimo_requerido
                - npsha
            )


            st.error(
                "⚠️ NO CUMPLE\n\n"
                "El sistema presenta un "
                "déficit aproximado de "
                f"**{deficit:.2f} m** de NPSH."
            )


        st.markdown(
            "### Procedimiento"
        )


        st.latex(
            rf"P_{{atm}}="
            rf"{patm:.2f}\;kPa"
        )


        st.latex(
            rf"P_v="
            rf"{pv:.3f}\;kPa"
        )


        st.latex(
            rf"NPSH_a="
            rf"\frac{{"
            rf"({patm:.2f}"
            rf"+{presion_deposito:.2f}"
            rf"-{pv:.3f})"
            rf"\times1000"
            rf"}}"
            rf"{{"
            rf"{densidad:.1f}"
            rf"\times9.81"
            rf"}}"
            rf"+({altura_succion:.2f})"
            rf"-{perdidas_succion:.2f}"
        )


        st.latex(
            rf"NPSH_a="
            rf"{npsha:.2f}\;m"
        )


        st.latex(
            rf"NPSH_{{mínimo}}="
            rf"NPSH_r+margen="
            rf"{minimo_requerido:.2f}\;m"
        )


# ============================================================
# 3. POTENCIA DE LA BOMBA
# ============================================================

with tab_potencia:

    st.subheader(
        "⚙️ Potencia de bomba"
    )


    st.success(
        "Este cálculo es local y "
        "NO consume tu saldo API."
    )


    st.latex(
        r"P_h=\rho g Q H"
    )


    st.latex(
        r"P_{eje}="
        r"\frac{P_h}{\eta_b}"
    )


    col1, col2 = st.columns(2)


    with col1:

        caudal_ls = st.number_input(

            "Caudal Q (L/s)",

            min_value=0.0,

            value=20.0,

            step=1.0
        )


        altura_total = st.number_input(

            "Altura dinámica total H (m)",

            min_value=0.0,

            value=30.0,

            step=1.0
        )


    with col2:

        rendimiento = st.number_input(

            "Rendimiento de la bomba (%)",

            min_value=1.0,
            max_value=100.0,

            value=75.0,

            step=1.0
        )


        densidad_potencia = st.number_input(

            "Densidad del líquido (kg/m³)",

            min_value=500.0,
            max_value=1500.0,

            value=1000.0,

            step=1.0
        )


    if st.button(

        "⚙️ Calcular potencia",

        type="primary",

        use_container_width=True
    ):

        Q = (
            caudal_ls
            / 1000
        )


        eta = (
            rendimiento
            / 100
        )


        potencia_hidraulica = (
            densidad_potencia
            * G
            * Q
            * altura_total
        )


        potencia_eje = (
            potencia_hidraulica
            / eta
        )


        ph_kw = (
            potencia_hidraulica
            / 1000
        )


        peje_kw = (
            potencia_eje
            / 1000
        )


        peje_hp = (
            peje_kw
            / 0.7457
        )


        st.divider()

        st.subheader(
            "Resultados"
        )


        c1, c2, c3 = st.columns(3)


        c1.metric(
            "Potencia hidráulica",
            f"{ph_kw:.2f} kW"
        )


        c2.metric(
            "Potencia al eje",
            f"{peje_kw:.2f} kW"
        )


        c3.metric(
            "Potencia al eje",
            f"{peje_hp:.2f} HP"
        )


        st.markdown(
            "### Procedimiento"
        )


        st.latex(
            rf"Q="
            rf"{caudal_ls:.2f}\;L/s"
            rf"="
            rf"{Q:.4f}\;m^3/s"
        )


        st.latex(
            rf"P_h="
            rf"{densidad_potencia:.0f}"
            rf"(9.81)"
            rf"({Q:.4f})"
            rf"({altura_total:.2f})"
        )


        st.latex(
            rf"P_h="
            rf"{ph_kw:.2f}\;kW"
        )


        st.latex(
            rf"P_{{eje}}="
            rf"\frac{{"
            rf"{ph_kw:.2f}"
            rf"}}"
            rf"{{"
            rf"{eta:.2f}"
            rf"}}"
            rf"="
            rf"{peje_kw:.2f}\;kW"
        )


        st.latex(
            rf"P_{{eje}}="
            rf"{peje_hp:.2f}\;HP"
        )


# ============================================================
# 4. CURVAS DE BOMBA
# ============================================================

with tab_curvas:

    st.subheader(
        "📈 Curvas características"
    )


    st.success(
        "Este módulo funciona localmente "
        "y NO consume saldo API."
    )


    st.write(
        "Ingresa los datos de la curva "
        "del fabricante."
    )


    # --------------------------------------------------------
    # TABLA INICIAL
    # --------------------------------------------------------

    datos_iniciales = pd.DataFrame(
        {
            "Q (L/s)": [
                0.0,
                10.0,
                20.0,
                30.0,
                40.0,
                50.0
            ],

            "H (m)": [
                48.0,
                46.0,
                42.0,
                36.0,
                28.0,
                18.0
            ],

            "Rendimiento (%)": [
                40.0,
                60.0,
                75.0,
                82.0,
                76.0,
                60.0
            ],

            "NPSHr (m)": [
                1.5,
                1.7,
                2.2,
                3.0,
                4.2,
                6.0
            ]
        }
    )


    datos = st.data_editor(

        datos_iniciales,

        num_rows="dynamic",

        use_container_width=True,

        hide_index=True,

        column_config={

            "Q (L/s)":
                st.column_config.NumberColumn(
                    format="%.2f"
                ),

            "H (m)":
                st.column_config.NumberColumn(
                    format="%.2f"
                ),

            "Rendimiento (%)":
                st.column_config.NumberColumn(
                    format="%.1f"
                ),

            "NPSHr (m)":
                st.column_config.NumberColumn(
                    format="%.2f"
                )
        }
    )


    st.caption(
        "Puedes modificar los valores, "
        "agregar filas o eliminar puntos."
    )


    st.divider()


    # --------------------------------------------------------
    # CURVA DEL SISTEMA
    # --------------------------------------------------------

    st.subheader(
        "Curva del sistema"
    )


    st.latex(
        r"H_s="
        r"H_{estática}"
        r"+KQ^2"
    )


    col1, col2 = st.columns(2)


    with col1:

        h_estatica = st.number_input(

            "Altura estática del sistema (m)",

            min_value=0.0,

            value=10.0,

            step=1.0
        )


    with col2:

        k_sistema = st.number_input(

            "Coeficiente K "
            "con Q en L/s",

            min_value=0.0,

            value=0.015,

            step=0.001,

            format="%.4f"
        )


    # --------------------------------------------------------
    # GENERAR
    # --------------------------------------------------------

    if st.button(

        "📊 Generar curvas y calcular punto de operación",

        type="primary",

        use_container_width=True
    ):

        # Convertir a números
        datos_num = (
            datos
            .apply(
                pd.to_numeric,
                errors="coerce"
            )
            .dropna()
        )


        # Ordenar por caudal
        datos_num = (
            datos_num
            .sort_values(
                "Q (L/s)"
            )
        )


        if (
            len(datos_num)
            < 2
        ):

            st.error(
                "Debes ingresar al menos "
                "dos puntos de la curva."
            )

            st.stop()


        # ----------------------------------------------------
        # EXTRAER DATOS
        # ----------------------------------------------------

        Q = (
            datos_num[
                "Q (L/s)"
            ]
            .to_numpy()
        )


        H = (
            datos_num[
                "H (m)"
            ]
            .to_numpy()
        )


        eficiencia = (
            datos_num[
                "Rendimiento (%)"
            ]
            .to_numpy()
        )


        npshr_curva = (
            datos_num[
                "NPSHr (m)"
            ]
            .to_numpy()
        )


        # ----------------------------------------------------
        # INTERPOLACIÓN
        # ----------------------------------------------------

        q_min = float(
            Q.min()
        )


        q_max = float(
            Q.max()
        )


        q_fino = np.linspace(
            q_min,
            q_max,
            800
        )


        h_bomba = np.interp(
            q_fino,
            Q,
            H
        )


        eficiencia_fina = np.interp(
            q_fino,
            Q,
            eficiencia
        )


        npshr_fino = np.interp(
            q_fino,
            Q,
            npshr_curva
        )


        h_sistema = (
            h_estatica
            + k_sistema
            * q_fino ** 2
        )


        # ----------------------------------------------------
        # PUNTO DE OPERACIÓN
        # ----------------------------------------------------

        diferencia = (
            h_bomba
            - h_sistema
        )


        q_operacion = None


        for i in range(
            len(q_fino) - 1
        ):

            d1 = diferencia[i]
            d2 = diferencia[i + 1]


            # Punto exacto
            if d1 == 0:

                q_operacion = (
                    q_fino[i]
                )

                break


            # Cruce entre curvas
            if (
                d1 * d2 < 0
            ):

                q1 = q_fino[i]
                q2 = q_fino[i + 1]


                q_operacion = (
                    q1
                    - d1
                    * (q2 - q1)
                    / (d2 - d1)
                )

                break


        # ----------------------------------------------------
        # CURVA Q-H
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "Curva Q-H y curva del sistema"
        )


        grafico_qh = pd.DataFrame(
            {
                "Caudal Q (L/s)":
                    q_fino,

                "Bomba H (m)":
                    h_bomba,

                "Sistema H (m)":
                    h_sistema
            }
        )


        grafico_qh = (
            grafico_qh
            .set_index(
                "Caudal Q (L/s)"
            )
        )


        st.line_chart(
            grafico_qh,
            use_container_width=True
        )


        # ----------------------------------------------------
        # RESULTADO PUNTO DE OPERACIÓN
        # ----------------------------------------------------

        if (
            q_operacion
            is not None
        ):

            h_operacion = (
                h_estatica
                + k_sistema
                * q_operacion ** 2
            )


            eta_operacion = np.interp(
                q_operacion,
                Q,
                eficiencia
            )


            npshr_operacion = np.interp(
                q_operacion,
                Q,
                npshr_curva
            )


            st.success(
                "✅ Se encontró el punto "
                "de operación de la bomba."
            )


            c1, c2, c3, c4 = (
                st.columns(4)
            )


            c1.metric(
                "Q operación",
                f"{q_operacion:.2f} L/s"
            )


            c2.metric(
                "H operación",
                f"{h_operacion:.2f} m"
            )


            c3.metric(
                "Rendimiento",
                f"{eta_operacion:.1f} %"
            )


            c4.metric(
                "NPSHr",
                f"{npshr_operacion:.2f} m"
            )


            st.latex(
                rf"Q_{{op}}="
                rf"{q_operacion:.2f}"
                rf"\;L/s"
            )


            st.latex(
                rf"H_{{op}}="
                rf"{h_operacion:.2f}"
                rf"\;m"
            )


        else:

            st.warning(
                "⚠️ No existe una intersección "
                "entre la curva de la bomba y "
                "la curva del sistema dentro "
                "del rango ingresado."
            )


        # ----------------------------------------------------
        # CURVA DE RENDIMIENTO
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "Curva de rendimiento"
        )


        grafico_eta = pd.DataFrame(
            {
                "Caudal Q (L/s)":
                    q_fino,

                "Rendimiento (%)":
                    eficiencia_fina
            }
        )


        grafico_eta = (
            grafico_eta
            .set_index(
                "Caudal Q (L/s)"
            )
        )


        st.line_chart(
            grafico_eta,
            use_container_width=True
        )


        # ----------------------------------------------------
        # CURVA NPSHr
        # ----------------------------------------------------

        st.subheader(
            "Curva NPSHr"
        )


        grafico_npsh = pd.DataFrame(
            {
                "Caudal Q (L/s)":
                    q_fino,

                "NPSHr (m)":
                    npshr_fino
            }
        )


        grafico_npsh = (
            grafico_npsh
            .set_index(
                "Caudal Q (L/s)"
            )
        )


        st.line_chart(
            grafico_npsh,
            use_container_width=True
        )


        # ----------------------------------------------------
        # BEP
        # ----------------------------------------------------

        indice_bep = np.argmax(
            eficiencia_fina
        )


        q_bep = (
            q_fino[
                indice_bep
            ]
        )


        eta_bep = (
            eficiencia_fina[
                indice_bep
            ]
        )


        h_bep = (
            h_bomba[
                indice_bep
            ]
        )


        npshr_bep = (
            npshr_fino[
                indice_bep
            ]
        )


        st.divider()

        st.subheader(
            "⭐ Punto de mejor eficiencia — BEP"
        )


        b1, b2, b3, b4 = (
            st.columns(4)
        )


        b1.metric(
            "Q en BEP",
            f"{q_bep:.2f} L/s"
        )


        b2.metric(
            "H en BEP",
            f"{h_bep:.2f} m"
        )


        b3.metric(
            "Rendimiento máximo",
            f"{eta_bep:.1f} %"
        )


        b4.metric(
            "NPSHr en BEP",
            f"{npshr_bep:.2f} m"
        )


        # ----------------------------------------------------
        # COMPARAR OPERACIÓN CON BEP
        # ----------------------------------------------------

        if (
            q_operacion
            is not None
            and q_bep > 0
        ):

            porcentaje_bep = (
                q_operacion
                / q_bep
                * 100
            )


            st.write(
                "El caudal de operación "
                "representa aproximadamente "
                f"**{porcentaje_bep:.1f} %** "
                "del caudal del BEP."
            )