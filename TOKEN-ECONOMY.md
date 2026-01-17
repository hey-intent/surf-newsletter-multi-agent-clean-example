# Token Economy Analysis

This document analyzes the token consumption of the newsletter pipeline based on **real measurements**.

## Model Recommendation

**Use a fast, small reasoning model** - this pipeline does NOT require a large-scale model because:

1. **Structured output tasks** - All agent tasks return JSON with predictable schemas
2. **Clear evaluation criteria** - Personas have explicit scoring rubrics
3. **Independent decisions** - Each grading task is self-contained
4. **No complex reasoning** - Simple classification and scoring

---

## Real Token Usage (Measured)

### Grok 4.1 Fast

https://openrouter.ai/x-ai/grok-4.1-fast

Run with **90 articles sourced**, **15 selected**, **8 finalists**.

| Call Type            | Calls | Input      | Output     | Avg In | Avg Out |
| -------------------- | ----- | ---------- | ---------- | ------ | ------- |
| selection            | 3     | 16,631     | 4,922      | 5,544  | 1,641   |
| batch_grading_phase3 | 3     | 4,757      | 6,109      | 1,586  | 2,036   |
| batch_grading_final  | 3     | 4,769      | 6,039      | 1,590  | 2,013   |
| **TOTAL**            | **9** | **26,157** | **17,070** | -      | -       |

**Total: 43,227 tokens**

---

### Mistral Small 3.2 24B

https://openrouter.ai/mistralai/mistral-small-3.2-24b-instruct

Run with **90 articles sourced**, **18 selected**, **8 finalists**.

| Call Type            | Calls | Input      | Output    | Avg In | Avg Out |
| -------------------- | ----- | ---------- | --------- | ------ | ------- |
| selection            | 3     | 17,450     | 1,427     | 5,816  | 475     |
| batch_grading_phase3 | 3     | 5,528      | 4,237     | 1,842  | 1,412   |
| batch_grading_final  | 3     | 4,850      | 3,133     | 1,616  | 1,044   |
| **TOTAL**            | **9** | **27,828** | **8,797** | -      | -       |

**Total: 36,625 tokens**

---

## Model Comparison

| Model             | Input  | Output | Total  | Output Ratio |
| ----------------- | ------ | ------ | ------ | ------------ |
| Grok 4.1 Fast     | 26,157 | 17,070 | 43,227 | 39%          |
| Mistral Small 3.2 | 27,828 | 8,797  | 36,625 | 24%          |

**Observation**: Mistral Small produces **48% fewer output tokens** than Grok. More concise reasoning.

---

## Cost Comparison

Prices from OpenRouter (context ≤128K tokens).

| Model | Input Rate | Output Rate | Input Cost | Output Cost | **Total** |
| --- | --- | --- | --- | --- | --- |
| `x-ai/grok-4.1-fast` | $0.20/1M | $0.50/1M | $0.005 | $0.009 | **$0.014** |
| `mistralai/mistral-small-3.2-24b-instruct` | $0.075/1M | $0.20/1M | $0.002 | $0.002 | **$0.004** |

**All models are very cheap** for this pipeline (~$0.005-$0.015 per run).

---

## Latency Comparison

| Model             | Selection | Phase 3 | Phase 4 | Total     |
| ----------------- | --------- | ------- | ------- | --------- |
| Grok 4.1 Fast     | ~18s      | ~26s    | ~29s    | **~73s**  |
| Mistral Small 3.2 | ~19s      | ~89s    | ~112s   | **~220s** |

**Observation**: Mistral Small is **3x slower** than Grok. Trade-off: cost vs speed.

---

## API Calls (Batch Prompting Impact)

| Phase             | Before (per-article) | After (batch) | Reduction |
| ----------------- | -------------------- | ------------- | --------- |
| Phase 3           | 45-54 calls          | 3 calls       | **93%**   |
| Phase 4           | 45 calls             | 3 calls       | **93%**   |
| **Total grading** | **~90 calls**        | **6 calls**   | **93%**   |

Based on [Cheng et al. (2023)](https://arxiv.org/abs/2301.08721) - Batch Prompting.

---

## Recommended Models

| Use Case | Model | Cost/Run | Speed |
| --- | --- | --- | --- |
| **Production (cost-optimized)** | `mistralai/mistral-small-3.2-24b-instruct` | $0.004 | Slow |
| **Production (quality)** | `x-ai/grok-4.1-fast` | $0.014 | Fast |

---

## Configuration

Edit `src/core/config.py`:

```python
# Cost-optimized (current)
LLM_MODEL = "mistralai/mistral-small-3.2-24b-instruct"

# Fast but expensive
LLM_MODEL = "x-ai/grok-4.1-fast"
```

---

## References

- Cheng et al. (2023): [Batch Prompting](https://arxiv.org/abs/2301.08721)
- OpenRouter pricing: https://openrouter.ai/models
