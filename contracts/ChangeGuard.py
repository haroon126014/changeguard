# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class ChangeGuard(gl.Contract):
    title: str
    old_url: str
    new_url: str
    verdict: str
    change_type: str
    changed_sections: str
    impact: str
    reasoning: str
    evaluated: bool

    def __init__(self):
        self.title = ""
        self.old_url = ""
        self.new_url = ""
        self.verdict = "NOT_EVALUATED"
        self.change_type = ""
        self.changed_sections = ""
        self.impact = ""
        self.reasoning = ""
        self.evaluated = False

    @gl.public.write
    def create_comparison(
        self,
        title: str,
        old_url: str,
        new_url: str
    ) -> None:
        title = title.strip()
        old_url = old_url.strip()
        new_url = new_url.strip()

        if self.title != "":
            raise gl.vm.UserError("Comparison already created")

        if title == "":
            raise gl.vm.UserError("Title cannot be empty")

        if len(title) > 200:
            raise gl.vm.UserError("Title is too long")

        if old_url == "":
            raise gl.vm.UserError("Old URL cannot be empty")

        if new_url == "":
            raise gl.vm.UserError("New URL cannot be empty")

        if old_url == new_url:
            raise gl.vm.UserError("URLs must be different")

        if not self._valid_url(old_url):
            raise gl.vm.UserError("Old URL must use HTTP or HTTPS")

        if not self._valid_url(new_url):
            raise gl.vm.UserError("New URL must use HTTP or HTTPS")

        if len(old_url) > 1000 or len(new_url) > 1000:
            raise gl.vm.UserError("URL is too long")

        self.title = title
        self.old_url = old_url
        self.new_url = new_url

    @gl.public.write
    def evaluate(self) -> None:
        if self.title == "":
            raise gl.vm.UserError("No comparison exists")

        if self.evaluated:
            raise gl.vm.UserError("Comparison already evaluated")

        title = self.title
        old_url = self.old_url
        new_url = self.new_url

        def compare_versions():
            try:
                old_page = gl.nondet.web.render(
                    old_url,
                    mode="text"
                )
                new_page = gl.nondet.web.render(
                    new_url,
                    mode="text"
                )
            except Exception:
                return json.dumps(
                    {
                        "verdict": "SOURCE_UNAVAILABLE",
                        "change_type": "UNKNOWN",
                        "changed_sections": "Unable to compare sources.",
                        "impact": "UNKNOWN",
                        "reasoning": (
                            "One or both document versions could "
                            "not be accessed or rendered."
                        ),
                    },
                    sort_keys=True,
                )

            prompt = f"""
Compare two versions of the same rules, policy, terms,
requirements, or public document.

COMPARISON:
{title}

OLD VERSION:
{old_page}

NEW VERSION:
{new_page}

Your job is to identify whether the meaning or practical effect
changed, not just whether words are different.

Return exactly one verdict:

NO_MATERIAL_CHANGE
MATERIAL_CHANGE
BREAKING_CHANGE

Definitions:

NO_MATERIAL_CHANGE:
There are wording, formatting, clarification, or minor edits that
do not meaningfully change obligations, permissions, eligibility,
rights, costs, deadlines, access, or user behavior.

MATERIAL_CHANGE:
The new version meaningfully changes one or more rules, obligations,
permissions, requirements, eligibility conditions, costs, deadlines,
rights, or expected behavior.

BREAKING_CHANGE:
The new version introduces a major change that removes or severely
restricts an existing right, access path, eligibility condition,
critical capability, or introduces a major new obligation or
restriction that could substantially affect users or integrations.

Also classify change_type as exactly one of:

NONE
ELIGIBILITY
DEADLINE
COST_OR_FEE
PERMISSION
RESTRICTION
OBLIGATION
ACCESS
PROCESS
MULTIPLE
OTHER

Also classify impact as exactly one of:

NONE
LOW
MEDIUM
HIGH

Rules:
- Use only the supplied document versions.
- Do not use outside knowledge.
- Ignore purely cosmetic changes.
- Do not invent missing rules.
- Focus on semantic and practical impact.
- If multiple meaningful changes exist, use MULTIPLE.
- Keep changed_sections and reasoning concise.
- changed_sections should identify the main affected section or topic.

Return JSON with exactly these fields:

{{
  "verdict": "NO_MATERIAL_CHANGE|MATERIAL_CHANGE|BREAKING_CHANGE",
  "change_type": "NONE|ELIGIBILITY|DEADLINE|COST_OR_FEE|PERMISSION|RESTRICTION|OBLIGATION|ACCESS|PROCESS|MULTIPLE|OTHER",
  "changed_sections": "short description",
  "impact": "NONE|LOW|MEDIUM|HIGH",
  "reasoning": "brief factual explanation"
}}
"""

            result = gl.nondet.exec_prompt(
                prompt,
                response_format="json"
            )

            if not isinstance(result, dict):
                raise gl.vm.UserError("Invalid comparison output")

            verdict = str(result.get("verdict", "")).strip()
            change_type = str(
                result.get("change_type", "")
            ).strip()
            changed_sections = str(
                result.get("changed_sections", "")
            ).strip()
            impact = str(result.get("impact", "")).strip()
            reasoning = str(result.get("reasoning", "")).strip()

            allowed_verdicts = (
                "NO_MATERIAL_CHANGE",
                "MATERIAL_CHANGE",
                "BREAKING_CHANGE",
            )

            allowed_change_types = (
                "NONE",
                "ELIGIBILITY",
                "DEADLINE",
                "COST_OR_FEE",
                "PERMISSION",
                "RESTRICTION",
                "OBLIGATION",
                "ACCESS",
                "PROCESS",
                "MULTIPLE",
                "OTHER",
            )

            allowed_impacts = (
                "NONE",
                "LOW",
                "MEDIUM",
                "HIGH",
            )

            if verdict not in allowed_verdicts:
                raise gl.vm.UserError("Invalid verdict")

            if change_type not in allowed_change_types:
                raise gl.vm.UserError("Invalid change type")

            if impact not in allowed_impacts:
                raise gl.vm.UserError("Invalid impact")

            if changed_sections == "":
                raise gl.vm.UserError("Changed sections cannot be empty")

            if reasoning == "":
                raise gl.vm.UserError("Reasoning cannot be empty")

            if verdict == "NO_MATERIAL_CHANGE":
                if impact not in ("NONE", "LOW"):
                    raise gl.vm.UserError(
                        "Impact does not match verdict"
                    )

            if verdict == "BREAKING_CHANGE":
                if impact != "HIGH":
                    raise gl.vm.UserError(
                        "Breaking change must have HIGH impact"
                    )

            if len(changed_sections) > 500:
                changed_sections = changed_sections[:500]

            if len(reasoning) > 1000:
                reasoning = reasoning[:1000]

            return json.dumps(
                {
                    "verdict": verdict,
                    "change_type": change_type,
                    "changed_sections": changed_sections,
                    "impact": impact,
                    "reasoning": reasoning,
                },
                sort_keys=True,
            )

        result_json = gl.eq_principle.prompt_comparative(
            compare_versions,
            principle="""
The verdict must be exactly identical.

The change_type must identify the same main category of change.

The impact must be identical.

The changed_sections and reasoning may use different wording,
but they must describe substantially the same semantic change
and practical effect.

NO_MATERIAL_CHANGE is never equivalent to MATERIAL_CHANGE
or BREAKING_CHANGE.

BREAKING_CHANGE is only equivalent to BREAKING_CHANGE.

SOURCE_UNAVAILABLE is only equivalent to SOURCE_UNAVAILABLE.
""",
        )

        result = json.loads(result_json)

        self.verdict = result["verdict"]
        self.change_type = result["change_type"]
        self.changed_sections = result["changed_sections"]
        self.impact = result["impact"]
        self.reasoning = result["reasoning"]
        self.evaluated = True

    def _valid_url(self, url: str) -> bool:
        return (
            url.startswith("https://")
            or url.startswith("http://")
        )

    @gl.public.view
    def get_title(self) -> str:
        return self.title

    @gl.public.view
    def get_old_url(self) -> str:
        return self.old_url

    @gl.public.view
    def get_new_url(self) -> str:
        return self.new_url

    @gl.public.view
    def get_verdict(self) -> str:
        return self.verdict

    @gl.public.view
    def get_change_type(self) -> str:
        return self.change_type

    @gl.public.view
    def get_changed_sections(self) -> str:
        return self.changed_sections

    @gl.public.view
    def get_impact(self) -> str:
        return self.impact

    @gl.public.view
    def get_reasoning(self) -> str:
        return self.reasoning

    @gl.public.view
    def is_evaluated(self) -> bool:
        return self.evaluated
