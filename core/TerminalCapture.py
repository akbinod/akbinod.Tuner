import tempfile
import sys


class TerminalCapture:
    def __init__(self, *, capture:bool=True, name:str = 'capture',dir:str="", append_to_file:str = None) -> None:
        '''
        Captures the output to terminal.
        params:
        capture: Seems silly to have a capture param - but makes for cleaner code on the calling side.
        name: whatever you want to name this - part of the file name
        dir: if you have a dir you want to place this in
        append_to: if you have a file to append this output to
        '''
        self.func_name = name if not name is None else ""

        self.stdout = None
        self.stderr = None
        self.capture = capture
        self.captureFIle = None

        self.__fileName = append_to_file
        if self.__fileName is None and self.capture:
            _, self.__fileName = tempfile.mkstemp(prefix= self.func_name
                                , suffix=".txt"
                                , dir=dir
                                , text=True)
        return

    def __enter__(self):
        if self.capture:
            self.stdout = sys.stdout
            self.stderr = sys.stderr

            self.captureFIle = open(self.__fileName, 'w+')

            # redirect output to the file
            sys.stdout = self.captureFIle
            sys.stderr = self.captureFIle

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if not self.stdout is None:
            # return stdout to whatever it was
            sys.stdout = self.stdout
            sys.stderr = self.stderr

        if not self.captureFIle is None:
            # write it out
            self.captureFIle.flush()
            self.captureFIle.close()

        return

    @property
    def file_name(self):
        return self.__fileName

    @property
    def output(self):
        ret = None
        if not self.capture: return

        with open(self.file_name) as f:
            ret = f.read()
        return ret


    def __str__(self) -> str:

        return self.output
