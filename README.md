# zenforge
Pathforge Workplace Productivity Application

## GitHub Data Sync

### Installation
Make sure you have Poetry installed, then run:
```bash
poetry install
```

### Usage

First-time bootstrap:
```bash
poetry run python -m tools.github.github_sync --bootstrap --force
```

Schedule daily sync:
```bash
poetry run python -m tools.github.github_sync --schedule daily
```

Add new repositories by updating the `config/github_repos.json` file and running bootstrap again.

### Configuration
The sync tool uses several environment variables that should be set in your `.env` file:
```env
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_environment
MONGO_URI=your_mongodb_uri
```

You can add or modify repositories to sync by editing `config/github_repos.json`.

# Run GitHub sync daily at midnight PST
0 0 * * * cd /path/to/project && poetry run python -m tools.github.github_sync --once >> /var/log/github_sync.log 2>&1
