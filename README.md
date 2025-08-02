# Proof2Hybrid

# Fully Automated Framework for Mathematical Benchmark Synthesis

This project is an automated pipeline based on Large Language Models (LLMs), designed to convert mathematical definitions or proofs into high-quality true/false questions suitable for model evaluation.

## ✨ Features

- **Data Generation**: Utilizes multiple different LLMs (such as GPT, Gemini, Claude, etc.) to batch-rewrite correct mathematical definitions/proofs into misleading versions that contain subtle errors.
- **Quality Filtering**: Employs a set of "adjudicator" LLMs to perform multi-round cross-validation on the generated data, automatically filtering for questions that are of moderate difficulty and are logically valid.
- **Highly Configurable**: All models, parameters, and file paths can be easily configured in 'config.py'.
- **Modular Design**: The code structure is clear, follows software engineering best practices, and is easy to maintain and further develop.

## 🏛️ Project Structure

```
math_question_pipeline/
├── README.md               # Project description
├── requirements.txt        # Dependencies
├── config.py               # Global configuration file
├── main.py                 # Main program entry point
└── src/
    ├── __init__.py
    ├── llm_api.py          # LLM API interaction module
    ├── prompts.py          # Prompt template module
    ├── stages.py           # Core pipeline stages module
    └── utils.py            # General utility functions module
```

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/RenBing-Sumeru/Multi-agent-Mathematical-Proof.git
cd Multi-agent-Mathematical-Proof
```

### 2. Create and activate a virtual environment (Recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

This project requires access to the APIs of multiple LLMs. Please set your API keys as environment variables:

```bash
# macOS / Linux
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIzaSy..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="..." # Set as needed

# Windows (CMD)
set OPENAI_API_KEY=sk-...
set GOOGLE_API_KEY=AIzaSy...
# ...
```

### 5. Run the pipeline

```bash
python main.py
```

The program will automatically create the data directory and a sample input file, and then begin execution. The final high-quality dataset will be saved in 'data/qualified_data.json'.

## ⚙️ Configuration

To change models or adjust parameters (such as the number of evaluation rounds, screening score thresholds), please directly modify the 'config.py' file.
