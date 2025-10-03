
import os
import time
import random
import copy

import glux
import moderngl as mgl

from glux import imgui


os.environ["ALSOFT_CONF"] = "alsoft.ini"

window = glux.Window(1280, 720, "ASCII Tetris")
ctx = mgl.create_context()
oal_ctx = glux.oal.Context()
stream = oal_ctx.create_stream()
stream.play("tetris-theme.mp3", loop=True)
stream.pause()

io = imgui.get_io()
io.font_global_scale = 3

lines_cleared = 0
shapes = []
keys_held = set()

screen = [[' .' for i in range(10)] for i in range(20)]
screen_str = '\n'.join([''.join([col for col in row]) for row in screen])
tick_rate = 0.5
timer = time.time()
current_shape = []
current_shape_base = []
ticking = False

shape_templates = {
    # I piece
    'I': [
        [[0,0], [1,0], [2,0], [3,0]],          # Horizontal
        [[0,0], [0,1], [0,2], [0,3]]           # Vertical
    ],
    # O piece
    'O': [
        [[0,0], [1,0], [0,1], [1,1]]           # Only one rotation
    ],
    # T piece
    'T': [
        [[0,0], [1,0], [2,0], [1,1]],          # ┴
        [[1,0], [0,1], [1,1], [1,2]],          # ├
        [[1,0], [0,1], [1,1], [2,1]],          # ┬
        [[0,0], [0,1], [1,1], [0,2]]           # ┤
    ],
    # L piece
    'L': [
        [[0,0], [0,1], [1,1], [2,1]],          # └
        [[0,0], [1,0], [0,1], [0,2]],          # ┌
        [[0,0], [1,0], [2,0], [2,1]],          # ┐
        [[1,0], [1,1], [0,2], [1,2]]           # ┘
    ],
    # J piece
    'J': [
        [[2,0], [0,1], [1,1], [2,1]],          # mirrored L ┘
        [[0,0], [0,1], [0,2], [1,2]],          # mirrored └
        [[0,0], [1,0], [2,0], [0,1]],          # mirrored ┌
        [[0,0], [1,0], [1,1], [1,2]]           # mirrored ┐
    ],
    # S piece
    'S': [
        [[1,0], [2,0], [0,1], [1,1]],          # Horizontal
        [[0,0], [0,1], [1,1], [1,2]]           # Vertical
    ],
    # Z piece
    'Z': [
        [[0,0], [1,0], [1,1], [2,1]],          # Horizontal
        [[1,0], [0,1], [1,1], [0,2]]           # Vertical
    ],
}

def shift_current_shape(value):
    global current_shape_base
    for shape in current_shape_base:
        can_shift = True
        for block in shape:
            for sh in shapes:
                for b in sh:
                    if block[1] == b[1] and block[0] + value == b[0]:
                        can_shift = False
        if can_shift:
            for block in shape:
                if block[0] + value not in range(0, 10):
                    return
            for block in shape:
                block[0] += value

def spawn_random_shape():
    global current_shape_base, current_shape
    current_shape_base = copy.deepcopy(random.choice(list(shape_templates.values())))
    shift_current_shape(3)
    current_shape = current_shape_base[0]

spawn_random_shape()

def can_slide():
    global current_shape
    for block in current_shape:
        if block[1] == 19:
            return False
        for sh in shapes:
            for b in sh:
                if block[1] + 1 == b[1] and block[0] == b[0]:
                    return False
    return True

def events():
    global tick_rate, current_shape, current_shape_base, keys_held
    if glux.keyboard.action == glux.actions.PRESS:
        keys_held.add(glux.keyboard.key)

    if glux.keyboard.action == glux.actions.RELEASE:
        keys_held.discard(glux.keyboard.key)
    if glux.keyboard.action == glux.actions.PRESS:
        if glux.keyboard.key == glux.keys.K_LEFT:
            shift_current_shape(-1)
        if glux.keyboard.key == glux.keys.K_RIGHT:
            shift_current_shape(1)
        if glux.keyboard.key == glux.keys.K_UP:
            if len(current_shape_base) > 1:
                current_shape = current_shape_base[1]
                temp = current_shape_base.pop(0)
                current_shape_base.append(temp)
    if glux.get_key(window, glux.keys.K_DOWN) == glux.actions.PRESS:
        tick_rate = 0.05
    else:
        tick_rate = 0.5

def process():
    global screen_str, timer, current_shape, lines_cleared, ticking
    if stream.is_playing():
        stream.update()
    if ticking:
        screen = [[' .' for i in range(10)] for i in range(20)]
        for shape in shapes:
            if shape == []:
                shapes.remove(shape)
            else:
                for block in shape:
                    screen[block[1]][block[0]] = ' #'
                        
        for block in current_shape:
            screen[block[1]][block[0]] = ' #'

        if time.time() - timer > tick_rate:
            timer = time.time()

            if can_slide():
                for shape in current_shape_base:
                    for block in shape:
                        block[1] += 1
            else:
                shapes.append(current_shape)
                spawn_random_shape()

                for i, line in enumerate(screen):
                    complete = True
                    for c in line:
                        if c != " #":
                            complete = False
                            break
                    if complete:
                        lines_cleared += 1
                        for shape in shapes:
                            new = []
                            for block in shape:
                                if block[1] != i:
                                    new.append(block)
                                if block[1] < i:
                                    block[1] += 1
                            shape[:] = new
                
        screen_str = '\n'.join([''.join([col for col in row]) for row in screen])

def render():
    ctx.clear(0, 0, 0, 1)

def render_ui():
    global shapes, ticking, screen_str, lines_cleared
    imgui.set_next_window_pos(imgui.Vec2(window.get_size()[0] // 2, 0))
    imgui.set_next_window_size(imgui.Vec2(window.get_size()[0] // 2, window.get_size()[1]))
    imgui.begin("ASCII Tetris", flags=imgui.WindowFlags.NoResize | imgui.WindowFlags.NoCollapse)
    imgui.text('')
    for l in screen_str.split('\n'):
        imgui.text(' |' + l + ' |')
    imgui.text(" " + "= " * 12)
    imgui.end()

    imgui.set_next_window_pos(imgui.Vec2(0, 0))
    imgui.set_next_window_size(imgui.Vec2(window.get_size()[0] // 2, window.get_size()[1]))
    imgui.begin("Dashboard", flags=imgui.WindowFlags.NoResize | imgui.WindowFlags.NoCollapse)
    if imgui.button("Start"):
        ticking = True
        stream.resume()
    if imgui.button("Pause"):
        ticking = False
        stream.pause()
    if imgui.button("Restart"):
        stream.stop()
        lines_cleared = 0
        screen = [[' .' for i in range(10)] for i in range(20)]
        screen_str = '\n'.join([''.join([col for col in row]) for row in screen])
        shapes.clear()
        spawn_random_shape()
        ticking = False
        stream.play("tetris-theme.mp3", loop=True)
        stream.pause()
    imgui.text(f"Lines cleared: {lines_cleared}")
    imgui.end()
    
window.set_events_callback(events)
window.set_process_callback(process)
window.set_render_callback(render)
window.set_render_ui_callback(render_ui)
window.run()