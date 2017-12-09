import gym
from gym import spaces
import numpy as np
import sys
from six import StringIO


class GridWorldEnv(gym.Env):
    metadata = {'render.modes': ['human', 'ansi', 'graphic']}

    def __init__(self, grid_shape=(4, 4), initial_state=0, **kwargs):
        # set state space params
        self.x_max = grid_shape[0]
        self.y_max = grid_shape[1]
        self.world = self._generate_world()
        # set action space params
        self.action_space = spaces.Discrete(4)
        self.actions_list = np.array([(0, 1), (1, 0), (0, -1), (-1, 0)], dtype='int16, int16')
        self.action_descriptors = ['up', 'right', 'down', 'left']
        # set observed params: [current state, world state]
        self.observation_space = spaces.Box(spaces.Discrete(self.world.size),
                                            spaces.Box(spaces.Discrete(self.x_max), spaces.Discrete(self.y_max)))
        # set initial state for the agent
        self.previous_state = self.current_state = self.initial_state = initial_state
        # set terminal state(s)
        self.terminal_states = kwargs['terminal_states'] if 'terminal_states' in kwargs else [self.world.size - 1]
        # set reward matrix
        self.reward_matrix = np.full(self.world.shape, -1)
        for terminal_state in self.terminal_states:
            self.reward_matrix[terminal_state] = 0
        # self.reward_range = [-inf, inf] # default values already
        # set additional parameters for the environment
        self.done = False
        self.info = {}

    def _generate_world(self):
        """
        Creates and returns the gridworld map as a numpy array.

        The states are defined by their index and contain a tuple of uint16 values that represent the
        coordinates (x,y) of a state in the grid.
        """
        world = np.fromiter(((x, y) for x in np.nditer(np.arange(self.x_max))
                             for y in np.nditer(np.arange(self.y_max))), dtype='int16, int16')
        return world

    def look_step_ahead(self, state, action):
        """
        Computes the results of a hypothetical action taking place at the given state.

        Returns the state to what that action would lead, the reward at that new state and a boolean value that
        determines if the next state is terminal
        """
        if self._is_terminal(state):
            next_state = state
        else:
            state_x, state_y = self.world[state]
            movement_x, movement_y = self.actions_list[action]
            next_location = np.array((state_x + movement_x, state_y + movement_y), dtype='int16, int16')
            next_state = np.where(self.world == next_location)[0][0] if self._is_valid_location(next_location) \
                else state

            if not self._is_valid_state(next_state):
                next_state = state

        return next_state, self.reward_matrix[next_state], self._is_terminal(next_state)

    def _is_valid_location(self, location):
        """
        Checks if a given state is inside the grid.
        """
        return True if location in self.world else False

    def _is_valid_state(self, state):
        """
        Checks if a given state is inside the grid.
        """
        return True if 0 <= state < self.world.size else False

    def _is_terminal(self, state):
        """
        Check if the input state is terminal.
        """
        for t_state in self.terminal_states:
            if state == t_state:
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


if __name__ == '__main__':
    env = GridWorldEnv()
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