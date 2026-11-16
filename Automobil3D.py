import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import customtkinter as ctk
from customtkinter import CTkLabel
import os
import sqlite3
from tkinter import messagebox
import json
from datetime import datetime
import math


NAME_DB = "auto_db.db"
MUSIC_FOLDER = "music"
JSON_NAME = "autos_settings.json"
ACHIVEMENTS = ["Обьехать 30 машин за 1 минуту","Обьехать 20 машин на скорости более 20км/ч","Обьехать 35 машин за 30 сек",
               "Продержаться на максимальной скорости 30 сек","Не тормозить 1 минуту","Не тормозить и не бросать газ 20 сек"]
WIDTH,HEIGHT = 1550,1000
RAIN_COUNT = 800
SNOW_COUNT = 500
MECHANICK_LIMIT = 0
CURRENT_PER = 0
SELECTED_SPEED = 0
DAYS = 4
CURRENT_DAY = 0
dorogaY = 4.7
dorogaX = 1.5
dorogaW = 1.0
speed_to_kmh = 0
last_day_change = 0
passed_count = 0
seconds = 0
time = 4
camera_z = 10
camera_x = -2
camera_y = -5
speed = 0
autos = []
road_segments = [[0, -200]]
snowdrops = []  # список капель: каждый элемент = [x, y, length, speed]
raindrops = []  # список капель: каждый элемент = [x, y, length, speed]
lr_colors = [(0, 0, 205),(0, 100, 0),(178, 34, 34),(255, 218, 185),(25, 25, 112),(255, 0, 255),
             (75, 0, 130),(205, 133, 63)]
pered_colors = [(70, 130, 180),(173, 255, 47),(255, 69, 0),(255, 239, 213),(0, 0, 139),(186, 85, 211),
                (72, 61, 139),(218, 165, 32)]
world_settings = {"sky":(),"ground":(),"road":(),"stars":False,"rain":False,"snow":False,"is_dark":False,
                  'music_in_back':False,"changed_days":False,"cars":True,"mode":"Карьера","korobka_p":"",
                  "speedometr_type":"","mx_speed":0,"max_speed_value":0}
game_start_ticks = None
game_over = False
start = False
running = True
mes = ""
stars = [(random.uniform(-500, WIDTH), random.uniform(5, 500)) for _ in range(300)]
playlist = [f"{MUSIC_FOLDER}/mus1.mp3", f"{MUSIC_FOLDER}/mus2.mp3", f"{MUSIC_FOLDER}/mus3.mp3",f"{MUSIC_FOLDER}/mus4.mp3",
            f"{MUSIC_FOLDER}/mus5.mp3",f'{MUSIC_FOLDER}/mus6.mp3',f'{MUSIC_FOLDER}/mus7.mp3']
current_track_index = 0
music_volume = 0.5
sounds = {}
engine_volume = 0

pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)
start_channel = pygame.mixer.Channel(0)
engine_channel = pygame.mixer.Channel(1)
brake_channel = pygame.mixer.Channel(2)
reverse_channel = pygame.mixer.Channel(3)
rain_channel = pygame.mixer.Channel(4)
transmisson_channel = pygame.mixer.Channel(5)

def logging(data):
    timestamp = datetime.now().strftime('%d_%m_%Y_%H:%M:%S')

    if os.path.exists("auto_log.txt"):
        with open('auto.txt',"a",encoding='utf-8') as f:
            f.write(f"{timestamp} - {data}\n")
    else:
        with open('auto.txt',"w",encoding='utf-8') as f:
            f.write(f"{timestamp} - {data}\n")
def normalize_color(c):
    return tuple([x / 255 for x in c])
days = [{"sky":normalize_color((255, 182, 193)),"ground":normalize_color((50, 205, 50)),"road":normalize_color((169, 169, 169))},
        {"sky":normalize_color((0, 191, 255)),"ground":normalize_color((154, 205, 50)),"road":normalize_color((128, 128, 128))},
        {"sky":(0.4, 0.7, 1.0),"ground":(0, 0.6, 0),"road":(0.3, 0.3, 0.3)},
        {"sky":normalize_color((255, 178, 102)),"ground":normalize_color((107, 142, 35)),"road":normalize_color((128, 128, 128))},
        {"sky":normalize_color((252, 94, 83)),"ground":normalize_color((85, 107, 47)),"road":normalize_color((105, 105, 105))},
        {"sky":normalize_color((135, 150, 235)),"ground":normalize_color((85, 107, 47)),"road":normalize_color((105, 105, 105))},
        {"sky":normalize_color((0, 0, 128)),"ground":normalize_color((0, 100, 0)),"road":(0,0,0)},
        {"sky":normalize_color((0, 0, 70)),"ground":normalize_color((0, 100, 0)),"road":(0,0,0)}]
