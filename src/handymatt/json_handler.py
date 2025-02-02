# Changes
# 2024-06-18
# - tweaked appendValue()
# 
# TODO:
# - add removeKey() functionality
# - [REVISE] simplity method names
# - [REVISE] Extend dict functinality, handler[key] = value, del handler[key], key in handler, len(handler)
import json
import os
import shutil
from datetime import datetime

class JsonHandler:

    def __init__(self, filepath, readonly=False, prettify=False):
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
    
    def addItem(self, key, value, nosave=False):
        if self.hasKey(key):
            return False
        self.jsonObject[key] = value
        if not nosave:
            self.save()
        return True
    
    def setValue(self, key, value, nosave=False):
        self.jsonObject[key] = value
        if not nosave:
            self.save()
        return True
    
    def appendValue(self, key, value, nosave=False):
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
        return self.jsonObject.keys()
    
    def hasKey(self, key):
        return key in self.jsonObject
    
    def getValues(self):
        return list(self.jsonObject.values())

    def getValue(self, key, noValueRet=None):
        if key not in self.jsonObject:
            return noValueRet
        return self.jsonObject[key]

    def getItems(self):
        return list(self.jsonObject.items())
    
    def load(self):
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




if __name__ == "__main__":
    ...
