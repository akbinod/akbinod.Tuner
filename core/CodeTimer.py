import time

class CodeTimer:
    def __init__(self, name = None, precision=5) -> None:

        self.func_name = name if not name is None else ""
        self.precision = precision if not precision is None and precision > 0 else 5
        self.proc_time1 = None
        self.t1 = None

        self.elapsed_proc_time = None
        self.elapsed_time = None

        return
    def __enter__(self):

        self.t1 = time.time()
        self.proc_time1 = time.process_time()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.elapsed_proc_time  = time.process_time() - self.proc_time1
        self.elapsed_time = time.gmtime(time.time() - self.t1)

        return
    def __str__(self) -> str:
        outp = f"""{self.func_name} processed in {time.strftime('%H:%M:%S', self.elapsed_time )}, process_time: {round(self.elapsed_proc_time,self.precision)}"""
        # if self.elapsed_time.tm_sec <= 1 or self.elapsed_proc_time < 1:
        #     #if the number of seconds resolves to 1 or 0, twekas will
        #     #result in changes noticable only in process_time deltas
        #     #also, stop obsessing past the 5th decimal place
        #     outp += f"""\t[sub second process_time: {round(self.elapsed_proc_time,self.precision)}]"""

        return outp
