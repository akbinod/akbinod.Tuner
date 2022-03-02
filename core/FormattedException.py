import sys
import traceback
import json
import os

class FormattedException():
    def __init__(self) -> None:
        # format the error string and the call stack
        self.error = f"{sys.exc_info()[0]} - {sys.exc_info()[1]}"
        l = traceback.format_tb(sys.exc_info()[2])
        # we're always at the top, so get rid of that
        # TODO - revisit this
        l.pop(0)
        # I like to see the most recent call up at the top
        # - not scroll to the bottom for it
        l.reverse()

        # TODO - better representation
        # function tree, with line + file as values
        better_l = []
        for li in l:
            method = ""
            rest = ""
            line_no = ""
            file = ""
            pat = ""
            t = li.rpartition(", in ", )
            if not t is None:
                method = t[2]
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
                    t = (
                        file + "::" + method
                        , line_no + " in " + pat + file
                    )
                    better_l.append(t)
        self.stack = l
        self.stack = better_l

        return

    @property
    def json(self) -> dict:
        this = {}
        this["error"] = self.error
        this["stack"] = self.stack
        return this

    def __str__(self) -> str:

        return json.dumps(self.json)

