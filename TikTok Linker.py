import time
import threading
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
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
url = "https://raw.githubusercontent.com/Nirvanatistos/TikTokLinkerBeta/refs/heads/main/TikTok_Linker.ico  "
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
dark_mode = True  # Variable para manejar el modo oscuro

# Diccionario para manejar el uso de comandos: {comando: [conteo, último_tiempo_reset]}
command_usage = {}

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

# Función para crear el archivo de comando
def create_command_file(command):
    global delay_active  # Declara variable delay para espera de 5 segundos en la creación de archivos dentro de sammicomandos
    if delay_active:  # Verifica si el retraso está activo
        return  # No hace nada si el retraso está activo
    if not os.path.exists(directory):
        os.makedirs(directory)  # Crear el directorio si no existe
    filename = f"{directory}/{command[1:]}.txt"  # Eliminar el guion bajo
    with open(filename, 'w', encoding="utf-8") as f:
        f.write(f"Comando {command} ejecutado.")  # Guardar información en el archivo
    print(f"Archivo creado: {filename}")

# Función para manejar el retraso inicial
def disable_delay():
    global delay_active
    time.sleep(3)
    delay_active = False

# Iniciar un hilo para manejar el retraso de 3 segundos
delay_thread = threading.Thread(target=disable_delay)
delay_thread.start()

# Función para crear comandos.txt si no existe
def ensure_comandos_file_exists():
    if not os.path.exists("comandos.txt"):
        with open("comandos.txt", "w", encoding="utf-8") as f:
            f.write("# Formato: _comando,max_usos,cooldown_minutos\n")
            f.write("# Ejemplo: _desaparece,3,5  -> 3 veces cada 5 minutos\n")
            f.write("# Ejemplo 2: _krool,-1,-1 -> hará que el comando no tenga límite de tiempo ni cant. de veces a ejecutar.\n")
        print("Se ha creado comandos.txt. Agrega tus comandos permitidos.")

# Diccionario para almacenar la configuración de comandos: { "_comando": (max_usos, cooldown_segundos) }
allowed_commands = {}

