import random
import time
import curses
import asyncio
from curses_tools import draw_frame, get_frame_size, read_controls
from os import path

TIC_TIMEOUT = 0.1
STAR_SYMBOLS = ["+", "*", ".", ":"]
MAX_STARS = 100
ANIMATON_DATA_FOLDER = './animation_frames'


def draw(canvas):
    canvas.nodelay(True)
    canvas.border()
    curses.curs_set(False)

    max_row, max_column = canvas.getmaxyx()

    coroutines = list()

    for star in range(MAX_STARS):
        star = blink(canvas,
                     random.randint(2, max_row - 2),
                     random.randint(2, max_column - 2),
                     symbol=random.choice(STAR_SYMBOLS))

        coroutines.append(star)

    rocket_frames = get_rocket_animation_data()

    coroutines.append(animate_spaceship(canvas, max_row, max_column, rocket_frames))
    coroutines.append(fire(canvas, max_row // 2, max_column // 2))

    while True:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)

        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, symbol='*'):
    await delay_animation(random.randint(0, 20))
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await delay_animation(10)

        canvas.addstr(row, column, symbol)
        await delay_animation(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await delay_animation(5)

        canvas.addstr(row, column, symbol)
        await delay_animation(3)


async def delay_animation(ticks):
    for i in range(ticks * 2):
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
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

    canvas.border()


def get_rocket_position(row, col, row_delta, col_delta, max_row, max_column,
                        rocket_rows, rocket_cols):
    new_row = row + row_delta
    new_col = col + col_delta

    if new_row < 2 or new_row > (max_row - rocket_rows - 2):
        new_row = row

    if new_col < 2 or new_col > (max_column - rocket_cols - 2):
        new_col = col

    return new_row, new_col


async def animate_spaceship(canvas, max_row, max_column, rocket_frames):
    rocket_rows, rocket_cols = get_frame_size(rocket_frames[0])

    row = (max_row - rocket_rows) // 2
    col = (max_column - rocket_cols) // 2 + 1

    while True:
        row_delta, col_delta, is_space_pressed = read_controls(canvas)
        row, col = get_rocket_position(row=row, col=col,
                                       row_delta=row_delta, col_delta=col_delta,
                                       max_row=max_row, max_column=max_column,
                                       rocket_rows=rocket_rows, rocket_cols=rocket_cols)
        for frame in rocket_frames:
            draw_frame(canvas, start_row=row, start_column=col, text=frame)
            canvas.refresh()
            await asyncio.sleep(0)
            draw_frame(canvas, row, col, text=frame, negative=True)


def read_frame(fname):
    with open(fname) as hdlr:
        return hdlr.read()


def get_rocket_animation_data():
    return [
        read_frame(path.join(ANIMATON_DATA_FOLDER, 'rocket_frame_1.txt')),
        read_frame(path.join(ANIMATON_DATA_FOLDER, 'rocket_frame_2.txt'))
    ]


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()
