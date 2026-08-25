# My Agent Skills

A collection of reusable Agent Skills following the [Agent Skills](https://agentskills.io) standard. Each skill is defined by a `SKILL.md` file and can be loaded by any compatible AI agent (TraeCode, Claude Code, Cursor, Copilot, Codex, Gemini CLI, etc.).

## Skills

| Skill | Description |
|---|---|
| `glossary-translation` | Terminology lookup and translation using a Google Sheets glossary (38K+ terms, 12 languages). |
| `ppt-page` | Create single-file HTML presentation galleries as a vertical scrollable feed of slide cards. |
| `slides` | Create and edit PowerPoint slide decks (`.pptx`) with PptxGenJS, layout helpers, and render/validation utilities. |
| `subtitle-translation-splitter` | Split multilingual translations from an Excel file into per-language SRT subtitle files based on an English segmented SRT. |

## Install

### Option 1: Clone into your project's `.agents/skills/` directory

```bash
git clone https://github.com/USER/my-skills.git
cp -r my-skills/.agents/skills/* /your-project/.agents/skills/
```

### Option 2: Use the `skills` CLI (if available)

```bash
skills install --from https://github.com/USER/my-skills
```

## Directory Structure

```
.agents/skills/
├── glossary-translation/
│   ├── SKILL.md
│   ├── data/
│   └── scripts/
├── ppt-page/
│   ├── SKILL.md
│   ├── assets/
│   ├── references/
│   └── scripts/
├── slides/
│   ├── SKILL.md
│   ├── agents/
│   ├── assets/
│   ├── references/
│   └── scripts/
└── subtitle-translation-splitter/
    ├── SKILL.md
    └── split_translations.py
```

## License

Personal use. See individual skill directories for specific licenses.
