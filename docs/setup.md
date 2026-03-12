# Setup

## 1. Prerequisites

- Python 3.10+
- `ffmpeg` and `ffprobe`

macOS:

```bash
brew install ffmpeg
```

## 2. Install

```bash
pip install .
```

Development:

```bash
pip install -e .[dev]
```

## 3. Verify

```bash
flas --help
```

## 4. Basic run

```bash
flas transcribe /path/to/audio.mp3 --format text
```

## 5. Suggested env baseline

```bash
export FUNASR_USE_WORKER=0
export FUNASR_ENABLE_VAD=0
export FUNASR_SENTENCE_TIMESTAMP=0
export FUNASR_CHUNK_SECONDS=60
export FUNASR_DEVICE=cpu
```
