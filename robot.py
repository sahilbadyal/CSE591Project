import numpy as np
from occupancy_grid import OccupancyGrid


class Robot(object):

    def __init__(self, name, coord, dims):
        self.time = 0
        self.pos = coord
        self.name = name
        self.limits = dims
        self.obs = None
        self.S = OccupancyGrid(False, dims[0], dims[1])
        self.D = OccupancyGrid(False, dims[0], dims[1])
        self.T = OccupancyGrid(length=dims[0], width=dims[1])
        self.C = 80.0

    def move_right(self):
        ## check if no static  object
        self.pos[1] = self.pos[1] + 1 if self.pos[1] < self.limits[1] - 1 else self.pos[1]
        return self.pos

    def move_left(self):
        self.pos[1] = self.pos[1] - 1 if self.pos[1] > 0 else self.pos[1]
        return self.pos

    def move_up(self):
        self.pos[0] = self.pos[0] - 1 if self.pos[0] > 0 else self.pos[0]
        return self.pos

    def move_down(self):
        self.pos[0] = self.pos[0] + 1 if self.pos[0] < self.limits[0] - 1 else self.pos[0]
        return self.pos

    def setObs(self, observation):
        self.obs = observation #3*3
        list_global = {}
        for i in range(3):
            for j in range(3):
                if observation[i][j] == -1:
                    continue
                observation[i][j] = 0 if observation[i][j] >= 3 else observation[i][j]
                gx = self.pos[0]
                gy = self.pos[1]
                lx, ly = 1, 1
                nx = gx - (lx - i)
                ny = gy - (ly - j)
                list_global[(nx, ny)] = observation[i][j]
        for pose, obs in list_global.items():
            # print(pose, obs)
            # print(self.get_static_inv_sensor_model(pose, obs))
            self.update_static_grid(self.get_static_inv_sensor_model(pose, obs), pose)
            self.update_dynamic_grid(self.get_dynamic_inv_sensor_model(pose, obs), pose)
            self.T.update(self.time, pose)

        self.update_time()

    def update_time(self):
        observed = np.array(self.T.get_arr() > 0, np.int)
        delT = np.full((self.limits[0], self.limits[1]), self.time) * observed - self.T.get_arr()
        delT = delT/self.C
        self.T.mat = self.T.mat - delT

    def merge(self, robot_S, robot_D, robot_T):
        for i in range(self.limits[0]):
            for j in range(self.limits[1]):
                if robot_T[i, j] > self.T.get_arr()[i, j]:
                    self.S.update(robot_S[i, j], (i, j))
                    self.D.update(robot_D[i, j], (i, j))
                    self.T.update(robot_T[i, j], (i, j))




    def get_position(self):
        return self.pos

    def get_static_inv_sensor_model(self, pose, obs):
        """
        :param s_prob_val: The previous occupancy probability value at the (x,y) position
        :param obs: The observation at a particular (x,y) location. 0: Free | 1: Occupied
        :return: The inverse sensor model
        """
        # print(self.S.get_arr())
        s_prob_val = self.S.get_arr()[pose]
        free_threshold = 0.45  # Probability below which position is certainly free
        occupied_threshold = 0.55  # Probability above which position is certainly occupied
        inv_sensor_low = 0.05
        inv_sensor_high = 0.85
        if s_prob_val <= free_threshold:
            if obs:
                return 0.01
            else:
                return inv_sensor_low  # Free, Free and Free, Occupied
        elif s_prob_val >= occupied_threshold:
            if obs:
                return inv_sensor_high  # Occupied, Occupied
            else:
                return inv_sensor_low  # Occupied, Free
        else:  # If unknown
            if obs:
                return inv_sensor_high  # Unknown, Occupied
            else:
                return inv_sensor_low  # Unknown, Free

    def get_dynamic_inv_sensor_model(self, pose, obs):
        """
        :param s_prob_val: The previous occupancy probability value at the (x,y) position
        :param obs: The observation at a particular (x,y) location. 0: Free | 1: Occupied
        :return: The inverse sensor model
        """
        s_prob_val = self.S.get_arr()[pose]
        free_threshold = 0.1  # Probability below which position is certainly free
        occupied_threshold = 0.9  # Probability above which position is certainly occupied
        inv_sensor_low = 0.05
        inv_sensor_high = 0.99
        if s_prob_val <= free_threshold:
            if obs:
                return inv_sensor_high  # Free, Occupied
            else:
                return inv_sensor_low  # Free, Free
        elif s_prob_val >= occupied_threshold:
            if obs:
                return inv_sensor_low  # Occupied, Free and Occupied, Occupied
            else:
                return 0.2
        else:  # If unknown
            return inv_sensor_low  # Unknown, Free and Unknown, Occupied

    def update_static_grid(self, inv_sensor_model, pose):
        prev_S = self.S.get_arr()[pose]
        S_update = 0
        for x, y in np.ndindex(self.S.get_arr().shape):
            c = np.exp(np.log(inv_sensor_model / (1 - inv_sensor_model)) + np.log(prev_S / (1.00001 - prev_S)))
            S_update = c/(1 + c)
        self.S.update(S_update, pose)

    def update_dynamic_grid(self, inv_sensor_model, pose):
        prev_D = self.D.get_arr()[pose]
        D_update = 0
        for x, y in np.ndindex(self.D.get_arr().shape):
            c = np.exp(np.log(inv_sensor_model / (1 - inv_sensor_model)) + np.log(prev_D / (1.00001 - prev_D)))
            D_update = c / (1 + c)
        self.D.update(D_update, pose)


    def step(self,action):
        self.time += 1
        if action == "r":
            return self.move_right()
        elif action == "o":
            return self.get_position()
        elif action == "l":
            return  self.move_left()
        elif action == "u":
            return  self.move_up()
        elif action == "d":
            return  self.move_down()

if __name__ == "__main__":
    og = Robot()
    og.show()
