# How to submit Clawlendar to the MCP Server Directory

## Step 1: Fork and clone the MCP servers repo

```bash
# Fork https://github.com/modelcontextprotocol/servers on GitHub first, then:
git clone https://github.com/<your-username>/servers.git
cd servers
```

## Step 2: Add Clawlendar entry

Edit `README.md` in the servers repo. Find the appropriate section
(likely "Community Servers" or a similar table) and add:

```markdown
### Clawlendar

Timestamp-first perpetual calendar interop for AI agents. Converts dates across
Gregorian, Julian, ISO week, Minguo, Japanese era, Buddhist, sexagenary, solar
terms, Chinese lunar, Islamic, Hebrew, and Persian calendars.

- **Repository**: https://github.com/Hosuke/Clawlendar
- **Install**: `pip install clawlendar`
- **Tools**: `capabilities`, `convert`, `timeline`
```

## Step 3: Create the PR

```bash
git checkout -b add-clawlendar
git add README.md
git commit -m "Add Clawlendar: timestamp-first calendar interop MCP server"
git push origin add-clawlendar
```

Then open a PR on GitHub with this description:

---

**Title**: Add Clawlendar — Timestamp-first calendar interop MCP server

**Description**:

Clawlendar is a Python MCP server that provides cross-calendar conversion and
timestamp-first timeline projection for AI agents.

**What it does:**
- `capabilities` — discover supported calendars and payload schemas
- `convert` — convert dates between 13+ calendar systems (Gregorian, Julian,
  ISO week, Minguo/ROC, Japanese era, Buddhist, sexagenary, solar terms,
  Chinese lunar, Islamic, Hebrew, Persian)
- `timeline` — normalize any instant (Unix timestamp, ISO datetime, etc.) and
  project into multiple calendar systems with timezone awareness

**Install:**
```bash
pip install clawlendar
```

**Claude Desktop config:**
```json
{
  "mcpServers": {
    "clawlendar": {
      "command": "clawlendar"
    }
  }
}
```

**Links:**
- PyPI: https://pypi.org/project/clawlendar/
- GitHub: https://github.com/Hosuke/Clawlendar

---

## Step 4: Before submitting the PR

Make sure you have already:

1. Published to PyPI (see below)
2. Tested that `pip install clawlendar && clawlendar` works
3. Verified Claude Desktop can connect to the server

## Publishing to PyPI

```bash
# Install build tools
pip install build twine

# Build the package
cd /path/to/Clawlendar
python -m build

# Upload to Test PyPI first (optional but recommended)
twine upload --repository testpypi dist/*

# Upload to real PyPI
twine upload dist/*
```

You will need a PyPI account and API token:
1. Register at https://pypi.org/account/register/
2. Create an API token at https://pypi.org/manage/account/token/
3. Use `__token__` as username and the token as password when twine prompts
