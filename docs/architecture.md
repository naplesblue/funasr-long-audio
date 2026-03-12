# Architecture

## Data flow

1. Input audio
2. Optional chunking (`ffmpeg`) for long files
3. Per-chunk FunASR inference
4. Timestamp offset merge
5. Emit text/json transcript

## Modules

- `engine.py`
  - model loading
  - chunking + merge
  - worker server protocol (`--worker`)
  - CLI-compatible transcription execution
- `worker.py`
  - persistent worker client (`FunASRWorkerClient`)
  - process lifecycle/termination helpers
  - fallback to one-shot CLI execution
- `cli.py`
  - user entrypoint routing (`transcribe` / `worker`)
- `model_loader.py` and `cleanup.py`
  - stable export surface for integration

## Stability design

- Default `VAD=0` to avoid known unstable combinations.
- Chunking default `60s` to reduce memory peak and hallucination/repetition risk.
- Signal handling and explicit model/cache release for safer shutdown.
