# ChangeGuard

ChangeGuard is a GenLayer Intelligent Contract that compares two versions of a public document and decides whether the update actually changes its meaning or practical effect.

I made ChangeGuard because normal text diffs can show what changed, but not whether the change actually affects the rules.

You provide an old document URL and a new document URL. Validators read both versions, compare them semantically, and reach consensus on the result. The final classification and explanation are stored on-chain.

## What it checks

ChangeGuard does not treat every wording change as important.

For example, changing:

> Users can withdraw funds anytime.

to:

> Users may withdraw funds at any time.

should normally not be considered a meaningful policy change.

But changing:

> Users may withdraw funds at any time.

to:

> Withdrawals require a 7-day waiting period and a 2% fee.

has a clear practical impact.

The contract tries to distinguish between those cases instead of only looking at raw text differences.

## Verdicts

A comparison ends with one of these verdicts:

### `NO_MATERIAL_CHANGE`

Used when the document contains wording, formatting, clarification, or other minor edits without meaningfully changing how the rules work.

### `MATERIAL_CHANGE`

Used when the new version changes something that can affect users, such as:

- eligibility
- deadlines
- fees
- permissions
- obligations
- restrictions
- access
- required processes

### `BREAKING_CHANGE`

Used for larger changes that significantly restrict an existing right or capability, introduce an important new obligation, or otherwise have a major effect on users or integrations.

### `SOURCE_UNAVAILABLE`

Used when one or both document versions cannot be accessed or rendered.

## Additional classification

The contract also stores a change category.

Possible values are:

- `NONE`
- `ELIGIBILITY`
- `DEADLINE`
- `COST_OR_FEE`
- `PERMISSION`
- `RESTRICTION`
- `OBLIGATION`
- `ACCESS`
- `PROCESS`
- `MULTIPLE`
- `OTHER`

It also assigns an impact level:

- `NONE`
- `LOW`
- `MEDIUM`
- `HIGH`

Along with those fields, ChangeGuard stores:

- the main section or topic that changed
- a short explanation of why the change received that classification

## How it works

The contract has two main stages.

### 1. Create a comparison

`create_comparison()` stores:

- a title
- the old document URL
- the new document URL

Both sources must use HTTP or HTTPS.

The contract rejects:

- empty titles
- empty URLs
- invalid URL schemes
- identical old and new URLs
- URLs that are too long
- a second comparison on the same contract instance

### 2. Evaluate the change

Calling `evaluate()` starts the actual comparison.

Each validator:

1. fetches the old document
2. fetches the new document
3. reads both versions
4. compares their meaning and practical effect
5. classifies the change
6. produces a short explanation

The evaluation is intentionally focused on semantic changes.

Validators are told to ignore cosmetic edits and avoid filling in information that is not present in the supplied documents.

## Consensus

ChangeGuard uses GenLayer's nondeterministic execution and equivalence mechanism.

The main pieces used by the contract are:

- `gl.nondet.web.render`
- `gl.nondet.exec_prompt`
- `gl.eq_principle.prompt_comparative`

The web renderer retrieves both public documents.

The model then evaluates the difference between them using the rules defined in the contract.

The equivalence principle requires validators to agree on the important parts of the result.

The following fields have strict consensus requirements:

- verdict
- impact

Validators must also identify substantially the same type of change.

The wording of `changed_sections` and `reasoning` can differ, but they must describe the same underlying change and practical effect.

A `BREAKING_CHANGE` result cannot be considered equivalent to a `MATERIAL_CHANGE` or `NO_MATERIAL_CHANGE` result.

## Contract methods

### Write methods

#### `create_comparison(title, old_url, new_url)`

Creates the comparison that will later be evaluated.

This can only be called once for a contract instance.

#### `evaluate()`

Fetches both documents and runs the semantic comparison through GenLayer consensus.

Evaluation can only happen once.

### Read methods

#### `get_title()`

Returns the comparison title.

#### `get_old_url()`

Returns the original document URL.

#### `get_new_url()`

Returns the updated document URL.

#### `get_verdict()`

Returns the final verdict.

#### `get_change_type()`

Returns the main category of the detected change.

#### `get_changed_sections()`

Returns a short description of the main affected topic or section.

