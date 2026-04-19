### 1. Установка виртуального окружения

```terminaloutput
python3 -m venv .venv
source .venv/bin/activate
pip install "fastapi[all]"
```

**Лучше установить FastAPI с флагом [all]. Это также установит Uvicorn (ASGI-сервер, чтобы запускать код) и
Pydantic автоматически.**

### 2. Запуск сервера:

```terminaloutput
uvicorn main:app --reload
```