#!/usr/bin/env python
import argparse
from design_search import RobotDesignEnv, make_graph, build_normalized_robot, presimulate, simulate
import numpy as np
import os
import pyrobotdesign as rd
import random
import tasks
import time

# Runs the simulation trajectory while calling a callback at each step.
def run_trajectory(sim, robot_idx, input_sequence, task, step_callback):
    step_callback(0)
    for j in range(input_sequence.shape[1]):
        for k in range(task.interval):
            step_idx = j * task.interval + k
            if input_sequence is not None:
                sim.set_joint_targets(robot_idx, input_sequence[:, j].reshape(-1, 1))
            task.add_noise(sim, step_idx)
            sim.step()
            step_callback(step_idx + 1)

# Finalize robot design by setting default link shapes and joint types if needed.
def finalize_robot(robot):
    for link in robot.links:
        link.label = ""
        link.joint_label = ""
        if link.shape == rd.LinkShape.NONE:
            link.shape = rd.LinkShape.CAPSULE
            link.length = 0.1
            link.radius = 0.025
            link.color = [1.0, 0.0, 1.0]
        if link.joint_type == rd.JointType.NONE:
            link.joint_type = rd.JointType.FIXED
            link.joint_color = [1.0, 0.0, 1.0]

def main():
    parser = argparse.ArgumentParser(description="Robot design headless simulation and optimization.")
    parser.add_argument("task", type=str, help="Task (Python class name)")
    parser.add_argument("grammar_file", type=str, help="Grammar file (.dot)")
    parser.add_argument("rule_sequence", nargs="+", help="Rule sequence to apply")
    parser.add_argument("-o", "--optim", default=False, action="store_true",
                        help="Optimize a trajectory")
    parser.add_argument("-s", "--opt_seed", type=int, default=None,
                        help="Trajectory optimization seed")
    parser.add_argument("-e", "--episodes", type=int, default=1,
                        help="Number of optimization episodes")
    parser.add_argument("-j", "--jobs", type=int, required=True,
                        help="Number of jobs/threads")
    parser.add_argument("--input_sequence_file", type=str,
                        help="File to save input sequence to (.csv)")
    parser.add_argument("--save_obj_dir", type=str,
                        help="Directory to save .obj files to")
    parser.add_argument("-l", "--episode_len", type=int, default=128,
                        help="Length of episode")
    args = parser.parse_args()

    # Load the task, grammar, and design rules.
    task_class = getattr(tasks, args.task)
    task = task_class(episode_len=args.episode_len)
    graphs = rd.load_graphs(args.grammar_file)
    rules = [rd.create_rule_from_graph(g) for g in graphs]
    rule_sequence = [int(s.strip(",")) for s in args.rule_sequence]

    # Determine the optimization seed.
    if args.opt_seed is not None:
        opt_seed = args.opt_seed
    else:
        opt_seed = random.getrandbits(32)
        print("Using optimization seed:", opt_seed)

    # Build and finalize the robot.
    graph = make_graph(rules, rule_sequence)
    robot = build_normalized_robot(graph)
    finalize_robot(robot)

    # If trajectory optimization is enabled, compute an input sequence.
    if args.optim:
        input_sequence, result = simulate(robot, task, opt_seed, args.jobs, args.episodes)
        print("Optimization Result:", result)
    else:
        input_sequence = None

    # Optionally save the optimized input sequence.
    if args.input_sequence_file and input_sequence is not None:
        import csv
        with open(args.input_sequence_file, 'w', newline='') as input_seq_file:
            writer = csv.writer(input_seq_file)
            for col in input_sequence.T:
                writer.writerow(col)
        print("Saved input sequence to file:", args.input_sequence_file)

    # Pre-simulate the robot to obtain its initial position and check for self-collisions.
    robot_init_pos, has_self_collision = presimulate(robot)
    if has_self_collision:
        print("Warning: robot self-collides in initial configuration")

    # Set up the simulation.
    main_sim = rd.BulletSimulation(task.time_step)
    task.add_terrain(main_sim)
    # Rotate 180 degrees around the y axis, so the base points to the right.
    main_sim.add_robot(robot, robot_init_pos, rd.Quaterniond(0.0, 0.0, 1.0, 0.0))
    robot_idx = main_sim.find_robot_index(robot)

    # Headless simulation: if no input sequence exists, create a default zero-input sequence.
    if input_sequence is None:
        try:
            num_joints = robot.get_num_joints()
        except AttributeError:
            num_joints = len(robot.links)
        num_cols = args.episode_len // task.interval
        input_sequence = np.zeros((num_joints, num_cols))

    # Save the initial simulation state, then record the starting position.
    main_sim.save_state()
    start_lower = np.zeros(3)
    start_upper = np.zeros(3)
    main_sim.get_robot_world_aabb(robot_idx, start_lower, start_upper)
    start_pos = 0.5 * (start_lower + start_upper)

    # Run the simulation trajectory (without any additional callbacks).
    run_trajectory(main_sim, robot_idx, input_sequence, task, lambda step: None)

    # After simulation, compute the final position and the distance travelled.
    end_lower = np.zeros(3)
    end_upper = np.zeros(3)
    main_sim.get_robot_world_aabb(robot_idx, end_lower, end_upper)
    end_pos = 0.5 * (end_lower + end_upper)
    distance_travelled = np.linalg.norm(end_pos - start_pos)
    print("Simulation complete.")
    print("Start position:", start_pos)
    print("Final position:", end_pos)
    print("Distance travelled:", distance_travelled)
    if args.optim:
        print("Optimization Result, Average Reward:", result)

    # Optionally, save simulation snapshots as .obj files.
    if args.save_obj_dir and input_sequence is not None:
        import export_mesh
        os.makedirs(args.save_obj_dir, exist_ok=True)
        def save_obj_callback(step_idx):
            if step_idx % 128 != 0:
                return
            obj_file_name = os.path.join(args.save_obj_dir, 'robot_{:04}.obj'.format(step_idx))
            mtl_file_name = os.path.join(args.save_obj_dir, 'robot.mtl')
            with open(obj_file_name, 'w') as obj_file, open(mtl_file_name, 'w') as mtl_file:
                dumper = export_mesh.ObjDumper(obj_file, mtl_file)
                obj_file.write("mtllib {}\n".format(os.path.split(mtl_file_name)[-1]))
                export_mesh.dump_robot(robot_idx, main_sim, dumper)
                dumper.finish()
        main_sim.restore_state()
        run_trajectory(main_sim, robot_idx, input_sequence, task, save_obj_callback)

if __name__ == '__main__':
    main()
