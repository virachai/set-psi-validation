# Idea 101: Skill Knowledge Graph & Semantic Crawler

## Overview

While ecosystems like `skills.sh` exist as leaderboards/indexes for Agent Skills (supporting keyword and owner searches like `npx skills find`), there is a distinct opportunity to build a much smarter **Semantic Crawler & Knowledge Graph** for skills rather than relying solely on raw GitHub tags or repository names.

---

## Proposed Architecture: Skill Knowledge Graph

Instead of storing simple metadata:
```json
{
  "name": "git-guardrails-claude-code",
  "repo": "mattpocock/skills"
}
```

Store enriched graph nodes:
```json
{
  "id": "mattpocock/skills@git-guardrails-claude-code",
  "source": {
    "owner": "mattpocock",
    "repo": "skills",
    "path": "git-guardrails-claude-code"
  },
  "keywords": [
    "git",
    "guardrails",
    "claude",
    "claude-code",
    "code"
  ],
  "categories": [
    "git",
    "developer-tools",
    "code-quality",
    "ai-agent"
  ],
  "agents": [
    "claude-code"
  ],
  "related": [
    "git-hooks",
    "git-workflow",
    "code-review",
    "security",
    "commit"
  ],
  "github": {
    "stars": 123,
    "forks": 10,
    "updated_at": "..."
  }
}
```

---

## Keyword Expansion & Taxonomy

GitHub topics are often sparse. By inspecting the actual `SKILL.md` contents, we can infer taxonomy across three tiers with confidence scores:

1. **GitHub Metadata**
2. **`SKILL.md` Parsed Content**
3. **LLM / Keyword Inferred Metadata**

### Example Expansion:
- **git** ➔ `git-hooks`, `git-workflow`, `git-commit`, `git-security`, `git-guardrails`
- **claude-code** ➔ `claude`, `agent`, `coding-agent`, `anthropic`, `ai-agent`
- **guardrails** ➔ `security`, `safety`, `policy`, `validation`, `code-quality`

---

## Crawler Pipeline

```
Seed Skill
  ↓
Extract Keywords
  ↓
GitHub Search
  ↓
Discover Candidate Repos
  ↓
Detect SKILL.md
  ↓
Extract Metadata
  ↓
Keyword Expansion
  ↓
Deduplicate
  ↓
Build Knowledge Graph
```

---

## Advanced Search & Intent Querying

Moving beyond simple exact-match queries (`skills find git`):

- **Intent-based search**: `skill-index search "protect git commits"`
  - *Matches*: `git-guardrails-claude-code`, `git-hooks`, `commit-validation`, `security-review`, `pre-commit`
- **Multi-dimensional ranking**:
  - Semantic similarity
  - Keyword overlap
  - GitHub stars & install counts
  - Freshness
  - Skill quality / structure

---

## Storage Structure (`index/`)

```
index/
├── skills.json
├── keywords.json
├── categories.json
└── graph.json
```

### `skills.json`
```json
{
  "git-guardrails-claude-code": {
    "repo": "mattpocock/skills",
    "path": "...",
    "keywords": ["git", "guardrails", "claude-code"],
    "categories": ["git", "security", "developer-tools"]
  }
}
```

### `graph.json`
```json
{
  "git": [
    "git-hooks",
    "git-guardrails",
    "git-workflow",
    "commit"
  ],
  "claude-code": [
    "agent-skills",
    "coding-agent",
    "claude"
  ]
}
```

---

## Conclusion

Combining an offline crawler with a local JSON index and graph search enables developers to find agent skills based on **intent and deep content semantics** rather than superficial repository names or sparse GitHub tags.
