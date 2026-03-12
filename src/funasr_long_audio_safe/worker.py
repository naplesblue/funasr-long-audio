import json
import logging
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

AUDIO_MODEL_NAME = "FunAudioLLM/Fun-ASR-Nano-2512"
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")


def resolve_engine_script(script_path: str | None = None) -> Path:
    if script_path:
        return Path(script_path).expanduser().resolve()
    env_path = os.getenv("FUNASR_SCRIPT_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path(__file__).with_name("engine.py").resolve()


def terminate_subprocess(proc: subprocess.Popen | None, process_name: str, grace_seconds: int = 8) -> None:
    """Terminate subprocess and its process group to avoid memory leaks."""
    if not proc or proc.poll() is not None:
        return

    try:
        if os.name == "nt":
            proc.terminate()
        else:
            os.killpg(proc.pid, signal.SIGTERM)
        logging.warning("%s received SIGTERM, waiting graceful exit...", process_name)
    except Exception as exc:
        logging.warning("Failed to send terminate signal (%s): %s", process_name, exc)

    try:
        proc.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        if os.name == "nt":
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        logging.warning("%s did not exit within %ss, killed.", process_name, grace_seconds)
    except Exception as exc:
        logging.warning("Failed to force kill (%s): %s", process_name, exc)
    finally:
        try:
            proc.wait(timeout=3)
        except Exception:
            pass


def extract_audio(video_path: str, audio_dir: str) -> tuple[str | None, bool]:
    """
    Prepare mp3 input for ASR.

    Returns (audio_path, should_cleanup):
      - should_cleanup=True means generated temporary mp3 and should be deleted later.
      - should_cleanup=False means original file is reused.
    """
    logging.info("Preparing audio input: %s", video_path)
    video_path_obj = Path(video_path)
    audio_dir_obj = Path(audio_dir)
    if not video_path_obj.exists():
        logging.error("Input file not found: %s", video_path_obj)
        return None, False

    if video_path_obj.suffix.lower() == ".mp3":
        logging.info("Input already mp3, skip ffmpeg re-encode.")
        return str(video_path_obj.resolve()), False

    audio_dir_obj.mkdir(parents=True, exist_ok=True)
    audio_output_path = audio_dir_obj / f"{video_path_obj.stem}.mp3"
    command = [
        FFMPEG_PATH,
        "-i", str(video_path_obj),
        "-vn",
        "-codec:a", "libmp3lame",
        "-q:a", "2",
        "-y",
        str(audio_output_path),
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        if result.stderr:
            logging.debug("ffmpeg stderr:\n%s", result.stderr)
        return str(audio_output_path.resolve()), True
    except FileNotFoundError:
        logging.error("ffmpeg not found: %s", FFMPEG_PATH)
    except subprocess.TimeoutExpired:
        logging.error("ffmpeg timed out: %s", video_path_obj)
    except subprocess.CalledProcessError as exc:
        logging.error("ffmpeg failed (rc=%s): %s\n%s", exc.returncode, video_path_obj, exc.stderr)
    except Exception as exc:
        logging.error("Unexpected ffmpeg error: %s", exc)

    audio_output_path.unlink(missing_ok=True)
    return None, False


class FunASRWorkerClient:
    """Persistent worker client for engine.py --worker mode."""

    def __init__(
        self,
        script_path: str | None = None,
        startup_timeout: int = 900,
        request_timeout: int = 1800,
        worker_max_jobs: int = 6,
        worker_idle_timeout: int = 180,
        worker_max_seconds: int = 1800,
        worker_max_retries: int = 1,
        extra_hotwords: str = "",
        verbose: bool = False,
    ):
        self.script_path = str(resolve_engine_script(script_path))
        self.startup_timeout = startup_timeout
        self.request_timeout = request_timeout
        self.worker_max_jobs = max(0, worker_max_jobs)
        self.worker_idle_timeout = max(0, worker_idle_timeout)
        self.worker_max_seconds = max(0, worker_max_seconds)
        self.worker_max_retries = max(0, worker_max_retries)
        self.extra_hotwords = (extra_hotwords or "").strip()
        self.verbose = verbose
        self.proc: subprocess.Popen | None = None
        self.request_seq = 0

    @staticmethod
    def _compact_error_text(raw: object) -> str:
        text = str(raw or "").replace("\r", " ").replace("\n", " ").strip()
        return text[:220] + ("..." if len(text) > 220 else "")

    def _build_command(self) -> list[str]:
        cmd = [
            sys.executable,
            self.script_path,
            "--worker",
            "--format",
            "text",
            "--worker-parent-pid",
            str(os.getpid()),
            "--worker-max-jobs",
            str(self.worker_max_jobs),
            "--worker-idle-timeout",
            str(self.worker_idle_timeout),
            "--worker-max-seconds",
            str(self.worker_max_seconds),
        ]
        if self.extra_hotwords:
            cmd += ["--hotwords", self.extra_hotwords]
        if self.verbose:
            cmd.append("--verbose")
        return cmd

    def _is_running(self) -> bool:
        return bool(self.proc and self.proc.poll() is None)

    def _read_json_line(self, timeout_seconds: int) -> dict | None:
        if not self.proc or not self.proc.stdout:
            return None

        end_time = time.time() + timeout_seconds
        try:
            fd = self.proc.stdout.fileno()
        except Exception:
            return None

        while time.time() < end_time:
            remaining = max(0.0, end_time - time.time())
            try:
                readable, _, _ = select.select([fd], [], [], remaining)
            except Exception:
                return {"event": "eof"}
            if not readable:
                return None

            try:
                line = self.proc.stdout.readline()
            except Exception:
                return {"event": "eof"}
            if line == "":
                return {"event": "eof"}

            line = line.strip()
            if not line:
                continue

            try:
                return json.loads(line)
            except json.JSONDecodeError:
                start = line.find("{")
                end = line.rfind("}")
                if start != -1 and end > start:
                    maybe = line[start : end + 1]
                    try:
                        return json.loads(maybe)
                    except json.JSONDecodeError:
                        pass
                logging.debug("Ignore non-JSON worker output: %s", line[:200])
        return None

    def start(self) -> bool:
        if self._is_running():
            return True

        script_path_obj = Path(self.script_path)
        if not script_path_obj.exists():
            logging.error("engine.py not found: %s", script_path_obj)
            return False

        popen_kwargs = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": None,
            "text": True,
            "encoding": "utf-8",
            "bufsize": 1,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["preexec_fn"] = os.setsid

        try:
            self.proc = subprocess.Popen(self._build_command(), **popen_kwargs)
        except Exception as exc:
            logging.error("Failed to start worker: %s", exc)
            self.proc = None
            return False

        ready_msg = self._read_json_line(self.startup_timeout)
        if not ready_msg or ready_msg.get("event") != "ready":
            logging.error("Worker startup failed, ready message missing: %s", ready_msg)
            self.stop()
            return False

        logging.info("FunASR worker is ready.")
        return True

    def stop(self) -> None:
        if not self.proc:
            return

        try:
            if self.proc.poll() is None and self.proc.stdin:
                shutdown_req = {"id": "shutdown", "cmd": "shutdown"}
                self.proc.stdin.write(json.dumps(shutdown_req, ensure_ascii=False) + "\n")
                self.proc.stdin.flush()
                self._read_json_line(5)
        except Exception:
            pass
        finally:
            terminate_subprocess(self.proc, "funasr_worker")
            self.proc = None

    def transcribe(self, audio_path: str) -> str | None:
        audio_path_str = str(Path(audio_path).resolve())
        total_attempts = self.worker_max_retries + 1

        for attempt in range(1, total_attempts + 1):
            if not self.start():
                return None

            self.request_seq += 1
            request_id = f"req-{int(time.time() * 1000)}-{self.request_seq}"
            payload = {
                "id": request_id,
                "cmd": "transcribe",
                "audio_path": audio_path_str,
            }

            try:
                if not self.proc or not self.proc.stdin:
                    raise RuntimeError("worker stdin unavailable")
                self.proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
                self.proc.stdin.flush()
            except Exception as exc:
                logging.warning("Failed to send worker request (attempt=%s): %s", attempt, exc)
                self.stop()
                continue

            response = self._read_json_line(self.request_timeout)
            if not response:
                logging.warning("Worker response timed out (attempt=%s)", attempt)
                self.stop()
                continue
            if response.get("event") == "eof":
                logging.warning("Worker exited unexpectedly (attempt=%s)", attempt)
                self.stop()
                continue
            if response.get("event") == "bye":
                logging.info("Worker exited: %s", response.get("reason"))
                self.stop()
                continue
            if response.get("id") != request_id:
                logging.warning("Worker response id mismatch: %s", response)
                self.stop()
                continue
            if not response.get("ok"):
                logging.warning(
                    "Worker transcription failed (attempt=%s, type=%s): %s [%s]",
                    attempt,
                    self._compact_error_text(response.get("error_type")) or "unknown",
                    self._compact_error_text(response.get("error")),
                    self._compact_error_text(response.get("error_repr")),
                )
                self.stop()
                continue

            transcript = str(response.get("transcript") or "")
            if transcript.strip():
                return transcript
            logging.error("Worker returned empty transcript.")
            return None

        return None


def get_raw_transcript_with_timestamps(
    audio_path: str,
    *,
    script_path: str | None = None,
    worker_client: FunASRWorkerClient | None = None,
    allow_cli_fallback: bool = True,
) -> str | None:
    """
    Transcribe with timestamp text output.

    If worker_client is provided, try worker first, then optionally fallback to single-shot CLI.
    """
    logging.info("Transcribing with local %s: %s", AUDIO_MODEL_NAME, audio_path)
    audio_path_obj = Path(audio_path)

    if not audio_path_obj.exists():
        logging.error("Audio file not found: %s", audio_path_obj)
        return None
    if audio_path_obj.stat().st_size == 0:
        logging.error("Audio file is empty: %s", audio_path_obj)
        return None

    if worker_client is not None:
        transcript = worker_client.transcribe(str(audio_path_obj))
        if transcript and transcript.strip():
            logging.info("Worker transcription done, %s lines.", len(transcript.splitlines()))
            return transcript
        if not allow_cli_fallback:
            logging.error("Worker failed and CLI fallback is disabled.")
            return None
        logging.warning("Worker failed, fallback to single CLI call.")

    engine_script = resolve_engine_script(script_path)
    if not engine_script.exists():
        logging.error("engine script not found: %s", engine_script)
        return None

    command = [sys.executable, str(engine_script), str(audio_path_obj), "--format", "text"]

    extra_hotwords = os.getenv("FUNASR_HOTWORDS", "").strip()
    if extra_hotwords:
        command += ["--hotwords", extra_hotwords]

    if os.getenv("FUNASR_VERBOSE", "0").strip().lower() in {"1", "true", "yes", "on"}:
        command.append("--verbose")

    timeout_seconds = int(os.getenv("FUNASR_REQUEST_TIMEOUT", "1800") or "1800")
    proc = None
    try:
        popen_kwargs = {}
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["preexec_fn"] = os.setsid

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            **popen_kwargs,
        )
        stdout_data, stderr_data = proc.communicate(timeout=timeout_seconds)

        if proc.returncode != 0:
            logging.error("engine.py failed (rc=%s)", proc.returncode)
            logging.error("stderr:\n%s", (stderr_data or "")[-2000:])
            return None

        transcript = (stdout_data or "").strip()
        if not transcript:
            logging.error("Empty transcript returned from engine.py")
            return None

        logging.info("CLI transcription done, %s lines.", len(transcript.splitlines()))
        return transcript

    except subprocess.TimeoutExpired:
        logging.error("engine.py timed out (%ss)", timeout_seconds)
        terminate_subprocess(proc, "engine.py")
        return None
    except KeyboardInterrupt:
        logging.warning("Interrupted, terminating engine.py subprocess...")
        terminate_subprocess(proc, "engine.py")
        raise
    except Exception as exc:
        logging.error("CLI transcription error: %s", exc, exc_info=True)
        terminate_subprocess(proc, "engine.py")
        return None
