from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr #libreria de calculo de matrizes
from ObjLoader import ObjLoader
import win32con
import win32gui
import win32api

#Speech
from OpenGL.GLU import *
from OpenGL.GLUT import *
import threading #permite paralelismo
from multiprocessing import Value #, Array
import os

import speech_recognition #voz a texto
import pyttsx3 #texto a voz
import pywhatkit #carga videos de youtube
import datetime, locale
import wikipedia
import subprocess #ejecuta programas de linea de comandos
import re #estandariza texto para eliminar los asentos
from unicodedata import normalize
import random
from pytube import Playlist
import pyautogui #envia teclado a aplicacion, en este caso para poner youtube en modo cine
import time #genera espera en algunos procesos para liberar procesador

from googletrans import Translator #pip install googletrans==3.1.0a0, para el traductor
from gtts import gTTS #de texto a voz para el traductor
from playsound import playsound #pip install playsound==1.2.2 , para reproducir la voz del traductor
import winsound #para producir el beep
import glfw #manejo de las ventanas

vertex_src = """
# version 330

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_texture;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 projection;
uniform mat4 view;

out vec2 v_texture;

void main()
{
    gl_Position = projection * view * model * vec4(a_position, 1.0);
    v_texture = a_texture;
}
"""

fragment_src = """
# version 330

in vec2 v_texture;

out vec4 out_color;
uniform vec4 color;

uniform sampler2D s_texture;

void main()
{
    //out_color = texture(s_texture, v_texture);
    out_color = color; //vec4(0.0, 1.0, 0.0, 1.0);
}
"""


# glfw callback functions
def window_resize(window, width, height):
    glViewport(0, 0, width, height)
    projection = pyrr.matrix44.create_perspective_projection_matrix(45, width / height, 0.1, 100)
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)

def make_Windows(width, height, title):
    # initializing glfw library
    if not glfw.init():
        raise Exception("glfw can not be initialized!")
        return
    
    # creating the window
    glfw.window_hint(glfw.DECORATED, glfw.FALSE) #Sin bordes
    #glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE) #Opcion de transparencia, bueno
    #glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE) #Sin bordes

    window = glfw.create_window(width, height, title, None, None)
    # check if window was created
    if not window:
        glfw.terminate()
        raise Exception("glfw window can not be created!")
        return

    # set window's position
    #glfw.set_window_pos(window, 400, 200)
    # set the callback function for window resize
    #glfw.set_window_size_callback(window, window_resize)

    # make the context current
    glfw.make_context_current(window)
    '''
    #https://www.glfw.org/docs/3.3/window_guide.html#window_icon
    GLFWimage images[2];
    images[0] = load_icon("my_icon.png");
    images[1] = load_icon("my_icon_small.png");

    glfwSetWindowIcon(window, 2, images);
    '''
    return window

def back_transparency(title, hwnd):
    ##### Genera fondo Transparante
    # https://stackoverflow.com/questions/550001/fully-transparent-windows-in-pygame/51845075#51845075
    fuchsia = (0, 128, 0)  # Transparency color
    # Create layered window
    #hwnd = win32gui.FindWindow(None, title) #Busca identificar la ventana
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    # Set window transparency color
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*fuchsia), 0, win32con.LWA_COLORKEY)
    #Dispone ventana sobre todo
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE)
    #https://stackoverflow.com/questions/59141094/python-return-for-another-function
    #Cambia formato del color a RGB
    fuchsia = (1 / 255 * fuchsia[0], 1 / 255 * fuchsia[1], 1 / 255 * fuchsia[2])
    #####
    return fuchsia

def draw():
      
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    rot_y = pyrr.Matrix44.from_y_rotation(0.8 * glfw.get_time())
    #                                                          nose, Y, Z
    Obj_pos = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 2, -16]))
    model = pyrr.matrix44.multiply(rot_y, Obj_pos)

    # draw the Obj character
    glBindVertexArray(VAO[0])

    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)

    #Dibuja objeto con relleno negro
    glUniform4fv(solid_color_loc, 1, pyrr.Vector4([0, 0, 0, 1]))
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glDrawArrays(GL_TRIANGLES, 0, len(obj_indices))
    
    #Dibuja objeto, solo lineas de color
    glUniform4fv(solid_color_loc, 1, pyrr.Vector4([mRed.value, mGreen.value, 0, 1]))
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, 0, len(obj_indices))   

def Make_VAO_VBO_EBO(obj_indices, obj_buffer ):
    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))
    # VAO and VBO
    VAO = glGenVertexArrays(2)
    VBO = glGenBuffers(2)
    EBO = glGenBuffers(1) ###

    # Obj VAO
    glBindVertexArray(VAO[0])
    # Obj Vertex Buffer Object
    glBindBuffer(GL_ARRAY_BUFFER, VBO[0])
    glBufferData(GL_ARRAY_BUFFER, obj_buffer.nbytes, obj_buffer, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO) ###
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, obj_indices.nbytes, obj_indices, GL_STATIC_DRAW) ###

    # Obj vertices
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, obj_buffer.itemsize * 8, ctypes.c_void_p(0))
    # Obj normals
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, obj_buffer.itemsize * 8, ctypes.c_void_p(20))
    glEnableVertexAttribArray(2)
    glUseProgram(shader)

    return shader, VAO

