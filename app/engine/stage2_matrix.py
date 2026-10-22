from typing import Tuple
from app.models.blueprint import StoryBlueprint, PlotLine, ArcBeat
from app.models.simulation import StoryMatrix, MatrixEvent
from app.engine.llm_client import llm
from app.engine.prompts import MATRIX_SYSTEM_PROMPT

async def execute_stage2(blueprint: StoryBlueprint) -> Tuple[StoryBlueprint, StoryMatrix]:
    """Stage 2: Weaves the Story Matrix (Character x Episode grid, plotlines, beats) in English."""

    char_names = [c.core.name for c in blueprint.cast.characters]
    user_prompt = f"""
Novel: "{blueprint.title}"
Logline: {blueprint.logline}
Synopsis: {blueprint.synopsis}
Setting & World: {blueprint.world.city}, {blueprint.world.country} ({blueprint.world.era})
Characters: {char_names}
Total Chapters Planned: {blueprint.total_episodes} (Short Story / Novella Arc)
Plot Structure: {blueprint.plot.structure}
Ending Style: {blueprint.plot.resolution}

STRICT NARRATIVE PACING DIRECTIVES:
This story MUST be tightly constructed to conclude within exactly {blueprint.total_episodes} chapters.
- Chapter 1: Inciting Incident, entry into the scenario, introduction of characters and initial clash of objectives.
{'- Chapters 2 to ' + str(blueprint.total_episodes - 1) + ': Escalation of conflict, revelations, shifting alliances, and high-tension confrontations.' if blueprint.total_episodes > 2 else ''}
- Chapter {blueprint.total_episodes} (FINAL CHAPTER): The dramatic climax, resolution of the central conflict/premise, and definitive conclusion. Every open question reaches closure.

Construct the comprehensive narrative matrix chapter by chapter:
For each chapter:
1. Core pivotal dramatic event.
2. For each character: their objective and arc development in this chapter.
3. Primary POV character.

Return strictly a JSON object matching this schema:
{{
  "timeline": ["Phase 1", "Phase 2"],
  "plot_lines": [
    {{
      "title": "Primary Plotline Title",
      "is_main": true,
      "synopsis": "Trajectory synopsis of this plotline",
      "beats": [
        {{"beat": "Key Event 1", "consequence": "Consequence 1", "milestone": "Milestone 1"}}
      ]
    }}
  ],
  "episodes_plan": [
    {{
      "episode_number": 1,
      "event_title": "Episode Event Title",
      "description": "What transpires in this episode",
      "pov_character": "{char_names[0] if char_names else 'Julian'}",
      "character_goals": {{
        "{char_names[0] if char_names else 'Julian'}": "Active objective in this episode"
      }}
    }}
  ]
}}
"""

    async def fallback():
        grid = {}
        for c in char_names:
            grid[c] = [
                f"Initial encounter with the mystery and resistance to danger",
                f"Discovery of the first anomalous clue and rising interpersonal friction",
                f"The crucible of crisis and moral dilemma",
                f"Decisive revelation and emerging transformed"
            ]
        
        episodes_plan = []
        for i in range(1, blueprint.total_episodes + 1):
            pov = char_names[(i - 1) % len(char_names)] if char_names else "Julian"
            episodes_plan.append({
                "episode_number": i,
                "event_title": f"Chapter {i}: Shadows and Crossroads",
                "description": f"Pivotal developments in Chapter {i} converge the fates of the protagonists.",
                "pov_character": pov,
                "character_goals": {c: f"Overcome the immediate obstacle of Chapter {i}" for c in char_names}
            })

        return {
            "timeline": [f"Phase {i}" for i in range(1, blueprint.total_episodes + 1)],
            "plot_lines": [
                {
                    "title": "Primary Thread: The Secret of the Blackwood Ledger",
                    "is_main": True,
                    "synopsis": "A race to unearth forgotten documents before institutional silence seals the truth forever.",
                    "beats": [
                        {"beat": "Inciting Incident", "consequence": "Shattered assumptions", "milestone": "Call to Adventure"},
                        {"beat": "Point of No Return", "consequence": "Entering hostile territory", "milestone": "Crossing the Threshold"}
                    ]
                }
            ],
            "episodes_plan": episodes_plan
        }

    data = await llm.generate_json(MATRIX_SYSTEM_PROMPT, user_prompt, fallback_generator=fallback)

    # Build StoryMatrix
    matrix = StoryMatrix()
    matrix.timeline = data.get("timeline", [])
    
    char_map = {c.core.name: c.key for c in blueprint.cast.characters}
    grid = {}
    for ep in data.get("episodes_plan", []):
        ep_num = ep.get("episode_number", 1)
        matrix.events.append(MatrixEvent(
            event_key=f"ev_ep_{ep_num}",
            episode_number=ep_num,
            title=ep.get("event_title", f"Episode {ep_num}"),
            description=ep.get("description", ""),
            character_keys=[char_map.get(k, k) for k in ep.get("character_goals", {}).keys()]
        ))
        for cname, goal in ep.get("character_goals", {}).items():
            ckey = char_map.get(cname, cname)
            if ckey not in grid:
                grid[ckey] = []
            grid[ckey].append(goal)

    matrix.character_episode_grid = grid

    # Plot Lines
    plot_lines = []
    for idx, pl in enumerate(data.get("plot_lines", [])):
        beats = [ArcBeat(**b) for b in pl.get("beats", [])]
        plot_lines.append(PlotLine(
            key=f"pl_{idx+1}",
            title=pl.get("title", f"Plotline {idx+1}"),
            is_main=pl.get("is_main", True),
            synopsis=pl.get("synopsis", ""),
            beats=beats
        ))
    if plot_lines:
        blueprint.plot.plot_lines = plot_lines

    return blueprint, matrix