def main_func(name,score):
    def save_score(name, score):
        global NAME_DB
        conn = sqlite3.connect(NAME_DB)
        cursor = conn.cursor()
        row = cursor.execute("SELECT name,score FROM users WHERE name = ?", (name,)).fetchone()
        if row:
            if int(row[1]) < score:
                cursor.execute("UPDATE users SET score = ? WHERE name = ?", (score, name))
        else:
            cursor.execute("INSERT INTO users(name,score) VALUES(?,?)", (name, score))
        conn.commit()
    def init_snow():
        global snowdrops
        snowdrops = []
        for _ in range(SNOW_COUNT):
            x = random.uniform(0, WIDTH)
            y = random.uniform(0, HEIGHT)
            length = random.uniform(8, 20)
            speed = random.uniform(300, 600)
            snowdrops.append([x, y, length, speed])
    def init_rain():
        global raindrops
        raindrops = []
        for _ in range(RAIN_COUNT):
            x = random.uniform(0, WIDTH)
            y = random.uniform(0, HEIGHT)
            length = random.uniform(8, 20)
            speed = random.uniform(300, 600)
            raindrops.append([x, y, length, speed])
    def update_snow(dt):
        global snowdrops
        for i in range(len(snowdrops)):
            x, y, length, speed = snowdrops[i]
            y += speed * dt
            if y > HEIGHT:  # если вышла за экран → респавн сверху
                x = random.uniform(0, WIDTH)
                y = -length
            snowdrops[i] = [x, y, length, speed]
    def update_rain(dt):
        global raindrops
        for i in range(len(raindrops)):
            x, y, length, speed = raindrops[i]
            y += speed * dt
            if y > HEIGHT:  # если вышла за экран → респавн сверху
                x = random.uniform(0, WIDTH)
                y = -length
            raindrops[i] = [x, y, length, speed]
    def start_music_loop():
        global current_track_index
        if not playlist:
            return
        track = playlist[current_track_index]
        if os.path.exists(track):
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play()
            logging(f"Сейчас играет: {track}")
        else:
            logging(f"Файл {track} не найден, пропуск")
            next_track()
    def next_track():
        global current_track_index
        current_track_index = (current_track_index + 1) % len(playlist)
        start_music_loop()
    def play_sound(file_path, volume=1.0, channel=None):
        global sounds
        try:
            if not os.path.exists(file_path):
                logging(f"Ошибка: Файл {file_path} не найден!")
                return None
            if file_path not in sounds:
                logging(f"Загрузка звука: {file_path}")
                sounds[file_path] = pygame.mixer.Sound(file_path)
            sound = sounds[file_path]
            sound.set_volume(max(0.0, min(volume, 1.0)))
            if channel is not None:
                channel.play(sound, loops=-1 if file_path == f"{MUSIC_FOLDER}/start.mp3" else 0)
                logging(f"Воспроизведён звук: {file_path} на канале {channel}")
            return sound
        except Exception as e:
            logging(f"Ошибка при воспроизведении звука {file_path}: {e}")
            return None
    def render_text(text, x, y, color=(255, 255, 255), size=32):
        font = pygame.font.SysFont("Arial", size)
        text_surface = font.render(text, True, color)
        text_surface = text_surface.convert_alpha()
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        width, height = text_surface.get_size()

        # переключаемся в 2D-режим (HUD)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)  # <-- вместо фиксированного 800x800
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # (x,y) теперь совпадают с координатами спидометра
        glRasterPos2f(x, y)
        glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        glDisable(GL_BLEND)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    def draw_doroga():
        global world_settings
        for seg_start, seg_end in road_segments:
            # --- полотно дороги ---
            glBegin(GL_QUADS)
            glColor3f(*world_settings["road"])  # серый цвет полотна
            glVertex3f(dorogaX, dorogaY + 0.01, seg_start)
            glVertex3f(dorogaX + dorogaW, dorogaY + 0.01, seg_start)
            glVertex3f(dorogaX + dorogaW, dorogaY + 0.01, seg_end)
            glVertex3f(dorogaX, dorogaY + 0.01, seg_end)

            glEnd()

            # --- разметка ---
            glBegin(GL_LINES)
            glColor3f(1, 1, 1)  # белая
            step = -10 if seg_start > seg_end else 10
            for i in range(seg_start, seg_end, step):
                glVertex3f(dorogaX + dorogaW / 2, dorogaY + 0.01, i)  # чуть выше дороги
                glVertex3f(dorogaX + dorogaW / 2, dorogaY + 0.01, i + step // 2)
            glEnd()

            # --- столбы ---
            glLineWidth(1.5)
            glBegin(GL_LINES)
            glColor3f(0.3, 0.3, 0.3)
            step = -20 if seg_start > seg_end else 20
            for i in range(seg_start, seg_end, step):
                # левый столб
                glVertex3f(dorogaX - 0.2, dorogaY, i)  # низ
                glVertex3f(dorogaX - 0.2, dorogaY + 1, i)  # верх (тот же Z!)

                # правый столб
                glVertex3f(dorogaX + dorogaW + 0.2, dorogaY, i)
                glVertex3f(dorogaX + dorogaW + 0.2, dorogaY + 1, i)
            glEnd()
            glLineWidth(0.5)
    def draw_cube(x, y, z, w, h, d, color):
        """Прямоугольный параллелепипед"""
        glColor3f(*color)
        glBegin(GL_QUADS)

        # Перед
        glVertex3f(x, y, z)
        glVertex3f(x + w, y, z)
        glVertex3f(x + w, y + h, z)
        glVertex3f(x, y + h, z)

        # Зад
        glVertex3f(x, y, z - d)
        glVertex3f(x + w, y, z - d)
        glVertex3f(x + w, y + h, z - d)
        glVertex3f(x, y + h, z - d)

        # Лево
        glVertex3f(x, y, z)
        glVertex3f(x, y, z - d)
        glVertex3f(x, y + h, z - d)
        glVertex3f(x, y + h, z)

        # Право
        glVertex3f(x + w, y, z)
        glVertex3f(x + w, y, z - d)
        glVertex3f(x + w, y + h, z - d)
        glVertex3f(x + w, y + h, z)

        # Верх
        glVertex3f(x, y + h, z)
        glVertex3f(x + w, y + h, z)
        glVertex3f(x + w, y + h, z - d)
        glVertex3f(x, y + h, z - d)

        # Низ
        glVertex3f(x, y, z)
        glVertex3f(x + w, y, z)
        glVertex3f(x + w, y, z - d)
        glVertex3f(x, y, z - d)

        glEnd()
    def draw_autos():
        size = dorogaW / 2 - 0.20
        for ax, ay, az, clr1, clr2, counted in autos:
            body_h = size * 0.6
            roof_h = size * 0.4
            car_len = size * 6

            # Кузов (основной прямоугольник)
            draw_cube(ax, ay, az, size, body_h, car_len, clr1)

            # Кабина по центру кузова
            cabin_len = car_len * 0.4
            cabin_offset = (car_len - cabin_len) / 2  # смещение так, чтобы была по центру
            draw_cube(ax, ay + body_h, az - cabin_offset, size, roof_h, cabin_len, clr2)
    def check_x_coord(camera_x):
        global game_over,dorogaX,mes
        if abs(camera_x) < dorogaX - 0.3 or abs(camera_x) > dorogaX + 1.1:
            game_over = True
            mes = "Выезд с трассы"
    def draw_ground():
        global passed_count,world_settings

        to = -20000
        if passed_count % 2 == 0:
            to *= 2

        glBegin(GL_QUADS)
        glColor3f(*world_settings["ground"])  # зелёная трава
        glVertex3f(-100, dorogaY, 200)
        glVertex3f(100, dorogaY, 200)
        glVertex3f(100, dorogaY, to)
        glVertex3f(-100, dorogaY, to)
        glEnd()
    def draw_stars():
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)  # верх = 0, низ = HEIGHT


        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glColor3f(1, 1, 1)
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for x, y in stars:
            glVertex2f(x, y)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    def draw_rain():
        if not raindrops:
            return

        # переключаемся в 2D режим
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glLineWidth(1.5)

        glBegin(GL_LINES)
        for x, y, length, speed in raindrops:
            glColor4f(0.7, 0.8, 1.0, 0.8)
            glVertex2f(x, y)
            glColor4f(0.6, 0.7, 1.0, 0.3)
            glVertex2f(x, y + length)
        glEnd()

        glLineWidth(1.0)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_BLEND)

        # возвращаем матрицы
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    def draw_snow():
        if not snowdrops:
            return

        # переключаемся в 2D режим
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        for x, y, length, speed in snowdrops:
            glColor4f(1.0, 1.0, 1.0, 1.0)

            glVertex2f(x, y)
        glEnd()

        glLineWidth(1.0)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_BLEND)

        # возвращаем матрицы
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    def draw_speedometr():
        global speed, speed_to_kmh, WIDTH, HEIGHT

        center_x, center_y, radius = 100, 170, 80  # Центр остаётся

        max_speed_kmh = world_settings["max_speed_value"]
        current_speed_kmh = speed * speed_to_kmh
        if current_speed_kmh > max_speed_kmh:
            current_speed_kmh = max_speed_kmh

        # 2D-режим
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # фон шкалы (нижняя дуга)
        glColor3f(0.1, 0.1, 0.1)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(center_x, center_y)
        for angle in range(180, 360, 2):  # нижняя половина круга
            rad = math.radians(angle)
            glVertex2f(center_x + math.cos(rad) * radius,
                       center_y + math.sin(rad) * radius)
        glEnd()

        # окантовка
        glColor3f(1, 1, 1)
        glLineWidth(2)
        glBegin(GL_LINE_STRIP)
        for angle in range(180, 360, 1):
            rad = math.radians(angle)
            glVertex2f(center_x + math.cos(rad) * radius,
                       center_y + math.sin(rad) * radius)
        glEnd()

        # деления и подписи
        num_marks = 10
        for i in range(num_marks + 1):
            angle = 180 + 180 * i / num_marks  # нижняя дуга
            rad = math.radians(angle)

            # деление
            x1 = center_x + math.cos(rad) * (radius - 5)
            y1 = center_y + math.sin(rad) * (radius - 5)
            x2 = center_x + math.cos(rad) * radius
            y2 = center_y + math.sin(rad) * radius
            glBegin(GL_LINES)
            glVertex2f(x1, y1)
            glVertex2f(x2, y2)
            glEnd()

            # подпись
            speed_label = int(round(max_speed_kmh * i / num_marks))
            label_radius = radius + 13
            x = center_x + math.cos(rad) * label_radius
            y = center_y + math.sin(rad) * label_radius + 5
            render_text(str(speed_label), x - 10, y - 6, (255, 255, 255), 14)

        # стрелка
        frac = current_speed_kmh / max_speed_kmh if max_speed_kmh > 0 else 0.0
        angle = 180 + 180 * frac  # стрелка идёт по нижней дуге
        rad = math.radians(angle)
        glColor3f(1, 0, 0)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex2f(center_x, center_y)
        glVertex2f(center_x + math.cos(rad) * (radius - 10),
                   center_y + math.sin(rad) * (radius - 10))
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    def generate_new_evenly():
        global autos
        num_cars = random.randint(4,9)
        seg_start, seg_end = road_segments[-1]
        length = seg_start - seg_end  # положительное
        if num_cars > 0:
            interval = length / (num_cars + 1)
        else:
            interval = 0
        z_pos = seg_start - interval
        for i in range(num_cars):
            idx = random.randint(0, len(lr_colors) - 1)
            clr1, clr2 = normalize_color(lr_colors[idx]), normalize_color(pered_colors[idx])
            lane_choice = random.choice([0.1,0.6])
            autos.append([dorogaX + lane_choice, dorogaY, z_pos, clr1, clr2, False])
            z_pos -= interval
    def update_passed(player_z):
        global passed_count
        size = dorogaW / 2 - 0.15
        car_length = size * 6
        half_length = car_length / 2
        player_back_z = player_z + half_length  # зад игрока

        for car in autos:
            ax, ay, az, clr1, clr2, counted = car
            car_center_z = az - half_length
            car_rear_z = car_center_z - half_length
            # игрок сзади → проехал машину
            if not counted and player_back_z >= car_rear_z and player_z < az:
                passed_count += 1
                car[5] = True
    def detect_collision(player_x, player_z):
        size = dorogaW / 2 - 0.15
        car_width = size
        car_length = size * 6
        half_width = car_width / 2
        half_length = car_length / 2
        player_center_x = player_x
        player_center_z = player_z
        player_half_width = half_width
        player_half_length = half_length
        for car in autos:
            car_center_x = car[0] + car_width / 2
            car_center_z = car[2] - half_length
            dx = abs(player_center_x - car_center_x)
            dz = abs(player_center_z - car_center_z)
            if dx < (player_half_width + half_width) - 0.1 and dz < (player_half_length + half_length):
                return True
        return False
    def set_engine_volume(speed):
        global engine_volume
        if abs(speed * 150) < 20:
            engine_volume = 0.1
        elif abs(speed * 150) < 40 and abs(speed * 150) > 20:
            engine_volume = 0.3
        elif abs(speed * 150) < 70 and abs(speed * 150) > 40:
            engine_volume = 0.5
        elif abs(speed * 150) < 90 and abs(speed * 150) > 70:
            engine_volume = 0.8
        elif abs(speed * 150) > 70:
            engine_volume = 1.0
    def restart(name,score):
        global game_over,passed_count,last_day_change,autos,current_track_index,road_segments,CURRENT_DAY,road_segments,\
            camera_z,camera_x,camera_y,speed,seconds
        game_over = False
        last_day_change = 0
        passed_count = 0
        current_track_index = 0
        autos.clear()
        road_segments = [[0, -200]]
        camera_z = 10
        camera_x = -2
        camera_y = -5
        speed = 0
        seconds = 0
        save_score(name,score)
        main()
    def print_per():
        global CURRENT_PER
        if CURRENT_PER == -1:
            return "R"
        elif CURRENT_PER == 0:
            return "N"
        else:
            return CURRENT_PER
    def transmission(mode):
        global CURRENT_PER,MECHANICK_LIMIT,world_settings,SELECTED_SPEED,speed
        if mode == "up" and CURRENT_PER < 5 and CURRENT_PER >= -1:
            if CURRENT_PER == -1 and int(speed) == 0:
                CURRENT_PER = 0
                MECHANICK_LIMIT = 0
            elif CURRENT_PER == 0 and int(speed) == 0:
                CURRENT_PER += 1
                MECHANICK_LIMIT = 20
            elif CURRENT_PER == 1 and int(speed*150) > 18:
                CURRENT_PER += 1
                MECHANICK_LIMIT = 40
            elif CURRENT_PER == 2 and int(speed*150) > 38:
                CURRENT_PER += 1
                MECHANICK_LIMIT = 60
            elif CURRENT_PER == 3 and int(speed*150) > 58:
                CURRENT_PER += 1
                MECHANICK_LIMIT = 80
            elif CURRENT_PER == 4 and int(speed*150) > 78:
                CURRENT_PER += 1
                MECHANICK_LIMIT = SELECTED_SPEED
            world_settings["max_speed_value"] = MECHANICK_LIMIT
            world_settings["mx_speed"] = MECHANICK_LIMIT / 150
        elif mode == "down" and CURRENT_PER > -1:
            if CURRENT_PER == 5:
                MECHANICK_LIMIT = 80
            elif CURRENT_PER == 4:
                MECHANICK_LIMIT = 60
            elif CURRENT_PER == 3:
                MECHANICK_LIMIT = 40
            elif CURRENT_PER == 2:
                MECHANICK_LIMIT = 20
            elif CURRENT_PER == 1:
                MECHANICK_LIMIT = 0
            elif CURRENT_PER == 0:
                MECHANICK_LIMIT = -15
            CURRENT_PER -= 1
            world_settings["max_speed_value"] = MECHANICK_LIMIT
            world_settings["mx_speed"] = MECHANICK_LIMIT / 150
        elif mode == "set":
            CURRENT_PER = 0
            MECHANICK_LIMIT = 0
            world_settings["max_speed_value"] = MECHANICK_LIMIT
            world_settings["mx_speed"] = 0
    def main():
        global passed_count, autos, start, time, game_start_ticks, game_over, mes, running, speed, WIDTH, HEIGHT, \
            world_settings, engine_volume,DAYS,CURRENT_DAY,days,last_day_change,camera_z,camera_x,camera_y,MECHANICK_LIMIT,\
        CURRENT_PER

        start_played = False

        pygame.init()

        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h

        #pygame.display.set_mode((screen_width, screen_height),DOUBLEBUF | OPENGL | FULLSCREEN)
        pygame.display.set_mode((WIDTH,HEIGHT),DOUBLEBUF | OPENGL)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIDTH / HEIGHT, 0.1, 2000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        camera_z = 10
        camera_x = -2
        camera_y = -5
        clock = pygame.time.Clock()
        glClearColor(*world_settings["sky"], 1)  # голубое небо
        if world_settings["cars"]:
            generate_new_evenly()  # Генерируем первые машины равномерно
        start_ticks = pygame.time.get_ticks()
        if world_settings["rain"]:
            init_rain()
        if world_settings["snow"]:
            init_snow()
        if world_settings["korobka_p"] != "Автомат":
            transmission('set')
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return
                elif event.type == KEYDOWN:
                    if event.key == pygame.K_r:
                        logging(f"[инфо] Рестарт из игры")
                        restart(name,passed_count)
                    elif event.key == pygame.K_e:
                        logging(f"[инфо] Выход из игры")
                        save_score(name, passed_count)
                        running = False
                    if world_settings["korobka_p"] != "Автомат":
                        if event.key == K_UP:
                            transmission("up")
                            if not transmisson_channel.get_busy():  # Play engine sound only if not already playing
                                play_sound(f"{MUSIC_FOLDER}/transmission.mp3", volume=0.5,
                                           channel=transmisson_channel)

                        elif event.key == K_DOWN:
                            transmission("down")
                            if not transmisson_channel.get_busy():  # Play engine sound only if not already playing
                                    play_sound(f"{MUSIC_FOLDER}/transmission.mp3", volume=0.5,
                                               channel=transmisson_channel)
            if game_over:
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                render_text(mes, WIDTH // 2 - 50, HEIGHT // 2 - 50, (255, 0, 0), 45)
                render_text("Игра окончена!", WIDTH // 2 - 50, HEIGHT // 2 - 100, (255, 0, 0), 45)
                if not world_settings["is_dark"]:
                    render_text("E - Выход", WIDTH // 2 - 50, HEIGHT // 2, (0, 0, 0), 45)
                    render_text("R - Рестарт", WIDTH // 2 - 50, HEIGHT // 2 + 50, (0, 0, 0), 45)
                else:
                    render_text("E - Выход", WIDTH // 2 - 50, HEIGHT // 2, size=45)
                    render_text("R - Рестарт", WIDTH // 2 - 50, HEIGHT // 2 + 50, size=45)

                start_channel.stop()
                engine_channel.stop()
                brake_channel.stop()
                pygame.display.flip()
                pygame.time.wait(100)
            else:
                global last_day_change
                seconds = (pygame.time.get_ticks() - start_ticks) // 1000
                keys = pygame.key.get_pressed()
                if world_settings["changed_days"]:
                    if seconds - last_day_change >= 13:
                        world_settings["sky"] = days[CURRENT_DAY]["sky"]
                        if not world_settings["snow"]:
                            world_settings["ground"] = days[CURRENT_DAY]["ground"]

                        world_settings["road"] = days[CURRENT_DAY]["road"]

                        glClearColor(*world_settings["sky"], 1)
                        CURRENT_DAY += 1
                        if world_settings["snow"] and CURRENT_DAY in [3,4]:
                            world_settings["ground"] = normalize_color((169, 169, 169))
                        elif world_settings["snow"] and CURRENT_DAY in [1,2]:
                            world_settings["ground"] = (1, 1, 1)

                        if CURRENT_DAY in [4,5,6,7,8]:
                            world_settings["stars"] = True
                            world_settings["is_dark"] = True
                        else:
                            world_settings["stars"] = False
                            world_settings["is_dark"] = False
                        if CURRENT_DAY >= len(days):
                            CURRENT_DAY = 0
                        last_day_change = seconds
                if start:
                    if world_settings["korobka_p"] == "Автомат":
                        if not keys[K_z] or not keys[K_w]:
                            if speed > 0:
                                speed *= 0.9995
                                set_engine_volume(speed)
                        if keys[K_z] or keys[K_w]:
                            if speed < world_settings["mx_speed"]:
                                speed += 0.001
                                set_engine_volume(speed)
                        if keys[K_q] or keys[K_a]:
                            if not world_settings["snow"] and not world_settings["rain"]:
                                camera_x += 0.02
                            else:
                                camera_x += 0.04
                        if keys[K_d]:
                            if not world_settings["snow"] and not world_settings["rain"]:
                                camera_x -= 0.02
                            else:
                                camera_x -= 0.04
                        if keys[K_s]:
                            if speed > -0.1:
                                if not world_settings["snow"]:
                                    speed -= 0.005
                                else:
                                    speed -= 0.002
                                set_engine_volume(speed)
                                if speed > 0:
                                    if not brake_channel.get_busy():
                                        play_sound(f"{MUSIC_FOLDER}/brake.mp3", volume=0.5, channel=brake_channel)
                                else:
                                    if not reverse_channel.get_busy():
                                        play_sound(f"{MUSIC_FOLDER}/reverse.mp3", volume=0.5, channel=reverse_channel)
                    else:
                        if not keys[K_z] or not keys[K_w]:
                            if speed > 0:
                                speed *= 0.9995
                                set_engine_volume(speed)
                        if keys[K_z] or keys[K_w]:
                            if (speed * 150) < 1 and CURRENT_PER not in [-1, 1]:
                                speed = 0.0
                            elif CURRENT_PER == -1:
                                if speed >= -0.1:
                                    if not world_settings["snow"] or not world_settings["rain"]:
                                        speed -= 0.005
                                    else:
                                        speed -= 0.002
                                if not reverse_channel.get_busy():
                                    play_sound(f"{MUSIC_FOLDER}/reverse.mp3", volume=0.5,
                                               channel=reverse_channel)
                            else:
                                if speed < world_settings["mx_speed"]:
                                    if int(speed) == 0 and CURRENT_PER == 1:
                                        speed += 0.001
                                    elif speed > 0:
                                        speed += 0.001
                                    set_engine_volume(speed)
                        if keys[K_s]:
                            if speed > 0.0:
                                if not world_settings["snow"] or not world_settings["rain"]:
                                    speed -= 0.005
                                else:
                                    speed -= 0.002
                                set_engine_volume(speed)
                            elif CURRENT_PER == -1 and (speed * 150) > -0.8 and (speed * 150) < 0:
                                speed = 0.0
                            elif abs(speed) > -0.1:
                                if not world_settings["snow"] or not world_settings["rain"]:
                                    speed += 0.005
                                else:
                                    speed += 0.002
                                if speed > 0:
                                    if not brake_channel.get_busy():
                                        play_sound(f"{MUSIC_FOLDER}/brake.mp3", volume=0.5, channel=brake_channel)
                        if keys[K_q] or keys[K_a]:
                            if speed > 0 or speed < 0:
                                if not world_settings["snow"] and not world_settings["rain"]:
                                    camera_x += 0.02
                                else:
                                    camera_x += 0.04
                        if keys[K_d]:
                            if speed > 0 or speed < 0:
                                if not world_settings["snow"] and not world_settings["rain"]:
                                    camera_x -= 0.02
                                else:
                                    camera_x -= 0.04


                if abs(speed * 150) <= 0.0001:  # Проверка с малой погрешностью
                    if not start_played:
                        play_sound(f"{MUSIC_FOLDER}/start.mp3", volume=0.5, channel=start_channel)
                        start_played = True
                    if engine_channel.get_busy():
                        engine_channel.stop()  # Stop engine sound when car is stopped
                else:
                    if start_played:
                        start_channel.stop()  # Stop start sound when car moves
                        start_played = False
                    if not engine_channel.get_busy():  # Play engine sound only if not already playing
                        if abs(speed*150) > 1:
                            play_sound(f"{MUSIC_FOLDER}/engine.mp3", volume=engine_volume, channel=engine_channel)
                if world_settings["music_in_back"]:
                    if not pygame.mixer.music.get_busy():  # если музыка закончилась
                        next_track()
                # --- Движение камеры ---
                camera_z += speed
                player_x = -camera_x
                player_z = -camera_z
                update_passed(player_z)

                if autos and all(car[5] for car in autos):
                    autos = []
                    generate_new_evenly()

                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glLoadIdentity()
                glTranslatef(camera_x, camera_y, camera_z)
                # обновление дождя — используем время кадра в секундах
                dt = clock.get_time() / 1000.0

                if world_settings["rain"]:
                    # если список капель ещё пуст (например дождь включили позже), инициализируем рядом с текущей камерой
                    if not raindrops:
                        init_snow()
                    update_rain(dt)
                if world_settings["snow"]:
                    # если список капель ещё пуст (например дождь включили позже), инициализируем рядом с текущей камерой
                    if not snowdrops:
                        init_snow()
                    update_snow(dt)
                if world_settings["stars"]:
                    draw_stars()
                draw_ground()
                check_x_coord(camera_x)
                if detect_collision(player_x, player_z):
                    game_over = True
                    mes = "Столкновение со встречной машиной!"
                    start_channel.stop()
                    engine_channel.stop()
                    brake_channel.stop()
                    reverse_channel.stop()

                if abs(camera_z) > abs(road_segments[-1][1]) - 70:
                    last_end = road_segments[-1][1]
                    road_segments.append([last_end, last_end - 200])


                draw_doroga()
                if world_settings["cars"]:
                    draw_autos()
                if world_settings["rain"]:
                    # чтобы капли были видны поверх сцены, можно временно отключить глубину (опционально)
                    glPushAttrib(GL_DEPTH_BUFFER_BIT)
                    glDisable(GL_DEPTH_TEST)
                    draw_rain()
                    if not rain_channel.get_busy():  # Play engine sound only if not already playing

                        play_sound(f"{MUSIC_FOLDER}/rain.mp3", volume=0.6, channel=rain_channel)
                    glPopAttrib()
                if world_settings["snow"]:
                    # чтобы капли были видны поверх сцены, можно временно отключить глубину (опционально)
                    glPushAttrib(GL_DEPTH_BUFFER_BIT)
                    glDisable(GL_DEPTH_TEST)
                    draw_snow()
                    glPopAttrib()
                if not start:
                    remaining = time - seconds
                    if remaining > 0:
                        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                        glLoadIdentity()
                        glTranslatef(camera_x, camera_y, camera_z)
                        render_text(f"Старт через: {remaining}", WIDTH // 2 - 150, HEIGHT // 2, (255, 0, 0), 55)
                    else:
                        start = True
                        game_start_ticks = pygame.time.get_ticks()

                if start:
                    game_time = (pygame.time.get_ticks() - game_start_ticks) / 1000
                    render_text(f"Время: {game_time:.1f} c", WIDTH - 150, HEIGHT - 960, (255, 255, 255))

                render_text(f"Проехавшие машины: {passed_count}", 10, HEIGHT - 960, (255, 255, 255))
                render_text('©Developped by Sergiy Bagach,Sviatoslav Bulygin', 10, HEIGHT - 20, color=(255, 255, 255),
                            size = 20)
                if world_settings["speedometr_type"] == "Digital":
                    current_speed_kmh = speed * speed_to_kmh
                    render_text(f"Скорость: {current_speed_kmh:.1f} км/ч", 10, HEIGHT - 900, (255, 255, 255))
                else:
                    draw_speedometr()
                if world_settings["korobka_p"] != "Автомат":
                    render_text(f"Передача: ",10, HEIGHT - 850, (255, 255,255))
                    if print_per() == 'R':
                        render_text(f"{print_per()}", 140, HEIGHT - 850, (255, 0, 0))
                    elif print_per() == 'N':
                        render_text(f"{print_per()}", 140, HEIGHT - 850, (0, 255, 0))
                    else:
                        render_text(f"{print_per()}", 140, HEIGHT - 850, (255, 255, 255))
                pygame.display.flip()
                clock.tick(60)
    main()
def start_func():
    def export(name, sutki, weather, max_speed,korobka,spedometr,music,cars,mode):
        global JSON_NAME

        data = {
            "name": name,
            "day": sutki,
            "weather": weather,
            "max_speed":max_speed,
            "transmission":korobka,
            "speedometr":spedometr,
            "music":music,
            'mode':mode,
            "cars":cars
        }

        try:
            with open(JSON_NAME, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успех","Настройки успешно экспортированны")
        except Exception as e:
            messagebox.showerror("Ошибка",f"Ошибка: {e}")
    def on_submit(name,sutki,weather,mx_speed,korobka,spedometr,music,carss):
        def insert_to_db(name):
            conn = sqlite3.connect(NAME_DB)
            cursor = conn.cursor()
            row = cursor.execute("SELECT name FROM users WHERE name = ?",(name,)).fetchone()
            if not row:
                cursor.execute("INSERT INTO users(name,score) VALUES(?,?)",(name,0))
        def set_info(name,s,w,mx_spd,korobka):
            global sutki,weather,world_settings,speed_to_kmh,SELECTED_SPEED

            if s == "День":
                world_settings["sky"] = (0.4, 0.7, 1.0)
                world_settings["ground"] = (0, 0.6, 0)
                world_settings["road"] =(0.3, 0.3, 0.3)
            elif s == "Ночь":
                world_settings["sky"] = normalize_color((0, 0, 70))
                world_settings["ground"] = normalize_color((10, 60, 10))
                world_settings["road"] = (0, 0, 0)
                world_settings["stars"] = True
                world_settings["is_dark"] = True
            elif s == "Меняющийся":
                world_settings["sky"] = normalize_color((255, 182, 193))
                world_settings["ground"] = normalize_color((50, 205, 50))
                world_settings["road"] = normalize_color((169, 169, 169))
                world_settings["changed_days"] = True
            elif s == "Динамический":
                now = datetime.now()
                hour = now.hour
                if int(hour) > 5 and int(hour) < 8:
                    world_settings["sky"] = normalize_color((255, 182, 193))
                    world_settings["ground"] = normalize_color((50, 205, 50))
                    world_settings["road"] = normalize_color((169, 169, 169))
                if int(hour) > 8 and int(hour) < 11:
                    world_settings["sky"] = normalize_color((0, 191, 255))
                    world_settings["ground"] = normalize_color((154, 205, 50))
                    world_settings["road"] = normalize_color((128, 128, 128))
                elif int(hour) > 11 and int(hour) < 16:
                    world_settings["sky"] = (0.4, 0.7, 1.0)
                    world_settings["ground"] = (0, 0.6, 0)
                    world_settings["road"] = (0.3, 0.3, 0.3)
                elif int(hour) > 16 and int(hour) < 18:
                    world_settings["sky"] = normalize_color((255, 178, 102))
                    world_settings["ground"] = normalize_color((107, 142, 35))
                    world_settings["road"] = normalize_color((128, 128, 128))
                    world_settings["stars"] = True
                    world_settings["is_dark"] = True
                elif int(hour) > 18 and int(hour) < 19:
                    world_settings["sky"] = normalize_color((252, 94, 83))
                    world_settings["ground"] = normalize_color((85, 107, 47))
                    world_settings["road"] = normalize_color((105, 105, 105))
                    world_settings["stars"] = True
                    world_settings["is_dark"] = True
                elif int(hour) > 19 and int(hour) < 21:
                    world_settings["sky"] =  normalize_color((135, 150, 235))
                    world_settings["ground"] = normalize_color((85, 107, 47))
                    world_settings["road"] = normalize_color((105, 105, 105))
                    world_settings["stars"] = True
                    world_settings["is_dark"] = True
                elif int(hour) > 21 and int(hour) < 23:
                    world_settings["sky"] =  normalize_color((0, 0, 128))
                    world_settings["ground"] = normalize_color((0, 100, 0))
                    world_settings["road"] = (0, 0, 0)
                    world_settings["stars"] = True
                    world_settings["is_dark"] = True
                else:
                    world_settings["sky"] = normalize_color((0, 0, 70))
                    world_settings["ground"] = normalize_color((10, 60, 10))
                    world_settings["road"] = (0, 0, 0)
                    world_settings["stars"] = True
                    world_settings["is_dark"] = True

            if w == "Ясно":
                world_settings["rain"] = False
                world_settings["snow"] = False
            elif w == "Дождь":
                world_settings["rain"] = True
                world_settings["snow"] = False
            elif w == "Снег":
                world_settings["snow"] = True
                world_settings["rain"] = False
                world_settings["ground"] = (1, 1, 1)

            if mx_spd == "150 км/ч":
                world_settings["mx_speed"] = 1.0
                world_settings["max_speed_value"] = 150
                SELECTED_SPEED = 150
            elif mx_spd == "180 км/ч":
                world_settings["mx_speed"] = 1.2
                world_settings["max_speed_value"] = 180
                SELECTED_SPEED = 180
            elif mx_spd == "210 км/ч":
                world_settings["mx_speed"] = 1.4
                world_settings["max_speed_value"] = 210
                SELECTED_SPEED = 210
            speed_to_kmh = world_settings["max_speed_value"] / world_settings["mx_speed"]

            if korobka == "Автомат":
                world_settings["korobka_p"] = "Автомат"
            else:
                world_settings["korobka_p"] = "Mechanic"
            if spedometr == "Цифровой":
                world_settings["speedometr_type"] = "Digital"
            else:
                world_settings["speedometr_type"] = "Arrow"
            if music:
                world_settings["music_in_back"] = True
            else:
                world_settings["music_in_back"] = False
            world_settings["cars"] = carss
            insert_to_db(name)
            app.destroy()
            main_func(name,0)
        set_info(name,sutki,weather, mx_speed,korobka)
    def enter_pressed(event):
        on_submit(name.get(), sutki.get(), weather.get(),
                  max_speed.get(), korobka.get(), speedometr.get(), musVar.get(),carsVar.get())
    def set_mode(mod,check,CarsVar):
        global world_settings
        world_settings["mode"] = mod
        if mod == "Карьера":
            check.configure(state = "disabled")
            world_settings["cars"] = True
            CarsVar.set(True)
        else:
            check.configure(state="normal")
    global NAME_DB,JSON_NAME
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Вход")

    sc_width = app.winfo_screenwidth()
    sc_height = app.winfo_screenheight()
    x = sc_width // 2 - 20
    y = sc_height // 2 - 150
    app.resizable(False,False)
    app.geometry(f"450x550+{x}+{y}")

    user_name = ""
    loaded_data = {"day":"День","weather":"Ясно","max_speed":"180 км/ч","transmission":"Автомат","speedometr":"Цифровой",
                   "music":False,"mode":"Карьера","cars":True}

    if os.path.exists(NAME_DB):
        conn = sqlite3.connect(NAME_DB)
        cursor = conn.cursor()
        row = cursor.execute('SELECT name FROM users WHERE id = ?',(1,)).fetchone()
        if row:
            user_name = row[0]
        else:
            user_name = "Player"
        conn.close()
    else:
        conn = sqlite3.connect(NAME_DB)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE users (
            [id] INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL
                    UNIQUE,
            score   INTEGER NOT NULL
            );""")
        conn.commit()
        conn.close()
    if os.path.exists(JSON_NAME):
        with open(JSON_NAME, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)
    lbl = ctk.CTkLabel(app, text="Введите имя")
    lbl.pack()

    name = ctk.CTkEntry(app, placeholder_text="Введите имя", width=100)
    name.pack()
    name.insert(0,user_name)

    lbl = ctk.CTkLabel(app,text = "Выберите время суток")
    lbl.pack()

    sutki = ctk.CTkComboBox(app,values = ["День","Ночь","Динамический","Меняющийся"])
    sutki.pack()
    sutki.set(loaded_data["day"])
    sutki.configure(state="readonly")

    lbl = ctk.CTkLabel(app, text="Выберите погоду")
    lbl.pack()

    weather = ctk.CTkComboBox(app, values=["Ясно", "Дождь", "Снег"])
    weather.pack()
    weather.set(loaded_data["weather"])
    weather.configure(state="readonly")

    lbl = ctk.CTkLabel(app, text="Выберите максимальную скорость")
    lbl.pack()

    max_speed = ctk.CTkComboBox(app, values=["150 км/ч", "180 км/ч", "210 км/ч"])
    max_speed.pack()
    max_speed.set(loaded_data["max_speed"])
    max_speed.configure(state="readonly")

    lbl = ctk.CTkLabel(app, text="Выберите коробку передач")
    lbl.pack()

    korobka = ctk.CTkComboBox(app, values=["Автомат", "Механика"])
    korobka.pack()
    korobka.set(loaded_data["transmission"])
    korobka.configure(state="readonly")

    lbl = ctk.CTkLabel(app, text="Выберите тип спедометра")
    lbl.pack()

    speedometr = ctk.CTkComboBox(app, values=["Цифровой", "Стрелочный"])
    speedometr.pack()
    speedometr.set(loaded_data["speedometr"])
    speedometr.configure(state="readonly")

    lbl = ctk.CTkLabel(app, text="Выберите режим")
    lbl.pack()
    carsVar = ctk.BooleanVar(value=loaded_data["cars"])
    modeC = ctk.CTkComboBox(app, values=["Карьера", "Свободный"], command=lambda value: set_mode(value, carsB,carsVar))
    modeC.pack()
    modeC.set(loaded_data["mode"])
    modeC.configure(state="readonly")

    carsB = ctk.CTkCheckBox(app, text="Машины", onvalue=True, offvalue=False, variable=carsVar)
    carsB.pack()
    set_mode(modeC.get(),carsB,carsVar)

    musVar = ctk.BooleanVar(value=loaded_data["music"])
    mus = ctk.CTkCheckBox(app,text="Музыка на фоне",onvalue=True,offvalue=False,variable=musVar)
    mus.pack()

    btn_ok = ctk.CTkButton(app,text="OK", command=lambda:
    on_submit(name.get(),sutki.get(),weather.get(),max_speed.get(),korobka.get(),speedometr.get(),musVar.get(),carsVar.get()))
    btn_ok.pack(pady = 10)
    app.bind("<Return>",enter_pressed)
    btn = ctk.CTkButton(app, text="Экспорт настроек в JSON",
                        command=lambda:export(name.get(), sutki.get(), weather.get(), max_speed.get(),korobka.get(),
                                              speedometr.get(),musVar.get(),carsVar.get(),modeC.get()),
                        fg_color = "#FF8C00",hover_color = "#FF4500")
    btn.pack()

    app.mainloop()

if __name__ == "__main__":
    start_func()
