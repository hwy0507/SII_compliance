# Overnight v18 statistical summary (120 replicates)

| controller | score | Fint | peak | errF | win-rate |
|---|---|---|---|---|---|
| FW | 9.07±0.00 | 53.1±0.0 | 133.7±0.0 | 0.5±0.0 | 0% |
| VMC | 9.03±0.00 | 48.0±0.0 | 133.1±0.0 | 0.5±0.0 | 6% |
| MLP | 9.10±0.44 | 53.9±1.7 | 137.0±11.5 | 2.9±1.2 | 10% |
| MLP-DL | 8.95±0.63 | 54.1±1.6 | 135.3±15.8 | 7.9±1.3 | 32% |
| ESN-DL | 8.72±0.61 | 54.8±1.7 | 126.8±14.9 | 7.3±1.6 | 52% |

ESN-DL beats: MLP-DL 58%, MLP 72%, VMC 72%, FW 72%

## P(rank #1) under 2000 random weightings
| FW | VMC | MLP | MLP-DL | ESN-DL |
|---|---|---|---|---|
| 15% | 53% | 1% | 10% | 21% |

## Per-metric best
- **Fint**: VMC (VMC < FW < MLP < MLP-DL < ESN-DL)
- **peak**: ESN-DL (ESN-DL < VMC < FW < MLP-DL < MLP)
- **errF_mm**: FW (FW < VMC < MLP < ESN-DL < MLP-DL)
- **contact_s**: FW (FW < MLP < MLP-DL < ESN-DL < VMC)
- **chatter**: MLP-DL (MLP-DL < ESN-DL < MLP < FW < VMC)
- **saturation_s**: VMC (VMC < MLP-DL < MLP < ESN-DL < FW)

Alt config (default reservoir) cue peak: 154±9 N (config sensitivity)

Champion: rep004 (ESN-DL 7.73, peak 104 N)