def ejecutaCadaHora():
    minuto = 0
    diHora = True
    while not(detener_hedy.value):
        tiempo_hora = int(time.strftime("%H",time.localtime()))
        tiempo_minutos = int(time.strftime("%M",time.localtime()))
        tiempo_segundos = int(time.strftime("%S",time.localtime()))
        tiempo = time.strftime("%H:%M:%S",time.localtime())   
        # Alarma cada hora
        if tiempo_minutos == minuto and diHora:
            diHora = False
            hora = datetime.datetime.now().strftime('%I:%M %p')
            talk('querido amo, para usted, son las ' + hora)
        
        if tiempo_minutos == minuto + 1:
            diHora = True

        time.sleep(3)   # 3 segundos.

''' 
***************************************
    Lits de Musica
***************************************
'''
def load_play_list():
    listas = [
        'https://www.youtube.com/playlist?list=PLTwcVto04J2E4anmLGQlf-BStyP1skBaW',
        'https://www.youtube.com/playlist?list=PLTwcVto04J2GbAWod-E76qedXGq71SOFm',
        'https://www.youtube.com/playlist?list=PLTwcVto04J2Fce6C5_7iBUdqO70LOaF-O'
    ]
    for lista in listas:
        pl =  Playlist(lista)
        print(lista + " Video: " + str(len(pl)))
        for url in pl.videos:
            #print(url.title)
            videos.append(url.watch_url)
            titulos.append(url.title)    
    return None

def talk(text):
    engine.say(text)
    engine.runAndWait()

def listenCommand():
    listener = speech_recognition.Recognizer()
    with speech_recognition.Microphone() as source:
        print("Escuchando...")
        #Cambia el color a verde
        mRed.value = 0.0
        mGreen.value = 0.8

        listener.pause_threshold = 1
        listener.energy_threshold = 300
        listener.adjust_for_ambient_noise(source) ###
        voice = listener.listen(source, phrase_time_limit=6)
        #Cambia el color a rojo
        mRed.value = 1.0
        mGreen.value = 0.0
    try:
        query = listener.recognize_google(voice, language="es-US")
    except Exception as e:
        print('no entiendo')
        return "None"
    return query

