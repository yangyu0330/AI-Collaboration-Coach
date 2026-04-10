# 텔레그램 봇 설정 가이드

## 1. 봇 생성

1. 텔레그램에서 [@BotFather](https://t.me/BotFather)에게 `/newbot` 명령을 보냅니다.
2. 봇 이름과 유저네임을 설정합니다. 유저네임은 `_bot`으로 끝나야 합니다.
3. 발급받은 Bot Token을 `.env`의 `TELEGRAM_BOT_TOKEN`에 저장합니다.

## 2. Privacy Mode 비활성화 (필수)

그룹의 일반 메시지를 모두 수신하려면 Privacy Mode를 꺼야 합니다.

`@BotFather -> /mybots -> 대상 봇 -> Bot Settings -> Group Privacy -> Turn off`

Privacy Mode가 켜져 있으면 봇은 아래 메시지만 받습니다.
- `/` 명령어
- 봇 멘션 메시지
- 봇 메시지에 대한 답장

## 3. .env 설정

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_SECRET_TOKEN=...
WEBHOOK_URL=https://your-domain.example/api/v1/telegram/webhook
```

## 4. 로컬 테스트 (ngrok)

```bash
# API 서버 실행
uvicorn apps.api.main:app --reload --port 8000

# ngrok 터널 생성
ngrok http 8000

# .env 의 WEBHOOK_URL 업데이트 후 등록
python -m scripts.set_webhook --set
```

## 5. 운영 환경 설정

```bash
# Webhook 등록
python -m scripts.set_webhook --set

# Webhook 상태 확인
python -m scripts.set_webhook --info

# Webhook 해제
python -m scripts.set_webhook --delete
```

## 6. 점검 포인트

- `POST /api/v1/telegram/webhook` 호출 시 HTTP 200이 반환되는지 확인
- `raw_messages`에 메시지가 저장되는지 확인
- `users`와 `channels`가 자동 생성/업데이트되는지 확인
- 메시지 편집 시 `raw_messages.edited_at`이 갱신되는지 확인

