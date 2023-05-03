import pygame
import math
from Robot import Robot
from SemiRobot import SemiRobot


def get_next_point(pos_x, pos_y, angle, dist):
    new_x = pos_x + dist * math.cos(math.radians(angle))
    new_y = pos_y + (dist * math.sin(math.radians(angle)) * -1)

    return new_x, new_y


def distance(x1, x2, y1, y2):
    dis = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return dis


class Path:
    def __init__(self, screen_width, screen_height, start_x, start_y, robot_width, robot_height,
                 wheel_dis, image_board, image_robot, mm_px):
        self.is_double_click = False
        self.previous_turning = 0

        self.has_arrived_robot_pos = -1  # False
        self.current_path_position = 0

        self.m_px = mm_px / 1000
        self.start_x = start_x
        self.start_y = start_y
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.robot_width = robot_width
        self.robot_height = robot_height
        self.wheel_dis = wheel_dis

        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 255)
        self.yellow = (250, 200, 0)
        self.exl = 1

        self.robots = [Robot(0, robot_width, robot_height, [30, 380])]

        self.robot_image = image_robot
        self.board_image = image_board

        self.press = 0
        self.x = 0
        self.y = 0
        self.last_x = 0
        self.last_y = 0
        self.last_press = 0
        self.pressed_robot = 0
        self.pressed_turn = 0
        self.touch_turn = False
        self.touching_robot = False
        self.turning_positions = []
        self.turn_directions = []
        self.exception_turning_points = [0]
        self.centers = []
        self.important_positions = []

        self.work = 0
        self.semi_robot = SemiRobot(self.robots[0], self.wheel_dis)

    def does_any_robot_touched(self):
        for i in range(len(self.robots))[::-1]:
            touch_robot = self.robots[i].touch_the_robot(self.x, self.y, 2)
            if touch_robot:
                return True, i
        return False, self.pressed_robot

    def does_any_turning_touched(self):
        for i in range(len(self.turning_positions)):
            if distance(self.x, self.turning_positions[i][0][0], self.y, self.turning_positions[i][0][1]) <= 10:
                return True, i
        return False, self.pressed_turn

    def get_robot_in_screen_limits(self, robot):
        # get the robot in the screen if it out of the screen's limits
        if robot.min_x() < 0:
            robot.center[0] -= robot.min_x()

        if robot.max_x() > self.screen_width:
            robot.center[0] -= robot.max_x() - self.screen_width

        if robot.max_y() > self.screen_height:
            robot.center[1] -= robot.max_y() - self.screen_height

        if robot.min_y() < 0:
            robot.center[1] -= robot.min_y()

        robot.update()

        return robot

    def update_changes(self):
        # find the place the robot lines concentrated
        self.important_positions = []
        lines = []
        self.turning_positions = []
        for j in range(len(self.robots)):
            # middle points
            self.important_positions.append(self.robots[j].center)

            # lines
            lines.append(self.robots[j].lines[4])
            if j > 0:
                if (self.robots[j].angle + 360) % 180 != (self.robots[j - 1].angle + 360) % 180:
                    # turning points
                    if (self.robots[j - 1].angle + 360) % 180 != 90 and (self.robots[j].angle + 360) % 180 != 90:
                        turn_x = (lines[j][1] - lines[j - 1][1]) / (lines[j - 1][0] - lines[j][0])
                        turn_y = turn_x * lines[j - 1][0] + lines[j - 1][1]
                        turn_x = turn_x
                    elif (self.robots[j - 1].angle + 360) % 180 == 90:
                        turn_x = self.important_positions[j - 1][0]
                        turn_y = turn_x * lines[j][0] + lines[j][1]
                    else:
                        turn_x = self.important_positions[j][0]
                        turn_y = turn_x * lines[j - 1][0] + lines[j - 1][1]
                    self.turning_positions.append([[turn_x, turn_y], [turn_x, turn_y], [turn_x, turn_y]])

        # defined turn type, the center of the turning, the radius of the turning...
        for h in range(len(self.turning_positions)):
            x_circle = self.turning_positions[h][1][0] + self.exception_turning_points[h] * math.cos(
                math.radians(self.robots[h].angle))
            y_circle = self.turning_positions[h][1][1] + self.exception_turning_points[h] * math.sin(
                math.radians(self.robots[h].angle)) * -1

            d1 = distance(self.turning_positions[h][1][0], x_circle, self.turning_positions[h][1][1], y_circle)

            self.turning_positions[h][0][0] = x_circle
            self.turning_positions[h][0][1] = y_circle

            direction = 0
            if self.exception_turning_points[h] != 0:
                direction = self.exception_turning_points[h] / abs(self.exception_turning_points[h]) * (-1)

            self.turning_positions[h][2][0], self.turning_positions[h][2][1] = get_next_point(
                self.turning_positions[h][1][0],
                self.turning_positions[h][1][1],
                self.robots[h + 1].angle, d1 * direction)

            permit = d1 / (
                math.cos(math.radians(
                    (self.robots[h].angle + self.robots[h + 1].angle) / 2 - 90 - self.robots[h + 1].angle)))

            x_center, y_center = get_next_point(self.turning_positions[h][1][0], self.turning_positions[h][1][1],
                                                (self.robots[h].angle + self.robots[h + 1].angle) / 2 + 90,
                                                direction * permit * -1)
            self.centers[h] = x_center, y_center

    def change(self, press, x, y, events, keys_pressed):
        if self.work < 1:
            # get robot poss by mouse
            self.last_x = self.x
            self.last_y = self.y
            self.last_press = self.press
            self.press, self.x, self.y = press, x - self.start_x, y - self.start_y
            if self.press == 1:
                if self.last_press == 0:
                    if self.is_double_click:
                        self.previous_turning = self.pressed_turn

                    self.touching_robot, self.pressed_robot = self.does_any_robot_touched()
                    self.touch_turn, self.pressed_turn = self.does_any_turning_touched()

                    if self.touch_turn:
                        self.touching_robot = False

                    if self.touch_turn and self.is_double_click:
                        self.mate_turnings(self.previous_turning, self.pressed_turn)
                else:
                    if self.touching_robot:
                        self.robots[self.pressed_robot].center[0] += self.x - self.last_x
                        self.robots[self.pressed_robot].center[1] += self.y - self.last_y
                        self.robots[self.pressed_robot].update()

        # use the events
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.work < 1:
                    if event.key == pygame.K_KP_PLUS:
                        if len(self.robots) - len(self.turning_positions) == 1:
                            self.robots.append(Robot(0, self.robot_width, self.robot_height, [30, 380]))
                            self.pressed_robot = len(self.robots) - 1
                            self.exception_turning_points.append(0)
                            self.centers.append([0, 0])
                            self.turn_directions.append(1)

                    if (event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE) and len(self.robots) > 1:
                        self.robots.remove(self.robots[self.pressed_robot])
                        self.exception_turning_points.remove(self.exception_turning_points[self.pressed_robot - 1])
                        self.centers.remove(self.centers[self.pressed_robot - 1])
                        self.turn_directions.remove(self.turn_directions[self.pressed_robot])
                        self.pressed_robot = -1

                    if event.key == pygame.K_SPACE and len(
                            self.turn_directions) > self.pressed_turn and self.touch_turn:
                        self.turn_directions[self.pressed_turn] *= -1

                if event.key == pygame.K_KP_ENTER and len(self.robots) - len(self.turning_positions) == 1:
                    self.semi_robot = SemiRobot(self.robots[0], self.wheel_dis)
                    self.semi_robot.get_all_path(self.robots,
                                                 self.turning_positions, self.centers, self.turn_directions)
                    self.semi_robot.update()
                    self.work += 1

                # Quit
                if event.key == pygame.K_ESCAPE:
                    exit(0)
            # Quit
            if event.type == pygame.QUIT:
                exit(0)

        # change the position of the robot
        for i in range(1):
            if keys_pressed[pygame.K_LCTRL] and self.work < 1:
                self.is_double_click = True
            else:
                self.is_double_click = False

            if keys_pressed[pygame.K_UP]:
                if self.exl < 9:
                    self.exl += 1
            if keys_pressed[pygame.K_DOWN]:
                if self.exl > 1:
                    self.exl -= 1
            if keys_pressed[pygame.K_a]:
                if self.work < 1:
                    if self.touching_robot:
                        self.robots[self.pressed_robot].center[0] -= self.exl
                    elif self.touch_turn:
                        self.exception_turning_points[self.pressed_turn] = self.exception_turning_points[
                                                                               self.pressed_turn] - self.exl
                elif self.work == 1:
                    self.semi_robot.shift(self.exl * -1)

            if keys_pressed[pygame.K_d]:
                if self.work < 1:
                    if self.touching_robot:
                        self.robots[self.pressed_robot].center[0] += self.exl
                    elif self.touch_turn:
                        self.exception_turning_points[self.pressed_turn] = self.exception_turning_points[
                                                                               self.pressed_turn] + self.exl
                elif self.work == 1:
                    self.semi_robot.shift(self.exl)

            if keys_pressed[pygame.K_w]:
                if self.work < 1:
                    if self.touching_robot:
                        self.robots[self.pressed_robot].center[1] -= self.exl
            if keys_pressed[pygame.K_s]:
                if self.work < 1:
                    if self.touching_robot:
                        self.robots[self.pressed_robot].center[1] += self.exl

            # turn the robot and change the exception
            turn = 0
            if keys_pressed[pygame.K_LEFT]:
                if self.work < 1:
                    if self.touching_robot:
                        turn = 1
                    elif self.touch_turn:
                        self.exception_turning_points[self.pressed_turn] = self.exception_turning_points[
                                                                               self.pressed_turn] - self.exl
                elif self.work == 1:
                    self.semi_robot.shift(self.exl * -1)
            elif keys_pressed[pygame.K_RIGHT]:
                if self.work < 1:
                    if self.touching_robot:
                        turn = -1
                    elif self.touch_turn:
                        self.exception_turning_points[self.pressed_turn] = self.exception_turning_points[
                                                                               self.pressed_turn] + self.exl
                elif self.work == 1:
                    self.semi_robot.shift(self.exl)
            else:
                turn = 0

            if self.work < 1:
                self.robots[self.pressed_robot].angle = self.robots[self.pressed_robot].angle + self.exl * turn
                self.robots[self.pressed_robot].angle = ((self.robots[self.pressed_robot].angle % 360) + 360) % 360
                self.robots[self.pressed_robot].update()

        if self.work < 1:
            # get the robot in the screen if it out of the screen's limits
            self.robots[self.pressed_robot] = self.get_robot_in_screen_limits(self.robots[self.pressed_robot])

    def mate_turnings(self, previous_turning, current_turning):
        first_turning, last_turning = min(previous_turning, current_turning), max(previous_turning, current_turning)
        delta_x = self.turning_positions[last_turning][0][0] - self.turning_positions[first_turning][2][0]
        delta_y = self.turning_positions[last_turning][0][1] - self.turning_positions[first_turning][2][1]

        self.robots[first_turning + 1].center[0] = self.turning_positions[first_turning][2][0]
        self.robots[first_turning + 1].center[1] = self.turning_positions[first_turning][2][1]
        self.robots[first_turning + 1].update()
        for i in range(first_turning + 1, len(self.turning_positions)):
            self.turning_positions[i][0][0] -= delta_x
            self.turning_positions[i][0][1] -= delta_y

            self.turning_positions[i][1][0] -= delta_x
            self.turning_positions[i][1][1] -= delta_y

            self.turning_positions[i][2][0] -= delta_x
            self.turning_positions[i][2][1] -= delta_y

            self.robots[i + 1].center[0] -= delta_x
            self.robots[i + 1].center[1] -= delta_y
            self.robots[i + 1].update()

    def draw(self, screen, start_x, start_y):
        # draw the screen's elements

        # draw the board
        board = pygame.image.load(self.board_image)
        board = pygame.transform.scale(board, (self.screen_width, self.screen_height))
        screen.blit(board, (start_x, start_y))

        # draw the important-positions-path_robots
        if self.work < 1:
            for i in range(len(self.robots)):
                robot = pygame.image.load(self.robot_image)
                robot = pygame.transform.scale(robot, (round(self.robot_width), round(self.robot_height)))
                robot = pygame.transform.rotate(robot, self.robots[i].angle)
                extensions = self.robots[i].get_extensions()
                screen.blit(robot, (
                    self.robots[i].center[0] + extensions[0] + start_x,
                    self.robots[i].center[1] - extensions[1] + start_y))

                pygame.draw.circle(screen, (0, 0, 0), self.robots[i].center, 10)
                if i == self.pressed_robot and self.touching_robot:
                    self.draw_corners(screen, self.robots[i].square, self.start_x, self.start_y, self.yellow)
                else:
                    self.draw_corners(screen, self.robots[i].square, self.start_x, self.start_y, self.green)

        # draw the simulated robot along the path
        if self.work == 1:
            robot = pygame.image.load(self.robot_image)
            robot = pygame.transform.scale(robot, (round(self.robot_width), round(self.robot_height)))
            robot = pygame.transform.rotate(robot, self.semi_robot.angle)
            extensions = self.semi_robot.get_extensions()
            screen.blit(robot, (
                self.semi_robot.center[0] + extensions[0] + start_x,
                self.semi_robot.center[1] - extensions[1] + start_y))

            self.draw_corners(screen, self.semi_robot.square, start_x, start_y, self.yellow)

        # draw the simulated drive path
        for i in range(len(self.robots)):
            if i > 0 and len(self.turning_positions) > i - 1:
                # draw line from robot to it's next turn, and from the next turn to the next robot
                ####
                pygame.draw.line(screen, self.red,
                                 [self.important_positions[i - 1][0] + start_x,
                                  self.important_positions[i - 1][1] + start_y],
                                 [self.turning_positions[i - 1][0][0] + start_x,
                                  self.turning_positions[i - 1][0][1] + start_y], 5)
                pygame.draw.line(screen, self.red,
                                 [self.turning_positions[i - 1][2][0] + start_x,
                                  self.turning_positions[i - 1][2][1] + start_y],
                                 [self.important_positions[i][0] + start_x, self.important_positions[i][1] + start_y],
                                 5)
                ####
                angle_turn = (self.robots[i].angle - self.robots[i - 1].angle + 720) % 360

                if angle_turn >= 180:
                    angle_turn -= 360
                if angle_turn % 180 != 0 and distance(self.centers[i - 1][0], self.turning_positions[i - 1][1][0],
                                                      self.centers[i - 1][1],
                                                      self.turning_positions[i - 1][1][1]) > 1:

                    radius = distance(self.centers[i - 1][0], self.turning_positions[i - 1][0][0],
                                      self.centers[i - 1][1],
                                      self.turning_positions[i - 1][0][1])
                    point = get_next_point(
                        self.centers[i - 1][0], self.centers[i - 1][1],
                        self.robots[i - 1].angle - 90 + 180, radius)
                    if distance(self.turning_positions[i - 1][0][0], point[0],
                                self.turning_positions[i - 1][0][1], point[1]) > 0.1:
                        radius *= -1

                    last_point = [self.turning_positions[i - 1][0][0], self.turning_positions[i - 1][0][1]]
                    new_point = [0, 0]
                    dist = 1
                    direction_turn = 1
                    if angle_turn >= 0:
                        direction_turn *= 1
                    else:
                        direction_turn *= -1

                    angle_delta = (dist / (abs(radius) * 2 * math.pi)) * 360 * self.turn_directions[
                        i - 1] * direction_turn
                    current_angle = self.robots[i - 1].angle
                    for j in range(round((2 * abs(radius) * math.pi / dist) * (
                            (1 - self.turn_directions[i - 1]) / 2 + self.turn_directions[i - 1] * abs(
                        angle_turn) / 360))):
                        new_point[0], new_point[1] = get_next_point(
                            self.centers[i - 1][0], self.centers[i - 1][1],
                            current_angle - 90 + 180 + angle_delta, radius)
                        current_angle += angle_delta
                        pygame.draw.line(screen, self.blue, [last_point[0] + start_x, last_point[1] + start_y],
                                         [new_point[0] + start_x, new_point[1] + start_y], 5)
                        last_point[0], last_point[1] = new_point[0], new_point[1]
                    pygame.draw.line(screen, self.blue, [last_point[0] + start_x, last_point[1] + start_y],
                                     [self.turning_positions[i - 1][2][0] + start_x,
                                      self.turning_positions[i - 1][2][1] + start_y], 5)

                if self.touch_turn and self.pressed_turn + 1 == i and self.work < 1:
                    pygame.draw.circle(screen, self.yellow,
                                       [self.turning_positions[i - 1][0][0] + start_x,
                                        self.turning_positions[i - 1][0][1] + start_y],
                                       10,
                                       10)
                else:
                    pygame.draw.circle(screen, self.blue,
                                       [self.turning_positions[i - 1][0][0] + start_x,
                                        self.turning_positions[i - 1][0][1] + start_y], 10,
                                       10)

    def shift_semi_robot1(self, shift):
        for i in range(abs(shift)):
            on_the_line = self.semi_robot.angle == self.robots[self.current_path_position].angle

            is_before_turn = self.current_path_position < len(self.robots) - 1 and distance(
                self.semi_robot.center[0],
                self.turning_positions[
                    self.current_path_position][
                    0][0],
                self.semi_robot.center[1],
                self.turning_positions[
                    self.current_path_position][
                    0][
                    1]) < 1 and shift > 0 and self.has_arrived_robot_pos == 1
            is_after_turn = self.current_path_position > 0 and (distance(self.semi_robot.center[0],
                                                                         self.turning_positions[
                                                                             self.current_path_position - 1][
                                                                             2][0],
                                                                         self.semi_robot.center[1],
                                                                         self.turning_positions[
                                                                             self.current_path_position - 1][
                                                                             2][
                                                                             1]) < 1) and shift < 0 and self.has_arrived_robot_pos == -1
            start_limit = self.current_path_position == 0 and distance(self.semi_robot.center[0],
                                                                       self.robots[0].center[0],
                                                                       self.semi_robot.center[1],
                                                                       self.robots[0].center[
                                                                           1]) < 1 and shift < 0
            end_limit = self.current_path_position == len(self.robots) - 1 and distance(
                self.semi_robot.center[0],
                self.robots[-1].center[0],
                self.semi_robot.center[1],
                self.robots[-1].center[
                    1]) < 1 and shift > 0
            if on_the_line and (not is_before_turn) and (not is_after_turn) and (not start_limit) and (
                    not end_limit):
                line_direction = 1
                if self.current_path_position < len(self.robots) - 1:
                    if distance(self.semi_robot.center[0],
                                self.robots[self.current_path_position].center[0],
                                self.semi_robot.center[1],
                                self.robots[self.current_path_position].center[1]) < 1 and (
                            (self.has_arrived_robot_pos == -1 and shift > 0) or (
                            self.has_arrived_robot_pos == 1 and shift < 0)):
                        self.has_arrived_robot_pos *= -1
                        self.semi_robot.center[0] = self.robots[self.current_path_position].center[0]
                        self.semi_robot.center[1] = self.robots[self.current_path_position].center[1]
                        self.semi_robot.update()
                    if self.current_path_position > 0 and self.robots[
                        self.current_path_position].is_direct_forward(
                        self.turning_positions[self.current_path_position][0][0],
                        self.turning_positions[self.current_path_position][0][1]) == self.robots[
                        self.current_path_position].is_direct_forward(
                        self.turning_positions[self.current_path_position - 1][2][0],
                        self.turning_positions[self.current_path_position - 1][2][1]):
                        line_direction *= self.has_arrived_robot_pos

                    if self.robots[self.current_path_position].is_direct_forward(
                            self.turning_positions[self.current_path_position][0][0],
                            self.turning_positions[self.current_path_position][0][1]):
                        line_direction *= 1
                    else:
                        line_direction *= -1
                else:
                    if self.robots[-1].is_direct_forward(self.turning_positions[-1][2][0],
                                                         self.turning_positions[-1][2][1]):
                        line_direction *= -1
                    else:
                        line_direction *= 1
                self.semi_robot.center[0], self.semi_robot.center[1] = get_next_point(
                                self.semi_robot.center[0], self.semi_robot.center[1],
                                self.semi_robot.angle, abs(shift) / shift * line_direction)
                self.semi_robot.update()
            else:
                if (not start_limit) and self.current_path_position < len(self.robots) - 1 and (
                        not is_after_turn):
                    angle_turn = (self.robots[self.current_path_position + 1].angle - self.robots[
                        self.current_path_position].angle + 720) % 360
                    if angle_turn >= 180:
                        angle_turn -= 360

                    direction_turn = 1
                    if angle_turn >= 0:
                        direction_turn *= 1
                    else:
                        direction_turn *= -1

                    angle_delta = self.turn_directions[
                                      self.current_path_position] * direction_turn * abs(shift) / shift
                    radius = distance(self.centers[self.current_path_position][0],
                                      self.turning_positions[self.current_path_position][0][0],
                                      self.centers[self.current_path_position][1],
                                      self.turning_positions[self.current_path_position][0][1])
                    point = get_next_point(
                        self.centers[self.current_path_position][0],
                        self.centers[self.current_path_position][1],
                        self.robots[self.current_path_position].angle - 90 + 180, radius)
                    if distance(self.turning_positions[self.current_path_position][0][0], point[0],
                                self.turning_positions[self.current_path_position][0][1],
                                point[1]) > 0.0001:
                        radius *= -1

                    if shift > 0 and abs(
                            self.robots[
                                self.current_path_position + 1].angle - self.semi_robot.angle) <= abs(angle_delta):
                        angle_delta = self.robots[
                                          self.current_path_position + 1].angle - self.semi_robot.angle
                        self.semi_robot.angle += angle_delta
                        self.semi_robot.update()

                        self.current_path_position += 1
                        self.has_arrived_robot_pos = -1
                    elif shift < 0 and abs(
                            self.robots[
                                self.current_path_position].angle - self.semi_robot.angle) <= abs(
                        angle_delta):

                        angle_delta = self.semi_robot.angle - self.robots[
                            self.current_path_position].angle

                        self.semi_robot.angle -= angle_delta
                        self.semi_robot.update()

                        self.has_arrived_robot_pos = 1
                    else:
                        dist = 1

                        if abs(radius) > 0:
                            angle_delta *= (dist / (abs(radius) * 2 * math.pi)) * 360

                        self.semi_robot.angle += angle_delta
                        self.semi_robot.update()
                else:
                    if self.current_path_position > 0:
                        if distance(self.semi_robot.center[0],
                                    self.turning_positions[self.current_path_position - 1][2][0],
                                    self.semi_robot.center[1],
                                    self.turning_positions[self.current_path_position - 1][2][
                                        1]) < 1 and shift < 0:
                            self.current_path_position -= 1
                            self.has_arrived_robot_pos = 1

                        elif self.current_path_position == len(self.robots) - 1:
                            self.semi_robot.center[0] = self.robots[-1].center[0]
                            self.semi_robot.center[1] = self.robots[-1].center[1]
                            self.semi_robot.angle = self.robots[-1].angle
                            self.semi_robot.update()
                    else:
                        self.semi_robot.center[0] = self.robots[0].center[0]
                        self.semi_robot.center[1] = self.robots[0].center[1]
                        self.semi_robot.angle = self.robots[0].angle
                        self.semi_robot.update()

    def recover_path_from_rtf_file(self):
        current_robot = 0
        turning_index = 0
        positions_num = 0
        self.turn_directions = []
        with open("ImportantPositions.rtf") as file:
            for line in file:
                if line[0] == "p":
                    positions_num += 1
                    if (positions_num - 1) % 3 == 0:
                        position_type = "robot"
                        current_robot += 1
                        if current_robot > 1:
                            self.robots.append(Robot(0, self.robot_width, self.robot_height, [0, 0]))
                        self.turning_positions.append([[0, 0], [0, 0], [0, 0]])
                        self.turn_directions.append(1)
                    else:
                        position_type = "turning_point"
                        if (positions_num - 1) % 3 == 1:
                            turning_index = 0
                        else:
                            turning_index = 2
                else:
                    if line[0] == "d":
                        self.turn_directions[current_robot - 1] = int(line[16::])
                    if line[0] == "x":
                        if position_type == "robot":
                            self.robots[current_robot - 1].center[0] = float(line[4::]) / self.m_px
                        else:
                            self.turning_positions[current_robot - 1][turning_index][0] = float(line[4::]) / self.m_px
                    elif line[0] == "y":
                        if position_type == "robot":
                            self.robots[current_robot - 1].center[1] = float(line[4::]) / self.m_px
                        else:
                            self.turning_positions[current_robot - 1][turning_index][1] = float(line[4::]) / self.m_px
                    elif line[0] == "a":
                        if position_type == "robot":
                            self.robots[current_robot - 1].angle = float(line[8::1])

        lines = []
        self.exception_turning_points = []
        self.important_positions = []
        self.centers = []
        for i in range(len(self.robots)):
            self.robots[i].update()
            self.important_positions.append(self.robots[i].center)

            # adjust the rest of the variables to the path_robots & turning_points:
            lines.append(self.robots[i].lines[4])
            if i > 0:
                if (self.robots[i].angle + 360) % 180 != (self.robots[i - 1].angle + 360) % 180:
                    # turning points
                    if (self.robots[i - 1].angle + 360) % 180 != 90 and (self.robots[i].angle + 360) % 180 != 90:
                        turn_x = (lines[i][1] - lines[i - 1][1]) / (lines[i - 1][0] - lines[i][0])
                        turn_y = turn_x * lines[i - 1][0] + lines[i - 1][1]
                    elif (self.robots[i - 1].angle + 360) % 180 == 90:
                        turn_x = self.important_positions[i - 1][0]
                        turn_y = turn_x * lines[i][0] + lines[i][1]
                    else:
                        turn_x = self.important_positions[i][0]
                        turn_y = turn_x * lines[i - 1][0] + lines[i - 1][1]
                    self.turning_positions[i - 1][1] = [turn_x, turn_y]

                self.exception_turning_points.append(distance(self.turning_positions[i - 1][0][0],
                                                              self.turning_positions[i - 1][1][0],
                                                              self.turning_positions[i - 1][0][1],
                                                              self.turning_positions[i - 1][1][1]))
                if self.exception_turning_points[-1] != 0:
                    d1 = distance(self.turning_positions[i - 1][1][0], self.turning_positions[i - 1][0][0],
                                  self.turning_positions[i - 1][1][1], self.turning_positions[i - 1][0][1])
                    new_x, new_y = get_next_point(self.turning_positions[i - 1][1][0],
                                                  self.turning_positions[i - 1][1][1], self.robots[i - 1].angle, d1)

                    if distance(new_x, self.turning_positions[i - 1][0][0], new_y,
                                self.turning_positions[i - 1][0][1]) < 0.0001:
                        direction_turn = 1
                    else:
                        direction_turn = -1

                    self.exception_turning_points[-1] *= direction_turn

                self.centers.append([0, 0])

    def PrintImportantPositions_to_rtf_file(self):
        rtf_file = "ImportantPositions.rtf"
        open(rtf_file, 'w').write(r'')  # clean the file

        for i in range(len(self.turning_positions)):
            open(rtf_file, 'a').write(r'' + "position " + str(3 * i + 1) + ":" + '\n')

            text = str(self.robots[i].center[0] * self.m_px)
            open(rtf_file, 'a').write(r'' + "x = " + text + '\n')

            text = str(self.robots[i].center[1] * self.m_px)
            open(rtf_file, 'a').write(r'' + "y = " + text + '\n')

            text = str(self.robots[i].angle)
            open(rtf_file, 'a').write(r'' + "angle = " + text + '\n')

            open(rtf_file, 'a').write(r'' + '\n')
            open(rtf_file, 'a').write(r'' + "position " + str(3 * i + 2) + '\n')

            text = str(self.turning_positions[i][0][0] * self.m_px)
            open(rtf_file, 'a').write(r'' + "x = " + text + '\n')

            text = str(self.turning_positions[i][0][1] * self.m_px)
            open(rtf_file, 'a').write(r'' + "y = " + text + '\n')

            text = str(self.robots[i].angle)
            open(rtf_file, 'a').write(r'' + "angle = " + text + '\n')

            text = str(self.turn_directions[i])
            open(rtf_file, 'a').write(r'' + '\n')
            open(rtf_file, 'a').write(r'' + "direction turn = " + text + '\n')

            open(rtf_file, 'a').write(r'' + '\n')
            open(rtf_file, 'a').write(r'' + "position " + str(3 * i + 3) + '\n')

            text = str(self.turning_positions[i][2][0] * self.m_px)
            open(rtf_file, 'a').write(r'' + "x = " + text + '\n')

            text = str(self.turning_positions[i][2][1] * self.m_px)
            open(rtf_file, 'a').write(r'' + "y = " + text + '\n')

            text = str(self.robots[i + 1].angle)
            open(rtf_file, 'a').write(r'' + "angle = " + text + '\n')
            open(rtf_file, 'a').write(r'' + '\n')

        open(rtf_file, 'a').write(r'' + "position " + str((len(self.robots) * 3 - 1)) + '\n')

        text = str(self.robots[-1].center[0] * self.m_px)
        open(rtf_file, 'a').write(r'' + "x = " + text + '\n')

        text = str(self.robots[-1].center[1] * self.m_px)
        open(rtf_file, 'a').write(r'' + "y = " + text + '\n')

        text = str(self.robots[-1].angle)
        open(rtf_file, 'a').write(r'' + "angle = " + text + '\n')

    def print_FLL_path_to_rtf_file(self):
        rtf_file = "Instructions_For_Path.rtf"
        open(rtf_file, 'w').write(r'')  # clean the file

        text = ""
        dis = 0
        for i in range(len(self.turning_positions)):
            # drive straight from current position to the next turn-position
            if dis != 0 and len(text) > 0:
                if (text[15] == "f" and False == self.robots[i].is_direct_forward(self.turning_positions[i][0][0],
                                                                        self.turning_positions[i][0][1])) or (
                        text[15] == "b" and self.robots[i].is_direct_forward(self.turning_positions[i][0][0],
                                                                        self.turning_positions[i][0][1])):
                    open(rtf_file, 'a').write(r'' + text + '\n')
                    dis = 0

            text = "Drive straight"
            if self.robots[i].is_direct_forward(self.turning_positions[i][0][0], self.turning_positions[i][0][1]):
                text += " forward "
            else:
                text += " backward "
            dis += distance(self.robots[i].center[0], self.turning_positions[i][0][0], self.robots[i].center[1],
                            self.turning_positions[i][0][1]) * self.m_px * 1000
            text += str(round(dis))
            text += " millimeters"

            if dis != 0:
                open(rtf_file, 'a').write(r'' + text + '\n')
                open(rtf_file, 'a').write(r'' + '\n')

            # declare turn type, wheels percentage-powers...
            angle_turn = (self.robots[i + 1].angle - self.robots[i].angle + 720) % 360
            if angle_turn > 180:
                angle_turn -= 360

            direction_turn = 1
            text = "Turn"
            if self.exception_turning_points[i] == 0:
                text += " in place "
                if (angle_turn < 0) ^ (self.turn_directions[i] == -1):
                    direction_turn = -1
            elif (self.exception_turning_points[i] < 0) ^ (self.turn_directions[i] == -1):
                text += " forward "
            else:
                text += " backward "
                direction_turn = -1

            if self.turn_directions[i] == -1:
                angle_turn -= 360 * abs(angle_turn) / angle_turn

            text += str(round(angle_turn))
            text += " degrees"

            open(rtf_file, 'a').write(r'' + text + '\n')

            radius = distance(self.centers[i][0], self.turning_positions[i][0][0], self.centers[i][1],
                              self.turning_positions[i][0][1])
            dominant_motors = radius + (self.wheel_dis / 2)
            less_dominant_motors = radius - (self.wheel_dis / 2)

            dominant_motors_percentage = 100
            less_dominant_motors_percentage = less_dominant_motors * (dominant_motors_percentage / dominant_motors)

            if (direction_turn == -1 and angle_turn < 0) or (direction_turn == 1 and angle_turn > 0):
                right_motor_percentage = dominant_motors_percentage * direction_turn
                left_motor_percentage = less_dominant_motors_percentage * direction_turn
            else:
                right_motor_percentage = less_dominant_motors_percentage * direction_turn
                left_motor_percentage = dominant_motors_percentage * direction_turn

            text = "Right-Motors Power: "
            text += str(round(right_motor_percentage))
            open(rtf_file, 'a').write(r'' + text + '\n')

            text = "Left-Motors Power: "
            text += str(round(left_motor_percentage))
            open(rtf_file, 'a').write(r'' + text + '\n')

            open(rtf_file, 'a').write(r'' + '\n')

            # drive straight to the next mark position
            dis = distance(self.robots[i + 1].center[0], self.turning_positions[i][2][0], self.robots[i + 1].center[1],
                           self.turning_positions[i][2][1])

            text = "Drive straight"
            if not self.robots[i + 1].is_direct_forward(self.turning_positions[i][2][0],
                                                        self.turning_positions[i][2][1]):
                text += " forward "
            else:
                text += " backward "

            dis *= self.m_px * 1000
            text += str(round(dis))
            text += " millimeters"

        # drive straight from current position to the next turn-position
        if dis != 0:
            open(rtf_file, 'a').write(r'' + text + '\n')
            open(rtf_file, 'a').write(r'' + '\n')

    def print_FRC_path_to_rtf_file(self, cpu_iterations_for_sec, speed_meters_by_sec):
        # print("minimal speed", self.m_px*cpu_iterations_for_sec)
        rtf_file = "Milestones.rtf"
        open(rtf_file, 'w').write(r'')  # clean the file
        delta_pos = round((speed_meters_by_sec / self.m_px) / cpu_iterations_for_sec)
        at_end = 1
        while at_end >= 0:
            text = "x: "
            text += str(self.semi_robot.center[0] * self.m_px)
            text += " y: "
            text += str(self.semi_robot.center[1] * self.m_px)
            text += " angle: "
            text += str(self.semi_robot.angle)
            open(rtf_file, 'a').write(r'' + text + '\n')
            self.semi_robot.shift(delta_pos)
            if (self.semi_robot.center[0] == self.robots[-1].center[0] and
               self.semi_robot.center[1] == self.robots[-1].center[1] and
               self.semi_robot.angle == self.robots[-1].angle):
                at_end -= 1
            else:
                at_end = 1

    @staticmethod
    def draw_corners(screen, square, start_x, start_y, color):
        pygame.draw.line(screen, color, [round(square[0][0] + start_x), round(square[0][1] + start_y)],
                         [round(square[1][0] + start_x), round(square[1][1] + start_y)], 3)

        pygame.draw.line(screen, color, [round(square[1][0] + start_x), round(square[1][1] + start_y)],
                         [round(square[2][0] + start_x), round(square[2][1] + start_y)], 3)

        pygame.draw.line(screen, color, [round(square[2][0] + start_x), round(square[2][1] + start_y)],
                         [round(square[3][0] + start_x), round(square[3][1] + start_y)], 3)

        pygame.draw.line(screen, color, [round(square[3][0] + start_x), round(square[3][1] + start_y)],
                         [round(square[0][0] + start_x), round(square[0][1] + start_y)], 3)