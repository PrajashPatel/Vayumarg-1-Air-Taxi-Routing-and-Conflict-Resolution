# UAM Drone Technology

A prototype UAM / air taxi route planner using OSMnx and NetworkX to evaluate multi-drone flight requests, perform battery feasibility checks, detect conflicts, and visualize planned routes over a road network.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Expected Output](#expected-output)
- [Visualizations](#visualizations)
- [Project Structure](#project-structure)
- [GitHub Push Steps](#github-push-steps)

---

## Project Overview

This project loads a real-world road network around a city center using `osmnx`, simplifies the graph, removes nodes inside a defined no-fly zone, and plans routes for multiple air taxis.

Each flight request is evaluated for:
- shortest route based on travel time,
- battery feasibility,
- conflict detection between accepted flights,
- conflict resolution by delay or altitude separation.

---

## Key Features

- Build a directed drivable graph from OpenStreetMap
- Simplify graph and keep the largest strongly connected component
- Define a No-Fly Zone (NFZ) polygon and remove affected nodes
- Compute travel time on each edge using a drone speed model
- Process multiple air taxi requests with origin/destination matching
- Accept or reject flights based on battery feasibility
- Detect route conflicts:
  - same-path conflicts
  - crossing-path conflicts
- Resolve conflicts by:
  - time delay
  - altitude separation
- Visualize accepted flight routes on a single map

---

## Requirements

- Python 3.8+
- `osmnx`
- `networkx`
- `shapely`
- `matplotlib`

Install dependencies with:

```bash
pip install osmnx networkx shapely matplotlib