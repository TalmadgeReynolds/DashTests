# Adapter Interface Contracts

## VeoAdapter
```python
def create_job(script: str, reference_image_url: str | None, fps: int, aspect: str, max_duration: int) -> str: ...
def poll_result(provider_job_id: str) -> dict:  # {'status': 'QUEUED'|'RUNNING'|'DONE'|'ERROR', 'video_url': str|None}
```

## ElevenLabsAdapter
```python
def ensure_voice(voice_name: str) -> str
def synthesize(text: str, voice_id: str | None, stability: float = 0.65, similarity_boost: float = 0.75, pace: float = 1.0) -> str
```

## HeygenAdapter
```python
def create_talking_photo(image_url: str, audio_url: str, action_prompt: str | None, fps: int) -> str
def poll_result(provider_job_id: str) -> dict
```
