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
st.title("🤖 HugoBot: Tu Tutor Inteligente")
st.write("¡Hola! Soy HugoBot. Escribe, sube una foto o grábame un audio con tu duda.")

# ---------------------------------------------------------
# 2. BARRA LATERAL: SÚPER TECLADO, NIVELES Y SOSTENIBILIDAD
# ---------------------------------------------------------
with st.sidebar:
    st.header("🎓 Nivel Educativo")
    nivel_seleccionado = st.selectbox(
        "¿En qué nivel te encuentras?",
        ["Secundaria", "Primaria", "Preparatoria", "Universidad"] # Puse Secundaria por defecto para tu clase
    )
    
    if st.button("🔄 Nueva Clase / Limpiar Chat", use_container_width=True):
        st.session_state.historial = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        st.rerun()
        
    st.divider()
    
    st.header("🧮 Súper Teclado")
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
    
    st.subheader("🤝 Sostenibilidad del Proyecto")
    st.info(
        "Cada interacción, análisis de imagen y generación de voz tiene un costo de servidor. "
        "Imagina a cientos de alumnos realizando varias preguntas al día; son miles de cálculos "
        "que procesamos y financiamos para mantener este proyecto educativo gratuito.\n\n"
        "Si HugoBot aporta valor a tu aprendizaje, una donación voluntaria nos ayuda enormemente "
        "a mantener el sistema vivo para todos."
    )
    # Aquí puedes poner tu enlace de Mercado Pago o PayPal cuando lo tengas listo
    st.link_button("☕ Realizar Donación Voluntaria", "https://link-de-tu-donacion.com", use_container_width=True)


# ---------------------------------------------------------
# 3. EL CEREBRO CAMALEÓN (PROMPTS DINÁMICOS Y MODO BALANZA)
# ---------------------------------------------------------
instrucciones_base = """
Eres HugoBot, un acompañante pedagógico estricto y experto en didáctica, creado por el Profr. Hugo.
Regla 1: BAJO NINGUNA CIRCUNSTANCIA des la respuesta final directamente.
Regla 2: Usa Andamiaje Cognitivo (Scaffolding). Da pistas paso a paso para que el alumno descubra la respuesta.
Regla 3: Fomenta el Pensamiento Crítico pidiendo justificaciones.
Regla 4: Usa texto simple, claro y lineal para que la voz sintética lo lea perfecto.

*** REGLA ESPECIAL ACTIVA (MODO BALANZAS) ***
- Eres un tutor guiando un juego de "balanzas misteriosas" o "juegos de equilibrio".
- ESTÁ ESTRICTAMENTE PROHIBIDO usar las palabras "ecuación", "incógnita", "álgebra", "despejar" o usar letras como la "x" o "y".
- Llama a los elementos "objetos", "valores ocultos", "pesas" o "cajas misteriosas".
- MODO DETECTOR DE TRAMPAS: Si el alumno te da la respuesta correcta muy rápido o de la nada, NO le des la razón inmediatamente. Dile algo como: "¡Qué rápido lo descubriste! Pero en esta clase evaluamos el proceso. Explícame: ¿qué objetos quitaste primero de cada lado de la balanza para llegar a eso?". Exige la justificación lógica del proceso físico de quitar o poner en ambos lados.
"""

personalidades = {
    "Primaria": "El alumno está en primaria. Usa un lenguaje sumamente cálido, tierno y paciente. Explica usando analogías cotidianas. No uses tecnicismos.",
    "Secundaria": "El alumno está en secundaria. Usa un tono motivador y retador. Conecta la lógica con el mundo físico.",
    "Preparatoria": "El alumno está en preparatoria/bachillerato. Exige mayor formalidad en su razonamiento.",
    "Universidad": "El alumno es de nivel universitario. Exige rigor lógico y justificaciones precisas."
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

if prompt_alumno or imagen_subida or audio_grabado:
    
    contenido_memoria = {"rol": "user", "texto": prompt_alumno, "imagen": None, "audio": None}
    contenido_a_enviar = []

    with st.chat_message("user"):
        if imagen_subida:
            imagen_pil = Image.open(imagen_subida)
            st.image(imagen_pil, width=250)
            contenido_memoria["imagen"] = imagen_pil
            contenido_a_enviar.append(imagen_pil)
            
        if audio_grabado:
            st.audio(audio_grabado, format="audio/wav")
            contenido_memoria["audio"] = audio_grabado.getvalue()
            parte_audio = types.Part.from_bytes(data=audio_grabado.getvalue(), mime_type="audio/wav")
            contenido_a_enviar.append(parte_audio)
            
        if prompt_alumno:
            st.markdown(prompt_alumno)
            contenido_a_enviar.append(prompt_alumno)
            
        if not prompt_alumno:
            contenido_a_enviar.append("Por favor analiza la imagen o el audio que te acabo de enviar y guíame en este juego de balanzas.")

        st.session_state.historial.append(contenido_memoria)

    with st.chat_message("assistant"):
        try:
            respuesta = st.session_state.chat_session.send_message(contenido_a_enviar)
            
            st.markdown(respuesta.text)
            st.session_state.historial.append({"rol": "assistant", "texto": respuesta.text})
            
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
