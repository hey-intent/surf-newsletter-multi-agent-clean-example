# TEACHME: Surf Newsletter Generator

> Estimated time: 3-4h | Level: Junior | Last updated: 2026-01-17

A multi-agent system that curates surf news using LangGraph for orchestration. Three AI "editors" with distinct personalities evaluate and rank articles.

## What You'll Learn

- How to orchestrate multiple AI agents with LangGraph
- The Persona pattern for customizing agent behavior
- The `Send()` API for parallel execution
- A 5-phase pipeline with result aggregation
- The architecture of a real multi-agent system

---

## Step 0: First Contact (15 min)

### Run the project

```bash
# Install dependencies
uv sync

# Configure your API key (OpenRouter)
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY=sk-or-v1-...

# Run the pipeline
python main.py --days 3 --debug
```

### What you should see

```
==================================================
   SURF NEWSLETTER PIPELINE (LangGraph)
==================================================

Phase 1: Sourcing articles (last 3 days)...
   Sourced 47 articles
Phase 2: Dispatching selection to 3 agents...
   Johnny: Selecting 6 articles...
   Annie: Selecting 6 articles...
   Joana: Selecting 6 articles...
[...]
==================================================
   PIPELINE COMPLETE
==================================================

Newsletter generated: newsletter_20260117.html
```

### Try this

- [ ] Open `newsletter_20260117.html` in your browser
- [ ] Note the scores and comments from each editor
- [ ] Re-run with `--days 1` - observe the difference in content

### Question to keep in mind

"How do 3 agents with different personalities collaborate to produce ONE newsletter?"

Don't read the code now. Just observe.

---

## Step 1: The Entry Point (30 min)

### Find the entry file

The project starts in: `main.py`

### Read ONLY these lines

```python
# main.py - lines 66-72
from src.pipelines.newsletter_orchestrator import NewsletterPipeline

pipeline = NewsletterPipeline(days=args.days, debug=args.debug)
result = pipeline.run(output_path)
```

That's it. The rest is CLI setup.

### Draw the first level

```
main.py
    |
    +-- NewsletterPipeline (newsletter_orchestrator.py)
            |
            +-- newsletter_graph (newsletter_graph.py)
                    |
                    +-- [5 pipeline phases]
```

### Mission

Answer this question: "What does `NewsletterPipeline.run()` actually do?"

Hint: look at `src/pipelines/newsletter_orchestrator.py`, lines 62-68.

Your answer: _______________ (spoiler: `self.graph.invoke(initial_state)`)

---

## Step 2: The Happy Path (45 min)

### The scenario

We'll follow: "An article arrives from RSS and ends up in the HTML newsletter"

### Your detective mission

Find all the files traversed when an article is processed.

### Hints

1. Start by searching for "Phase 1" in `src/pipelines/newsletter_nodes.py`
2. You'll see `sourcing_node` which calls `fetch_articles`
3. Follow the phases one by one...

### Trace the path

```
[RSS Feeds]
    |
    v
src/compute/fetcher.py        --> fetch_articles()
    |                              Returns: list[Article]
    v
src/pipelines/newsletter_nodes.py --> sourcing_node()
    |                              Stores in state["articles"]
    v
src/pipelines/newsletter_graph.py --> route_to_selection()
    |                              Creates 3 Send() to "selection"
    v
src/agents/selector.py        --> SelectorAgent.run()
    |                              Each persona chooses 6 articles
    v
src/compute/aggregator.py     --> build_selected_articles()
    |                              Merges selections (~15-18 unique)
    v
[Phase 3: Cross-grading...]
    v
[Phase 4: Final grading...]
    v
src/compute/renderer.py       --> render_newsletter()
    |                              Generates HTML with Jinja2
    v
[newsletter_YYYYMMDD.html]
```

### Checkpoint

- [ ] I found 8+ files involved
- [ ] I can explain the role of `newsletter_nodes.py` vs `newsletter_graph.py`
- [ ] I understand why there's "aggregation" after each parallel phase

