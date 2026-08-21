# Overnight v10 statistical summary (175 replicates)

| controller | score | Fint | peak | errF | win-rate |
|---|---|---|---|---|---|
| FW | 12.43±0.39 | 91.4±3.1 | 117.9±9.0 | 0.4±0.0 | 3% |
| VMC | 11.99±0.22 | 134.1±3.7 | 92.3±8.3 | 25.6±0.0 | 22% |
| MLP | 12.29±0.93 | 97.3±6.4 | 128.5±17.7 | 3.8±1.8 | 30% |
| ESN | 12.12±0.90 | 92.2±4.4 | 119.0±14.9 | 0.7±0.1 | 24% |
| ESN10 | 12.01±0.79 | 91.8±4.5 | 117.3±11.5 | 0.7±0.1 | 21% |

ESN beats MLP in **53%** of replicates. ESN10 beats MLP in **56%**.

## P(rank #1) under 2000 random score weightings
| FW | VMC | MLP | ESN | ESN10 |
|---|---|---|---|---|
| 66% | 34% | 0% | 0% | 0% |

## Per-metric best controller
- **Fint**: FW (FW < ESN10 < ESN < MLP < VMC)
- **peak**: VMC (VMC < ESN10 < FW < ESN < MLP)
- **errF_mm**: FW (FW < ESN < ESN10 < MLP < VMC)
- **contact_s**: MLP (MLP < FW < ESN10 < ESN < VMC)
- **chatter**: VMC (VMC < FW < ESN10 < ESN < MLP)
- **saturation_s**: VMC (VMC < FW < MLP < ESN < ESN10)

Champion replicate: rep170 (ESN 10.11 vs MLP 12.29)