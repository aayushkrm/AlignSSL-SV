"""Log native errno 121 stack locations without suppressing native failures.

Diagnostic entry point for a tiny synthetic S0 run only. No monkey patches,
retry, data alteration, or conversion of partial results to successes.
"""
import sys
import threading
import traceback


def trace_io(frame, event, arg):
    filename = frame.f_code.co_filename
    if event == "exception":
        _, error, _ = arg
        if isinstance(error, OSError) and error.errno == 121:
            print(f"DIAGNOSTIC_ERRNO121 {filename}:{frame.f_lineno}: {error}", file=sys.stderr)
            traceback.print_stack(frame, file=sys.stderr)
    return trace_io if "/lifton/" in filename else None


def main(argv=None):
    from lifton.lifton import main as native_main

    prior = sys.gettrace()
    prior_thread = threading.gettrace()
    sys.settrace(trace_io)
    threading.settrace(trace_io)
    try:
        return native_main(sys.argv[1:] if argv is None else argv)
    finally:
        sys.settrace(prior)
        threading.settrace(prior_thread)


if __name__ == "__main__":
    raise SystemExit(main())
