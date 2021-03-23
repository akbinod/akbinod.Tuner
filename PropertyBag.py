import json

class PropertyBag(dict):
    '''
    Provides a js style object on which you can randomly create properties. Caveat emptor.
    Derives from dict, so you can use those members as well.
    '''
    def __init__(self) -> None:
        super().__init__()
        # self.props = {}
        pass
    def __delattr__(self, name: str) -> None:
        if name in self: del(self[name])

    def __getattr__(self, name: str):
        if name in self:
            return self[name]
        else:
            return super().__getattr__(name)
        return ret

    def __setattr__(self, name: str, value) -> None:

        self[name] = value

        return

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        # return a json repr of this dict
        #
        return(json.dumps(self))

    def update(self, val):
        return super().update(val)




