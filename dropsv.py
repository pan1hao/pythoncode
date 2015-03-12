import re
import os
import sys

def subfile(filename):
    print 'open file %s' % filename
    fp = open(filename, 'r')
    str = fp.read()
    newstr = re.sub('<SCRIPT Language=VBScript>(.|\n)*</SCRIPT>', '',str)
    fp.close()
    if newstr == str:
        return
    print 'wirte file %s' % filename
    f = open(filename, 'w')
    f.write(newstr)
    f.close()
  
def endWith(s,*endstring):
    array = map(s.endswith,endstring)
    if True in array:
        return True
    else:
        return False
  
def gci(path, filelist):
    try:
        parents = os.listdir(path)
    except:
        return
    for parent in parents:
        child = os.path.join(path, parent)
        if os.path.isdir(child):
            gci(child, filelist)
        else:
            if endWith(child,'.html'):
                print child
                filelist.append(child)

def gci2(path):
    try:
        parents = os.listdir(path)
    except:
        return
    for parent in parents:
        child = os.path.join(path, parent)
        if os.path.isdir(child):
            gci2(child)
        else:
            if endWith(child, '.html', '.htm'):
                print child
                subfile(child)
                
def delsvoexe(path):
    filelist = []
    gci(path, filelist)
    for i in filelist:
        subfile(i)

if __name__ == "__main__":
    print sys.argv[1]
    path = sys.argv[1]
    #delsvoexe(path)
    gci2(path)
