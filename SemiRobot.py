import math


def get_next_point(pos_x, pos_y, angle, dist):
    new_x = pos_x + dist * math.cos(math.radians(angle))
    new_y = pos_y + (dist * math.sin(math.radians(angle)) * -1)

    return new_x, new_y


def distance(pos1, pos2):
    return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5


class SemiRobot:
    def __init__(self, robot, wheel_dis):
        self.all_path_parts_lengths = []
        self.wheel_dis = wheel_dis
        self.path_part = 0
        self.path_pos = 0
        self.path_edge = 0
        self.angle = robot.angle
        self.center = [robot.center[0], robot.center[1]]

        self.width = robot.width
        self.height = robot.height

        self.front = [0, 0]
        self.back = [0, 0]
        self.square = [[0, 0], [0, 0], [0, 0], [0, 0]]

        self.path_robots = []
        self.path_turns = []
        self.path_center_turns = []
        self.path_turns_directions = []

    def find_back_and_front(self):
        self.front = self.center[0] + self.width / 2 * math.cos(math.radians(self.angle)), self.center[
            1] + self.width / 2 * math.sin(math.radians(self.angle)) * -1

        self.back = self.center[0] - self.width / 2 * math.cos(math.radians(self.angle)), self.center[
            1] - self.width / 2 * math.sin(math.radians(self.angle)) * -1

    def find_corners(self):
        self.square = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.square[0] = self.front[0] + self.height / 2 * math.sin(math.radians(self.angle)), self.front[
            1] + self.height / 2 * math.cos(math.radians(self.angle))

        self.square[1] = self.front[0] - self.height / 2 * math.sin(math.radians(self.angle)), self.front[
            1] - self.height / 2 * math.cos(math.radians(self.angle))

        self.square[2] = self.back[0] - self.height / 2 * math.sin(math.radians(self.angle)), self.back[
            1] - self.height / 2 * math.cos(math.radians(self.angle))

        self.square[3] = self.back[0] + self.height / 2 * math.sin(math.radians(self.angle)), self.back[
            1] + self.height / 2 * math.cos(math.radians(self.angle))

    def is_direct_forward(self, x, y):
        d1 = distance(self.front, [x, y])
        d2 = distance(self.back, [x, y])

        return d1 <= d2

    def update(self):
        self.find_back_and_front()
        self.find_corners()

    def get_extensions(self):
        x_extension = self.min_x() - self.center[0]
        y_extension = self.center[1] - self.min_y()
        return x_extension, y_extension

    def max_x(self):
        return max(self.square[0][0], self.square[1][0], self.square[2][0], self.square[3][0])

    def min_x(self):
        return min(self.square[0][0], self.square[1][0], self.square[2][0], self.square[3][0])

    def max_y(self):
        return max(self.square[0][1], self.square[1][1], self.square[2][1], self.square[3][1])

    def min_y(self):
        return min(self.square[0][1], self.square[1][1], self.square[2][1], self.square[3][1])

    def get_all_path(self, robots, turning_positions, turns_centers, turn_directions):
        self.path_robots = robots
        self.path_turns = turning_positions
        self.path_center_turns = turns_centers
        self.path_turns_directions = turn_directions
        self.all_path_parts_lengths = []
        for i in range(2 * len(turning_positions) + 1):
            self.all_path_parts_lengths.append(0)
            if i % 2 == 0:
                if i // 2 > 0:
                    self.all_path_parts_lengths[i] += distance(self.path_robots[i // 2].center,
                                                               self.path_turns[i // 2 - 1][2])
                if i // 2 < len(self.path_turns):
                    self.all_path_parts_lengths[i] += distance(self.path_robots[i // 2].center,
                                                               self.path_turns[i // 2][0])
            else:
                radius = distance(self.path_center_turns[i // 2], self.path_turns[i // 2][0])
                angle_turn = ((self.path_robots[i // 2].angle - self.path_robots[i // 2 + 1].angle) % 360 + 360) % 360
                if angle_turn > 180:
                    angle_turn -= 360
                    angle_turn = abs(angle_turn)
                if self.path_turns_directions[i // 2] == -1:
                    angle_turn = 360 - angle_turn
                self.all_path_parts_lengths[i] += (angle_turn / 360) * abs(
                    math.pi * (abs(radius + (self.wheel_dis / 2)) + abs(radius - (self.wheel_dis / 2))))
        self.path_edge = self.all_path_parts_lengths[0]

    def shift_forward(self, delta):
        while delta > 0:
            max_dis_to_edge = self.path_edge - self.path_pos
            if delta >= max_dis_to_edge:
                if self.path_part // 2 < len(self.path_turns):
                    self.center[0] =\
                        self.path_turns[self.path_part // 2][2 * (self.path_part % 2)][0]
                    self.center[1] =\
                        self.path_turns[self.path_part // 2][2 * (self.path_part % 2)][1]
                else:
                    self.center[0] = self.path_robots[-1].center[0]
                    self.center[1] = self.path_robots[-1].center[1]
                self.angle = self.path_robots[(self.path_part + 1) // 2].angle
                delta -= max_dis_to_edge
                self.path_pos = self.path_edge
                if self.path_part < len(self.all_path_parts_lengths) - 1:
                    self.path_part += 1
                    self.path_edge += self.all_path_parts_lengths[self.path_part]
                else:
                    delta -= delta
            else:
                is_line = (self.path_part % 2 == 0)
                if is_line:
                    direction = 1
                    if self.path_part // 2 < len(self.path_turns):
                        dis_robot_to_next_turning = distance(self.path_robots[self.path_part // 2].center,
                                                             self.path_turns[self.path_part // 2][0])
                        if max_dis_to_edge <= dis_robot_to_next_turning:
                            if not self.is_direct_forward(
                                    self.path_turns[self.path_part // 2][0][0],
                                    self.path_turns[self.path_part // 2][0][1]):
                                direction *= -1
                            self.center[0], self.center[1] =\
                                get_next_point(self.center[0], self.center[1],
                                               self.angle, delta * direction)
                            self.path_pos += delta
                        else:
                            if not self.is_direct_forward(
                                    self.path_robots[self.path_part // 2].center[0],
                                    self.path_robots[self.path_part // 2].center[1]):
                                direction *= -1
                            self.center[0], self.center[1] =\
                                get_next_point(self.center[0],
                                               self.center[1], self.angle, delta * direction)
                            self.path_pos += delta
                            max_dis_to_edge -= delta
                            if max_dis_to_edge <= dis_robot_to_next_turning\
                                    and self.path_robots[self.path_part // 2].is_direct_forward(
                                            self.path_turns[self.path_part // 2][0][0],
                                            self.path_turns[self.path_part // 2][0][1]) ==\
                                    self.path_robots[self.path_part // 2].is_direct_forward(
                                        self.path_turns[self.path_part // 2 - 1][2][0],
                                        self.path_turns[self.path_part // 2 - 1][2][1]):
                                self.center[0], self.center[1] = get_next_point(
                                    self.center[0],
                                    self.center[1],
                                    self.angle,
                                    2 * (dis_robot_to_next_turning - max_dis_to_edge) * direction * -1)
                    else:
                        if not self.is_direct_forward(
                                self.path_robots[self.path_part // 2].center[0],
                                self.path_robots[self.path_part // 2].center[1]):
                            direction *= -1
                        self.center[0], self.center[1] = get_next_point(self.center[0], self.center[1],
                                                                        self.angle, delta * direction)
                        self.path_pos += delta
                else:
                    angle_turn = ((self.path_robots[self.path_part // 2 + 1].angle -
                                   self.path_robots[self.path_part // 2].angle) % 360 + 360) % 360
                    direction = 1
                    if angle_turn >= 180:
                        angle_turn -= 360
                        direction *= -1

                    angle_delta = self.path_turns_directions[self.path_part // 2] * direction
                    radius = distance(self.path_center_turns[self.path_part // 2],
                                      self.path_turns[self.path_part // 2][0])
                    angle_delta *= delta * 360 / (math.pi * (abs(abs(radius) + (self.wheel_dis / 2)) +
                                                             abs(abs(radius) - (self.wheel_dis / 2))))

                    angle_to_semi_robot = self.angle - 90
                    point = get_next_point(self.path_center_turns[self.path_part // 2][0],
                                           self.path_center_turns[self.path_part // 2][1],
                                           angle_to_semi_robot, radius)
                    if round(distance(self.center, point)) != 0:
                        angle_to_semi_robot += 180

                    self.center[0], self.center[1] =\
                        get_next_point(self.path_center_turns[self.path_part // 2][0],
                                       self.path_center_turns[self.path_part // 2][1],
                                       angle_to_semi_robot + angle_delta, radius)
                    self.angle += angle_delta
                    self.path_pos += delta
                delta = 0
            self.update()

    def shift_backward(self, delta):
        while delta < 0:
            max_dis_to_edge = self.path_edge - self.all_path_parts_lengths[self.path_part] - self.path_pos
            if abs(delta) >= abs(max_dis_to_edge):
                if self.path_part > 0:
                    self.center[0] =\
                        self.path_turns[(self.path_part - 1) // 2][2 * (1 - self.path_part % 2)][0]
                    self.center[1] =\
                        self.path_turns[(self.path_part - 1) // 2][2 * (1 - self.path_part % 2)][1]
                    self.angle = self.path_robots[self.path_part // 2].angle
                    delta -= abs(max_dis_to_edge) * delta / abs(delta)
                    self.path_pos = self.path_edge - self.all_path_parts_lengths[self.path_part]
                    self.path_part -= 1
                    self.path_edge -= self.all_path_parts_lengths[self.path_part + 1]
                else:
                    self.center[0] = self.path_robots[0].center[0]
                    self.center[1] = self.path_robots[0].center[1]
                    self.angle = self.path_robots[(self.path_part + 1) // 2].angle
                    delta -= delta
            else:
                is_line = (self.path_part % 2 == 0)
                if is_line:
                    direction = abs(delta) / delta
                    if self.path_part > 0 and self.path_part // 2 < len(self.path_turns):
                        dis_robot_to_next_turning = distance(self.path_robots[self.path_part // 2].center,
                                                             self.path_turns[self.path_part // 2 - 1][2])
                        if abs(max_dis_to_edge) <= dis_robot_to_next_turning:
                            if self.is_direct_forward(
                                    self.path_turns[self.path_part // 2 - 1][2][0],
                                    self.path_turns[self.path_part // 2 - 1][2][1]):
                                direction *= -1
                            self.center[0], self.center[1] =\
                                get_next_point(self.center[0], self.center[1],
                                               self.angle, abs(delta) * direction)
                            self.path_pos += delta
                        else:
                            if self.is_direct_forward(
                                    self.path_robots[self.path_part // 2].center[0],
                                    self.path_robots[self.path_part // 2].center[1]):
                                direction *= -1
                            self.center[0], self.center[1] =\
                                get_next_point(self.center[0],
                                               self.center[1], self.angle, abs(delta) * direction)
                            self.path_pos += delta
                            max_dis_to_edge -= abs(delta) * max_dis_to_edge / abs(max_dis_to_edge)
                            if abs(max_dis_to_edge) <= dis_robot_to_next_turning\
                                    and self.path_robots[self.path_part // 2].is_direct_forward(
                                            self.path_turns[self.path_part // 2 - 1][2][0],
                                            self.path_turns[self.path_part // 2 - 1][2][1]) ==\
                                    self.path_robots[self.path_part // 2].is_direct_forward(
                                        self.path_turns[self.path_part // 2][0][0],
                                        self.path_turns[self.path_part // 2][0][1]):
                                self.center[0], self.center[1] = get_next_point(
                                    self.center[0],
                                    self.center[1],
                                    self.angle,
                                    2 * (dis_robot_to_next_turning - abs(max_dis_to_edge)) * direction * -1)
                    else:
                        if self.path_part == 0 and self.is_direct_forward(
                                self.path_robots[0].center[0],
                                self.path_robots[0].center[1]):
                            direction *= -1
                        if self.path_part // 2 == len(self.path_turns) and self.is_direct_forward(
                                self.path_turns[-1][2][0],
                                self.path_turns[-1][2][1]):
                            direction *= -1
                        self.center[0], self.center[1] = get_next_point(self.center[0], self.center[1],
                                                                        self.angle, abs(delta) * direction)
                        self.path_pos += delta
                else:
                    angle_turn = ((self.path_robots[self.path_part // 2 + 1].angle -
                                   self.path_robots[self.path_part // 2].angle) % 360 + 360) % 360
                    direction = 1
                    if angle_turn >= 180:
                        angle_turn -= 360
                        direction *= -1

                    angle_delta = self.path_turns_directions[self.path_part // 2] * direction
                    radius = distance(self.path_center_turns[self.path_part // 2],
                                      self.path_turns[self.path_part // 2][0])
                    angle_delta *= delta * 360 / (math.pi * (abs(abs(radius) + (self.wheel_dis / 2)) +
                                                             abs(abs(radius) - (self.wheel_dis / 2))))

                    angle_to_semi_robot = self.angle - 90
                    point = get_next_point(self.path_center_turns[self.path_part // 2][0],
                                           self.path_center_turns[self.path_part // 2][1],
                                           angle_to_semi_robot, radius)
                    if round(distance(self.center, point)) != 0:
                        angle_to_semi_robot += 180

                    self.center[0], self.center[1] =\
                        get_next_point(self.path_center_turns[self.path_part // 2][0],
                                       self.path_center_turns[self.path_part // 2][1],
                                       angle_to_semi_robot + angle_delta, radius)
                    self.angle += angle_delta
                    self.path_pos += delta
                delta = 0
            self.update()

    def shift(self, delta):
        self.shift_forward(delta)
        self.shift_backward(delta)
