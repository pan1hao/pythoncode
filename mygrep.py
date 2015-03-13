import  re
import os
import sys

class MyGrep(object):
    def __init__(self,mstr):
        self.mstr = mstr

    def findstr(self, filename):
        myre = re.compile(self.mstr)
        with open(filename, 'r') as f:
            fstr = f.read()
            if myre.search(fstr):
                print filename
        
    def gci(self, path):
        try:
            parents = os.listdir(path)
        except:
            return
        for parent in parents:
            child = os.path.join(path, parent)
            if os.path.isdir(child):
                self.gci(child)
            else:
                self.findstr(child)



if __name__ == "__main__":
    path = sys.argv[1]
    strgre = sys.argv[2]
    mgrp = MyGrep(strgre)
    mgrp.gci(path)
    
