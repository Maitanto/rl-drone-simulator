# Reinforcement Learning Drone Environment Simulator

## Polytech Grenoble - 4th Year Software Engineering Portfolio

This repository contains a custom-built, pure Python simulation environment modeling an autonomous patrol drone. Designed conceptually around Markov Decision Processes (MDP), this environment provides a formal, object-oriented framework for training and testing Reinforcement Learning (RL) agents or planning algorithms.

The primary objective of the simulated agent is to maximize the coverage of a mathematical grid divided into 4 distinct sectors, all while managing a limited battery supply and actively avoiding dynamically generated danger zones.

## Key Technical Features

* **No External Dependencies:** The engine is written in standard Python and requires no additional modules to run.


* **Native Tabular RL Compatibility:** The core `Etat` (State) data structure implements `__eq__` and `__hash__` methods natively, allowing state objects to be used directly as dictionary keys for tabular Q-learning or similar algorithms.


* **Model-Based Planning Support:** The environment provides a generative `successeurs(etat: Etat)` function. This deterministic method calculates all legal and possible subsequent states from any given state without altering the current active environment, making it ideal for graph-based exploration and Model-Based RL.


* **Customizable Environments:** Upon initialization, the user can configure the X and Y bounds of the grid, as well as a "danger rate" (0 to 100), which dictates the percentage of the map covered by fatal obstacles.



## Markov Decision Process (MDP) Formulation

The architecture separates the physical rules (handled by classes like `Environnement`, `Zone`, and `Drone`) from the mathematical state.

### 1. State Space (`Etat`)

At any timestep $t$, the agent observes a discrete, finite state. The state encapsulates:

* **Position:** Integer coordinates bounded by the defined grid length and width.


* **Resources:** Battery level, represented as an integer strictly between 0 and 100.


* **Operational Status:** Boolean flags maintaining physical consistency (`airborne`, `docked`, `crashed`).


* **Perception (`obstacle_distance`):** An abstract indicator informing the agent of imminent danger. Transitioning into a danger zone drops this value to 0, signaling a critical/terminal state to the RL wrapper.


* **Coverage (`visZones`):** A set tracking the identifiers of successfully explored zones (out of the 4 available) to evaluate patrol performance.



### 2. Action Space

The agent interacts with the environment using a discrete set of actions, each bound by strict preconditions (e.g., a docked drone cannot move, an empty battery prevents all actions):

* `takeoff_cmd`: Launches the drone from the base. Requires battery > 0.


* `move_step`: Moves the drone one tile, bounded by the grid. Consumes 1 battery point.


* `avoid_maneuver`: A defensive movement prioritizing safety by attempting to transition to a non-danger tile. Consumes 2 battery points.


* `return_home`: Moves the drone one tile closer to the base located at (0,0). Consumes 1 battery point.


* `dock_cmd` & `undock_cmd`: Handles attaching and detaching the drone from the base.


* `charge_step`: Recharges the drone's battery in increments of 5%. Requires the drone to be docked.


* `emergency_stop`: Forces an immediate crash (terminal state).



## Modes of Interaction

The simulator includes three built-in execution modes for testing and validation:

* **Mode 1 (Manual):** Interactive step-by-step piloting via the console, displaying adjacent valid tiles for movement.


* **Mode 2 (Automatic Sequence):** Reads a predefined flight plan from a `sequence.csv` file (formatted as semicolon-separated coordinate pairs, e.g., `(1,0);(2,0)`) and executes the trajectory.


* **Mode 3 (Exhaustive Exploration):** An analysis tool that uses graph exploration to calculate and display every mathematically reachable state from the initial position. This is highly useful for verifying the size of the state space before initializing an RL training loop.



## Integrating with an RL Agent (Developer Notes)

* **Reward Function Design:** This codebase is strictly an environment simulator enforcing physical constraints and transitions. It does **not** emit a reward signal natively. The reward function must be entirely designed and encapsulated within your custom RL agent wrapper layer.


* **Automating the Loop:** To automate training, bypass the interactive `input()` loop located at the bottom of the script. Instead, instantiate the environment programmatically via your master RL script to handle rapid, non-blocking episodic training.
