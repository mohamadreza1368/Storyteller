---
name: qloo-cultural-intelligence
description: Connects narrative seeds, character tastes, and atmospheric settings to Qloo's real-time Cultural AI Taste Graph across books, cinema, music, and places.
---

# Qloo Cultural Intelligence Skill: Taste-Driven Narrative Architecture

## Overview
This skill leverages Qloo's Taste AI APIs (`/search`, `/v2/insights`) to infuse stories with authentic cultural affinities, character aesthetic dossiers, and geographic verisimilitude rather than generic tropes.

## Architecture & Integration Pipeline

```mermaid
flowchart LR
    A[User Seed Inputs] --> B[Qloo Entity Resolution /search]
    B --> C[Qloo Taste Graph /v2/insights]
    C --> D[Cross-Domain Affinities: Books, Films, Music, Places]
    D --> E[Scenario Generator: 3 Distinct High-Concept Premises]
    E --> F[Character Taste Profiles & Setting Details in Engine]
```

## Key Capabilities

### 1. Cross-Domain Entity Resolution
- Converts user-provided titles (e.g. *The Road*, *Blade Runner*, *Harry Potter*, *Tokyo*) into canonical Qloo entity identifiers.
- Searches across multiple domains:
  - `urn:entity:book`
  - `urn:entity:movie`
  - `urn:entity:place`
  - `urn:entity:artist`

### 2. Multi-Entity Taste Graph Inferences
- Aggregates taste vectors from diverse user inputs (e.g., matching a favorite novel and a favorite film simultaneously).
- Discovers non-obvious cultural correlations:
  - A preference for neo-noir cinema yields architectural, literary, and musical motifs that match the underlying mood.
  - Geographical place searches pull verified historical, atmospheric, and architectural points of interest into the world-building dossier.

### 3. Dynamic Premise & Scenario Synthesis
- Ingests the resolved affinities to generate 3 sharply distinct story scenarios:
  - **Scenario 1**: Plot-driven thriller, noir, or high-stakes investigation.
  - **Scenario 2**: Atmospheric, psychological, or character-driven drama.
  - **Scenario 3**: Speculative, historical, or high-concept mystery.
- Each scenario synthesizes an authentic title, logline, protagonist flaw, core conflict, and setting grounded in real cultural signals.

### 4. Character Taste Profiling
- Assigns cultural habits to characters based on their social strata, occupation, and temperament.
- Replaces generic character traits with specific musical preferences, reading habits, and aesthetic choices derived from real cultural graphs.
