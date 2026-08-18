(% 汇报文档：算法细节与数学建模 %)
# Direct ESN Compliance Controller: Algorithm Details & Mathematical Modeling

## 1. System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Proposed Architecture                 │
│                                                          │
│  WBC (Whole-Body Controller)                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Input: joint state q, q̇                           │    │
│  │ Output: nominal task twist ξ_nom (6-D)            │    │
│  │         joint velocity command q̇_cmd = J⁻¹ ξ_nom  │    │
│  └────────────────────┬────────────────────────────┘    │
│                       │ velocity command                  │
│                       ▼                                   │
│  Velocity Servo (shared, non-learned)                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │ τ_servo = K_v(q̇_cmd - q̇) + τ_gravity            │    │
│  └────────────────────┬────────────────────────────┘    │
│                       │ servo torque                     │
│                       ▼                                   │
│  Compliance Policy (learned or hand-designed)           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Input: 32-D deployable observation               │    │
│  │   [q(7), q̇(7), ξ_nom(6), e_pose(6), ė_twist(6)]│    │
│  │ Output: 7-D per-joint residual torque            │    │
│  │   τ_residual = π(x) · Δτ_budget                  │    │
│  └────────────────────┬────────────────────────────┘    │
│                       │ residual torque                   │
│                       ▼                                   │
│  τ_total = clip(τ_servo + τ_residual, -τ_max, τ_max)  │
│                       │                                   │
│                       ▼                                   │
│              Franka Research 3 (MuJoCo)                 │
│              + Panda Hand gripper                       │
└─────────────────────────────────────────────────────────┘
```

### Key Design Choice

The compliance policy outputs a **torque residual** added on top of the WBC velocity servo, not a modification of the velocity reference. This is **impedance-style** compliance: the residual torque directly changes the force balance at the moment of collision, reducing contact force and end-effector deviation. In contrast, reference-modification (admittance-style) can only shift the trajectory target without changing the contact dynamics.

---

## 2. WBC (Whole-Body Controller)

The WBC provides the nominal behavior. It outputs a task-space velocity command:

$$\xi_{\text{nom}}(t) = \begin{bmatrix} v_{\text{nom}}(t) \\ \omega_{\text{nom}}(t) \end{bmatrix} \in \mathbb{R}^6$$

joint velocity command via the Jacobian:

$$\dot{q}_{\text{cmd}} = J(q)^{-1} \, \xi_{\text{nom}}(t)$$

### Velocity Servo (execution layer)

$$\tau_{\text{servo}} = K_v (\dot{q}_{\text{cmd}} - \dot{q}) + \tau_{\text{gravity}}(q)$$

where $K_v \in \mathbb{R}^{7\times7}$ is a diagonal velocity gain, $\tau_{\text{gravity}}$ is the gravity compensation torque.

**Fixed WBC** = zero residual torque ($\tau_{\text{residual}} = 0$). This is the baseline: the robot rigidly tracks the nominal trajectory through the collision.

---

## 3. Deployable Observation (32-D)

The compliance policy reads only proprioceptive signals (no force/torque sensor, no contact information):

$$x_t = \big[\underbrace{q_t}_{7},\; \underbrace{\dot{q}_t}_{7},\; \underbrace{\xi_{\text{nom},t}}_{6},\; \underbrace{e_{\text{pose},t}}_{6},\; \underbrace{e_{\text{twist},t}}_{6}\big] \in \mathbb{R}^{32}$$

where:
- $e_{\text{pose},t} = p_{\text{nom}}(t) - p_{\text{ee}}(t)$ (3-D position error) $\oplus$ $\text{log}(R_{\text{nom}} R_{\text{ee}}^T)$ (3-D orientation error)
- $e_{\text{twist},t} = \xi_{\text{nom}}(t) - \xi_{\text{ee}}(t)$

**Forbidden signals** (privileged, training-only): contact force, contact normal, contact duration, signed distance, obstacle pose, obstacle velocity, release time.

---

## 4. Proposed: Direct ESN (Echo State Network)

### 4.1 Reservoir Dynamics

The ESN uses a fixed random recurrent reservoir with leaky-integrator dynamics:

$$s_{t+1} = (1-\alpha)\,s_t + \alpha \tanh(W_{\text{in}} x_t + W_r s_t + b)$$

where:
- $s_t \in \mathbb{R}^N$ is the reservoir state ($N=160$)
- $W_{\text{in}} \in \mathbb{R}^{N \times 32}$ is the input weight matrix (random, fixed)
- $W_r \in \mathbb{R}^{N \times N}$ is the recurrent weight matrix (random, fixed, spectral radius $\rho < 1$)
- $b \in \mathbb{R}^N$ is the bias (random, fixed)
- $\alpha = \Delta t / \tau$ is the leak rate ($\Delta t = 0.04$ s, $\tau = 0.12$ s)

The spectral radius constraint $\rho(W_r) < 1$ ensures the **echo state property**: the reservoir state is a fading function of the input history, making it a provably bounded dynamical system.

### 4.2 Linear Readout

$$a_t = \tanh(W_{\text{out}} \cdot [1;\, x_t;\, s_t]) \in [-1, 1]^7$$

where $W_{\text{out}} \in \mathbb{R}^{7 \times (1 + 32 + N)}$ is the only trained parameter.

The output $a_t$ is interpreted as a **per-joint residual torque in units of the budget**:

$$\tau_{\text{residual}} = a_t \odot \Delta\tau_{\text{budget}}$$

where $\Delta\tau_{\text{budget}} = 0.05 \times \tau_{\text{limits}}$ (5% of hardware torque limits).

### 4.3 Activation Gating

$$\text{gate}(e_{\text{pose}}) = \begin{cases} 0 & \|e_{\text{pos}}\| < \epsilon_1 \\ \text{smoothstep}\left(\frac{\|e_{\text{pos}}\| - \epsilon_1}{\epsilon_2 - \epsilon_1}\right) & \epsilon_1 \leq \|e_{\text{pos}}\| \leq \epsilon_2 \\ 1 & \|e_{\text{pos}}\| > \epsilon_2 \end{cases}$$

with $\epsilon_1 = 4$ mm, $\epsilon_2 = 12$ mm. The gated output $a_t \cdot \text{gate}(e_{\text{pose}})$ is zero when the WBC tracks well (no collision) and ramps up during deviation (collision detected via position error).

### 4.4 Training: Privileged Distillation Pipeline

**Stage 1 — Counterfactual Teacher (offline, uses privileged information)**

At each timestep, the teacher evaluates candidate actions by rolling out a cloned MjData for $H = 24$ physics steps (96 ms):

$$a^* = \arg\min_{a \in \mathcal{C}} \sum_{h=1}^{H} \big[ w_f F_h^2 + w_I I_h^2 + w_e \|e_h\|^2 + w_\tau \|\tau_h\|^2 \big]$$

where $\mathcal{C}$ = {zero, slowdown, outward-yield} × magnitudes, $F_h$ = contact force, $I_h$ = impulse, $e_h$ = terminal tracking error, $\tau_h$ = torque. The teacher sees contact force (privileged), the student never does.

**Stage 2 — Teacher DAgger** (3 iterations, produces the deterministic reference teacher)

**Stage 3 — Coverage Behavior Cloning**

The teacher is rolled out across a parameterized grid of collision scenarios on FR3. The resulting $(x_t, a_t)$ pairs are the training data for a simple ridge regression:

$$W_{\text{out}} = \arg\min_W \sum_t \|W \phi(x_t) - a_t\|^2 + \lambda \|W\|^2$$

where $\phi(x_t) = [1; x_t; s_t]$ and $\lambda = 10^{-4}$.

### 4.5 Derivative-Matched Smoothness Regularizer (optional)

To jointly optimize accuracy and actuator safety (torque rate, jerk):

$$W_{\text{out}} = \arg\min_W \big[\|XW - Y\|^2 + \lambda\|W\|^2 + \lambda_s \|\Delta X W - \text{lp}_\alpha(\Delta Y)\|^2\big]$$

where $\Delta X$ = consecutive feature differences, $\Delta Y$ = teacher action differences, $\text{lp}_\alpha$ = exponential moving average with coefficient $\alpha$. This supervises the **rate of change** of the output toward the teacher's rate (not toward zero), allowing the student to respond as fast as the teacher but no faster.

---

## 5. Baseline 1: VMC-Torque (Virtual Model Control, impedance-style)

### 5.1 Spring-Carriage Dynamics

Following Zhang, Larby, Iida, Forni (IROS 2024) and Zhang, Iida, Forni (rock-chop), the VMC baseline uses a **virtual carriage** connected to the end-effector by a saturating spring-damper:

**Carriage dynamics:**
$$m \ddot{x}_c + d_c \dot{x}_c = f_{\text{drive}} + w(x_c, \dot{x}_c, f_{\text{ext}})$$

**EE coupling (saturating spring):**
$$w = \sigma \tanh\big(K_e (x_{\text{ee}} - x_c) / \sigma\big) + D_e (\dot{x}_{\text{ee}} - \dot{x}_c)$$

where $\sigma$ = saturation force (24 N), $K_e$ = coupling stiffness, $D_e$ = coupling damping.

### 5.2 Torque Injection

The coupling wrench $w$ is mapped to joint torque via the Jacobian transpose:

$$\tau_{\text{residual}} = \text{clip}(J(q)^T w,\; -\Delta\tau_{\text{budget}},\; \Delta\tau_{\text{budget}})$$

### 5.3 Tuned Configuration

- Damping-dominant: $K_e = 4.4$ N/m (very soft spring), $\zeta = 1.2$
- Budget: 5% of torque limits
- Proprioceptive drive (WBC tracking error, no force sensor)

---

## 6. Baseline 2: MLP (Memoryless Neural Network)

A 2-layer fully-connected network:

$$h = \tanh(W_1 \tilde{x} + b_1), \quad a = \tanh(W_2 h + b_2)$$

where $\tilde{x} = (x - \mu) / \sigma$ (input normalization from training statistics), $W_1 \in \mathbb{R}^{64 \times 32}$, $W_2 \in \mathbb{R}^{7 \times 64}$.

Trained by Adam on the same expert traces as the ESN (identical data, identical activation gating, identical action interpretation). The **only** architectural difference from the ESN is the absence of the recurrent reservoir — the MLP is memoryless (each frame processed independently), while the ESN's reservoir state integrates observation history.

---

## 7. Safety Envelope

All methods share the same safety adapter:

1. **Torque budget**: $|\tau_{\text{residual}}| \leq 0.05 \times \tau_{\text{limits}}$ per joint
2. **Total torque clamp**: $|\tau_{\text{total}}| \leq \tau_{\text{limits}}$ (hardware limits: joints 1–4: 87 Nm, joints 5–7: 12 Nm)
3. **No privileged information** at deployment (only the 32-D proprioceptive observation)

---

## 8. Performance Summary (FR3, 4-fixture matched benchmark)

| Method | fx0 ΔRMSE | fx1 ΔRMSE | fx2 ΔRMSE | fx3 (held-out) ΔRMSE | Gate | Seed σ |
|---|---:|---:|---:|---:|---|---|
| Fixed WBC | 0 | 0 | 0 | 0 | — | — |
| VMC-torque | −2.6 | −6.3 | −9.6 | **−14.4** | 1/1 | — |
| **ESN-torque** | **−3.3** | **−6.3** | **−10.3** | **−18.1** | **8/8** | **±0.9** |
| MLP-torque | −3.6 | −3.5 | −8.6 | −8.4 | 7/8 | ±5.3 |

- Negative ΔRMSE = improvement over Fixed WBC (better tracking after collision)
- ESN is the **only method** that is simultaneously: best on held-out, 8/8 seed-reliable, and exceeds its teacher
