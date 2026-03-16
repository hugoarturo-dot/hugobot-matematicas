import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import edge_tts
import asyncio
import tempfile
import os

# ---------------------------------------------------------
# 1. CONFIGURACIÓN VISUAL Y DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(page_title="HugoBot 2.0", page_icon="🤖", layout="wide")
st.title("🤖 HugoBot: Tu Tutor Inteligente de Matemáticas")
st.write("¡Hola! Soy HugoBot. Escribe, sube una foto o grábame un audio con tu duda.")

# ---------------------------------------------------------
# 2. BARRA LATERAL: SÚPER TECLADO, NIVELES Y SOSTENIBILIDAD
# ---------------------------------------------------------
with st.sidebar:
    st.header("🎓 Nivel Educativo")
    # Este selector cambiará la personalidad del bot
    nivel_seleccionado = st.selectbox(
        "¿En qué nivel te encuentras?",
        ["Primaria", "Secundaria", "Preparatoria", "Universidad"]
    )
    
    # Botón para limpiar el pizarrón (destrabar memoria)
    if st.button("🔄 Nueva Clase / Limpiar Chat", use_container_width=True):
        st.session_state.historial = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        st.rerun()
        
    st.divider()
    
    st.header("🧮 Súper Teclado Matemático")
    st.write("Copia (Ctrl+C) y pega (Ctrl+V) en el chat:")
    
    st.subheader("Aritmética y Conjuntos")
    st.code("+  -  ×  ÷  =  ≠  <  >  ≤  ≥  !  ∅  ∈  ⊆")
    
    st.subheader("Fracciones, Potencias y Raíces")
    st.code("½  ⅓  ¼  ²  ³  ^  √  ∛")
    
    st.subheader("Funciones y Logaritmos")
    st.code("sen()  cos()  tan()  csc()  sec()  cot()\nlog()  ln()  e^x")
    
    st.subheader("Cálculo y Álgebra")
    st.code("∫  ∂  ∑  ∏  lim  ∞  π  ±  ≈  |x|  f(x)")
    
    st.subheader("Lógica y Letras Griegas")
    st.code("∴  ∵  ∧  ∨  ⇒  ⇔\nα  β  γ  θ  λ  Δ  Σ  Ω")

    st.divider()
    
    # Mensaje Profesional de Donaciones
    st.subheader("🤝 Sostenibilidad del Proyecto")
    st.info(
        "Cada interacción, análisis de imagen y generación de voz tiene un costo de servidor. "
        "Imagina a cientos de alumnos realizando varias preguntas al día; son miles de cálculos "
        "matemáticos que actualmente procesamos y financiamos por nuestra cuenta para mantener "
        "este proyecto educativo gratuito.\n\n"
        "Si HugoBot está aportando valor a tu aprendizaje, multiplicar nuestro esfuerzo con una "
        "donación voluntaria nos ayuda enormemente a mantener el sistema vivo para todos."
    )
    # Reemplaza el enlace de abajo por tu link real de MercadoPago o PayPal
    st.link_button("☕ Realizar Donación Voluntaria", "https://link-de-tu-donacion.com", use_container_width=True)


# ---------------------------------------------------------
# 3. EL CEREBRO CAMALEÓN (PROMPTS DINÁMICOS)
# ---------------------------------------------------------
instrucciones_base = """
Eres HugoBot, un acompañante pedagógico estricto y experto en didáctica de las matemáticas, creado por el Profr. Hugo.
Regla 1: BAJO NINGUNA CIRCUNSTANCIA des la respuesta final directamente.
Regla 2: Usa Andamiaje Cognitivo (Scaffolding). Da pistas paso a paso para que el alumno descubra la respuesta.
Regla 3: Fomenta el Pensamiento Crítico pidiendo justificaciones.
Regla 4: Usa texto simple, claro y lineal para que la voz sintética lo lea perfecto.
"""

# Diccionario de personalidades según el nivel
personalidades = {
    "Primaria": "El alumno está en primaria. Usa un lenguaje sumamente cálido, tierno y paciente. Explica usando analogías cotidianas (dulces, juguetes, repartos simples). No uses tecnicismos.",
    "Secundaria": "El alumno está en secundaria. Usa un tono motivador. Explica los procedimientos paso a paso, fomenta el pensamiento lógico y conecta la matemática con la vida diaria.",
    "Preparatoria": "El alumno está en preparatoria/bachillerato. Exige el uso correcto del lenguaje algebraico y formal. Enfócate en la demostración de los resultados y prepáralo para la universidad.",
    "Universidad": "El alumno es de nivel universitario. Exige rigor matemático total y demostraciones formales. Asume que conoce la notación avanzada. Relaciona los conceptos con aplicaciones en ciencias o ingeniería."
}

instrucciones_finales = instrucciones_base + "\n\nCONTEXTO ACTUAL DEL ALUMNO: " + personalidades[nivel_seleccionado]