---

## Step 3: The Building Blocks (1h)

For each block, we'll answer:
- What is it? (1 sentence)
- What does it receive?
- What does it produce?
- Who does it talk to?

### Block 1: Persona

File: `src/core/personas/base.py`

**What is it**: A dataclass that defines an agent's "personality".

```python
@dataclass(frozen=True)
class Persona:
    name: str           # "Johnny", "Annie", "Joana"
    description: str    # Editor's background
    system_prompt: str  # System prompt for the LLM
    criteria_text: str  # Evaluation criteria with weights
```

**Input**: Nothing (it's a static definition)
**Output**: Used by agents to build their prompts
**Talks to**: `SelectorAgent`, `GraderAgent`

**Read this file**: `src/core/personas/johnny.py`

Observe how Johnny is defined:
- Performance (30%), Competition (30%), Tech (20%), Data (20%)

### Block 2: BaseAgent

File: `src/agents/base.py`

**What is it**: Abstract class that combines a Persona with LLM logic.

```python
class BaseAgent(ABC):
    def __init__(self, persona: Persona):
        self.persona = persona

    def _call_llm(self, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": self.persona.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.llm.invoke(messages)
```

**Input**: A `Persona` at construction
**Output**: Formatted LLM response
**Talks to**: OpenRouter API via LangChain

**Important**: Note the `@retry` decorator - built-in API error handling.

### Block 3: SelectorAgent

File: `src/agents/selector.py`

**What is it**: Agent that chooses the best articles according to its persona.

```python
class SelectorAgent(BaseAgent):
    def run(self, articles: list[Article], k: int = 6) -> list[int]:
        prompt = self._build_prompt(articles, k)
        response = self._call_llm(prompt)
        return self._parse_response(response, k, len(articles))
```

**Input**: List of articles + number to select
**Output**: List of indices of chosen articles
**Talks to**: LLM via `BaseAgent._call_llm()`

### Block 4: BatchGraderAgent

File: `src/agents/batch_grader.py`

**What is it**: Agent that scores MULTIPLE articles in a single LLM call (batch prompting).

```python
class BatchGraderAgent(BaseAgent):
    def run(self, articles: Sequence[SelectedArticle], is_final: bool = False) -> list[GradingResult]:
        prompt = self._build_batch_prompt(articles, is_final)
        response = self._call_llm(prompt)
        return self._parse_batch_response(response, len(articles))
```

**Input**: List of articles + "final round" flag
**Output**: List of `GradingResult` (one per article, same order)
**Talks to**: LLM via `BaseAgent._call_llm()`

**Why batch?** Reduces API calls by 93% (from ~72 to 6). Based on [Cheng et al. (2023)](https://arxiv.org/abs/2301.08721).

### Block 5: NewsletterState

File: `src/pipelines/newsletter_state.py`

**What is it**: The pipeline's "backpack" - all shared state.

```python
class NewsletterState(TypedDict, total=False):
    # Config
    days: int
    output_path: str

    # Phase 1
    articles: list[Article]

    # Phase 2 (MAGIC: Annotated with reducer!)
    selections: Annotated[dict[str, list[int]], merge_selections]

    # Phase 3
    phase3_grades: Annotated[list[dict], operator.add]
    [...]
```

**Input**: Initial state from `newsletter_orchestrator.py`
**Output**: Evolves through phases
**Talks to**: All graph nodes

**Crucial**: The `Annotated` types with reducers (`merge_selections`, `operator.add`) allow LangGraph to merge parallel results!

### Mission

Fill in this table:

| Block | Role (1 sentence) | Main input |
|-------|-------------------|------------|
| Persona | Defines the personality | - |
| BaseAgent | LLM wrapper with persona | Persona |
| SelectorAgent | Chooses best articles | list[Article] |
| BatchGraderAgent | Scores multiple articles in one call | list[SelectedArticle] |
| NewsletterState | Shared pipeline state | Initial config |

---

## Step 4: The Connections - LangGraph (1h)

### How the blocks talk to each other

The communication pattern: **LangGraph StateGraph with Send()**

### The graph schema

```
START
  |
  v
[sourcing] -----------------> Fetch RSS
  |
  | route_to_selection()     <-- Returns 3 Send()
  |
  +---> [selection] Johnny ---+
  +---> [selection] Annie  ---+--> [aggregate_selections]
  +---> [selection] Joana  ---+            |
                                           |
                            route_to_batch_cross_grading()
                                           |
  +---> [batch_cross_grading] Johnny ---+
  +---> [batch_cross_grading] Annie  ---+--> [aggregate_phase3]
  +---> [batch_cross_grading] Joana  ---+            |
                                                    |
                            route_to_batch_final_grading()
                                                    |
  +---> [batch_final_grading] Johnny ---+
  +---> [batch_final_grading] Annie  ---+--> [aggregate_final]
  +---> [batch_final_grading] Joana  ---+            |
                                                    v
                                              [generate]
                                                    |
                                                    v
                                                   END

Note: Batch mode = 3 API calls per phase (one per persona), not N×3!
```

### The key concept: Send()

Look at `src/pipelines/newsletter_graph.py`, lines 31-54:

```python
def route_to_selection(state: NewsletterState) -> list[Send]:
    """Route to parallel agent selection nodes."""
    return [
        Send(
            "selection",           # Target node name
            {
                "persona": persona,  # Input for THIS node
                "articles": articles,
            },
        )
        for persona in ALL_PERSONAS  # 3 personas = 3 Send()
    ]
```

**Send()** allows you to:
1. Launch multiple instances of the same node in parallel
2. Pass different inputs to each instance
3. LangGraph collects all results and merges them via reducers

### Find these connections in the code

**Connection 1**: Sourcing -> Selection (parallel)

In `newsletter_graph.py`, lines 177-181:
```python
graph.add_conditional_edges(
    "sourcing",
    route_to_selection,  # Function that returns list[Send]
    ["selection"],       # Possible nodes
)
```

Question: Why `conditional_edges` and not `add_edge`?

**Connection 2**: Selection -> Aggregation

In `newsletter_graph.py`, line 184:
```python
graph.add_edge("selection", "aggregate_selections")
```

LangGraph waits for ALL Send() to complete before executing `aggregate_selections`.

**Connection 3**: The reducers in State

In `newsletter_state.py`, line 36:
```python
selections: Annotated[dict[str, list[int]], merge_selections]
```

The `merge_selections` reducer combines:
- `{"Johnny": [1,2,3]}`
- `{"Annie": [4,5,6]}`
- `{"Joana": [7,8,9]}`

Into: `{"Johnny": [1,2,3], "Annie": [4,5,6], "Joana": [7,8,9]}`

### Mission

Add the missing numbers:

- Phase 2 launches ___ selections in parallel
- Phase 3 launches ___ batch grading calls (one per persona)
- Phase 4 launches ___ batch grading calls (one per persona)
- Total API calls for grading: ___ (was ~72 before batch mode!)

Answers: 3, 3, 3, 6

---

## Step 5: The Patterns (45 min)

### Patterns used in this project

#### Pattern 1: Persona Pattern

**Where**: `src/core/personas/`

**Why it's used here**: Allows creating multiple agent "personalities" without duplicating the agent code itself.

**How you recognize it**:
- Dataclass with `system_prompt` and `criteria`
- Agent that receives a Persona in constructor
- Same agent code, different behavior based on Persona

```python
# Same SelectorAgent, 3 different behaviors
johnny_selector = SelectorAgent(JOHNNY)
annie_selector = SelectorAgent(ANNIE)
joana_selector = SelectorAgent(JOANA)
```

#### Pattern 2: Map-Reduce (via Send/Aggregate)

**Where**: `src/pipelines/newsletter_graph.py`, `src/compute/aggregator.py`

**Why it's used here**: Distribute work across multiple agents then combine results.

**How you recognize it**:
- `route_to_*` function that returns `list[Send]` (MAP)
- `aggregate_*` node that combines results (REDUCE)
- Reducer in State (`Annotated[..., operator.add]`)

```
MAP:    route_to_selection() -> [Send, Send, Send]
        Each agent works independently

REDUCE: aggregate_selections_node()
        Combines the 3 results into 1 deduplicated list
```

#### Pattern 3: Pipeline/Chain of Responsibility

**Where**: `src/pipelines/newsletter_graph.py`

**Why it's used here**: Each phase depends on the previous one, with aggregation points.

**How you recognize it**:
- Linear graph with "parallel branches"
- `START -> node1 -> node2 -> ... -> END`
- Each node reads and writes to a shared State

#### Pattern 4: Lazy Initialization

**Where**: `src/agents/base.py`, lines 37-41

**Why it's used here**: Don't create the LLM client until we need it.

```python
@property
def llm(self) -> ChatOpenAI:
    if self._llm is None:
        self._llm = get_llm()
    return self._llm
```

### Mission

For each pattern, find ONE other place where you could apply it:

| Pattern | Possible application |
|---------|---------------------|
| Persona | Add a 4th editor "Carlos" for big waves |
| Map-Reduce | Parallelize RSS feed fetching |
| Pipeline | Add a "fact-checking" phase |
| Lazy Init | Load Jinja2 templates on demand |

---

## Step 6: First Commit (30 min)

### Your mission

Add a log to see batch grading results in Phase 4.

### Steps

1. Open `src/pipelines/newsletter_nodes.py`
2. Locate the `batch_final_grading_node` function (line ~132)
3. After the line `results = agent.run(articles, is_final=True)`, add:

```python
for i, result in enumerate(results):
    logger.info(
        f"      {persona.name} scored article #{i+1} -> {result.score}/5"
    )
```

4. Test with `python main.py --days 1 --debug`

### What can go wrong

- If error "logger not defined": Verify that `logger = logging.getLogger(__name__)` is at the top of the file (it's already there)
- If no log visible: Make sure to use `--debug`

### Congratulations!

You've modified the pipeline. It's no longer a black box.

---

## Validation Quiz

### Level 1: Navigation

- [ ] Without searching, in which file is `GradingResult` defined?
- [ ] How many files are in `src/pipelines/`?
- [ ] Where is the `ALL_PERSONAS` list?

### Level 2: Understanding

- [ ] Why is Phase 3 called "Cross-Grading"? (Hint: who does NOT grade?)
- [ ] What happens if 2 agents select the same article?
- [ ] Why use `Annotated[list, operator.add]` instead of a simple `list`?

### Level 3: Modification

- [ ] If you want to add a second Joana with different criteria, which files do you touch?
- [ ] Where would you add an "advanced deduplication" phase between Phase 2 and 3?
- [ ] How would you make Phase 4 grade only the top 10 instead of 15?

### Answers

<details>
<summary>Level 1</summary>

1. `src/core/models.py`
2. 5 files (`__init__.py`, `newsletter_state.py`, `newsletter_nodes.py`, `newsletter_graph.py`, `newsletter_orchestrator.py`)
3. `src/core/personas/__init__.py`

</details>

<details>
<summary>Level 2</summary>

1. Because agents who DID NOT select an article grade it (cross = across)
2. The article appears once in `selected_articles` but with `selected_by=["Johnny", "Annie"]`
3. So LangGraph automatically merges parallel results (lists are concatenated)

</details>

<details>
<summary>Level 3</summary>

1. Create `src/core/personas/joana2.py`, then add in `__init__.py`
2. Create a new node in `newsletter_nodes.py` and insert it in `newsletter_graph.py` between `aggregate_selections` and `route_to_cross_grading`
3. Modify `FINALISTS_COUNT` in `src/core/config.py`

</details>

---

## Mental Map of the Project

```
                         ┌─────────────────────────────────────┐
                         │        SURF NEWSLETTER              │
                         │   Multi-Agent AI Curation System    │
                         └─────────────────────────────────────┘
                                          │
           ┌──────────────────────────────┼──────────────────────────────┐
           │                              │                              │
           v                              v                              v
┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│      src/core/      │       │     src/agents/     │       │    src/pipelines/   │
│                     │       │                     │       │                     │
│ - models.py         │       │ - base.py           │       │ - newsletter_state  │
│   Article           │       │   BaseAgent         │       │   NewsletterState   │
│   GradingResult     │       │                     │       │                     │
│   SelectedArticle   │       │ - selector.py       │       │ - newsletter_nodes  │
│                     │       │   SelectorAgent     │       │   sourcing_node     │
│ - config.py         │       │                     │       │   selection_node    │
│   RSS_FEEDS         │       │ - batch_grader.py   │       │   batch_cross_      │
│   FINALISTS_COUNT   │       │   BatchGraderAgent  │       │     grading_node    │
│                     │       │                     │       │   batch_final_      │
│                     │       │                     │       │     grading_node    │
│ - personas/         │       └──────────┬──────────┘       │ - newsletter_graph  │
│   johnny.py         │                  │                  │   build_graph()     │
│   annie.py          │                  │                  │   Send() routing    │
│   joana.py          │                  │                  │                     │
└──────────┬──────────┘                  │                  │ - newsletter_       │
           │                             │                  │   orchestrator      │
           │                             │                  │   NewsletterPipeline│
           │                             │                  └──────────┬──────────┘
           │                             │                             │
           └─────────────────────────────┼─────────────────────────────┘
                                         │
                                         v
                              ┌─────────────────────┐
                              │    src/compute/     │
                              │                     │
                              │ - fetcher.py        │
                              │   fetch_articles()  │
                              │                     │
                              │ - aggregator.py     │
                              │   build_selected    │
                              │   aggregate_grades  │
                              │                     │
                              │ - renderer.py       │
                              │   render_newsletter │
                              └─────────────────────┘

Legend:
─────── Imports / Uses
┌─────┐
│     │ Module/Package
└─────┘
```

### Simplified Data Flow

```
RSS Feeds ──> fetch_articles() ──> list[Article]
                                        │
                     ┌──────────────────┴──────────────────┐
                     │           SELECTION                 │
                     │  Johnny ──┐                         │
                     │  Annie  ──┼──> list[SelectedArticle]│
                     │  Joana  ──┘    (~15-18 unique)      │
                     └──────────────────┬──────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     │      BATCH CROSS-GRADING            │
                     │  Each persona grades ALL articles   │
                     │  in ONE call ──> phase3_scores      │
                     │  (3 API calls total)                │
                     └──────────────────┬──────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     │      BATCH FINAL GRADING            │
                     │  Each persona grades ALL finalists  │
                     │  in ONE call ──> final_scores       │
                     │  (3 API calls total)                │
                     └──────────────────┬──────────────────┘
                                        │
                                        v
                              Top 15 ranked articles
                                        │
                                        v
                              newsletter_YYYYMMDD.html
```

---

## Going Further

### Modification Ideas

1. **Add a 4th editor**: Create `src/core/personas/carlos.py` for a big wave expert
2. **Modify the weights**: Change the percentages in Johnny's criteria
3. **Add an RSS source**: Modify `RSS_FEEDS` in `config.py`
4. **Customize the HTML template**: Edit `templates/newsletter.html`

### Advanced Concepts to Explore

- **LangGraph Checkpointing**: Save state to resume after errors
- **Streaming**: Display results in real-time
- **Human-in-the-loop**: Add human validation before Phase 5

---

**You've completed the TEACHME!** You now know the architecture of a real multi-agent system with LangGraph.
