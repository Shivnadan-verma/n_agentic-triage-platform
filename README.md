# Agentic Triage Platform

An intelligent bug triage and assignment system that uses multiple agents to analyze bugs and assign them to the most suitable engineers.

## Architecture

The platform consists of three main agents:

1. **Supervisor Agent**: Orchestrates the workflow, loads bug data, and coordinates downstream agents
2. **Bug Analysis Agent**: Analyzes bug severity and calculates impact scores
3. **Assignment Agent**: Selects the best engineer for a bug based on skills, product alignment, workload, rating, and acceptance rate

## Project Structure

```
agentic-triage-platform/
├── app/
│   ├── agents/
│   │   ├── supervisor/      # Supervisor agent
│   │   ├── bug_analysis/    # Bug analysis agent
│   │   ├── assignment/      # Assignment agent
│   │   └── common/          # Shared utilities
│   ├── data/
│   │   └── input/           # Input JSON files
│   ├── schemas/             # Data schemas
│   └── main.py              # Entry point
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account (for Google ADK and AI Platform)

## Installation

1. Clone or navigate to the project directory:
```bash
cd agentic-triage-platform
```

2. Create a virtual environment (recommended):
```bash
# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# On Linux/Mac:
python -m venv venv
source venv/bin/activate
```

**Note for Windows PowerShell**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: The project uses Google ADK (Agent Development Kit). You may need to:
- Install the Google ADK package (check the official Google documentation for the correct package name)
- Set up Google Cloud credentials if required
- Configure authentication for `google-cloud-aiplatform`

## Running Locally

### Option 1: Run with Python (Recommended for testing)
```bash
python -m app.main
```

**Note**: Always use `python -m app.main` instead of `python app/main.py` to avoid `ModuleNotFoundError`. This ensures Python correctly resolves the `app` module.

### Option 2: Run with ADK CLI (Interactive mode)
```bash
# Run the main Triage Agent interactively
adk run app/agents/triage

# Or run individual agents
adk run app/agents/supervisor
adk run app/agents/bug_analysis
adk run app/agents/assignment
```

The ADK CLI provides an interactive interface where you can chat with the agent and provide bug payloads directly.

## Input Format

The system accepts bug payloads in the following format:

### Bug Payload
```json
{
  "bug_id": "BUG-1001",
  "severity": "High",
  "product": "Checkout",
  "description": "Payment timeout during peak hours"
}
```

**Required fields:**
- `bug_id`: Unique identifier for the bug
- `severity`: Bug severity level (e.g., "High", "Critical", "Medium", "Low")
- `product`: Product name (e.g., "Checkout", "Orders")
- `description`: Description of the bug

### Input Files (Optional)

The system can also read from files:

#### `app/data/input/bug.json`
Contains bug information in the same format as above.

### `app/data/input/engineer.json`
Contains a list of available engineers:
```json
[
  {
    "ldap_id": "u101",
    "name": "Amit Sharma",
    "role": "Backend Engineer",
    "skill_set": ["Payments", "Java"],
    "product": "Checkout",
    "total_no_of_bugs": 12,
    "rating": 4.6,
    "acceptance_rate": 0.91
  }
]
```

## How It Works

1. **Supervisor Agent** loads the bug from `bug.json` and determines the processing routes
2. **Bug Analysis Agent** analyzes the bug severity:
   - High/Critical severity → Impact score: 80
   - Other severities → Impact score: 40
3. **Assignment Agent** selects the best engineer using a scoring algorithm that considers:
   - Skill set match (+30 points per match)
   - Product alignment (+20 points)
   - Workload balance (lower is better)
   - Rating (higher is better)
   - Acceptance rate (higher is better)

## Output

The system returns a comprehensive assignment result:

```json
{
  "bug_id": "BUG-1001",
  "assigned_to": "u101",
  "impact_score": 80,
  "engineer": {
    "ldap_id": "u101",
    "name": "Amit Sharma",
    "role": "Backend Engineer",
    "skill_set": ["Payments", "Java"],
    "product": "Checkout",
    "total_no_of_bugs": 12,
    "rating": 4.6,
    "acceptance_rate": 0.91
  },
  "reasoning": "Product match: Checkout; Skill match: Payments; High rating: 4.6; Good acceptance rate: 91.00%; Current workload: 12 bugs"
}
```

The output includes:
- Bug ID and assignment
- Impact score based on severity
- Complete engineer details
- Reasoning for the assignment

## Customization

You can modify:
- **Scoring algorithm**: Edit `app/agents/assignment/graph.py` → `select()` function
- **Impact calculation**: Edit `app/agents/bug_analysis/graph.py` → `analyze()` function
- **Agent prompts**: Edit the `prompt.py` files in each agent directory

## Troubleshooting

### ModuleNotFoundError: No module named 'adk'
- Make sure you've installed the Google ADK package
- Check that `pip install -r requirements.txt` completed successfully
- Verify the correct Google ADK package name in the official Google documentation

### ModuleNotFoundError: No module named 'app'
- Make sure you're running from the project root directory
- Use `python -m app.main` instead of `python app/main.py`

### FileNotFoundError
- Verify that `app/data/input/bug.json` and `app/data/input/engineer.json` exist
- Check that file paths in `main.py` are correct

### Google Cloud Authentication Errors
- Set up Google Cloud credentials: `gcloud auth application-default login`
- Ensure you have the necessary permissions for Google Cloud AI Platform

## License

This project is provided as-is for demonstration purposes.