#### `get_impact()`

Returns the impact level.

#### `get_reasoning()`

Returns the explanation stored after evaluation.

#### `is_evaluated()`

Returns whether the comparison has already been evaluated.

## Validation

I added input and state checks so invalid comparisons are rejected before evaluation.

The contract checks for:

- empty titles
- titles longer than the allowed limit
- empty old URLs
- empty new URLs
- invalid URL schemes
- identical URLs
- overly long URLs
- duplicate comparison creation
- evaluation before a comparison exists
- repeated evaluation
- invalid verdict values
- invalid change categories
- invalid impact values
- empty reasoning
- inconsistent verdict and impact combinations

For example, a `BREAKING_CHANGE` must have `HIGH` impact.

## Tests

The test suite uses `genlayer-test` against StudioNet.

Run it with:

    gltest tests/test_changeguard.py -v --network studionet

Current result:

    10 passed

The tests cover:

- initial contract state
- valid comparison creation
- empty title rejection
- empty old URL rejection
- empty new URL rejection
- identical URL rejection
- invalid old URL rejection
- invalid new URL rejection
- duplicate comparison rejection
- evaluation without an existing comparison

## Real StudioNet test

After the unit/state tests passed, I deployed the contract to GenLayer StudioNet and ran an actual document comparison.

Contract:

    0x9e60Ad8d53C9a540054e2f4617337e503C9E030E

Deployment transaction:

    0x07b5826f4fa0feba974f2635896eaf3935a79a50b3f622d182b6ac066e029a93

Evaluation transaction:

    0x04c251a5f10cb969d677d72ae98e6d04e3cb5484cc61e425f8d16e8658e489bd

For this test I used two simple withdrawal policy versions included in the `examples` directory.

The old version allowed withdrawals at any time with no waiting period and no withdrawal fee.

The new version added:

- a mandatory 7-day waiting period
- a 2% fee on every withdrawal

ChangeGuard returned:

    Verdict: BREAKING_CHANGE
    Change type: MULTIPLE
    Impact: HIGH
    Changed section: Withdrawal timing and fees

Stored reasoning:

    The update introduces a significant mandatory 7-day waiting period where none existed and imposes a new 2 percent financial penalty on all withdrawals, severely restricting immediate access to funds and increasing costs.

The evaluation reached GenLayer consensus and was accepted with `MAJORITY_AGREE`.

## Example files

The repository includes:

    examples/old-policy.md
    examples/new-policy.md

These are intentionally small examples so the behavior of the contract is easy to inspect and reproduce.

They are test data, not real financial terms or production policies.

## Possible uses

I built ChangeGuard as a general comparison contract rather than tying it to one application.

Some places where the same pattern could be useful:

- DAO rule changes
- governance policies
- grant requirements
- accelerator eligibility rules
- bounty terms
- marketplace policies
- protocol documentation
- service terms
- agent permissions
- API usage policies
- fee or withdrawal policy updates

A frontend or another contract could use the stored verdict to flag important updates for review.

## Why GenLayer

A normal diff can compare text, but this contract needs to decide whether a change affects meaning, rights, fees, access, or obligations.

That judgment is nondeterministic, so I use GenLayer validators and store the agreed result on-chain.

## Current limitations

The current version keeps the scope to one comparison per contract.

A few limitations remain:

- one contract instance handles one comparison
- each side currently uses one public URL
- the fetched page is evaluated at execution time
- document contents are not permanently snapshotted by the contract
- very large or heavily dynamic pages may not be ideal inputs
- the contract identifies the main change category instead of storing a full structured list of every changed clause
- the final classification still depends on validator interpretation within the rules defined by the contract

For production use, a future version could add document hashes or snapshots so the exact evaluated versions can be independently preserved.

## Repository structure

    changeguard/
    ├── contracts/
    │   └── ChangeGuard.py
    ├── examples/
    │   ├── old-policy.md
    │   └── new-policy.md
    ├── tests/
    │   └── test_changeguard.py
    ├── requirements.txt
    └── README.md

## Status

Current development status:

- contract implemented
- strict typecheck passed
- 10 StudioNet tests passed
- deployed to StudioNet
- real old/new document comparison completed
- consensus result successfully stored on-chain

## License

MIT
