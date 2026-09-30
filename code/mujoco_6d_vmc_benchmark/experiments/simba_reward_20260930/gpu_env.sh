# Source before launching this isolated SimbaV2 GPU environment.
export PATH=/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin:/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/home/arm1/vmc_mujoco_runtime/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:/home/arm1/vmc_mujoco_runtime/.venv/lib/python3.12/site-packages/nvidia/nccl/lib:/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export JAX_PLATFORMS=cuda
export XLA_PYTHON_CLIENT_PREALLOCATE=false
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export MUJOCO_GL=egl
