@echo off
python -m pip install -r requirements.txt
python core/setup_database.py
python -m streamlit run app.py
pause
