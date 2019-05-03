from . import global_state
import curses
import asyncio
import random
from .curses_tools import draw_frame, get_frame_size, read_controls
import os
from .physics import update_speed
from .explosion import explode
from .obstacles import Obstacle


STAR_SYMBOLS = ["+", "*", ".", ":"]
ROCKET_FOLDER = './animation_frames/rocket/'
GABARGE_FOLDER = './animation_frames/garbage/'
GAME_OVER_FOLDER = './animation_frames/'
PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}
year = 1957
YEAR_PLASMA_GUN = 2020

spaceship_frame = ""

obstacles = list()
obstacles_in_last_collisions = list()


def get_garbage_delay_tics():
    global year
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2

def get_garbage_speed():
    global year
    if year < 1961:
        return 0.3
    elif year < 1969:
        return 0.35
    elif year < 1981:
        return 0.4
    elif year < 1995:
        return 0.45
    elif year < 2010:
        return 0.5
    elif year < 2020:
        return 0.55
    else:
        return 0.6


async def game_over():
    frame = read_frame(GAME_OVER_FOLDER, 'game_over.txt')
    max_row, max_column = global_state.canvas_game.getmaxyx()
    frame_height, frame_width = get_frame_size(frame)
    row = (max_row - frame_height) // 2
    column = (max_column - frame_width) // 2
    while True:
        draw_frame(global_state.canvas_game, row, column, frame)
        await asyncio.sleep(0)


def animate_stars(max_stars_number):
    max_row, max_column = global_state.canvas_game.getmaxyx()
    for star in range(max_stars_number):
        star = blink(global_state.canvas_game,
                     random.randint(2, max_row - 2),
                     random.randint(2, max_column - 2),
                     symbol=random.choice(STAR_SYMBOLS))
        global_state.coroutines.append(star)


async def blink(canvas, row, column, symbol='*'):
    await sleep(random.randint(0, 20))
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(6)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(10)

        canvas.addstr(row, column, symbol)
        await sleep(6)


async def sleep(ticks=1):
    for i in range(ticks):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                global_state.coroutines.append(
                    explode(canvas, row, column))
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

    canvas.border()


def process_controls(row, col, max_row, max_column, rocket_rows, rocket_cols, rows_speed, columns_speed):
    global year
    row_delta, col_delta, is_space_pressed = read_controls(global_state.canvas_game)

    if is_space_pressed and year >= YEAR_PLASMA_GUN:
        global_state.coroutines.append(fire(global_state.canvas_game, row, col + 2))

    new_rows_speed, new_columns_speed = update_speed(rows_speed, columns_speed, row_delta, col_delta)

    new_row = row + new_rows_speed
    new_col = col + new_columns_speed

    if new_row < 2 or new_row > (max_row - rocket_rows - 2):
        new_rows_speed = 0
        new_row = row

    if new_col < 2 or new_col > (max_column - rocket_cols - 2):
        new_columns_speed = 0
        new_col = col

    return new_row, new_col, new_rows_speed, new_columns_speed


def animate_spaceship():
    global_state.coroutines.append(iterate_spaceship_frames())
    global_state.coroutines.append(run_spaceship())


async def iterate_spaceship_frames():
    global spaceship_frame
    rocket_frames = get_rocket_animation_data()
    while True:
        for spaceship_frame in rocket_frames:
            await sleep()


async def run_spaceship():
    global spaceship_frame
    rocket_frames = get_rocket_animation_data()
    rocket_rows, rocket_cols = get_frame_size(rocket_frames[0])
    max_row, max_column = global_state.canvas_game.getmaxyx()
    row = (max_row - rocket_rows) // 2
    col = (max_column - rocket_cols) // 2 + 1
    prev_spaceship_frame = spaceship_frame
    rows_speed = columns_speed = 0

    while True:
        for obstacle in obstacles:
            if obstacle.has_collision(row, col, rocket_rows, rocket_cols):
                global_state.coroutines.append(game_over())
                return
        prev_row, prev_col = row, col

        row, col, rows_speed, columns_speed = process_controls(row=row, col=col,
                                                               max_row=max_row, max_column=max_column,
                                                               rocket_rows=rocket_rows, rocket_cols=rocket_cols,
                                                               rows_speed=rows_speed, columns_speed=columns_speed)

        draw_frame(global_state.canvas_game, prev_row, prev_col + 1, prev_spaceship_frame, negative=True)
        draw_frame(global_state.canvas_game, prev_row, prev_col - 1, prev_spaceship_frame, negative=True)
        draw_frame(global_state.canvas_game, row, col, spaceship_frame, negative=False)
        await asyncio.sleep(0)


def read_frame(dir, file_name):
    file_path = os.path.join(dir, file_name)
    with open(file_path) as hdlr:
        return hdlr.read()


def get_rocket_animation_data():
    return [read_frame(ROCKET_FOLDER, file_name) for file_name in os.listdir(ROCKET_FOLDER)]


def get_garbage_animation_data():
    return [read_frame(GABARGE_FOLDER, file_name) for file_name in os.listdir(GABARGE_FOLDER)]


def animate_garbage():
    async def fill_orbit_with_garbage(max_column, garbage_frames):

        while True:
            garbage_delay = get_garbage_delay_tics()
            if garbage_delay:
                await sleep(garbage_delay)
            else:
                await sleep(20)

            random_column = random.randint(2, max_column - 2)
            random_garbage = random.choice(garbage_frames)

            global_state.coroutines.append(fly_garbage(global_state.canvas_game, random_column, random_garbage))


    _, max_column = global_state.canvas_game.getmaxyx()
    garbage_frames = get_garbage_animation_data()
    global_state.coroutines.append(fill_orbit_with_garbage(max_column, garbage_frames))


async def fly_garbage(canvas, column, garbage_frame):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    max_row, max_column = global_state.canvas_game.getmaxyx()

    column = max(column, 0)
    column = min(column, max_column - 1)

    row = 0

    rows_size, columns_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, rows_size, columns_size)
    obstacles.append(obstacle)
    try:
        while row < max_row:
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                return
            draw_frame(canvas, row, column, garbage_frame)
            await sleep()
            draw_frame(canvas, row, column, garbage_frame, negative=True)

            speed = get_garbage_speed()
            row += speed
            obstacle.row = row
            canvas.border()
    finally:
        obstacles.remove(obstacle)


def animate_years():
    async def years_counter(max_row, max_column):
        global year
        while True:
            message = PHRASES.get(year, '')
            text = f'Year {year}. {message}'
            message_row, message_column = max_row // 2, max_column // 2 - len(text) // 2

            draw_frame(global_state.canvas_text, message_row, message_column, text)
            await sleep(20)
            draw_frame(global_state.canvas_text, message_row, message_column, text, negative=True)

            year += 1

    max_row, max_column = global_state.canvas_text.getmaxyx()
    global_state.coroutines.append(years_counter(max_row, max_column))
