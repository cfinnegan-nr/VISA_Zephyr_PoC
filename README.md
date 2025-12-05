# VISA Zephyr PoC

A proof-of-concept project for integrating with Zephyr test management system for VISA QA processes.

## Project Overview

This project demonstrates integration capabilities with Zephyr for test management and QA workflows, leveraging GenAI capabilities for enhanced testing processes.

## Requirements

- Python 3.11+
- Virtual environment (venv)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/cfinnegan-nr/VISA_Zephyr_PoC.git
cd VISA_Zephyr_PoC
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### JIRA Ticket Reader Application

The JIRA Ticket Reader application reads ticket summaries from your Atlassian JIRA instance.

**Prerequisites:**
1. Create a `.env` file in the project root (see Configuration section below)
2. Ensure `AtlassianInput.txt` exists with your ticket keys

**Run the application:**
```bash
python -m src.jira_reader
```

Or:
```bash
python src/jira_reader.py
```

### Hello World Example

Run the hello world example:
```bash
python hello_world.py
```

## Configuration

### JIRA Credentials (Required for JIRA Ticket Reader)

**SECURITY WARNING: Never commit JIRA credentials to Git!**

The application requires JIRA credentials stored in a local `.env` file:

1. Copy the template file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your JIRA credentials:
   ```
   JIRA_SERVER_URL=https://your-instance.atlassian.net
   JIRA_USERNAME=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   ```

3. **Important:** The `.env` file is excluded from Git and should remain local only.

**To generate a JIRA API token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token and add it to your `.env` file

### Input File Format

The `AtlassianInput.txt` file should contain:
```
JIRA QA Ticket:INVHUB-21868
EPIC Ticket:INVHUB-19969
```

## Project Structure

```
VISA_Zephyr_PoC/
├── src/                    # Source code
│   ├── __init__.py
│   ├── jira_reader.py      # Main JIRA reader application
│   ├── config.py           # Configuration management
│   ├── utils.py            # Utility functions
│   └── exceptions.py       # Custom exceptions
├── hello_world.py          # Basic Hello World application
├── AtlassianInput.txt      # Input file with JIRA ticket keys
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .env                    # Local credentials (NOT committed)
├── AGENTS.md              # AI Agent development guidelines
├── README.md              # Project documentation
└── venv/                  # Virtual environment (not committed)
```

## Development Guidelines

Please refer to `AGENTS.md` for comprehensive development guidelines, coding standards, and best practices for this project.

## License

[Add your license here]

## Author

Ciaran Finnegan - SymphonyAI NetReveal

