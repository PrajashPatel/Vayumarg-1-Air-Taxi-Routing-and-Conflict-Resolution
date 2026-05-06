# Vayumarg-1

**Vayumarg-1** is a prototype Urban Air Mobility (UAM) and drone route planning system built using `osmnx`, `networkx`, `shapely`, and `matplotlib`.

The project evaluates multiple air taxi flight requests, checks battery feasibility, detects route conflicts, applies basic conflict resolution, and visualizes planned routes over a real-world road network.

The long-term vision of Vayumarg is to develop an intelligent, scalable, and accessible system for UAM and drone technology that can support safer aerial transportation, route planning, and airspace management.

> This is the first version of the project. More updates, improvements, and advanced features will be added in future versions.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Vision](#vision)
- [Key Features](#key-features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Expected Output](#expected-output)
- [Visualizations](#visualizations)
- [Project Structure](#project-structure)
- [Current Status](#current-status)
- [Planned Future Updates](#planned-future-updates)
- [GitHub Push Steps](#github-push-steps)

---

## Project Overview

Vayumarg-1 loads a real-world road network around a selected city center using `osmnx`, simplifies the graph, removes nodes inside a defined No-Fly Zone (NFZ), and plans routes for multiple air taxi or drone requests.

Each flight request is evaluated based on:

- shortest route based on travel time
- battery feasibility
- route conflict detection
- same-path and crossing-path classification
- conflict resolution using delay or altitude separation
- final route visualization

Although the current version uses a road network as the base graph, the concept is designed as a foundation for future drone corridors, UAM air routes, and intelligent aerial traffic management.

---

## Vision

The goal of Vayumarg is to build a useful system for future UAM and drone technology.

The larger vision includes:

- safer drone and air taxi route planning
- intelligent airspace conflict detection
- better visualization of aerial mobility routes
- support for emergency, delivery, and passenger drone operations
- future-ready tools for smart cities and aerial transport systems

Vayumarg-1 is the starting prototype for this broader idea.

---

## Key Features

- Build a directed drivable graph from OpenStreetMap
- Simplify the graph and keep the largest strongly connected component
- Define a No-Fly Zone polygon and remove restricted nodes
- Compute travel time using a drone speed model
- Process multiple air taxi flight requests
- Match each origin and destination to the nearest graph node
- Accept or reject flights based on battery feasibility
- Detect route conflicts:
  - same-path conflicts
  - crossing-path conflicts
- Resolve conflicts using:
  - time delay
  - altitude separation
- Generate a single visualization showing all accepted routes

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

