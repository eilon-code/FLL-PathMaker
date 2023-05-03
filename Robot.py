import math


def distance(x1, x2, y1, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def get_next_point(pos_x, pos_y, angle, dist):
    new_x = pos_x + dist * math.cos(math.radians(angle))
    new_y = pos_y + (dist * math.sin(math.radians(angle)) * -1)

    return new_x, new_y


class Robot:
    def __init__(self, angle, width, height, center):
        self.width = width
        self.height = height
        self.angle = (angle % 360 + 360) % 360
        self.center = [center[0], center[1]]

        self.front = [0, 0]
        self.back = [0, 0]
        self.square = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.lines = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]

        self.find_back_and_front()
        self.find_corners()
        self.find_lines()

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

    def find_lines(self):
        self.lines = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
        if self.angle != 270 and self.angle != 90:
            self.lines[0] = math.tan(math.radians(self.angle)) * -1, self.square[1][1] - self.square[1][0] * math.tan(
                math.radians(self.angle)) * -1
            self.lines[1] = math.tan(math.radians(self.angle)) * -1, self.square[2][1] - self.square[2][0] * math.tan(
                math.radians(self.angle)) * -1
        else:
            self.lines[0] = "infinity", -1
            self.lines[1] = "infinity", -1

        if self.angle % 180 != 0:
            self.lines[2] = math.tan(math.radians(self.angle + 90)) * -1, self.square[1][1] - self.square[1][
                0] * math.tan(
                math.radians(self.angle + 90)) * -1
            self.lines[3] = math.tan(math.radians(self.angle + 90)) * -1, self.square[3][1] - self.square[3][
                0] * math.tan(
                math.radians(self.angle + 90)) * -1
        else:
            self.lines[2] = "infinity", -1
            self.lines[3] = "infinity", -1

        if self.angle != 270 and self.angle != 90:
            self.lines[4] = math.tan(math.radians(self.angle)) * -1, self.front[1] - self.front[0] * math.tan(
                math.radians(self.angle)) * -1
        else:
            self.lines[4] = "infinity", -1

        if self.angle % 180 != 0:
            self.lines[5] = math.tan(math.radians(self.angle + 90)) * -1, self.center[1] - self.center[0] * math.tan(
                math.radians(self.angle + 90)) * -1
        else:
            self.lines[5] = "infinity", -1

    def update(self):
        self.angle = (self.angle % 360 + 360) % 360

        self.find_back_and_front()
        self.find_corners()
        self.find_lines()

    def touch_the_robot(self, pos_x, pos_y, error_range):
        if self.angle % 90 != 0:
            dis1 = abs((-1) * pos_y + (self.lines[4][0] * pos_x) + self.lines[4][1]) / (
                    ((self.lines[4][0] ** 2) + ((-1) ** 2)) ** 0.5)

            dis2 = abs((-1) * pos_y + (self.lines[5][0] * pos_x) + self.lines[5][1]) / (
                    ((self.lines[5][0] ** 2) + ((-1) ** 2)) ** 0.5)

            if dis1 - error_range <= self.height / 2 and dis2 - error_range <= self.width / 2:
                return True
            else:
                return False
        else:
            dis1 = abs(self.center[0] - pos_x)
            dis2 = abs(self.center[1] - pos_y)
            if self.angle % 180 == 0:
                if dis1 - error_range <= self.width / 2 and dis2 - error_range <= self.height / 2:
                    return True
                else:
                    return False
            else:
                if dis1 - error_range <= self.height / 2 and dis2 - error_range <= self.width / 2:
                    return True
                else:
                    return False

    def is_direct_forward(self, x, y):
        d1 = distance(self.front[0], x, self.front[1], y)
        d2 = distance(self.back[0], x, self.back[1], y)

        return d1 <= d2

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
