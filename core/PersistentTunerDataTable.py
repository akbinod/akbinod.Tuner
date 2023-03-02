# from ThetaUI import ThetaUI

import json
import hashlib as hl

class PersistentTunerDataTable:
    '''
    Manages the display of tabular data output by the tuned function.
    '''
    def __init__(self) -> None:
        self.tables = {}
        # holds objects that look like this and is keyed by the keyhash of the first item in the list of data
        # {
        #     "title":"data"
        #     , "data":[]
        # }

        return
    def keyhash(self, data:list):
        ret = None
        keys = []
        if len(data) >0:
            rep:dict = data[0]
            keys = rep.keys()
            ret = (hl.md5((str(keys)).encode('utf-8'))).hexdigest()

        return ret, keys

    def append(self, val):

        new_keyhash = None
        new_data:list = None
        old_data:list = None
        keys = []
        title = val["title"] if "title" in val else "whatever"
        if "data" in val: new_data = val["data"]
        if new_data is None:
            # hasnt provided data at all
            return
        new_keyhash, keys  = self.keyhash(new_data)
        if new_keyhash is None:
            # no row in data to append/create a new table
            return
        tablekey = title + "_" + new_keyhash

        if tablekey in self.tables:
            entry = self.tables[tablekey]
            old_data = entry["data"]
        if not old_data is None:
            # at this point old and new keyhashes match, and the title is the same
            # append to the old data list from the new data list
            old_data.extend (new_data)
            entry["dirty"] = True
        else:
            # need a new entry
            self.tables[tablekey] = {
                "title":title
                , "dirty":True
                , "cols":keys
                , "data":new_data
            }


        return
    def render(self):
        # bp - temp - just write out the output to the terminal for now until we figure out how to do the grid
        # these are already unique tables - just go ahead and render each
        for tablekey in self.tables:
            table = self.tables[tablekey]

            # ignore title for now
            # write out the header row - basically the keys
            item = "\t".join(table["cols"])
            print(item)


            # write out each col of each row
            for row in table["data"]:
                # gather field values into a list
                l = [str(row[col]) for col in table["cols"]]
                # join them with a tab and print
                print("\t".join(l))
        return
