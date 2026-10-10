import sys
import threading
from types import ModuleType

import pytest

from analysis.trace_lifton_io import main, trace_io


def test_trace_logs_only_errno121(capsys):
    frame = sys._getframe()
    error = OSError(121, "synthetic remote I/O")
    trace_io(frame, "exception", (type(error), error, None))
    assert "DIAGNOSTIC_ERRNO121" in capsys.readouterr().err
    for error in (OSError(5, "synthetic other I/O"), ValueError("synthetic")):
        trace_io(frame, "exception", (type(error), error, None))
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("failure", [False, True])
def test_native_result_or_failure_propagates_and_traces_restore(monkeypatch, failure):
    module = ModuleType("lifton.lifton")
    expected = ValueError("native failure sentinel")

    def native_main(argv):
        assert argv == ["synthetic-argument"]
        assert sys.gettrace() is trace_io and threading.gettrace() is trace_io
        if failure:
            raise expected
        return 7

    module.main = native_main
    monkeypatch.setitem(sys.modules, "lifton", ModuleType("lifton"))
    monkeypatch.setitem(sys.modules, "lifton.lifton", module)
    prior, prior_thread = sys.gettrace(), threading.gettrace()
    if failure:
        with pytest.raises(ValueError) as caught:
            main(["synthetic-argument"])
        assert caught.value is expected
    else:
        assert main(["synthetic-argument"]) == 7
    assert sys.gettrace() is prior and threading.gettrace() is prior_thread
