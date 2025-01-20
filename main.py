import random
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import pygame
import requests
from bs4 import BeautifulSoup

# def event_pump(): # For debug purposes a seperate pumping thread is required otherwise everything hangs indefinitely
#     while True:
#         pygame.event.pump()
#         time.sleep(0.01)


# threading.Thread(target=event_pump, daemon=True).start()

WIDTH, HEIGHT = 1000, 1000
ROWS, COLS = 1000, 1000
CELL_SIZE = WIDTH // COLS

ALIVE_COLOUR = (0, 255, 0)
DEAD_COLOUR = (30, 30, 30)
GHOST_COLOUR = (1, 200, 1)
CELL_BORDER_COLOUR = (50, 50, 50)

evaluating = False

cell_manager = {}


# Initialize screen


def draw_grid(screen):
    screen.fill(DEAD_COLOUR)
    for x, y in cell_manager:
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, ALIVE_COLOUR, rect)
        # if not evaluating:
        #     pygame.draw.rect(screen, CELL_BORDER_COLOUR, rect, 1)  # Cell border


def set_cell(pos, state):
    x, y = pos
    col = x // CELL_SIZE
    row = y // CELL_SIZE
    if 0 <= col < COLS and 0 <= row < ROWS:
        if state == -1:
            cell_manager[(col, row)] = state
        else:
            if (col, row) in cell_manager:
                cell_manager.pop((col, row))


def randomise():
    for x in range(ROWS):
        for y in range(COLS):
            if random.randint(0, 4) == 0:
                cell_manager[(x, y)] = -1


def exit_game():
    pygame.quit()
    sys.exit()


