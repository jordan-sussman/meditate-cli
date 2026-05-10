# Meditate CLI

Meditative breathing in your terminal.

## Features

- **Visual Breathing Guide**: A pulsing ASCII circle that scales with your breath.
- **Predefined Patterns**:
  - `box`: Box Breathing (4-4-4-4).
  - `relax`: 4-7-8 Relaxing Breath.
  - `equal`: Equal Breathing (4-4).
  - `coherent`: Coherent Breathing (5-5).
  - `triangle`: Triangle Breathing (4-4-4).
- **Auto-Termination**: Session automatically ends after a set duration.
- **Customizable**: Adjustable duration and breathing pattern.

## Visual Representation

```text

        •  •  •
     •          •
    •   INHALE   •
     •          •
        •  •  •


   [========      ]
```

## Usage

Run directly for an interactive setup:

```bash
python3 meditate.py
```

Or bypass the prompts by providing arguments:

```bash
# 10-minute Relaxing Breath (4-7-8)
python3 meditate.py --pattern relax --duration 10
```

## Options

- `--pattern`: Choose between `box` (default) or `relax`.
- `--duration`: Set the session length in minutes (default: 5.0).
