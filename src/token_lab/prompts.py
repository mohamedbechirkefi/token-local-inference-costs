# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Fixed prompt templates (protocol section 6 and S1).

T1: lettered choices as in the source, answer with the label only (primary).
T2: lettered choices, answer in the form "Answer: X".
T3: choices renumbered 1..k; the model's number is mapped back to the source label.

Each rendering returns the prompt and the label map from displayed label to
source label, so scoring is always done on source labels.
"""

from __future__ import annotations

from dataclasses import dataclass

from .items import Item

TEMPLATE_IDS = ("T1", "T2", "T3")


@dataclass(frozen=True)
class RenderedPrompt:
    template: str
    text: str
    display_to_source: dict[str, str]

    @property
    def display_labels(self) -> tuple[str, ...]:
        return tuple(self.display_to_source)


def render(item: Item, template: str) -> RenderedPrompt:
    if template not in TEMPLATE_IDS:
        raise ValueError(f"unknown template {template!r}; expected one of {TEMPLATE_IDS}")
    if template == "T3":
        display = [str(i + 1) for i in range(len(item.labels))]
    else:
        display = list(item.labels)
    mapping = dict(zip(display, item.labels))
    lines = [f"{d}. {t}" for d, t in zip(display, item.texts)]
    options = ", ".join(display)
    if template == "T1":
        instruction = f"Reply with the label of the correct choice only ({options}). Do not explain."
    elif template == "T2":
        instruction = f"Reply in the form 'Answer: X' where X is one of {options}. Do not explain."
    else:
        instruction = f"Reply with the number of the correct choice only ({options}). Do not explain."
    text = "Question: " + item.question.strip() + "\n" + "\n".join(lines) + "\n" + instruction
    return RenderedPrompt(template, text, mapping)
