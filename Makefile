all:
	.\venv\Scripts\activate && \
	pip install -r requirements.txt && \
	flask run --debug