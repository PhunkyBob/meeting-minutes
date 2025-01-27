# Meeting Minutes

A meeting transcription and analysis application built with Python and ❤️.

## Description

Meeting Minute helps you transcribe and analyze your meetings using AssemblyAI's speech-to-text and LeMUR capabilities. The application provides a user-friendly interface to view history and save pre-defined questions (prompts).

## Features

- Meeting audio transcription
- Meeting analysis
- Interactive data grid visualization
- Database storage using SQLite & SQLAlchemy

## Requirements

- Python 3.12 or higher
- Dependencies listed in `pyproject.toml`

## Installation

1. Clone this repository

2. Create a `.env` file with your AssemblyAI API key:

```txt
ASSEMBLYAI_API_KEY=your_api_key_here
```

3. Run with `uv` (it will create the virtual environment)

```sh
uv run streamlit run main.py
```

## Docker

1. Clone this repository

2. Run Docker

```sh
docker compose up
```

## Development

To install development dependencies:

```sh
pip install .[dev]
```

Run tests:

```sh
pytest
```

## License

TBD
