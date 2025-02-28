import time
import threading
from TikTokLive import TikTokLiveClient
from TikTokLive.events import FollowEvent
from TikTokLive.events import CommentEvent
from PIL import Image
import io
import pyttsx3
import os
import pygame
import tkinter as tk
import urllib.request

# Establecer el ícono directamente desde la URL de GitHub
url = "https://raw.githubusercontent.com/Nirvanatistos/TikTokLinkerBeta/refs/heads/main/TikTok_Linker.ico"
filename = "TikTok_Linker.ico"
urllib.request.urlretrieve(url, filename)


# Variable global para directorio sammicomandos
directory = "sammicomandos"

# Variable global para controlar el estado del retraso
delay_active = True

# Variable global para almacenar el último seguidor
last_follower = ""

# Lee el último seguidor desde lastfollower.txt si existe
if os.path.exists("lastfollower.txt"):
    with open("lastfollower.txt", "r", encoding="utf-8") as file:
        last_follower = file.read().strip()  # Leer y quitar espacios en blanco

# Inicializar Pygame y el motor de texto a voz
pygame.mixer.init()
engine = pyttsx3.init()

# Variable global para controlar el estado de text-to-speech
tts_enabled = False
dark_mode = False  # Variable para manejar el modo oscuro

# Diccionario para manejar el cooldown global de los comandos
cooldowns = {}  # {comando: tiempo_cooldown}
last_used_time = {}  # {comando: último tiempo usado}

# Función para manejar el retraso inicial
def disable_delay():
    global delay_active
    time.sleep(3)
    delay_active = False

# Iniciar un hilo para manejar el retraso de 3 segundos
delay_thread = threading.Thread(target=disable_delay)
delay_thread.start()

# Función para cargar cooldowns desde un archivo
def load_cooldowns():
    try:
        with open("cooldown.txt", "r", encoding="utf-8") as f:
            for line in f:
                command, time_cd = line.strip().split(",")
                time_cd = int(time_cd) * 60  # Convertir a segundos
                cooldowns[command] = time_cd
                last_used_time[command] = 0  # Inicializar el tiempo de uso
    except FileNotFoundError:
        print("El archivo cooldown.txt no se ha encontrado, se creará uno nuevo.")

# Función para guardar cooldowns en un archivo
def save_cooldowns():
    with open("cooldown.txt", "w", encoding="utf-8") as f:
        for command, time_cd in cooldowns.items():
            f.write(f"{command},{time_cd // 60}\n")  # Guardar en minutos

# Conjunto para almacenar comentarios vistos
seen_comments = set()

# Crear archivo tiktokchannel.txt si no existe
def ensure_tiktokchannel_exists():
    filename = "tiktokchannel.txt"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as file:
            file.write("tu_usuario_tiktok")  # Nombre de usuario de TikTok por defecto

# Obtener el nombre de usuario permitido desde el archivo tiktokchannel.txt
def get_allowed_user():
    ensure_tiktokchannel_exists()
    try:
        with open("tiktokchannel.txt", "r", encoding="utf-8") as file:
            return file.read().strip().lower()
    except FileNotFoundError:
        print("El archivo tiktokchannel.txt no se ha encontrado. se creará uno nuevo. Recuerde insertar su usuario de tiktok con minúscula en él.")
        return None

# Función para agregar texto al widget de chat
def add_chat_message(chat_display, message, nickname_color, text_color):
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, f"{message[0]}: ", "nickname")  
    chat_display.insert(tk.END, f"{message[1]}\n", "comment")
    chat_display.tag_config("nickname", foreground=nickname_color)
    chat_display.tag_config("comment", foreground=text_color)
    chat_display.config(state=tk.DISABLED)
    chat_display.see(tk.END)

# Función para manejar el chat en Tkinter
def display_chat_window():
    root = tk.Tk()
    root.iconbitmap(filename)
    root.title("TikTok Linker 2025 - By NirvanaRuns")
    root.geometry("600x800")  
    root.configure(bg="white")  

    # Crear el marco de chat
    chat_frame = tk.Frame(root, bg="white")  
    chat_frame.pack(expand=True, fill=tk.BOTH)

    # Crear un marco para el título y el botón
    title_frame = tk.Frame(chat_frame, bg="white")
    title_frame.pack(fill=tk.X)

    # Título del chat
    chat_label = tk.Label(title_frame, text="TikTok Chat", bg="white", font=("Arial Black", 12, "bold"))
    chat_label.pack(side=tk.LEFT, padx=10, pady=10)

    # Crear el botón para alternar entre modo claro y oscuro
    slider_button = tk.Button(title_frame, text="🌙", bg="#BB86FC", command=lambda: toggle_mode(slider_button, root, chat_display, title_frame, chat_label, bottom_frame), borderwidth=0, font=("Arial", 14))
    slider_button.pack(side=tk.RIGHT, padx=10)  # Mover el botón a la derecha del título

    # Crear el widget de texto para mostrar el chat
    chat_display = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, bg="white", fg="black", font=("Arial Black", 12))
    chat_display.pack(expand=True, fill=tk.BOTH)

    bottom_frame = tk.Frame(root, bg="white")
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

    allowed_user = get_allowed_user()
    if allowed_user:
        connection_label = tk.Label(bottom_frame, text=f"Conectado a: {allowed_user}", bg="darkgreen", fg="white", font=("Arial Black", 8, "bold"))
        connection_label.pack(pady=10)

        # Crear el botón para habilitar/deshabilitar TTS
        tts_button = tk.Button(bottom_frame, text="Habilitar TTS", bg="lightgreen", font=("Arial Black", 8, "bold"),
                               command=lambda: toggle_tts(tts_button))
        tts_button.pack(side=tk.RIGHT, padx=10, pady=10)

    return root, chat_display, add_chat_message, tts_button

