import time

import numpy as np

from core.envs.gridworld_env import GridWorldEnv
from core.algorithms.monte_carlo import run_episode, monte_carlo_evaluation
from core.algorithms import utils
import core.algorithms.dynamic_programming as dp

def run_policy_iteration_gridworld():
    print('\n' + '*' * 20 + 'Starting value and policy iteration' + '*' * 20 + '\n')
    # test policy evaluation
    # world_shape = (4, 4)
    # env = GridWorldEnv(grid_shape=world_shape, terminal_states=[3, 12])
    world_shape = (21, 31)
    # world_shape = (11, 11)
    env = GridWorldEnv(grid_shape=world_shape, random_maze=True)
    policy0 = np.ones([env.world.size, len(env.action_state_to_next_state)]) / len(env.action_state_to_next_state)
    v0 = np.zeros(env.world.size)
    val_fun = v0
    for k in range(500):
        val_fun = utils.single_step_policy_evaluation(policy0, env, value_function=val_fun)
    print(utils.reshape_as_gridworld(val_fun, world_shape))

    # todo why do the walls of policy map have ascii arrows? don't draw them?
    # todo print everthing below better
    # todo shouldn't have two outputs for policy_map! better name or better handling # todo have to make clear about tuple...
    # policy_arrow_array, policy_probabilities = utils.get_policy_map(optimal_policy, world_shape) # todo have to make clear about tuple...

    # test greedy policy
    policy1 = utils.greedy_policy_from_value_function(policy0, env, val_fun)
    policy_map1 = utils.get_policy_map(policy1, world_shape)
    print('Policy: (0=up, 1=right, 2=down, 3=left)\n', policy_map1)
    np.set_printoptions(linewidth=75 * 2, precision=4)
    print('Policy: (up, right, down, left)\n', utils.get_policy_map(policy1, world_shape))
    np.set_printoptions(linewidth=75, precision=8)

    # test policy iteration
    print('Policy iteration:')
    policy0 = np.ones([env.world.size, len(env.action_state_to_next_state)]) / len(env.action_state_to_next_state)
    optimal_value, optimal_policy = dp.policy_iteration(policy0, env, v0, threshold=0.001, max_steps=1000)
    print('Value:\n', utils.reshape_as_gridworld(optimal_value, world_shape))
    print('Policy: (0=up, 1=right, 2=down, 3=left)\n', utils.get_policy_map(optimal_policy, world_shape))
    np.set_printoptions(linewidth=75 * 2, precision=4)
    print('Policy: (up, right, down, left)\n', utils.get_policy_map(optimal_policy, world_shape))
    np.set_printoptions(linewidth=75, precision=8)

    # # test value iteration
    print('Value iteration:')
    policy0 = np.ones([env.world.size, len(env.action_state_to_next_state)]) / len(env.action_state_to_next_state)
    optimal_value, optimal_policy = dp.value_iteration(policy0, env, v0, threshold=0.001, max_steps=100)
    print('Value:\n', utils.reshape_as_gridworld(optimal_value, world_shape))
    print('Policy: (0=up, 1=right, 2=down, 3=left)\n', utils.get_policy_map(optimal_policy, world_shape))
    np.set_printoptions(linewidth=75 * 2, precision=4)
    print('Policy: (up, right, down, left)\n', utils.get_policy_map(optimal_policy, world_shape))
    np.set_printoptions(linewidth=75, precision=8)

    curr_state = env.reset()

    env.render_policy_arrows(optimal_policy)

    # Dynamic programming doesn't necessarily have the concept of an agent.
    # But you can create an agent to run on the environment using the found policy
    for t in range(100):
        env.render(mode='graphic')

        action = np.argmax(optimal_policy[curr_state])
        print('go ' + env.action_descriptors[action])
        curr_state, reward, done, info = env.step(action)

        if done:
            print('DONE in {} steps'.format(t + 1))
            env.render(mode='graphic') # must render here to see agent in final state
            time.sleep(6)
            break

def run_monte_carlo():
    print('\n' + '*' * 20 + 'Starting Monte Carlo evaluation and greedy policy' + '*' * 20 + '\n')
    world_shape = (8, 8)
    # env = GridWorldEnv(grid_shape=world_shape)
    env = GridWorldEnv(world_shape, random_maze=True)
    policy0 = np.ones([env.world.size, env.action_space.n]) / env.action_space.n

    print('Running an episode with a random agent (with initial policy)')
    st_history, rw_history, done = run_episode(policy0, env)
    print('States history: ' + str(st_history))
    print('Rewards history: ' + str(rw_history))

    print('Starting Monte-Carlo evaluation of random policy')
    value0 = monte_carlo_evaluation(policy0, env, every_visit=True)
    print(value0)

    # Create greedy policy from value function and run it on environment
    policy1 = utils.greedy_policy_from_value_function(policy0, env, value0)
    print(policy1)

    print('Policy: (up, right, down, left)\n', utils.get_policy_map(policy1, world_shape))
    np.set_printoptions(linewidth=75, precision=8)

    print('Starting greedy policy episode')
    curr_state = env.reset()
    env.render_policy_arrows(policy1)

    for t in range(500):
        env.render(mode='graphic')

        action = np.argmax(policy1[curr_state])
        print('go ' + env.action_descriptors[action])
        curr_state, reward, done, info = env.step(action)

        if done:
            print('DONE in {} steps'.format(t + 1))
            env.render(mode='graphic')
            time.sleep(5)
            break

if __name__ == '__main__':
    # Run specific algorithms on gridworld
    run_policy_iteration_gridworld()
    run_monte_carlo()