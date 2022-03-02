from importlib.resources import path
import sys
import traceback
import json
import os
import copy
import tkinter as tk

from core.ExceptionWindow import ExceptionWindow

class FormattedException():
    def __init__(self, *, reverse_stack=True) -> None:

        self.error = ""
        self.start = {}
        self.end = {}
        self.stack = []

        # format the error string and the call stack
        self.error = f"{sys.exc_info()[0]} - {sys.exc_info()[1]}"
        l = traceback.format_tb(sys.exc_info()[2])

        # we're always at the top, so get rid of that
        # TODO - revisit this
        l.pop(0)

        if reverse_stack:
            # I like to see the most recent call up at the top
            # - not scroll to the bottom for it
            l.reverse()

        self.__plain_stack = l

        for li in l:
            method = ""
            rest = ""
            line_no = ""
            file = ""
            pat = ""
            t = li.rpartition(", in ", )
            if not t is None:
                method = t[2]
                a = method.split('\n')
                method = a[0]
                line = a[1]
                rest = t[0]
                t = rest.rpartition(", line ", )
                if not t is None:
                    line_no = t[2]
                    rest = t[0]
                    rest = rest.strip()
                    file = rest[6:]
                    file = file.rstrip('"')
                    t = os.path.split(file)
                    file = t[1]
                    pat = t[0]
                    this = {
                        "path": pat.strip()
                        ,"file": file.strip()
                        ,"line_num":line_no.strip()
                        ,"line": line.strip()
                        ,"method":method.strip().replace('\n', ' : ')
                    }
                    # mo betta repr
                    self.stack.append(this)

        f = (0, len(self.stack) - 1) if reverse_stack else (len(self.stack) - 1, 0)
        self.end = self.format(self.stack[f[0]])
        self.start = self.format(self.stack[f[1]])

        # test
        self.show()
        return
    def format(self, this):
        s = f'{this["file"]} :: {this["method"]} : {this["line"]}  [line:{this["line_num"]}]'
        return s
    @property
    def json(self) -> dict:
        ret = {}
        ret["error"] = self.error
        ret["in proc"] = self.end
        ret["first call"] = self.start

        l = []
        for item in self.stack:
            t = (
                item["file"] + "::" + item["method"]
                , item["line_num"] + " in " + item["path"] + item["file"]
            )
            l.append(t)
        ret["stack"] = l
        return ret

    @property
    def json_tree(self) -> dict:
        ret = {}
        ret["error"] = self.error
        ret["in proc"] = self.end
        ret["first call"] = self.start
        # st = ret["stack"] = {}
        last = None
        # put it into a tree form
        for this in self.stack:
            curr = copy.deepcopy(this)
            curr["item"] = None
            if last is not None:
                last["item"] = curr
            else:
                # only the first item in the
                # list goes on here, from then on
                # new stack frames get appended to
                # the previous
                ret["stack"] = curr
            last = curr

        return ret
    def __str__(self) -> str:

        return json.dumps(self.json)

    def show(self, *, title="Exception"):
        ex = ExceptionWindow("Testing")
        ex.exception = self
        ex.show()
        return