# Cargar comandos desde comandos.txt
def load_allowed_commands():
    global allowed_commands
    allowed_commands.clear()
    try:
        with open("comandos.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue  # Saltar comentarios y líneas vacías
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                command, max_uses, cooldown_minutes = parts
                command = command.strip()
                try:
                    max_uses = int(max_uses)
                    cooldown_minutes = int(cooldown_minutes)
                    allowed_commands[command] = (max_uses, cooldown_minutes * 60)  # En segundos
                except ValueError:
                    print(f"Línea inválida en comandos.txt: {line}")
    except Exception as e:
        print(f"Error al cargar comandos.txt: {e}")

# Función para verificar si se puede ejecutar un comando
def check_global_cooldown(command):
    global command_usage
    current_time = time.time()

    if command not in allowed_commands:
        return False

    max_uses, cooldown_seconds = allowed_commands[command]

    # Caso especial: -1,-1 → ilimitado
    if max_uses == -1 and cooldown_seconds == -1:
        print(f"Ejecutando comando ilimitado: {command}")
        return True

    # Si el comando no se ha usado aún, inicializar
    if command not in command_usage:
        command_usage[command] = [1, current_time]
        print(f"Ejecutando comando: {command} (1/{max_uses}) - Quedan {max_uses - 1} usos")
        return True

    count, last_used = command_usage[command]

    # Si pasó el cooldown, reiniciar el contador
    if current_time - last_used >= cooldown_seconds:
        command_usage[command] = [1, current_time]
        print(f"Ejecutando comando: {command} (1/{max_uses}) - Cooldown reiniciado. Quedan {max_uses - 1} usos")
        return True

    # Si aún hay usos disponibles
    if count < max_uses:
        new_count = count + 1
        command_usage[command][0] = new_count
        remaining_uses = max_uses - new_count
        if remaining_uses > 0:
            print(f"Ejecutando comando: {command} ({new_count}/{max_uses}) - Quedan {remaining_uses} usos")
        else:
            print(f"Ejecutando comando: {command} ({new_count}/{max_uses}) - Último uso antes del cooldown")
        return True

    # Sin usos disponibles
    remaining = int((cooldown_seconds - (current_time - last_used)) // 60)
    seconds = int((cooldown_seconds - (current_time - last_used)) % 60)
    print(f"Cooldown activo para {command}. Para usar de nuevo el comando deben esperar {remaining}m {seconds}s")
    return False

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
    root.title("TikTok Linker Version 2.0 - por NirvanaRuns")
    root.geometry("600x800")

    # Crear el marco de chat
    chat_frame = tk.Frame(root)
    chat_frame.pack(expand=True, fill=tk.BOTH)

    # Crear un marco para el título y el botón
    title_frame = tk.Frame(chat_frame)
    title_frame.pack(fill=tk.X)

    # Título del chat
    chat_label = tk.Label(title_frame, text="TikTok Chat", font=("Arial Black", 12, "bold"))
    chat_label.pack(side=tk.LEFT, padx=10, pady=10)

    # Crear el botón para alternar entre modo claro y oscuro
    slider_button = tk.Button(title_frame, text="🌙", bg="#BB86FC", command=lambda: toggle_mode(slider_button, root, chat_display, title_frame, chat_label, bottom_frame), borderwidth=0, font=("Arial", 14))
    slider_button.pack(side=tk.RIGHT, padx=10)

    # Crear el widget de texto para mostrar el chat
    chat_display = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Arial Black", 12))
    chat_display.pack(expand=True, fill=tk.BOTH)

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Aplicar modo oscuro por defecto si dark_mode es True
    if dark_mode:
        root.configure(bg="#121212")
        chat_display.configure(bg="#121212", fg="#FFFFFF")
        title_frame.configure(bg="#121212")
        chat_label.configure(bg="#121212", fg="#FFFFFF")
        bottom_frame.configure(bg="#121212")
        chat_display.tag_config("nickname", foreground="yellow")
        chat_display.tag_config("comment", foreground="white")
        slider_button.config(bg="#FFFFFF", text="☀")
    else:
        root.configure(bg="white")
        chat_display.configure(bg="white", fg="black")
        title_frame.configure(bg="white")
        chat_label.configure(bg="white", fg="black")
        bottom_frame.configure(bg="white")
        chat_display.tag_config("nickname", foreground="red")
        chat_display.tag_config("comment", foreground="black")
        slider_button.config(bg="#BB86FC", text="🌙")

    # Configuración del canal y botón TTS
    allowed_user = get_allowed_user()
    if allowed_user:
        connection_label = tk.Label(bottom_frame, text=f"Conectado a: {allowed_user}", bg="darkgreen", fg="white", font=("Arial Black", 8, "bold"))
        connection_label.pack(pady=10)
        tts_button = tk.Button(bottom_frame, text="Habilitar TTS", bg="lightgreen", font=("Arial Black", 8, "bold"),
                               command=lambda: toggle_tts(tts_button))
        tts_button.pack(side=tk.RIGHT, padx=10, pady=10)
    else:
        tts_button = None

    return root, chat_display, add_chat_message, tts_button

# Función para alternar el modo
def toggle_mode(button, root, chat_display, title_frame, chat_label, bottom_frame):
    global dark_mode
    dark_mode = not dark_mode
    if dark_mode:
        root.configure(bg="#121212")
        chat_display.configure(bg="#121212", fg="#FFFFFF")
        title_frame.configure(bg="#121212")
        chat_label.configure(bg="#121212", fg="#FFFFFF")
        bottom_frame.configure(bg="#121212")
        chat_display.tag_config("nickname", foreground="yellow")
        chat_display.tag_config("comment", foreground="white")
        button.config(bg="#FFFFFF", text="☀")
    else:
        root.configure(bg="white")
        chat_display.configure(bg="white", fg="black")
        title_frame.configure(bg="white")
        chat_label.configure(bg="white", fg="black")
        bottom_frame.configure(bg="white")
        chat_display.tag_config("nickname", foreground="red")
        chat_display.tag_config("comment", foreground="black")
        button.config(bg="#BB86FC", text="🌙")

# Función para alternar TTS
def toggle_tts(button):
    global tts_enabled
    tts_enabled = not tts_enabled
    button.config(text="🔇 TTS" if tts_enabled else "🔊 TTS", bg="lightcoral" if tts_enabled else "lightgreen")

# Función para mostrar el estado "Cargando TTS"
def loading_tts(button):
    button.config(text="Cargando", bg="lightgray")
    time.sleep(3)
    button.config(text="🔊 TTS", bg="lightgreen")
    button.config(state=tk.NORMAL)

# Función para eliminar comandos de un comentario para el TTS
def remove_commands_for_tts(comment):
    words = [word for word in comment.split() if not word.startswith("_")]
    cleaned_comment = " ".join(words)
    return cleaned_comment

# Función para manejar el cliente de TikTok
def tiktok_client_thread(tiktok_client):
    tiktok_client.run()
    root.update()

# Función de cierre
def on_closing():
    print("Cerrando el cliente de TikTok...")
    if hasattr(tiktok_client, "stop"):
        tiktok_client.stop()
    root.destroy()

if __name__ == "__main__":
    # ✅ Cargar comandos permitidos desde comandos.txt
    ensure_comandos_file_exists()
    load_allowed_commands()

    allowed_user = get_allowed_user()
    if allowed_user:
        tiktok_username = "@" + allowed_user
        tiktok_client = TikTokLiveClient(unique_id=tiktok_username)

        # Crear la ventana del chat
        root, chat_display, add_chat_message_func, tts_button = display_chat_window()

        # Deshabilitar el botón de TTS al inicio
        if tts_button:
            tts_button.config(state=tk.DISABLED)
            # Cargar TTS inicialmente
            loading_thread = threading.Thread(target=loading_tts, args=(tts_button,))
            loading_thread.start()

        @tiktok_client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            username = event.user.unique_id
            comment = event.comment
            # Ajustar el color del apodo según el modo
            nickname_color = "red" if not dark_mode else "yellow"
            text_color = "black" if not dark_mode else "white"
            # Mostrar el comentario completo en el chat, incluyendo comandos
            if comment.strip() and comment not in seen_comments:
                seen_comments.add(comment)
                add_chat_message_func(chat_display, (username, comment), nickname_color=nickname_color, text_color=text_color)
                # Procesar comandos
                for word in comment.split():
                    if word.startswith("_"):
                        if not delay_active:
                            if word in allowed_commands:
                                if check_global_cooldown(word):
                                    create_command_file(word)
                                else:
                                    print(f"Cooldown activo actualmente para {word}")
                            else:
                                print(f"Comando no permitido (no está en comandos.txt): {word}")
                # Limpiar el comentario para TTS
                cleaned_comment = remove_commands_for_tts(comment)
                # Leer el comentario limpio con TTS si TTS está habilitado
                if tts_enabled and cleaned_comment.strip():
                    tts_message = f"{username} dijo: {cleaned_comment}"
                    engine.say(tts_message)
                    engine.runAndWait()

        @tiktok_client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            global last_follower
            nickname = event.user.nickname
            # Ruta al archivo de base de datos
            db_file = "lastfollowerdb.txt"
            # Verificar si lastfollower.db existe, y si no, crearlo
            if not os.path.exists(db_file):
                with open(db_file, "w", encoding="utf-8") as file:
                    file.write("")
            # Leer la base de datos y verificar si el usuario ya está registrado
            with open(db_file, "r", encoding="utf-8") as file:
                registered_users = file.read().splitlines()
            if nickname not in registered_users:
                # Registrar el usuario en la base de datos
                with open(db_file, "a", encoding="utf-8") as file:
                    file.write(nickname + "\n")
            # Verificar si lastfollower.txt existe, y si no, crearlo
            if not os.path.exists("lastfollower.txt"):
                with open("lastfollower.txt", "w", encoding="utf-8") as file:
                    file.write("")
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
                # Guardar copia numerada en sammicomandos/assets/img_users/
                img_dir = os.path.join("sammicomandos", "assets", "img_users")
                os.makedirs(img_dir, exist_ok=True)  # Asegurar que la carpeta existe

                # Listar archivos .jpg y extraer números
                existing_files = [
                    f for f in os.listdir(img_dir)
                    if f.endswith(".jpg") and f[:-4].isdigit()
                ]
                if existing_files:
                    numbers = [int(f[:-4]) for f in existing_files]
                    next_number = max(numbers) + 1
                else:
                    next_number = 1  # Si no hay imágenes, empezar en 1

                # Guardar nueva imagen como XX.jpg
                new_filename = f"{next_number}.jpg"
                new_filepath = os.path.join(img_dir, new_filename)
                image.convert("RGB").save(new_filepath, "JPEG", quality=95)  # Convertir a JPG

                print(f"Avatar guardado como {new_filename} en {img_dir}")

                # Actualizar el último seguidor
                last_follower = nickname
                # Esperar 5 segundos y luego eliminar el archivo
                def delete_file_after_delay():
                    time.sleep(5)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                threading.Thread(target=delete_file_after_delay, daemon=True).start()
            else:
                pass  # Si es el mismo seguidor, no realizar las acciones de nuevo

        # Iniciar el cliente de TikTok en un hilo
        client_thread = threading.Thread(target=tiktok_client_thread, args=(tiktok_client,))
        client_thread.daemon = True
        client_thread.start()

        # Manejar cierre de ventana
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    else:
        print("El archivo tiktokchannel.txt no se ha encontrado o está vacío.")
