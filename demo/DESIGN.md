<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# TOKEN demo: design plan (owner request, 2026-11-26)

## Subject, audience, job

- **Subject.** Running language models on one laptop: what an 8B model costs in memory, waiting time and accuracy when it is quantized more or less aggressively, and what a cold start costs. The study's world is silicon and heat: a die under a thermal camera, memory filling, a chip warming from cold when a model loads.
- **Audience.** A curious technical reader who runs models locally; an admissions committee reading quickly; a researcher who wants to check every number and its label.
- **Primary job.** Say in one sentence what the laptop showed (Q8_0 took far more memory than Q4_K_M and no accuracy difference was detected), show it as the study's own picture (memory bars), then let the reader audit every value with its label: measured, exploratory, modelled, sandbox, failed.

## Colour (dark only, a thermal camera image)

| Name | Hex | Role |
|---|---|---|
| Cold Plate | `#15123A` | page background: the coldest reading on an ironbow scale, a saturated indigo, not a tinted black |
| Die | `#211D55` | raised surfaces: chart plates, panels, the sticky bar |
| Trace | `#B4AEE6` | secondary text, grid lines (darkened), hairlines |
| Ironbow | `#E0559A` | the warm middle of the scale: the Q4_K_M series, exploratory label |
| Ember | `#F59A3C` | the hot end: the Q8_0 series, the measured label, focus ring |
| White Hot | `#FFF3D6` | headline text and the hottest point in the illustration |

Body text is Frost `#EFEBFF`, a tint of White Hot toward the background so long text does not glare. The label colours are semantic, each paired with a word and a border style (never colour alone): measured solid Ember chip, exploratory dotted Ironbow, modelled dashed amber `#FFC46B`, sandbox double teal `#8FE0CF` (the cold end of a rainbow thermal scale), failed solid coral `#FF8F86` with the words "no result".

The page is dark only. A thermal image has one natural ground, and a light variant of this palette would lose the "heat on a cold plate" reading.

## Type

- **Chakra Petch** (600, latin): headlines, section titles, the frontier control. Its cut corners echo the chamfered pin-1 corner of a chip package and the logo; it is used large, never for body text.
- **IBM Plex Sans** (variable, latin): body, tables, chart labels, numbers with tabular figures. A computing-heritage grotesque with honest figures; it carries every number on the page.

No monospace face for labels. Code paths keep the browser monospace only inside `<code>`.

## Layout

Left-aligned, one reading column of at most 68 characters for prose, with figures allowed to run wider (up to 72 rem). The hero is split: the question and the one-sentence answer on the left, the thermal die on the right; on phones the die sits under the answer at reduced height.

```
+--------------------------------------------------------------+
| [mark] TOKEN          Result Experiments Frontier ... Sandbox |  sticky bar (Die)
+--------------------------------------------------------------+
| How do local model configurations      |   +-----------+     |
| trade off quality, latency and         |   | die  heat |     |  hero
| resource use?                          |   +-----------+     |
| Answer sentence built from the data.   |  Illustration, not  |
| author line                            |  study data         |
+--------------------------------------------------------------+
| Memory bars: Q4_K_M ======        5,872.0 MiB  acc 0.717     |  key result
|              Q8_0   ==========    9,162.4 MiB  acc 0.733     |
|  difference chip with its interval                            |
+--------------------------------------------------------------+
| Labels key (five words, five border styles) | status | pending|
| Experiments (three panels, failures same weight)             |
| Frontier explorer (segmented control, moving points)         |
| Assumptions | Method and limitations | Pending decisions      |
| Modelled energy (dashed amber zone)                          |
| Sandbox (double teal zone)                                   |
| Reproduce | footer                                            |
+--------------------------------------------------------------+
```

## Motion

- **One orchestrated hero moment: the cold start.** The die is drawn cold (indigo); on load its blocks warm in a wave from the core outward, memory banks last, over about 1.6 s (opacity of heat layers only, 40 ms stagger, strong ease-out). It plays once. It is labelled "Illustration, not study data" and shows no number.
- **Motion that answers the visitor.** The frontier's segmented control has a sliding indicator and the two arm markers glide to their new position when the cost axis changes (transform, 320 ms, strong ease-in-out). The memory bars reveal once when scrolled into view (clip-path, 700 ms, 80 ms stagger). The sandbox run button gives press feedback (scale 0.97, 120 ms), the progress bar fills in heat colours, and a fresh result fades in (`@starting-style`, opacity and 4 px).
- **Reduced motion.** Every animation is removed or reduced to an instant state; the illustration shows its final warm state. Hover effects sit inside `(hover: hover) and (pointer: fine)`. No `transition: all`.

## The one memorable thing

The thermal die: the logo's chamfered chip, enlarged in the hero, warming from cold indigo to white hot as if a model were loading, with the label that it is an illustration.

## Review against the frontend-design tells and the other demos

- **Near-black with one acid accent (tell 2).** First draft: `#0E0E14` with an orange accent. Changed to a saturated indigo ground and a full thermal ramp (Ironbow to Ember to White Hot) whose colours encode heat and series, so the dark page reads as a thermal image rather than a dark theme.
- **All-caps tracked eyebrow (tell 5).** The old kicker ("TOKEN · a preregistered...") and the upper-case label chips are removed; labels are lower-case words in sentence case, distinguished by border style.
- **Middle-dot meta strings (tell 5).** Replaced by sentences and semicolons.
- **Mono for data labels (tell 5).** Rejected; numbers use Plex Sans tabular figures.
- **Identical rounded cards (tell 4).** Panels use a 2 px radius with a chamfered top-left corner (the brand's pin-1 corner) and no drop shadow; the energy and sandbox zones have their own border styles because they hold different kinds of value.
- **Fade-up on every section.** None. Only the hero, the memory bars and the visitor's own actions move.
- **Search tool output.** The UI/UX search proposed "Swiss Modernism 2.0", navy on slate and EB Garamond; rejected as generic for this subject.
- **Other demos.** SCALE is a light blueprint; MARKET a 1980s trading floor; PULSE a broadcast control room; SWARM a dusk murmuration. TOKEN is the only dark thermal-imaging page and the only one whose palette is a heat scale; the brief's warning against terminal green is respected (there is no green or mono on the page).

## Brand files

`public/brand/`: `token-mark.svg` (light), `token-mark-dark.svg`, `token-mark-mono.svg`, `token-wordmark.svg`, `token-lockup.svg`, `token-lockup-dark.svg`, `token-lockup-mono.svg`, `favicon.svg`, `favicon-32.png`, `og.png` (1200 x 630). Mark: a die seen from above, a chamfered square ring (the pin-1 corner) around a hot chamfered core. Wordmark: TOKEN built from straight strokes on a 120-unit cap height, with an octagonal O that echoes the chamfer. All paths are drawn by hand (`svg_audit.py`: no issues).
