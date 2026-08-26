# NOVA • Government Scheme Finder

A futuristic Streamlit Class 12 AI capstone that recommends Indian government schemes from a citizen profile and opens the scheme's official application/information route.

## Streamlit Community Cloud deployment

1. Create a new **public GitHub repository** (for example `nova-scheme-finder`).
2. Upload the **contents of this folder** to the repository. Do not upload `.venv`.
3. On Streamlit Community Cloud, create a new app and select the repository.
4. Set **Main file path** to `app.py`.
5. Deploy.
6. On the first launch, NOVA downloads the source CSV from Hugging Face and caches 500 usable records in SQLite. Later reruns use the local database.

### Important
The deployed environment needs outbound internet access during its first database setup. The source dataset is the SmartDuke Technologies Indian Government Schemes Dataset 2026, whose dataset card says the original source is myScheme.gov.in. The dataset is licensed CC BY 4.0.

Source: https://huggingface.co/datasets/smartduketech/indian-government-schemes-2025
Government discovery portal: https://www.myscheme.gov.in/

## Local run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```text
NOVA_SchemeFinder_Final/
├── app.py
├── requirements.txt
├── .gitignore
├── .streamlit/config.toml
├── core/
│   ├── database.py
│   └── setup_database.py
└── chatbot/
    └── bot_engine.py
```

NOVA is a school-project recommendation tool, not a government authority. Scheme eligibility and application routes can change, so users should verify the latest information on the linked official portal before applying.
