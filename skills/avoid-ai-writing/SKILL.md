---
name: avoid-ai-writing
description: Strict blacklist of overused AI buzzwords, dead cliches, and sensory substitution standards for grounded literary writing.
---

# Avoid AI Writing Skill: Vocabulary Blacklist & Sensory Concreteness

## Overview
Large language models gravitate toward a recurring subset of elevated, ornate words and melodramatic cliches that immediately identify a text as machine-generated. This skill enforces a zero-tolerance blacklist for those words and provides grounded physical substitutions.

## Dead AI Vocabulary Blacklist

### Prohibited Words & Metaphors
The following words, roots, and phrases are prohibited in all story prose, chapter narratives, scene staging, and dialogue:

| Banned Term / Phrase | Primary Problem | Concrete Literary Substitution |
|---|---|---|
| `delve` / `delving` / `delved` | Hallmark LLM jargon | investigate, search, sift, read, examine |
| `tapestry` / `rich tapestry` | Melodramatic abstraction | pattern, structure, complex reality |
| `testament` / `a testament to` | Cheap rhetorical weight | proof of, evidence, sign |
| `beacon` / `beacon of hope` | Overused inspirational cliche | guide, landmark, solitary lantern |
| `palpable` / `palpable tension` | Lazy emotional shorthand | heavy air, tense silence, rigid posture |
| `labyrinthine` | Generic complexity cliche | narrow, twisting, maze-like, winding |
| `unwavering` | Generic stoicism cliche | steady, firm, stubborn, rigid |
| `intertwined` | Abstract connection cliche | tangled, connected, bound together |
| `resonate` / `resonating` | Overused corporate/AI trope | struck a chord, carried weight, echoed |
| `dance of shadows / light` | Theatrical lighting cliche | flickering candlelight, shifting glare |
| `whispers of` | Melodramatic mood marker | hints of, rumors of, faint scent of |
| `a chill ran down [spine]` | Physiological melodrama | cold sweat on the neck, a stiffened spine |
| `air was thick with` | Stale atmosphere cliche | room smelled of, humidity clung to |
| `time stood still` | Temporal cliche | movement ceased, nobody breathed |
| `bustling` / `nestled` | Real estate / travelogue tropes | crowded, noisy, situated, tucked behind |
| `pivotal` | Over-telling importance | critical, decisive, dangerous |
| `inexorably` / `crescendo` | Artificial operatic escalation | steadily, sharp climb, sudden peak |
| `cacophony` / `kaleidoscope` | Excessive sensory inflation | harsh noise, clatter, shifting colors |

## Sensory Grounding Mandate

Instead of abstract adjectives, ground all scenes in concrete physical elements:
- **Materials**: wet slate, cold iron, raw pine, grease-stained brass, cracked leather, lime mortar.
- **Smells**: coal smoke, damp wool, bitter chicory, motor oil, ozone, wet pavement.
- **Sounds**: the scrape of a chair against uneven floorboards, the hum of a refrigeration unit, tires over wet gravel.
- **Temperatures & Tactility**: numb knuckles, sweat inside a collar, splintered handles, freezing brass door knobs.

## Automated Linting & Cleansing
In addition to prompt-level compliance, Storyteller's `writing_craft.py` runs an automated post-generation pass:
1. Scans every chapter text against the banned dictionary.
2. Applies contextual substitutions automatically when violations slip through stochastic sampling.
3. Cleans irregular or stacked punctuation (`.;`, `;;`, `..`, orphan semicolons) to preserve publication-grade mechanical cleanliness.
