# agentic-game

LangGraph 기반 전투/제작 샘플 에이전트입니다.

## 실행

```bash
uv sync
export LLM__API_KEY="..."
uv run agentic-game
```

CLI에서 메시지를 입력하면 에이전트가 응답합니다. `exit`, `quit`, `q`, `종료`를 입력하면 종료됩니다.

`.env` 파일로도 설정할 수 있습니다.

```dotenv
LLM__PROVIDER=google
LLM__API_KEY=...
LLM__MODEL=gemini-2.5-flash
LLM__TEMPERATURE=0
LLM__TIMEOUT_SECONDS=30
LLM__MAX_RETRIES=2
UI__APP_NAME=agentic-game
```