# Función para alternar el modo
def toggle_mode(button, root, chat_display, title_frame, chat_label, bottom_frame):
    global dark_mode
    dark_mode = not dark_mode
    if dark_mode:
        root.configure(bg="#121212")  # Fondo oscuro
        chat_display.configure(bg="#121212", fg="#FFFFFF")  # Texto blanco
        title_frame.configure(bg="#121212")  # Cambiar fondo del marco del título
        chat_label.configure(bg="#121212", fg="#FFFFFF")  # Cambiar color del título
        bottom_frame.configure(bg="#121212")  # Cambiar fondo del marco inferior
        chat_display.tag_config("nickname", foreground="yellow") # Cambiar nickname a amarillo
        chat_display.tag_config("comment", foreground="white") # Cambiar comentario a blanco
        button.config(bg="#FFFFFF", text="☀")  # Botón morado con sol
    else:
        root.configure(bg="white")  # Fondo claro
        chat_display.configure(bg="white", fg="black")  # Texto negro
        title_frame.configure(bg="white")  # Cambiar fondo del marco del título
        chat_label.configure(bg="white", fg="black")  # Cambiar color del título
        bottom_frame.configure(bg="white")  # Cambiar fondo del marco inferior
        chat_display.tag_config("nickname", foreground="red") # Cambia nickname a rojo
        chat_display.tag_config("comment", foreground="black") # Cambia comentario a negro
        button.config(bg="#BB86FC", text="🌙")  # Botón morado con luna

# Función para alternar TTS
def toggle_tts(button):
    global tts_enabled
    tts_enabled = not tts_enabled
    button.config(text="Deshabilitar TTS" if tts_enabled else "Habilitar TTS", bg="lightcoral" if tts_enabled else "lightgreen")

# Función para mostrar el estado "Cargando TTS"
def loading_tts(button):
    button.config(text="Cargando TTS", bg="lightgray")  # Cambiar el texto y el color
    time.sleep(3)  # Esperar 3 segundos
    button.config(text="Habilitar TTS", bg="lightgreen")  # Cambiar el texto del botón a "Habilitar TTS"
    button.config(state=tk.NORMAL)  # Habilitar el botón
    
# Función para verificar cooldown
def check_global_cooldown(command):
    current_time = time.time()
    if command in cooldowns:
        last_used = last_used_time.get(command, 0)
        cooldown_time = cooldowns[command]
        
        # Debugging para ver el tiempo transcurrido
        time_passed = current_time - last_used
        print(f"{command}: Ingresado a cooldown.")
        
        if time_passed < cooldown_time:
            remaining_time = cooldown_time - time_passed
            remaining_minutes, remaining_seconds = divmod(remaining_time, 60)
            print(f"Cooldown activo para {command}. Faltan {int(remaining_minutes)} minutos y {int(remaining_seconds)} segundos")
            return False
    
    # Actualizar el tiempo de uso del comando
    last_used_time[command] = current_time
    print(f"Ejecutando comando: {command}")
    return True

# Función para crear el archivo de comando
def create_command_file(command):
    global delay_active # Declara variable delay para espera de 5 segundos en la creación de archivos dentro de sammicomandos
    if delay_active: # Verifica si el retraso está activo
        return # No hace nada si el retraso está activo
    
    directory = "sammicomandos"
    if not os.path.exists(directory):
        os.makedirs(directory)  # Crear el directorio si no existe
    filename = f"{directory}/{command[1:]}.txt"  # Eliminar el guion bajo
    with open(filename, 'w', encoding="utf-8") as f:
        f.write(f"Comando {command} ejecutado.")  # Guardar información en el archivo
    print(f"Archivo creado: {filename}")
    
# Iniciar un hilo para manejar el retraso de 3 segundos
delay_thread = threading.Thread(target=disable_delay)
delay_thread.start()

# Función para manejar el cliente de TikTok
def tiktok_client_thread(tiktok_client):
    tiktok_client.run()
    root.update()  # Mantener la ventana actualizada

# Función de cierre
def on_closing():
    print("Cerrando el cliente de TikTok...")
    if hasattr(tiktok_client, "stop"):
        tiktok_client.stop()  # Asegúrate de detener el cliente de TikTok
    root.destroy()

