#!/bin/sh
python3 -m pip install -r requirements.txt
python3 core/setup_database.py
python3 -m streamlit run app.py
