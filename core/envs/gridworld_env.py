import gym
from gym import spaces
import numpy as np
import sys
from six import StringIO


class GridWorldEnv(gym.Env):
    metadata = {'render.modes': ['human', 'ansi', 'graphic']}

    def __init__(self, grid_shape=(4, 4), initial_state=0, terminal_states=None, walls=None, custom_world_fp=None):
        # set state space params
        if terminal_states is not None and not isinstance(terminal_states, list):
            raise ValueError("terminal_states parameter must be a list of integer indices")
        if walls is not None and not isinstance(walls, list):
            raise ValueError("walls parameter must be a list of integer indices")
        if not isinstance(grid_shape, tuple) or len(grid_shape) != 2 or not isinstance(grid_shape[0], int):
            raise ValueError("grid_shape parameter must be tuple of two integers")
        self.x_max = grid_shape[0]
        self.y_max = grid_shape[1]
        self.world = self._generate_world()
        # set action space params
        self.action_space = spaces.Discrete(4)
        # main boundary check for edges of map done here
        self.action_state_to_next_state = [lambda s: s if self.world[s][1] == (self.y_max - 1) else s + 1,
                                           lambda s: s if self.world[s][0] == (self.x_max - 1) else s + self.y_max,
                                           lambda s: s if self.world[s][1] == 0 else s - 1,
                                           lambda s: s if self.world[s][0] == 0 else s - self.y_max]
        self.action_descriptors = ['up', 'right', 'down', 'left']
        # set observed params: [current state, world state]
        self.observation_space = spaces.Discrete(self.world.size)
        # set initial state for the agent
        self.previous_state = self.current_state = self.initial_state = initial_state
        # set terminal state(s) and default terminal state if None given
        if terminal_states is None or len(terminal_states) == 0:
            self.terminal_states = [self.world.size - 1]
        else:
            self.terminal_states = terminal_states
        for t_s in self.terminal_states:
            if t_s < 0 or t_s > (self.world.size - 1):
                raise ValueError("Terminal state {} is out of grid bounds".format(t_s))
        # set walls
        # need index positioning for efficient check in _is_valid()
        # but also need list to easily access each wall sequentially (e.g in render())
        self.wall_indices = []
        self.walls = np.zeros(self.world.shape)
        if walls is not None:
            for wall_state_index in walls:
                if wall_state_index < 0 or wall_state_index > (self.world.size - 1):
                    raise ValueError("Wall index {} is out of grid bounds".format(wall_state_index))
                self.walls[wall_state_index] = 1
                self.wall_indices.append(wall_state_index)
        # set reward matrix
        self.reward_matrix = np.full(self.world.shape, -1)
        for terminal_state in self.terminal_states:
            self.reward_matrix[terminal_state] = 0
        # self.reward_range = [-inf, inf] # default values already
        # set additional parameters for the environment
        self.done = False
        self.info = {}

        if custom_world_fp:
            self.create_custom_world_from_file(custom_world_fp)

    def _generate_world(self):
        """
        Creates and returns the gridworld map as a numpy array.

        The states are defined by their index and contain a tuple of uint16 values that represent the
        coordinates (x,y) of a state in the grid.
        """
        world = np.fromiter(((x, y) for x in np.nditer(np.arange(self.x_max))
                             for y in np.nditer(np.arange(self.y_max))), dtype='int64, int64')
        return world

    def look_step_ahead(self, state, action):
        """
        Computes the results of a hypothetical action taking place at the given state.

        Returns the state to what that action would lead, the reward at that new state and a boolean value that
        determines if the next state is terminal
        """
        if self.is_terminal(state):
            next_state = state
        else:
            next_state = self.action_state_to_next_state[action](state)
            next_state = next_state if self._is_valid(next_state) else state

        return next_state, self.reward_matrix[next_state], self.is_terminal(next_state)

    def _is_valid(self, state):
        """
        Checks if a given state is a wall or any other element that shall not be trespassed.
        """
        if self.walls[state] == 1:
            return False
        return True

    def is_terminal(self, state):
        """
        Check if the input state is terminal.
        """
        if state in self.terminal_states:
            return True
        return False

    def _step(self, action):
        """
        Moves the agent one step according to the given action.
        """
        self.previous_state = self.current_state
        self.current_state, reward, self.done = self.look_step_ahead(self.current_state, action)
        return self.current_state, reward, self.done, self.info

    def _reset(self):
        self.done = False
        self.current_state = self.previous_state = self.initial_state
        return self.current_state

    def _render(self, mode='human', close=False):
        new_world = np.fromiter(('o' for _ in np.nditer(np.arange(self.x_max))
                                 for _ in np.nditer(np.arange(self.y_max))), dtype='S1')
        new_world[self.current_state] = 'x'
        for t_state in self.terminal_states:
            new_world[t_state] = 'T'

        for w_state in self.wall_indices:
            new_world[w_state] = '#'

        if mode == 'human' or mode == 'ansi':
            outfile = StringIO() if mode == 'ansi' else sys.stdout
            for row in np.reshape(new_world, (self.x_max, self.y_max))[:, ::-1].T:
                for state in row:
                    outfile.write((state.decode('UTF-8') + ' '))
                outfile.write('\n')
            outfile.write('\n')
            return outfile

        elif mode == 'graphic':
            raise NotImplementedError
        else:
            super(GridWorldEnv, self).render(mode=mode)

    def _close(self):
        pass

    def _seed(self, seed=None):
        raise NotImplementedError

    def create_custom_world_from_file(self, fp):
        f = open(fp, 'r') # change to "with" todo
        num_cols = None

        list_world = []
        self.terminal_states = []

        # x, y = 0, 0

        all_lines = f.readlines()
        # num_rows = len(all_lines)
        for y, line in enumerate(all_lines):
            list_world.append([])
            x = 0
            line = line.strip()
            if not num_cols:
                num_cols = len(line)
            if len(line) != num_cols:
                raise EnvironmentError

            for char in line:
                index = (num_cols * y) + x

                if char == 'T':
                    self.terminal_states.append(index)
                elif char == 'o':
                    pass
                elif char == '#':
                    pass
                elif char == 'x':
                    self.current_state = index
                else:
                    print('Invalid Character \"{}\". Returning'.format(char))
                    raise EnvironmentError

                list_world[y].append((x, y))
                x += 1
            y += 1

        print (list_world)
        # self.world = np.array(list_world).flatten()
        self.y_max = len(all_lines)
        self.x_max = num_cols
        self.world = self._generate_world()
        print(self.world)

        self.reward_matrix = np.full(self.world.shape, -1)
        for terminal_state in self.terminal_states:
            self.reward_matrix[terminal_state] = 0

        # todo put all above into functions so no repeat? setup_world() or something like that

        f.close()


if __name__ == '__main__':
    env = GridWorldEnv(custom_world_fp='test_env.txt')
    for i_episode in range(1):
        observation = env.reset()
        for t in range(100):
            env.render()
            action = env.action_space.sample()
            print('go ' + env.action_descriptors[action])
            observation, reward, done, info = env.step(action)

            if done:
                print("Episode finished after {} timesteps".format(t + 1))
                break