# Bresenham's Line Algorithm
def get_all_points_connecting_two_points(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    err = dx - dy

    x, y = x1, y1
    while True:
        points.append((x, y))
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return points


GOSPER_GLIDER_GUN = [
    (0, 24),
    (1, 22), (1, 24),
    (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
    (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
    (4, 0), (4, 1), (4, 10), (4, 16), (4, 20), (4, 21),
    (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
    (6, 10), (6, 16), (6, 24),
    (7, 11), (7, 15),
    (8, 12), (8, 13),
]
GLIDER_64P2H1V0 = [(0, 5), (0, 6), (0, 7), (0, 23), (0, 24), (0, 25), (1, 4), (1, 8), (1, 22), (1, 26), (2, 3), (2, 4),
                   (2, 9), (2, 21), (2, 26), (2, 27), (3, 2), (3, 4), (3, 6), (3, 7), (3, 9), (3, 10), (3, 14), (3, 15),
                   (3, 16), (3, 20), (3, 21), (3, 23), (3, 24), (3, 26), (3, 28), (4, 1), (4, 2), (4, 4), (4, 9),
                   (4, 11), (4, 12), (4, 14), (4, 15), (4, 16), (4, 18), (4, 19), (4, 21), (4, 26), (4, 28), (4, 29),
                   (5, 0), (5, 5), (5, 9), (5, 14), (5, 16), (5, 21), (5, 25), (5, 30), (6, 12), (6, 18), (7, 0),
                   (7, 1), (7, 9), (7, 10), (7, 20), (7, 21), (7, 29), (7, 30)]
SPACESHIP_LOBSTER = [(0, 12), (0, 13), (0, 14), (1, 12), (2, 13), (2, 16), (2, 17), (3, 16), (3, 17), (4, 12), (4, 13),
                     (5, 13), (5, 14), (6, 12), (6, 15), (8, 14), (8, 17), (9, 14), (9, 18), (10, 15), (10, 16),
                     (10, 17), (10, 19), (11, 20), (12, 0), (12, 1), (12, 4), (12, 6), (12, 20), (13, 0), (13, 2),
                     (13, 4), (13, 5), (13, 19), (14, 0), (14, 5), (14, 8), (14, 9), (14, 23), (14, 24), (15, 6),
                     (15, 10), (15, 17), (15, 18), (15, 21), (15, 22), (15, 25), (16, 2), (16, 3), (16, 10), (16, 17),
                     (16, 20), (17, 2), (17, 3), (17, 8), (17, 10), (17, 15), (17, 16), (18, 9), (18, 15), (18, 19),
                     (18, 23), (19, 10), (19, 13), (19, 18), (19, 19), (20, 11), (20, 12), (20, 16), (20, 22), (20, 24),
                     (21, 15), (21, 24), (21, 25), (22, 15), (22, 20), (23, 14), (23, 18), (24, 14), (24, 20), (24, 21),
                     (25, 15), (25, 21)]
KNIGHTSHIP_SIR_ROBIN = [(0, 4), (0, 5), (1, 4), (1, 7), (2, 4), (2, 8), (3, 6), (3, 7), (3, 8), (4, 2), (4, 3), (4, 10),
                        (4, 11), (4, 12), (4, 13), (5, 2), (5, 4), (5, 5), (5, 10), (5, 11), (5, 12), (5, 13), (6, 1),
                        (6, 6), (6, 13), (6, 14), (6, 15), (7, 2), (7, 3), (7, 4), (7, 5), (7, 10), (7, 11), (7, 15),
                        (8, 0), (8, 10), (8, 11), (9, 1), (9, 5), (10, 6), (10, 7), (10, 8), (10, 11), (10, 12),
                        (10, 15), (11, 2), (11, 3), (11, 11), (11, 16), (12, 13), (12, 15), (12, 16), (13, 10),
                        (13, 11), (13, 18), (14, 11), (14, 12), (14, 14), (14, 15), (14, 16), (14, 18), (15, 10),
                        (15, 11), (15, 15), (15, 18), (16, 10), (16, 12), (16, 15), (16, 16), (17, 10), (17, 13),
                        (17, 15), (17, 17), (18, 10), (18, 11), (18, 12), (18, 19), (19, 11), (19, 13), (19, 15),
                        (19, 19), (20, 14), (20, 15), (20, 17), (20, 19), (21, 11), (21, 18), (21, 19), (21, 20),
                        (23, 11), (23, 21), (24, 11), (24, 15), (24, 22), (25, 12), (25, 18), (25, 19), (25, 20),
                        (25, 21), (25, 22), (26, 12), (26, 13), (26, 14), (27, 16), (27, 17), (28, 13), (28, 14),
                        (28, 15), (28, 18), (29, 11), (29, 13), (29, 14), (29, 15), (29, 17), (30, 10), (30, 14),
                        (30, 17), (31, 11), (31, 16), (31, 17), (31, 19), (31, 20), (31, 21), (32, 13), (32, 14),
                        (32, 15), (32, 16), (32, 18), (32, 23), (32, 24), (33, 13), (33, 15), (33, 16), (33, 17),
                        (33, 18), (33, 23), (33, 24), (34, 19), (35, 20), (35, 23), (35, 24), (36, 20), (36, 21),
                        (37, 21), (37, 22), (37, 23), (37, 24), (37, 25), (38, 25), (38, 26), (39, 19), (39, 20),
                        (39, 21), (39, 28), (40, 20), (40, 22), (40, 26), (40, 28), (41, 19), (41, 23), (41, 27),
                        (42, 19), (42, 23), (42, 24), (43, 18), (43, 25), (43, 27), (43, 28), (43, 29), (44, 19),
                        (44, 20), (44, 24), (44, 28), (44, 29), (45, 20), (45, 21), (45, 22), (45, 23), (45, 26),
                        (45, 29), (46, 22), (46, 23), (46, 27), (47, 21), (48, 21), (48, 22), (48, 24), (49, 20),
                        (50, 19), (50, 20), (50, 21), (50, 22), (50, 23), (51, 19), (51, 24), (52, 18), (52, 19),
                        (52, 20), (52, 22), (52, 23), (52, 24), (53, 18), (53, 20), (53, 21), (53, 22), (53, 23),
                        (53, 24), (54, 18), (55, 20), (56, 16), (56, 21), (56, 22), (56, 23), (56, 24), (57, 20),
                        (57, 21), (57, 22), (57, 23), (57, 25), (57, 26), (58, 17), (58, 18), (58, 19), (58, 24),
                        (59, 24), (59, 26), (60, 28), (61, 24), (61, 27), (61, 28), (62, 25), (62, 26), (62, 27),
                        (63, 22), (63, 23), (64, 21), (64, 22), (64, 23), (64, 29), (65, 24), (65, 25), (65, 28),
                        (65, 30), (66, 21), (66, 24), (66, 25), (66, 26), (66, 28), (66, 30), (67, 22), (67, 23),
                        (67, 25), (67, 28), (68, 24), (68, 26), (68, 29), (68, 30), (69, 26), (69, 27), (70, 22),
                        (70, 23), (70, 24), (70, 29), (71, 22), (71, 23), (71, 24), (71, 29), (72, 23), (72, 24),
                        (72, 28), (72, 29), (72, 30), (73, 24), (73, 25), (73, 27), (73, 28), (74, 25), (74, 26),
                        (75, 25), (77, 24), (77, 25), (78, 26)]
TWO_ENGINE_CORDERSHIP = [(0, 19), (0, 20), (1, 19), (1, 20), (1, 21), (1, 22), (2, 19), (2, 21), (2, 22), (4, 20),
                         (5, 19), (5, 20), (6, 19), (6, 20), (6, 21), (7, 21), (8, 33), (8, 34), (9, 33), (9, 34),
                         (16, 36), (17, 35), (17, 36), (18, 34), (18, 38), (19, 35), (19, 36), (19, 39), (20, 40),
                         (21, 37), (21, 39), (22, 38), (23, 38), (24, 38), (24, 39), (25, 38), (25, 39), (28, 13),
                         (28, 24), (29, 12), (29, 13), (29, 14), (29, 15), (29, 16), (29, 22), (29, 24), (29, 25),
                         (29, 37), (30, 11), (30, 22), (30, 26), (30, 36), (31, 12), (31, 13), (31, 22), (31, 23),
                         (31, 24), (31, 26), (31, 36), (31, 37), (32, 13), (32, 14), (32, 24), (32, 25), (32, 38),
                         (33, 0), (33, 1), (33, 15), (33, 37), (33, 38), (33, 39), (34, 0), (34, 1), (34, 37), (34, 38),
                         (34, 39), (41, 8), (41, 9), (42, 8), (42, 9), (42, 21), (42, 22), (43, 19), (43, 20), (43, 23),
                         (44, 24), (44, 28), (45, 18), (45, 24), (45, 28), (46, 19), (46, 22), (46, 23), (46, 27),
                         (46, 29), (47, 20), (47, 21), (47, 22), (47, 28), (48, 28)]
TEN_ENGINE_CORDERSHIP = [(0, 42), (1, 42), (2, 44), (2, 50), (3, 43), (3, 50), (3, 52), (4, 42), (4, 46), (4, 49),
                         (5, 43), (5, 46), (5, 48), (5, 50), (5, 51), (6, 48), (6, 50), (6, 51), (7, 62), (7, 63),
                         (8, 62), (8, 63), (15, 70), (15, 71), (16, 26), (16, 27), (16, 30), (16, 70), (16, 71),
                         (17, 29), (17, 31), (18, 28), (20, 30), (20, 31), (22, 31), (22, 32), (23, 30), (23, 78),
                         (23, 79), (24, 28), (24, 29), (24, 31), (24, 32), (24, 78), (24, 79), (25, 31), (25, 32),
                         (26, 16), (26, 29), (27, 16), (27, 39), (27, 40), (27, 41), (28, 18), (28, 24), (28, 38),
                         (29, 17), (29, 24), (29, 26), (29, 37), (29, 42), (29, 43), (30, 16), (30, 20), (30, 23),
                         (30, 36), (30, 40), (31, 17), (31, 20), (31, 22), (31, 24), (31, 25), (31, 36), (31, 39),
                         (31, 44), (31, 86), (31, 87), (32, 22), (32, 24), (32, 25), (32, 36), (32, 40), (32, 44),
                         (32, 77), (32, 86), (32, 87), (33, 37), (33, 38), (33, 40), (33, 42), (33, 43), (33, 44),
                         (33, 76), (33, 78), (34, 40), (35, 41), (35, 42), (35, 43), (35, 44), (35, 76), (35, 79),
                         (36, 30), (36, 31), (36, 32), (36, 43), (36, 44), (36, 78), (36, 79), (37, 29), (37, 33),
                         (37, 79), (38, 28), (38, 33), (39, 27), (39, 31), (40, 27), (40, 30), (40, 32), (40, 33),
                         (40, 34), (41, 27), (41, 35), (42, 0), (42, 1), (42, 4), (42, 29), (42, 33), (42, 35),
                         (42, 76), (42, 77), (43, 3), (43, 5), (43, 29), (43, 33), (43, 35), (43, 36), (43, 78),
                         (44, 2), (44, 31), (44, 32), (44, 33), (44, 35), (44, 36), (44, 76), (44, 77), (46, 4),
                         (46, 5), (48, 5), (48, 6), (49, 4), (50, 2), (50, 3), (50, 5), (50, 6), (50, 59), (50, 61),
                         (50, 68), (50, 70), (51, 5), (51, 6), (51, 58), (51, 68), (51, 70), (52, 3), (52, 59),
                         (52, 62), (52, 69), (53, 61), (53, 62), (53, 63), (58, 51), (59, 50), (59, 52), (61, 50),
                         (61, 53), (62, 7), (62, 8), (62, 52), (62, 53), (63, 7), (63, 8), (63, 53), (68, 50), (68, 51),
                         (69, 52), (70, 15), (70, 16), (70, 50), (70, 51), (71, 15), (71, 16), (76, 33), (76, 35),
                         (76, 42), (76, 44), (77, 32), (77, 42), (77, 44), (78, 23), (78, 24), (78, 33), (78, 36),
                         (78, 43), (79, 23), (79, 24), (79, 35), (79, 36), (79, 37), (86, 31), (86, 32), (87, 31),
                         (87, 32)]


def get_pattern(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        lines = soup.text.strip().split('\r\n')
        pattern_data = [line for line in lines if not line.startswith('!')]
        output = []
        for index in range(len(pattern_data)):
            data = pattern_data[index]
            for index1 in range(len(data)):
                if data[index1] == "O":
                    output.append((index, index1))
        return output
    else:
        print("err")
        print("Status code: {response.status_code}")


def edit_grid(screen):
    global evaluating
    global cell_manager
    running = True
    drawing = False
    state = 0
    previous_mouse_position = None
    shape_index = 0
    shapes = ["square", "circle", "gun", "64P2H1V0", "lobster", "sir_robin", "2_engine_cordership",
              "10_engine_cordership"]
    size = 1
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
                exit_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                drawing = True
                state = -1 if event.button == 1 else 0 if event.button == 3 else None
            elif event.type == pygame.MOUSEBUTTONUP:
                drawing = False
                previous_mouse_position = None
            elif event.type == pygame.MOUSEWHEEL:
                size = size + 1 if event.y > 0 else -1
                if size < 0:
                    size = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                evaluating = True
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                cell_manager = {}
                randomise()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                cell_manager = {}
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                shape_index = (shape_index + 1) % len(shapes)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                evaluate_game_step()
        if drawing:
            if previous_mouse_position is None:
                previous_mouse_position = pygame.mouse.get_pos()

            points = get_all_points_connecting_two_points(previous_mouse_position, pygame.mouse.get_pos())

            for (x, y) in points:
                set_cells((x, y), state, size, shapes[shape_index])
            previous_mouse_position = pygame.mouse.get_pos()

        draw_grid(screen)
        pygame.display.flip()


def set_cells(pos, state, brush_size=0, brush_shape="square"):
    x, y = pos
    col = x // CELL_SIZE
    row = y // CELL_SIZE
    affected_cells = []

    if brush_shape == "gun":
        affected_cells = [(col + dx, row + dy) for dx, dy in GOSPER_GLIDER_GUN]
    elif brush_shape == "64P2H1V0":
        affected_cells = [(col + dx, row + dy) for dx, dy in GLIDER_64P2H1V0]
    elif brush_shape == "lobster":
        affected_cells = [(col + dx, row + dy) for dx, dy in SPACESHIP_LOBSTER]
    elif brush_shape == "sir_robin":
        affected_cells = [(col + dx, row + dy) for dx, dy in KNIGHTSHIP_SIR_ROBIN]
    elif brush_shape == "2_engine_cordership":
        affected_cells = [(col + dx, row + dy) for dx, dy in TWO_ENGINE_CORDERSHIP]
    elif brush_shape == "10_engine_cordership":
        affected_cells = [(col + dx, row + dy) for dx, dy in TEN_ENGINE_CORDERSHIP]
    elif brush_shape == "square":
        # Square brush
        for dx in range(-brush_size, brush_size + 1):
            for dy in range(-brush_size, brush_size + 1):
                affected_cells.append((col + dx, row + dy))
    elif brush_shape == "circle":
        # Circular brush
        for dx in range(-brush_size, brush_size + 1):
            for dy in range(-brush_size, brush_size + 1):
                if dx ** 2 + dy ** 2 <= brush_size ** 2:
                    affected_cells.append((col + dx, row + dy))

    # Apply the state to affected cells
    for c, r in affected_cells:
        if 0 <= c < COLS and 0 <= r < ROWS:
            if state == -1:
                cell_manager[(c, r)] = state
            else:
                if (c, r) in cell_manager:
                    cell_manager.pop((c, r))


def evaluate_game_step():
    global cell_manager
    updated_cell_manager = {}
    for x, y in cell_manager:
        neighbors = [
            (x - 1, y - 1), (x, y - 1), (x + 1, y - 1), (x - 1, y), (x + 1, y), (x - 1, y + 1), (x, y + 1),
            (x + 1, y + 1)
        ]
        for (x1, y1) in neighbors:
            x11 = x1 - COLS if x1 >= COLS else (x1 + COLS if x1 < 0 else x1)
            y11 = y1 - ROWS if y1 >= ROWS else (y1 + COLS if y1 < 0 else y1)
            item = (x11, y11)
            if item in updated_cell_manager:
                updated_cell_manager[item] = updated_cell_manager[item] + 1
            else:
                updated_cell_manager[item] = 1
        if (x, y) not in updated_cell_manager:
            updated_cell_manager[(x, y)] = 0

    for key, value in updated_cell_manager.items():
        if key in cell_manager:
            if value < 2 or value > 3:
                cell_manager.pop(key)
        elif value == 3:
            cell_manager[key] = -1


def run_game_of_life_window():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Conway's Game of Life")
    global evaluating
    running = True
    evaluating = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
                exit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                evaluating = not evaluating
        if evaluating:
            evaluate_game_step()
        else:
            pygame.display.set_caption("Conway's Game of Life - Setup")
            edit_grid(screen)
            evaluating = True
            pygame.display.set_caption("Conway's Game of Life - Evaluating")
        draw_grid(screen)
        pygame.display.flip()


def main():
    threading.Thread(target=run_game_of_life_window, daemon=True).start()
    run_control_window()
    exit_game()


def on_icon_button_click():
    messagebox.showinfo("Info", "Icon button clicked!")


def on_text_button_click():
    messagebox.showinfo("Info", "Text button clicked!")


def run_control_window():
    # Create the main window
    root = tk.Tk()
    root.title("Example GUI with Icons")
    root.geometry("400x300")

    tk.Label(root, text="Shape").grid(row=0, column=0)
    tk.Label(root, text="Size").grid(row=0, column=2)
    tk.Label(root, text="Preview").grid(row=0, column=3, columnspan=2)


    # Create a label
    # label = tk.Label(root, text="Click a button:")
    # label.pack(pady=10)
    #
    # # Create a text-only button
    # text_button = tk.Button(root, text="Text Button", command=on_text_button_click)
    # text_button.pack(pady=10)

    # Create an icon button
    # Ensure you have an image file (e.g., "icon.png") in the same directory or provide the full path
    # icon_image = tk.PhotoImage(file="icon.png")  # Replace with your icon file path
    # icon_button = tk.Button(root, image=icon_image, command=on_icon_button_click)
    # icon_button.pack(pady=10)

    # Create a button with both text and an icon
    # icon_text_button = tk.Button(root, text="Icon + Text", image=icon_image, compound="left",
    #                              command=on_icon_button_click)
    # icon_text_button.pack(pady=10)

    # Run the application
    root.mainloop()


if __name__ == "__main__":
    main()
