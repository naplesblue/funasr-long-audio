# FunASR Long Audio Safe

Reliable long-audio transcription toolkit for FunASR.
FunASR 长音频稳定转录工具。

[![License](https://img.shields.io/github/license/naplesblue/funasr-long-audio)](https://github.com/naplesblue/funasr-long-audio/blob/main/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/funasr-long-audio-safe)](https://pypi.org/project/funasr-long-audio-safe/)
[![PyPI](https://img.shields.io/pypi/v/funasr-long-audio-safe)](https://pypi.org/project/funasr-long-audio-safe/)

- EN docs: [English](#english)
- 中文文档: [中文](#中文)
- Release checklist / 发布清单: [docs/release-checklist.md](./docs/release-checklist.md)

---

## English

### What It Solves

In long-audio production workloads, two issues are common:

1. VAD-enabled paths may fail on some model/runtime combinations.
2. Disabling VAD and feeding very long audio directly can cause high memory usage.

This project addresses both with:

- `ffmpeg` chunking for long audio
- per-chunk inference
- timestamp offset merge
- worker/CLI process lifecycle controls
- explicit resource cleanup on errors/termination

### Features

- Long-audio chunk transcription (`FUNASR_CHUNK_SECONDS`, default `60`)
- Worker mode (`--worker`) and single-shot CLI mode
- JSON protocol worker endpoint for integration
- Process termination guards and memory cleanup
- Standalone package focused only on transcription runtime layer

### Installation

Prerequisites:

- Python `3.10+`
- `ffmpeg` and `ffprobe` in `PATH`

Install package:

```bash
pip install .
```

Dev install:

```bash
pip install -e .[dev]
```

### CLI Usage

```bash
# show help
flas --help

# transcribe (text)
flas transcribe /path/to/audio.mp3

# transcribe (json)
flas transcribe /path/to/audio.mp3 --format json --output transcript.json

# worker mode
flas worker --worker-max-jobs 10 --worker-idle-timeout 180 --worker-max-seconds 1800
```

You can also pass engine args directly:

```bash
flas /path/to/audio.mp3 --format text
```

### Recommended Stable Baseline

```bash
FUNASR_USE_WORKER=0
FUNASR_ENABLE_VAD=0
FUNASR_SENTENCE_TIMESTAMP=0
FUNASR_CHUNK_SECONDS=60
FUNASR_DEVICE=cpu
```

### Key Environment Variables

- `FUNASR_CHUNK_SECONDS` (default `60`)
- `FUNASR_ENABLE_VAD` (`0|1`, default `0`)
- `FUNASR_SENTENCE_TIMESTAMP` (`0|1|auto`, default `0`)
- `FUNASR_DEVICE` (`cpu|mps|auto|cuda:0`, default `cpu`)
- `FUNASR_MODEL_PY_PATH`
- `FUNASR_MODEL_DIR`
- `FUNASR_WORKER_MAX_JOBS`
- `FUNASR_WORKER_IDLE_TIMEOUT`
- `FUNASR_WORKER_MAX_SECONDS`

### Package Layout

```text
src/funasr_long_audio_safe/
  engine.py       # extracted transcription core
  worker.py       # worker client + CLI fallback helper
  cli.py          # public command entry
  model_loader.py # exported model-loading helpers
  cleanup.py      # exported cleanup helpers
```

### Scope and Non-Goals

This repository intentionally focuses on local transcription runtime only.

Not included:

- YouTube downloading
- LLM summarization/extraction
- Obsidian sync logic

### Release Checklist

See [docs/release-checklist.md](./docs/release-checklist.md).

### License

MIT

---

## 中文

### 解决的问题

在长音频生产场景中，常见两类问题：

1. 开启 VAD 的路径在部分模型/运行时组合下不稳定，可能失败。
2. 关闭 VAD 后直接喂超长音频，内存峰值可能过高。

本项目通过以下机制解决：

- `ffmpeg` 长音频切片
- 分片逐段推理
- 时间戳偏移合并
- worker/CLI 生命周期控制
- 异常与终止时显式资源释放

### 核心特性

- 长音频切片转录（`FUNASR_CHUNK_SECONDS`，默认 `60`）
- 支持常驻 worker（`--worker`）与单次 CLI 模式
- worker JSON 协议，便于外部集成
- 进程终止保护与内存回收
- 仅聚焦“本地转录运行时层”的独立包

### 安装

前置条件：

- Python `3.10+`
- 系统可用 `ffmpeg`、`ffprobe`

安装：

```bash
pip install .
```

开发安装：

```bash
pip install -e .[dev]
```

### CLI 使用

```bash
# 查看帮助
flas --help

# 文本输出
flas transcribe /path/to/audio.mp3

# JSON 输出
flas transcribe /path/to/audio.mp3 --format json --output transcript.json

# 常驻 worker
flas worker --worker-max-jobs 10 --worker-idle-timeout 180 --worker-max-seconds 1800
```

也支持直接透传 engine 参数：

```bash
flas /path/to/audio.mp3 --format text
```

### 推荐稳定基线

```bash
FUNASR_USE_WORKER=0
FUNASR_ENABLE_VAD=0
FUNASR_SENTENCE_TIMESTAMP=0
FUNASR_CHUNK_SECONDS=60
FUNASR_DEVICE=cpu
```

### 关键环境变量

- `FUNASR_CHUNK_SECONDS`（默认 `60`）
- `FUNASR_ENABLE_VAD`（`0|1`，默认 `0`）
- `FUNASR_SENTENCE_TIMESTAMP`（`0|1|auto`，默认 `0`）
- `FUNASR_DEVICE`（`cpu|mps|auto|cuda:0`，默认 `cpu`）
- `FUNASR_MODEL_PY_PATH`
- `FUNASR_MODEL_DIR`
- `FUNASR_WORKER_MAX_JOBS`
- `FUNASR_WORKER_IDLE_TIMEOUT`
- `FUNASR_WORKER_MAX_SECONDS`

### 项目边界

本仓库只负责“本地转录运行时能力”。

不包含：

- YouTube 下载
- LLM 摘要/提取
- Obsidian 同步

### 发布清单

请参考 [docs/release-checklist.md](./docs/release-checklist.md)。

### 致谢

该项目从更大的自动化工作流中抽取而来，抽取过程保持原仓库代码不改动。
