import pygame
from Path import Path

# size of screen:
width, height = 1200, 510  # height will be changed to suit the size of the board

# sizes (mm)
x_size_board = 34.2 + 200
y_size_board = 114.3
x_size_robot = 20.3
y_size_robot = 15

# distance between wheels (mm):
wheel_dis = 420

# image of robot and image of board:
image_robot = "resources/images/Electbot.png"
image_board = "resources/images/Map2023.png"


def display_screen():
    pygame.font.init()

    mm_px = x_size_board / width
    new_height = round(y_size_board / x_size_board * width)

    x_robot = (x_size_robot / x_size_board) * width
    y_robot = (y_size_robot / y_size_board) * new_height

    screen = pygame.display.set_mode([width, new_height])

    path = Path(width, new_height, 0, 0,
                x_robot, y_robot, wheel_dis,
                image_board, image_robot, mm_px)

    path.recover_path_from_rtf_file()

    simulator_screen(screen, path)
    path.PrintImportantPositions_to_rtf_file()
    path.print_FLL_path_to_rtf_file()
    path.print_FRC_path_to_rtf_file(50, 0.9)


def get_mouse_clicked_pos():
    pressed = pygame.mouse.get_pressed(3)
    pos = pygame.mouse.get_pos()
    return pressed[0], pos[0], pos[1]


def simulator_screen(screen, path):
    path.work = 0
    while path.work < 2:
        # update the screen
        pygame.display.flip()

        # clear the screen before drawing it again
        screen.fill(0)

        # get user input
        press, x, y = get_mouse_clicked_pos()
        events = pygame.event.get()
        pressed_keys = pygame.key.get_pressed()

        # change the path according to the user's input
        path.change(press, x, y, events, pressed_keys)
        path.update_changes()

        # draw the new path on the screen
        path.draw(screen, path.start_x, path.start_y)


def main():
    display_screen()


if __name__ == '__main__':
    main()
