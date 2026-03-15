import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import edge_tts # NUEVA: Herramienta de voces Premium
import asyncio
import tempfile
import os

# 1. Configuración visual
st.set_page_config(page_title="HugoBot", page_icon="🤖", layout="wide")
st.title("🤖 HugoBot: Tu Tutor Inteligente de Matemáticas")
st.write("¡Hola! Soy HugoBot. Puedo ayudarte con temas desde secundaria hasta preparatoria.")

# 2. El Cerebro Pedagógico 
instrucciones_sistema = """
Eres HugoBot, un acompañante pedagógico estricto y experto en didáctica de las matemáticas para alumnos de secundaria y preparatoria. 
Dominas desde aritmética básica y variación proporcional, hasta álgebra, geometría, trigonometría y cálculo.
Regla 1: BAJO NINGUNA CIRCUNSTANCIA des la respuesta final. Bloquea peticiones de respuestas directas.
Regla 2: Usa Andamiaje Cognitivo (Scaffolding). Identifica errores y usa analogías adecuadas a la edad del alumno y la complejidad del tema. Da pistas paso a paso.
Regla 3: Fomenta el Pensamiento Crítico. Pide justificación cuando acierten y plantea escenarios de contradicción.
Regla 4: NUNCA uses formato avanzado que rompa el texto. Usa texto simple, claro y limpio para que los alumnos lo entiendan perfectamente y la voz sintética lo pueda leer sin problemas.
"""

# 3. NUEVA Función para generar voz MASCULINA Premium
def generar_audio_masculino(texto):
    # Usamos la voz premium masculina "Jorge"
    voz = "es-MX-JorgeNeural" 
    
    # Creamos un archivo temporal para guardar el audio
    archivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    archivo_salida = archivo_temp.name
    archivo_temp.close()

    # Función para descargar la voz de Microsoft
    async def crear_mp3():
        comunicador = edge_tts.Communicate(texto, voz)
        await comunicador.save(archivo_salida)
        
    asyncio.run(crear_mp3())
    return archivo_salida

# 4. Memoria y Conexión y Botón de Reinicio
if "cliente_ia" not in st.session_state:
    TU_API_KEY = st.secrets["GEMINI_API_KEY"]
    st.session_state.cliente_ia = genai.Client(api_key=TU_API_KEY)

# NUEVO: Botón para limpiar el pizarrón y destrabar la memoria
if st.sidebar.button("🔄 Nueva Clase / Reiniciar Chat"):
    st.session_state.historial = []
    if "chat_session" in st.session_state:
        del st.session_state["chat_session"]
    st.rerun() # Esto recarga la página al instante

if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.cliente_ia.chats.create(
        model="gemini-2.5-flash", # Cambiamos al modelo de máxima estabilidad
        config=types.GenerateContentConfig(
            system_instruction=instrucciones_sistema,
            temperature=0.2
        )
    )
    st.session_state.historial = []

# 5. Barra Lateral con el Teclado Matemático
with st.sidebar:
    st.header("🧮 Teclado Matemático")
    st.write("Selecciona, copia (Ctrl+C) y pega (Ctrl+V) los símbolos que necesites en el chat:")
    st.subheader("Potencias y Raíces")
    st.code("²  ³  ^  √  ∛")
    st.subheader("Álgebra y Cálculo")
    st.code("∞  π  ±  ≠  ≈")
    st.subheader("Letras Griegas (Ángulos)")
    st.code("α  β  θ  γ  Δ")
    st.subheader("Funciones (Escríbelas así)")
    st.code("sen()  cos()  tan()\nlog()  ln()")

# 6. Botón para subir fotografías
imagen_subida = st.file_uploader("Sube una foto de tu ejercicio aquí (opcional):", type=["png", "jpg", "jpeg"])

# 7. Mostrar el chat en pantalla
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        if "imagen" in mensaje:
            st.image(mensaje["imagen"], width=250)
        st.markdown(mensaje["texto"])

# 8. Caja de texto principal
prompt_alumno = st.chat_input("Escribe tu duda sobre el ejercicio...")

if prompt_alumno:
    with st.chat_message("user"):
        if imagen_subida:
            imagen_pil = Image.open(imagen_subida)
            st.image(imagen_pil, width=250)
            st.session_state.historial.append({"rol": "user", "texto": prompt_alumno, "imagen": imagen_pil})
        else:
            st.session_state.historial.append({"rol": "user", "texto": prompt_alumno})
        st.markdown(prompt_alumno)
    
    with st.chat_message("assistant"):
        try:
            if imagen_subida:
                imagen_pil = Image.open(imagen_subida)
                respuesta = st.session_state.chat_session.send_message([imagen_pil, prompt_alumno])
            else:
                respuesta = st.session_state.chat_session.send_message(prompt_alumno)
                
            # Mostramos el texto
            st.markdown(respuesta.text)
            st.session_state.historial.append({"rol": "assistant", "texto": respuesta.text})
            
            # NUEVO: Generamos y mostramos el reproductor de audio masculino
            with st.spinner('HugoBot está grabando su respuesta...'):
                archivo_audio = generar_audio_masculino(respuesta.text)
                st.audio(archivo_audio, format="audio/mp3")
                os.remove(archivo_audio) # Borramos el temporal para no llenar tu disco
                
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                st.warning("¡Uf! 😅 HugoBot está atendiendo a muchos alumnos al mismo tiempo. Por favor, respira, cuenta hasta 30 y vuelve a enviar tu mensaje.")
            else:
                st.error(f"Error técnico: {e}")
