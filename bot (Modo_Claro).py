import time
import threading
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
import pyttsx3
import os
import pygame
import tkinter as tk

# Inicializar Pygame y el motor de texto a voz
pygame.mixer.init()
engine = pyttsx3.init()

# Variable global para controlar el estado de text-to-speech
tts_enabled = False

# Diccionario para manejar el cooldown global de los comandos
cooldowns = {}  # {comando: tiempo_cooldown}
last_used_time = {}  # {comando: último tiempo usado}

# Función para cargar cooldowns desde un archivo
def load_cooldowns():
    try:
        with open("cooldown.txt", "r") as f:
            for line in f:
                command, time_cd = line.strip().split(",")
                time_cd = int(time_cd) * 60  # Convertir a segundos
                cooldowns[command] = time_cd
                last_used_time[command] = 0  # Inicializar el tiempo de uso
    except FileNotFoundError:
        print("El archivo cooldown.txt no se ha encontrado, se creará uno nuevo.")

# Función para guardar cooldowns en un archivo
def save_cooldowns():
    with open("cooldown.txt", "w") as f:
        for command, time_cd in cooldowns.items():
            f.write(f"{command},{time_cd // 60}\n")  # Guardar en minutos

# Conjunto para almacenar comentarios vistos
seen_comments = set()

# Crear archivo tiktokchannel.txt si no existe
def ensure_tiktokchannel_exists():
    filename = "tiktokchannel.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            file.write("tu_usuario_tiktok")  # Nombre de usuario de TikTok por defecto

# Obtener el nombre de usuario permitido desde el archivo tiktokchannel.txt
def get_allowed_user():
    ensure_tiktokchannel_exists()
    try:
        with open("tiktokchannel.txt", "r") as file:
            return file.read().strip().lower()
    except FileNotFoundError:
        print("El archivo tiktokchannel.txt no se ha encontrado.")
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
    root.title("TikTok Linker 2024 - By NirvanaRuns")
    root.geometry("600x800")  
    root.configure(bg="white")  

    # Crear el marco de chat
    chat_frame = tk.Frame(root, bg="white")  
    chat_frame.pack(expand=True, fill=tk.BOTH)

    # Título del chat
    chat_label = tk.Label(chat_frame, text="TikTok Chat", bg="white", font=("Arial Black", 12, "bold"))
    chat_label.pack(pady=10, padx=10, anchor="w")

    # Crear el widget de texto para mostrar el chat
    chat_display = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, bg="white", fg="black", font=("Arial Black", 12))
    chat_display.pack(expand=True, fill=tk.BOTH)

    # Crear una fila adicional en la parte inferior
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

    return root, chat_display, add_chat_message

# Función para alternar TTS
def toggle_tts(button):
    global tts_enabled
    tts_enabled = not tts_enabled
    button.config(text="Deshabilitar TTS" if tts_enabled else "Habilitar TTS", bg="lightcoral" if tts_enabled else "lightgreen")

# Función para verificar cooldown
def check_global_cooldown(command):
    current_time = time.time()
    if command in cooldowns:
        last_used = last_used_time.get(command, 0)
        cooldown_time = cooldowns[command]
        
        # Debugging para ver el tiempo transcurrido
        time_passed = current_time - last_used
        print(f"Tiempo desde último uso de {command}: {time_passed:.2f} segundos")
        
        if time_passed < cooldown_time:
            remaining_time = cooldown_time - time_passed
            remaining_minutes, remaining_seconds = divmod(remaining_time, 60)
            print(f"Cooldown activo para {command}. Faltan {int(remaining_minutes)} minutos y {int(remaining_seconds)} segundos")
            return False
    
    # Actualizar el tiempo de uso del comando
    last_used_time[command] = current_time
    print(f"Ejecutando comando {command}")
    return True

# Función para crear el archivo de comando
def create_command_file(command):
    directory = "sammicomandos"
    if not os.path.exists(directory):
        os.makedirs(directory)  # Crear el directorio si no existe
    filename = f"{directory}/{command[1:]}.txt"  # Eliminar el guion bajo
    with open(filename, 'w') as f:
        f.write(f"Comando {command} ejecutado.")  # Guardar información en el archivo
    print(f"Archivo creado: {filename}")

# Función para manejar el cliente de TikTok
def tiktok_client_thread(tiktok_client):
    tiktok_client.run()

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
        root, chat_display, add_chat_message_func = display_chat_window()

        @tiktok_client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            username = event.user.unique_id
            comment = event.comment

            # Mostrar el comentario completo en el chat, incluyendo comandos
            if comment.strip() and comment not in seen_comments:
                seen_comments.add(comment)
                add_chat_message_func(chat_display, (username, comment), nickname_color="red", text_color="black")

                # Procesar comandos (manejo de cooldown y ejecución)
                for word in comment.split():
                    if word.startswith("_"):
                        if check_global_cooldown(word):
                            create_command_file(word)  # Ejecutar el comando
                        else:
                            print(f"Cooldown activo para {word}")

                # Limpiar el comentario para TTS
                cleaned_comment = remove_commands_for_tts(comment)
                
                # Leer el comentario limpio con TTS si TTS está habilitado
                if tts_enabled and cleaned_comment.strip():
                    engine.say(cleaned_comment)
                    engine.runAndWait()

        client_thread = threading.Thread(target=tiktok_client_thread, args=(tiktok_client,))
        client_thread.daemon = True
        client_thread.start()

        root.mainloop()
    else:
        print("El archivo tiktokchannel.txt no se ha encontrado o está vacío.")