# ---------------------------------------------------------
# 4. MEMORIA, CONEXIÓN Y GENERADOR DE VOZ
# ---------------------------------------------------------
def generar_audio_masculino(texto):
    voz = "es-MX-JorgeNeural" 
    archivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    archivo_salida = archivo_temp.name
    archivo_temp.close()

    async def crear_mp3():
        comunicador = edge_tts.Communicate(texto, voz)
        await comunicador.save(archivo_salida)
        
    asyncio.run(crear_mp3())
    return archivo_salida

if "cliente_ia" not in st.session_state:
    TU_API_KEY = st.secrets["GEMINI_API_KEY"]
    st.session_state.cliente_ia = genai.Client(api_key=TU_API_KEY)

# Si el usuario cambia de nivel, forzamos a reiniciar el chat para cambiar el cerebro
if "nivel_actual" not in st.session_state:
    st.session_state.nivel_actual = nivel_seleccionado

if st.session_state.nivel_actual != nivel_seleccionado:
    st.session_state.nivel_actual = nivel_seleccionado
    if "chat_session" in st.session_state:
        del st.session_state["chat_session"]
    st.session_state.historial = []

if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.cliente_ia.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=instrucciones_finales,
            temperature=0.2
        )
    )
    st.session_state.historial = []

# ---------------------------------------------------------
# 5. ZONA DE ENTRADA MULTIMODAL (FOTOS Y MICRÓFONO)
# ---------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    imagen_subida = st.file_uploader("📸 1. Sube una foto de tu ejercicio:", type=["png", "jpg", "jpeg"])
with col2:
    audio_grabado = st.audio_input("🎙️ 2. O graba tu duda con el micrófono:")

# ---------------------------------------------------------
# 6. MOSTRAR EL HISTORIAL DEL CHAT
# ---------------------------------------------------------
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        if "imagen" in mensaje and mensaje["imagen"]:
            st.image(mensaje["imagen"], width=250)
        if "audio" in mensaje and mensaje["audio"]:
            st.audio(mensaje["audio"], format="audio/wav")
        if mensaje["texto"]:
            st.markdown(mensaje["texto"])

# ---------------------------------------------------------
# 7. CAJA DE TEXTO Y PROCESAMIENTO PRINCIPAL
# ---------------------------------------------------------
prompt_alumno = st.chat_input("📝 3. Escribe aquí o simplemente presiona Enter si ya subiste foto/audio...")

# Si el alumno escribe algo, O si mandó foto/audio y presionó Enter en la caja
if prompt_alumno or imagen_subida or audio_grabado:
    
    # Preparamos los contenedores para la memoria y para enviar a Gemini
    contenido_memoria = {"rol": "user", "texto": prompt_alumno, "imagen": None, "audio": None}
    contenido_a_enviar = []

    with st.chat_message("user"):
        # Procesar Imagen
        if imagen_subida:
            imagen_pil = Image.open(imagen_subida)
            st.image(imagen_pil, width=250)
            contenido_memoria["imagen"] = imagen_pil
            contenido_a_enviar.append(imagen_pil)
            
        # Procesar Audio
        if audio_grabado:
            st.audio(audio_grabado, format="audio/wav")
            contenido_memoria["audio"] = audio_grabado.getvalue()
            # Convertimos el audio al formato que entiende Gemini
            parte_audio = types.Part.from_bytes(data=audio_grabado.getvalue(), mime_type="audio/wav")
            contenido_a_enviar.append(parte_audio)
            
        # Procesar Texto
        if prompt_alumno:
            st.markdown(prompt_alumno)
            contenido_a_enviar.append(prompt_alumno)
            
        # Si por alguna razón mandó foto/audio pero no texto, le agregamos una instrucción invisible
        if not prompt_alumno:
            contenido_a_enviar.append("Por favor analiza la imagen o el audio que te acabo de enviar y guíame.")

        # Guardamos en la memoria visual
        st.session_state.historial.append(contenido_memoria)

    # Respuesta de HugoBot
    with st.chat_message("assistant"):
        try:
            # Enviamos el paquete completo (Texto + Foto + Audio) a Gemini
            respuesta = st.session_state.chat_session.send_message(contenido_a_enviar)
            
            st.markdown(respuesta.text)
            st.session_state.historial.append({"rol": "assistant", "texto": respuesta.text})
            
            # Generamos la voz
            with st.spinner('HugoBot está grabando su respuesta...'):
                archivo_audio = generar_audio_masculino(respuesta.text)
                st.audio(archivo_audio, format="audio/mp3")
                os.remove(archivo_audio)
                
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                st.warning("¡Uf! 😅 HugoBot está atendiendo a muchos alumnos al mismo tiempo. Por favor, respira, cuenta hasta 30 y vuelve a enviar tu mensaje.")
            else:
                st.error(f"Error técnico: {e}")
