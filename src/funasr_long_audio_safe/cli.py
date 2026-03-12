import sys

from . import engine


def _help_text() -> str:
    return (
        "FunASR Long Audio Safe CLI\n\n"
        "Usage:\n"
        "  flas transcribe <audio> [engine options...]\n"
        "  flas worker [engine options...]\n"
        "\n"
        "Examples:\n"
        "  flas transcribe ./demo.mp3 --format text\n"
        "  flas transcribe ./demo.mp3 --format json --output out.json\n"
        "  flas worker --worker-max-jobs 10 --worker-idle-timeout 120\n"
        "\n"
        "You can also pass engine arguments directly without subcommand:\n"
        "  flas ./demo.mp3 --format text\n"
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in {"-h", "--help", "help"}:
        print(_help_text())
        return 0

    if args[0] == "transcribe":
        engine_args = args[1:]
    elif args[0] == "worker":
        engine_args = ["--worker", *args[1:]]
    else:
        engine_args = args

    prev_argv = sys.argv
    try:
        sys.argv = [prev_argv[0], *engine_args]
        engine.main()
        return 0
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
    finally:
        sys.argv = prev_argv


if __name__ == "__main__":
    raise SystemExit(main())
