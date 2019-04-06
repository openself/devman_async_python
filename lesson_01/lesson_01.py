import random
import time
import curses
import asyncio


TIC_TIMEOUT = 0.1
STAR_SYMBOLS = ["+", "*", ".", ":"]

def draw(canvas):
    canvas.border()
    curses.curs_set(False)

    (max_row, max_column) = canvas.getmaxyx()
    columns = [x for x in range(1, max_column - 1)]
    rows = [y for y in range(1, max_row - 1)]

    coroutines = list()

    for star in range(100):
        star = blink(canvas, random.choice(rows), random.choice(columns),
                     symbol=random.choice(STAR_SYMBOLS))

        coroutines.append(star)

    coroutines.append(fire(canvas, max_row // 2, max_column // 2))

    while True:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                del coroutines[-1]
            canvas.refresh()

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


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)