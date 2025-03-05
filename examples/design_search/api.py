#!/usr/bin/env python
from flask import Flask, request, jsonify
import random
import numpy as np
import os
import csv

import design_search
from design_search import make_graph, build_normalized_robot, presimulate, simulate
import pyrobotdesign as rd
import tasks

### EXAMPLE API USAGE
# {
#     "task": "SomeTaskClass",
#     "grammar_file": "path/to/grammar.dot",
#     "rule_sequence": [0, 1, 2],
#     "jobs": 4,
#     "optim": true,
#     "episodes": 5,
#     "episode_len": 128
# }


# For saving obj files during simulation snapshots.
import export_mesh

app = Flask(__name__)

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

@app.route('/ping', methods=['GET'])
def ping():
    return "Pong"

@app.route('/simulate', methods=['POST'])
def simulate_robot():
    try:
        # Get JSON data from the POST request.
        data = request.get_json()
        # Required parameters
        task_name = data.get('task')
        grammar_file = data.get('grammar_file')
        rule_sequence = data.get('rule_sequence')
        jobs = data.get('jobs')
        
        # Optional parameters with defaults.
        optim = data.get('optim', False)
        opt_seed = data.get('opt_seed')
        episodes = data.get('episodes', 1)
        episode_len = data.get('episode_len', 128)
        # These parameters will write files to disk if provided.
        input_sequence_file = data.get('input_sequence_file')
        save_obj_dir = data.get('save_obj_dir')
        
        # Check for required parameters.
        if not task_name or not grammar_file or rule_sequence is None or jobs is None:
            return jsonify({"error": "Missing one or more required parameters: task, grammar_file, rule_sequence, jobs"}), 400

        # Ensure rule_sequence is a list of ints.
        if isinstance(rule_sequence, list):
            rule_sequence = [int(x) for x in rule_sequence]
        else:
            # Try to split a comma-separated string.
            rule_sequence = [int(x.strip(",")) for x in rule_sequence.split()]

        # Instantiate the task from the tasks module.
        task_class = getattr(tasks, task_name)
        task = task_class(episode_len=episode_len)

        # Load grammar graphs and build rules.
        graphs = rd.load_graphs(grammar_file)
        rules = [rd.create_rule_from_graph(g) for g in graphs]

        # Determine the optimization seed.
        if opt_seed is not None:
            opt_seed_val = opt_seed
        else:
            opt_seed_val = random.getrandbits(32)
            print("Using optimization seed:", opt_seed_val)

        # Build and finalize the robot.
        graph = make_graph(rules, rule_sequence)
        robot = build_normalized_robot(graph)
        finalize_robot(robot)

        # Perform trajectory optimization if requested.
        if optim:
            input_sequence, result = simulate(robot, task, opt_seed_val, jobs, episodes)
        else:
            input_sequence = None
            result = None

        # Optionally save the input sequence to a file.
        if input_sequence_file and input_sequence is not None:
            with open(input_sequence_file, 'w', newline='') as input_seq_file:
                writer = csv.writer(input_seq_file)
                for col in input_sequence.T:
                    writer.writerow(col)
        
        # Pre-simulate the robot to obtain its initial position and check for self-collisions.
        robot_init_pos, has_self_collision = presimulate(robot)
        collision_warning = None
        if has_self_collision:
            collision_warning = "Warning: robot self-collides in initial configuration"

        # Set up the simulation.
        main_sim = rd.BulletSimulation(task.time_step)
        task.add_terrain(main_sim)
        # Rotate 180 degrees around the y axis, so the base points to the right.
        main_sim.add_robot(robot, robot_init_pos, rd.Quaterniond(0.0, 0.0, 1.0, 0.0))
        robot_idx = main_sim.find_robot_index(robot)

        # If no input sequence exists, create a default zero-input sequence.
        if input_sequence is None:
            try:
                num_joints = robot.get_num_joints()
            except AttributeError:
                num_joints = len(robot.links)
            num_cols = episode_len // task.interval
            input_sequence = np.zeros((num_joints, num_cols))

        # Save the initial simulation state and record the starting position.
        main_sim.save_state()
        start_lower = np.zeros(3)
        start_upper = np.zeros(3)
        main_sim.get_robot_world_aabb(robot_idx, start_lower, start_upper)
        start_pos = 0.5 * (start_lower + start_upper)

        # Run the simulation trajectory (no-op callback).
        run_trajectory(main_sim, robot_idx, input_sequence, task, lambda step: None)

        # After simulation, compute the final position and the distance travelled.
        end_lower = np.zeros(3)
        end_upper = np.zeros(3)
        main_sim.get_robot_world_aabb(robot_idx, end_lower, end_upper)
        end_pos = 0.5 * (end_lower + end_upper)
        distance_travelled = float(np.linalg.norm(end_pos - start_pos))

        # Optionally, save simulation snapshots as .obj files.
        obj_save_message = None
        if save_obj_dir and input_sequence is not None:
            os.makedirs(save_obj_dir, exist_ok=True)
            def save_obj_callback(step_idx):
                if step_idx % 128 != 0:
                    return
                obj_file_name = os.path.join(save_obj_dir, f'robot_{step_idx:04}.obj')
                mtl_file_name = os.path.join(save_obj_dir, 'robot.mtl')
                with open(obj_file_name, 'w') as obj_file, open(mtl_file_name, 'w') as mtl_file:
                    dumper = export_mesh.ObjDumper(obj_file, mtl_file)
                    obj_file.write("mtllib {}\n".format(os.path.split(mtl_file_name)[-1]))
                    export_mesh.dump_robot(robot_idx, main_sim, dumper)
                    dumper.finish()
            main_sim.restore_state()
            run_trajectory(main_sim, robot_idx, input_sequence, task, save_obj_callback)
            obj_save_message = f"Simulation snapshots saved in directory: {save_obj_dir}"

        # Build and return the JSON response.
        response = {
            "start_position": start_pos.tolist(),
            "end_position": end_pos.tolist(),
            "distance_travelled": distance_travelled,
            "optimization_seed": opt_seed_val,
            "optimization_result": result,
            "collision_warning": collision_warning,
            "obj_save_message": obj_save_message
        }
        return jsonify(response)
    except Exception as e:
        # If something goes wrong, return the error message.
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555) # Port 5555