# N8N
Community Helpdesk Chat-Bot for N8N-FlowFusion hackathon.

Paste these in the cmd of the folder the chatbot is contained:

pip install -r requirements.txt

python database/chroma_setup.py

Before using bot open two seperate cmd and paste these:
First cmd : venv\Scripts\activate
            python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

Second cmd: venv\Scripts\activate
            streamlit run frontend/streamlit_app.py
