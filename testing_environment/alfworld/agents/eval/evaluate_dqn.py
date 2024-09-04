import copy
import numpy as np
import torch

import os
import sys
from alfworld.agents.utils.misc import extract_admissible_commands


def evaluate_dqn(env, agent, num_games, debug=False):
    env.seed(42)
    agent.eval()
    episode_no = 0
    res_points, res_gcs, res_steps = [], [], []
    res_info = []
    with torch.no_grad():
        while(True):
            if episode_no >= num_games:
                break

            obs, infos = env.reset()
            game_names = infos["extra.gamefile"]
            batch_size = len(obs)

            agent.init(batch_size)
            previous_dynamics = None

            chosen_actions = []
            prev_step_dones, prev_rewards = [], []
            for _ in range(batch_size):
                chosen_actions.append("restart")
                prev_step_dones.append(0.0)
                prev_rewards.append(0.0)

            observation_strings = list(obs)
            task_desc_strings, observation_strings = agent.get_task_and_obs(observation_strings)
            task_desc_strings = agent.preprocess_task(task_desc_strings)
            observation_strings = agent.preprocess_observation(observation_strings)
            first_sight_strings = copy.deepcopy(observation_strings)
            agent.observation_pool.push_first_sight(first_sight_strings)
            if agent.action_space == "exhaustive":
                action_candidate_list = [extract_admissible_commands(intro, obs) for intro, obs in zip(first_sight_strings, observation_strings)]
            else:
                action_candidate_list = list(infos["admissible_commands"])
            action_candidate_list = agent.preprocess_action_candidates(action_candidate_list)
            observation_strings = [item + " [SEP] " + a for item, a in zip(observation_strings, chosen_actions)]  # appending the chosen action at previous step into the observation

            still_running_mask = []
            sequence_game_points = []
            goal_condition_points = []
            print_actions = []
            report = agent.report_frequency > 0 and (episode_no % agent.report_frequency <= (episode_no - batch_size) % agent.report_frequency)

            if debug:
                print(first_sight_strings[0])
                print(task_desc_strings[0])

            for step_no in range(agent.max_nb_steps_per_episode):
                # push obs into observation pool
                agent.observation_pool.push_batch(observation_strings)
                # get most recent k observations
                most_recent_observation_strings = agent.observation_pool.get()

                # predict actions
                if agent.action_space == "generation":
                    chosen_actions, _, current_dynamics = agent.command_generation_act_greedy(most_recent_observation_strings, task_desc_strings, previous_dynamics)
                elif agent.action_space == "beam_search_choice":
                    chosen_actions, _, current_dynamics, action_candidate_list = agent.beam_search_choice_act_greedy(most_recent_observation_strings, task_desc_strings, previous_dynamics)
                elif agent.action_space in ["admissible", "exhaustive"]:
                    chosen_actions, _, current_dynamics = agent.admissible_commands_act_greedy(most_recent_observation_strings, task_desc_strings, action_candidate_list, previous_dynamics)
                else:
                    raise NotImplementedError()

                obs, _, dones, infos = env.step(chosen_actions)
                scores = [float(item) for item in infos["won"]]
                dones = [float(item) for item in dones]
                gcs = [float(item) for item in infos["goal_condition_success_rate"]] if "goal_condition_success_rate" in infos else [0.0]*batch_size

                if debug:
                    print(chosen_actions[0])
                    print(obs[0])

                observation_strings = list(obs)
                observation_strings = agent.preprocess_observation(observation_strings)
                if agent.action_space == "exhaustive":
                    action_candidate_list = [extract_admissible_commands(intro, obs) for intro, obs in zip(first_sight_strings, observation_strings)]
                else:
                    action_candidate_list = list(infos["admissible_commands"])
                action_candidate_list = agent.preprocess_action_candidates(action_candidate_list)
                observation_strings = [item + " [SEP] " + a for item, a in zip(observation_strings, chosen_actions)]  # appending the chosen action at previous step into the observation
                previous_dynamics = current_dynamics

                if step_no == agent.max_nb_steps_per_episode - 1:
                    # terminate the game because DQN requires one extra step
                    dones = [1.0 for _ in dones]

                still_running = [1.0 - float(item) for item in prev_step_dones]  # list of float
                prev_step_dones = dones
                step_rewards = [float(curr) - float(prev) for curr, prev in zip(scores, prev_rewards)]  # list of float
                sequence_game_points.append(copy.copy(step_rewards))
                goal_condition_points.append(gcs)
                prev_rewards = scores
                still_running_mask.append(still_running)
                print_actions.append(chosen_actions[0] if still_running[0] else "--")

                # if all ended, break
                if np.sum(still_running) == 0:
                    break

            game_steps = np.sum(np.array(still_running_mask), 0).tolist()  # batch
            game_points = np.max(sequence_game_points, 0).tolist()  # batch
            game_gcs = np.max(np.array(goal_condition_points), 0).tolist() # batch
            for i in range(batch_size):
                if len(res_points) >= num_games:
                    break
                res_points.append(game_points[i])
                res_gcs.append(game_gcs[i])
                res_steps.append(game_steps[i])
                res_info.append("/".join(game_names[i].split("/")[-3:-1]) + ", score: " + str(game_points[i]) + ", step: " + str(game_steps[i]))

            # finish game
            agent.finish_of_episode(episode_no, batch_size)
            episode_no += batch_size

            if not report:
                continue
            print("Episode: {:3d} | {:s} |  game points: {:2.3f} | game goal-condition points: {:2.3f} | game steps: {:2.3f}".format(episode_no, game_names[0], np.mean(res_points), np.mean(res_gcs), np.mean(res_steps)))
            # print(game_id + ":    " + " | ".join(print_actions))
            print(" | ".join(print_actions))

        average_points, average_gc_points, average_steps = np.mean(res_points), np.mean(res_gcs), np.mean(res_steps)
        print("================================================")
        print("eval game points: " + str(average_points) + ", eval game goal-condition points : " + str(average_gc_points) + ", eval game steps: " + str(average_steps))
        for item in res_info:
            print(item)

        return {
            'average_points': average_points,
            'average_goal_condition_points': average_gc_points,
            'average_steps': average_steps,
            'res_points': res_points,
            'res_gcs': res_gcs,
            'res_steps': res_steps,
            'res_info': res_info
        }

