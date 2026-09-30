# PPO48→7 冻结部署适配准备

已准备独立SB3推理适配器及panel加载包装器，未改运行中的训练snapshot，也未在服务器启动新物理worker。当前验证只证明策略推理映射一致，闭环平台比较尚未执行。

- `scripts/canonical48_ppo_policy_20260923.py`：`Canonical48PPO(checkpoint, normalizer)`，接口仅 `act(observation48)` → bounded action7；reset无状态。
- `scripts/run_panel_ppo_20260923.py`：只替换policy loader，继续调用当前原panel main；要求UNIFIED_6D_TEACHER=1、mixture=0。不会覆盖任务、reset、WBC或safety。
- `tools/verify_canonical48_ppo_policy_20260923.py`：离线对照已记录的GPU推理动作。

适配器直接重用Stable-Baselines3 2.9.0推理，不重写神经网络。原48D observation先转换float32（与Gym actor边界一致），再使用保存的train-only VecNormalize均值、方差、epsilon=1e−8、clip_obs=12；normalizer冻结。网络Tanh及最终Box动作clip均由原SB3代码执行，action空间校验为slowdown[0,1]加6轴yield[−1,1]。推理固定CPU、单线程，输入不接受任何sim对象、contact oracle或phase标签。

640步checkpoint离线验证：使用rod/train确定性评估的600帧原始48D输入，与该次实际GPU评估记录的action比较，CPU适配最大绝对误差 **1.4901161e−8**，通过预声明atol=1e−6。均值/方差/count保持完全不变；±1e8观测stress probe的normalization恰好clip到±12。没有使用validation表现选模型。

证据：`outputs/canonical48_ppo_deployment_parity_20260923_r1/PARITY.json` 与预测NPZ。这是CPU/GPU浮点容差内一致，不宣称逐字节相等。验证用checkpoint SHA256为 `ce225502656d7deac9d0d605cae3ce8e1b19c9e900c2bdf59402fdd6bec01379`。

未来调用格式（在已固定同平台fixture配置环境中）：

```bash
UNIFIED_6D_TEACHER=1 python scripts/run_panel_ppo_20260923.py \
  --model /absolute/path/ppo_final.zip \
  --ppo-normalizer /absolute/path/vecnormalize_train_only.pkl \
  --output /absolute/path/rollout \
  --mixture 0 --scene push --teacher-force-source estimated --teacher-profile memory \
  ...原冻结fixture的其余参数...
```

包装器会在rollout旁写 `.ppo_deployment.json`，记录checkpoint/normalizer/source hashes、实际训练步数与更新数。8192预算结束后应使用预声明最后checkpoint，先对其重复离线parity，再在DGX按同一平台zero/VMC参考与冻结ESN/MLP的匹配条件评估；不按validation选择中间checkpoint。

## DGX离线兼容性实测

已确认服务器原有环境具备SB3，无需安装：Python3.12.3、aarch64、NumPy2.5.2、PyTorch2.13.0+cu130、SB3 2.9.0、MuJoCo3.11.0。只在独立目录 `outputs/ppo_deployment_20260923/offline640_r1/` 放入640步模型、normalizer、适配器和已记录600帧trace，执行纯CPU推理，没有创建或运行物理仿真。

DGX CPU预测对本机原GPU动作的最大绝对误差 **4.4703484e−8**，通过atol=1e−6；normalizer保持冻结，±12 clipping检查通过。证据为 `docs/evidence/canonical48_20260923/deployment/DGX_PARITY_640.json`。这确认当前checkpoint及normalizer能跨Python/Torch小版本加载并保持映射一致，仍不证明跨平台闭环物理轨迹一致。当前没有占用服务器物理实验worker。
