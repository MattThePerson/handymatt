# Ideas for v2:
# - add temp .~lock file when open (thing about this carefully, eg what happens when program crashes, how to use class instance id or something)
# - handler can be treated like a dict (handler[key] = value etc)
#   * handler[key] = value
#   * del handler[key]
#   * key in handler
#   * len(handler)
# - simplify methods    .getValue() -> .get()
# - add removeKey() (AND del handler[key])
# - add iteration of items without needing .items()
from typing import Any
import json
import os
import shutil
from datetime import datetime

class JsonHandler:
    """ A class for abtrsacting the reading and writing process of json files/data """
    
    def __init__(self, filepath: str, readonly:bool=False, prettify:bool=False):
        self.readonly = readonly
        self.prettify = prettify
        self.curdir = os.path.abspath(os.curdir)
        if ":" in filepath:
            self.filepath = filepath
        else:
            self.filepath = os.path.join(self.curdir, filepath)
        filedir = os.path.dirname(self.filepath)
        self.backupdir = os.path.join(filedir, "BAK")
        self.jsonObject = self.load()
    
    def addItem(self, key: Any, value: Any, nosave:bool=False):
        if self.hasKey(key):
            return False
        self.jsonObject[key] = value
        if not nosave:
            self.save()
        return True
    
    def setValue(self, key: Any, value: Any, nosave:bool=False):
        self.jsonObject[key] = value
        if not nosave:
            self.save()
        return True
    
    def appendValue(self, key: Any, value: Any, nosave:bool=False):
        if key in self.jsonObject:
            if not isinstance(self.jsonObject[key], list):
                return False
        else:
            self.jsonObject[key] = []
        self.jsonObject[key].append(value)
        if not nosave:
            self.save()
        return True

    def getKeys(self):
        return list(self.jsonObject.keys())
    
    def hasKey(self, key: Any):
        return key in self.jsonObject
    
    def getValues(self):
        return list(self.jsonObject.values())

    def getValue(self, key: Any, noValueRet:Any=None):
        if key not in self.jsonObject:
            return noValueRet
        return self.jsonObject[key]

    def getItems(self) -> list[tuple[Any, Any]]:
        return list(self.jsonObject.items())
    
    def load(self) -> dict[Any, Any]:
        #print("Loading json ...")
        try:
            with open(self.filepath, 'r') as openfile:
                jsonObject = json.load(openfile)
            return jsonObject
        except:
            return {}
        
    def save(self):
        if self.readonly:
            print("WARNING: Unable to save, handler in READONLY mode")
            return
        temppath = self.filepath + '.tmp'
        with open(temppath, "w") as outfile:
            if self.prettify:
                outfile.write(json.dumps(self.jsonObject, indent=4))
            else:
                outfile.write(json.dumps(self.jsonObject))
        os.replace(temppath, self.filepath)
        
    def backup(self):
        if not os.path.exists(self.backupdir):
            os.mkdir(self.backupdir)
            print("Made dir")
        savename = os.path.basename(self.filepath) + "_BAK_" + str(datetime.now().strftime("%y-%m-%d_%H-%M-%S")) + ".json"
        savepath = os.path.join(self.backupdir, savename)
        print("Saving backup to: ", savepath)
        shutil.copyfile(self.filepath, savepath)

