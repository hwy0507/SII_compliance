# FR3 robosuite-style tabletop benchmark

This experiment keeps the upstream FR3 asset, FLASK joint planner, and computed-torque WBC from the standalone sensorized FR3 environment. It adds an independent tabletop task layer organized after robosuite Stack/PickPlace conventions:

- raised-edge storage bin;
- tool tray with visual tools;
- two stacked task cubes;
- pick object and green goal marker;
- cabinet side and shelf;
- worktable apron and rear board.

The task objects are static in this development benchmark. The purpose is to validate scene organization, collision checking, trajectory routing, sensors, and WBC tracking. It is not a grasp-success claim.

Run on arm1:

    source /home/arm1/vmc_mujoco_runtime/robosuite_wbc_venv/bin/activate
    MUJOCO_GL=egl PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts:code/mujoco_6d_vmc_benchmark/experiments/flask_fr3_env_20261002 \
      python code/mujoco_6d_vmc_benchmark/experiments/robosuite_style_fr3_benchmark_20261002/run_benchmark.py \
      --fr3-xml /home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3_v2/fr3v2.xml \
      --time-scale 2.0 \
      --output /home/arm1/vmc_mujoco_runtime/robosuite_style_fr3_benchmark_20261002.mp4

The 2026-10-02 reference run created a two-segment collision-free route over 8.133 seconds (after 2x retiming), with 31 collision geometries, 23 sensors, 0 simulated contacts, 27.41 Nm peak commanded torque, 0.00980 rad peak joint tracking error, and 0.00940 rad final joint error. The result is available at:

- /home/arm1/vmc_mujoco_runtime/robosuite_style_fr3_benchmark_20261002.mp4
- /home/arm1/vmc_mujoco_runtime/robosuite_style_fr3_benchmark_20261002.json
- http://192.168.31.70:8765/robosuite_style_fr3_benchmark_20261002/