def hedy():
    hour = int(datetime.datetime.now().hour)
    if hour>=0 and hour<12:
        saludo = 'Buenos dias'
    elif hour>=12 and hour<19:
        saludo = 'Buenas tardes'
    else:
        saludo = 'Buenas noches'
    talk(saludo)

    while not(detener_hedy.value):
        rec = listenCommand()
        rec = rec.lower()
        #entiendo.value = rec.encode("utf-8")
        print('Lo que entiendo: ' + rec)

        if yourName in rec:
            winsound.Beep(2000, 100)
            rec = rec.replace(yourName, '')
            cmdOriginal = rec #Se usa para el traductor

            # -> NFD y eliminar diacríticos
            rec = re.sub(r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", normalize( "NFD", rec), 0, re.I)
            # -> NFC
            rec = normalize( 'NFC', rec)

            #Comandos
            if 'reproduce' in rec:
                music = rec.replace('reproduce', '')
                ##print('music: ' + music)
                pywhatkit.playonyt(music)
                talk('reproduciendo ' + music)
            if 'mi ip' in rec:
                ip = get('https://api.ipify.org/').text
                talk('tu ip publica es ' + ip)
            elif 'traduce' in rec: #validar cuando el texto es vacio
                rec = cmdOriginal.replace('traduce','').strip()
                translator = Translator() #Translator(service_urls=['translate.googleapis.com'])
                ##print('traduciendo: ' + rec)
                text_to_translate = translator.translate(rec, src = "es", dest="en",)
                text = text_to_translate.text
                try:
                    os.remove("voice.mp3")
                    speakgl = gTTS(text=text, lang="en", slow=True)
                    speakgl.save("voice.mp3")
                    talk(rec + " en ingles se dice")
                    playsound("voice.mp3")
                except:
                    talk("Lo siento, no puedo traducir este texto.")
            elif 'repite' in rec:
                #Repite la ultima traduccion
                playsound("voice.mp3")
            elif 'pon musica' in rec:
                talk('estoy preparando la musica')
                ##print("cantidad de videos: " + str(len(videos)))
                indice = random.randint(0,len(videos)-1)

                #"C:\Program Files\VideoLAN\VLC\vlc.exe" :network-caching=1000M https://www.youtube.com/watch?v=8C6xDjQ66wM
                comando = "start chrome.exe /incognito --disable-accelerated-video --disable-gpu --disable-plugins --disable-extensions --disable-translate --app=\"data:text/html,<html><body><script>window.moveTo(580,240);window.resizeTo(800,600);window.location='-AquiVideo-';</script></body></html>\""
                comando = comando.replace('-AquiVideo-',videos[indice])

                subprocess.call(comando, shell=True)
                time.sleep(3)

                talk('reproduciendo ' + titulos[indice])
                pyautogui.press("t")
            elif 'estas ahi' in rec:
                minimizado.value = False
                hwnd = win32gui.FindWindow(None, title)  # Busca identificar la ventana
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                talk('aqui estoy')
            elif 'minimiza' in rec:
                talk('Minimizando')
                hwnd = win32gui.FindWindow(None, title)  # Busca identificar la ventana
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                minimizado.value = True
            elif 'abre' in rec:
                sites={
                    'google':'google.com',
                    'youtube':'youtube.com',
                    'whatsap':'whatsapp.com'
                }
                for i in list(sites.keys()):
                    if i in rec:
                        talk(f'abriendo {i}')
                        subprocess.call(f'start chrome.exe {sites[i]}', shell=True)
            elif 'hora es' in rec:
                hora = datetime.datetime.now().strftime('%I:%M %p')
                talk('son las ' + hora)
            elif 'es hoy' in rec:
                fecha = datetime.datetime.now().strftime("%A %d %B %Y")
                ##print(fecha)
                talk('hoy es ' + fecha)
            elif 'que es' in rec:
                order = rec.replace('que es', '')
                wikipedia.set_lang("es")
                info = wikipedia.summary(order, 1)
                ##print('wiki: ' + info)
                talk(info)
            elif 'apagate' in rec:
                talk('hasta la vista beibi')
                detener_hedy.value = True
            else:
                talk('disculpa, no entiendo lo que dices')

    talk('terminé')


if __name__ == '__main__':

    title = "Hedy Lamarr"
    window = make_Windows(200, 200, title)
    hwnd = win32gui.FindWindow(None, title) #Busca identificar la ventana
    fuchsia = back_transparency(title, hwnd)
    
    glClearColor(fuchsia[0], fuchsia[1], fuchsia[2], 0.0) # Define el color transparente como fondo
    obj_indices, obj_buffer = ObjLoader.load_model("hedy.obj", sorted=True) # load here the 3d meshes
    shader, VAO = Make_VAO_VBO_EBO(obj_indices, obj_buffer) #Rutina para cargar graficos en la GPU  

    projection = pyrr.matrix44.create_perspective_projection_matrix(45, 1.0, 0.1, 100)
    view = pyrr.matrix44.create_look_at(pyrr.Vector3([0, 0, 8]), pyrr.Vector3([0, 0, 0]), pyrr.Vector3([0, 1, 0])) # eye, target, up

    model_loc = glGetUniformLocation(shader, "model")
    proj_loc = glGetUniformLocation(shader, "projection")
    view_loc = glGetUniformLocation(shader, "view")

    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
    
    #Cambia el color de lineas
    solid_color_loc = glGetUniformLocation(shader, "color")
    glUniform4fv(solid_color_loc, 1, pyrr.Vector4([1, 0, 0, 1]))

    glEnable(GL_DEPTH_TEST) # No dibuja las caras traseras, deja de ser transparente
    
    #minimizado = False
    minimizado = Value('i', False)
    '''
    *** Sub Proceso que carga lista de musica
    '''
    videos = []
    titulos = []
    v = threading.Thread(target=load_play_list)
    v.start() 

    yourName = 'siri'
    locale.setlocale(locale.LC_ALL, "es-ES")
    
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', 170) #rate-30)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', volume+1)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[2].id)

    #Color para las lineas del objeto entre procesos
    mRed   = Value('d', 1.0)
    mGreen = Value('d', 0.0)

    ## Sub Proceso que escucha los comandos
    detener_hedy = Value('i', False)
    h = threading.Thread(target=hedy)
    h.start()

    ## Sub Proceso que dice la hora, cada hora
    t = threading.Thread(target=ejecutaCadaHora)
    t.start()

    winMovida = False
    #*********************************************
    # the main application loop
    #*********************************************
    while  h.is_alive():
        if glfw.window_should_close(window):
            detener_hedy.value = True

        if not(minimizado.value):
            glfw.poll_events() 
            draw()
            glfw.swap_buffers(window)
            #detecta si mouse esta sobre ventana para moverla
            x, y = pyautogui.position()
            if x >=0 and x <= 200 and y >= 0 and y <= 200 :
                if not winMovida :
                    hwnd = win32gui.FindWindow(None, title)
                    win32gui.MoveWindow(hwnd, 200, 0, 200, 200, True)
                    winMovida = True
            else:
                if winMovida:
                    hwnd = win32gui.FindWindow(None, title)
                    win32gui.MoveWindow(hwnd, 0, 0, 200, 200, True)
                    winMovida = False            
        ##else:
            ##time.sleep(0.05)

    # terminate glfw, free up allocated resources
    glfw.terminate()

    #pip freeze
    #pyinstaller --windowed --onefile --icon=./hedy.ico hedy3.py