# Función para eliminar comandos de un comentario para el TTS
def remove_commands_for_tts(comment):
    words = [word for word in comment.split() if not word.startswith("_")]  # Eliminar comandos que inician con "_"
    cleaned_comment = " ".join(words)
    return cleaned_comment

if __name__ == "__main__":
    load_cooldowns()  # Cargar los cooldowns al iniciar

    allowed_user = get_allowed_user()

    if allowed_user:
        tiktok_username = "@" + allowed_user
        tiktok_client = TikTokLiveClient(unique_id=tiktok_username)

        # Crear la ventana del chat
        root, chat_display, add_chat_message_func, tts_button = display_chat_window()
        
        # Deshabilitar el botón de TTS al inicio
        tts_button.config(state=tk.DISABLED)

        # Cargar TTS inicialmente
        loading_thread = threading.Thread(target=loading_tts, args=(tts_button,))
        loading_thread.start()  # Iniciar el hilo para mostrar "Cargando TTS"

        @tiktok_client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            username = event.user.unique_id
            comment = event.comment

            # Ajustar el color del apodo según el modo
            nickname_color = "red" if not dark_mode else "yellow"  # Ajustar el color del apodo según el modo
            text_color = "black" if not dark_mode else "white"  # Ajustar el color del texto según el modo
            
            # Mostrar el comentario completo en el chat, incluyendo comandos
            if comment.strip() and comment not in seen_comments:
                seen_comments.add(comment)
                add_chat_message_func(chat_display, (username, comment), nickname_color=nickname_color, text_color=text_color)

                # Procesar comandos (manejo de cooldown y ejecución)
                for word in comment.split():
                    if word.startswith("_"):
                        if not delay_active:
                            if check_global_cooldown(word):
                                create_command_file(word)  # Ejecutar el comando
                            else:
                                print(f"Cooldown activo actualmente para {word}")

                # Limpiar el comentario para TTS
                cleaned_comment = remove_commands_for_tts(comment)
                
                # Leer el comentario limpio con TTS si TTS está habilitado
                if tts_enabled and cleaned_comment.strip():
                    # Modificación aquí para incluir el nombre de usuario
                    tts_message = f"{username} dijo: {cleaned_comment}"
                    engine.say(tts_message)
                    engine.runAndWait()
                    
            @tiktok_client.on(FollowEvent)
            async def on_follow(event: FollowEvent):
                global last_follower  # Usamos una variable global para comparar
                nickname = event.user.nickname
                
                # Ruta al archivo de base de datos
                db_file = "lastfollowerdb.txt"
                
                # Verificar si lastfollower.db existe, y si no, crearlo
                if not os.path.exists(db_file):
                    with open(db_file, "w", encoding="utf-8") as file:
                        file.write("")  # Crear un archivo vacío si no existe
                        
                # Leer la base de datos y verificar si el usuario ya está registrado
                with open(db_file, "r", encoding="utf-8") as file:
                    registered_users = file.read().splitlines()  # Leer usuarios registrados línea por línea
                    
                if nickname not in registered_users:  # Solo proceder si el usuario no está en la base de datos
                    # Registrar el usuario en la base de datos
                    with open(db_file, "a", encoding="utf-8") as file:  # Modo 'append' para agregar al final
                        file.write(nickname + "\n")
                
                # Verificar si lastfollower.txt existe, y si no, crearlo
                if not os.path.exists("lastfollower.txt"):
                    with open("lastfollower.txt", "w", encoding="utf-8") as file:
                        file.write("")  # Crear un archivo vacío si no existe
                        
                # Comprobar si el nuevo seguidor es diferente al último
                if nickname != last_follower:
                # Guardar el nickname en lastfollower.txt
                    with open("lastfollower.txt", "w", encoding="utf-8") as file:
                        file.write(nickname)
                    file_path = os.path.join(directory, "lastfollower.txt")
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(nickname)
                    
                    # Descargar la imagen de perfil del seguidor
                    image_bytes: bytes = await tiktok_client.web.fetch_image(image=event.user.avatar_thumb)
                
                    # Convertir la imagen en un objeto PIL
                    image = Image.open(io.BytesIO(image_bytes))
                
                    # Redimensionar la imagen a 215x215 píxeles
                    image = image.resize((215, 215))
                
                    # Convertir y guardar la imagen como lastfollower.png
                    image.save("lastfollower.png", format="PNG")
                
                    # Actualizar el último seguidor
                    last_follower = nickname
                    
                    # Esperar 5 segundos y luego eliminar el archivo
                    def delete_file_after_delay():
                        time.sleep(5)  # Esperar 5 segundos
                        if os.path.exists(file_path):
                            os.remove(file_path)
                     
                    threading.Thread(target=delete_file_after_delay, daemon=True).start()
                
                else:
                    # Si es el mismo seguidor, no realizar las acciones de nuevo
                    pass  # Puedes usar 'pass' aquí si no hay más acciones necesarias

        client_thread = threading.Thread(target=tiktok_client_thread, args=(tiktok_client,))
        client_thread.daemon = True
        client_thread.start()

        root.mainloop()
    else:
        print("El archivo tiktokchannel.txt no se ha encontrado o está vacío.")
