import logging
from timeit_decorator import timeit

old_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    # record.test_field = ""
    if hasattr(record, "msg"):
        if ": Exec:" in record.msg:
            name_el = record.msg.split(" ")
            # record.test_field = "has exec"
            record.msg = name_el[1] if len(name_el) > 1 else record.msg
            record.exec_time = float(name_el[-1][:-1])
        else:
            # record.test_field = "no exec"
            record.exec_time = 0.0
        # record.custom_attribute = 0xdecafbad
    else:
        # record.test_field = f"no message {str(record.__dict__.keys())}"
        record.exec_time = 0.0
    return record


logging.setLogRecordFactory(record_factory)

# Configure logging
# (filename="basic.log",encoding="utf-8",level=logging.INFO,
# filemode = "w", format="%(process)d-%(levelname)s-%(message)s"
logging.basicConfig(
    # filename="setup.csv",
    # filemode="w",
    level=logging.INFO,
    format="%(asctime)s;%(message)s;%(exec_time).10f"
    # format="%(asctime)s;%(message)s;%(exec_time).10f"
)
