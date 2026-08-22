# Overnight v10 statistical summary (202 replicates)

| controller | score | Fint | peak | errF | win-rate |
|---|---|---|---|---|---|
| FW | 15.25±1.63 | 121.0±5.0 | 179.9±37.7 | 0.5±0.0 | 8% |
| VMC | 13.72±1.41 | 99.3±4.6 | 175.0±32.0 | 0.5±0.0 | 32% |
| MLP | 13.73±1.42 | 129.6±6.3 | 137.2±34.8 | 1.7±1.0 | 48% |
| ESN | 15.89±1.92 | 124.1±6.4 | 200.8±44.6 | 1.9±0.8 | 8% |
| ESN10 | 16.22±3.35 | 124.4±7.1 | 209.0±81.4 | 1.9±0.8 | 4% |

ESN beats MLP in **15%** of replicates. ESN10 beats MLP in **18%**.

## P(rank #1) under 2000 random score weightings
| FW | VMC | MLP | ESN | ESN10 |
|---|---|---|---|---|
| 0% | 99% | 1% | 0% | 0% |

## Per-metric best controller
- **Fint**: VMC (VMC < FW < ESN < ESN10 < MLP)
- **peak**: MLP (MLP < VMC < FW < ESN < ESN10)
- **errF_mm**: VMC (VMC < FW < MLP < ESN < ESN10)
- **contact_s**: VMC (VMC < FW < MLP < ESN10 < ESN)
- **chatter**: ESN (ESN < ESN10 < VMC < FW < MLP)
- **saturation_s**: VMC (VMC < MLP < ESN < ESN10 < FW)

Champion replicate: rep65 (ESN 11.87 vs MLP 13.30)