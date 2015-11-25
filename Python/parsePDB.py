# Copyright Thomas Dixon 2015
# With thanks to Charles Bury
import os
class atom(object):
    #Initialise class for a PDB file
    def __init__(self,atomnum=0,residuenum=0,atomtype="",resitype="",
                 chainID="",xyz_coords=[],atomidentifier="",bfactor=0,occupancy=1):   
        self.atomNum    = atomnum
        self.resiNum    = residuenum
        self.atomType   = atomtype
        self.resiType   = resitype 
        self.chainID    = chainID
        self.xyzCoords  = xyz_coords
        self.atomID     = atomidentifier
        self.bfactor    = bfactor
        self.occupancy  = occupancy
    #print a summary of atom info to command line 
    def getAtomSummary(self):
        summaryString = 'Chain: {}\nResidue: {}{}\nAtom type: {}'.format(self.chainID,self.resiType,self.resiNum,self.atomType)
        print summaryString
#parse pdb file with name 'fileName' and return list of atoms from 'atom' class above
def parsePDB(fileName):
    #check that file exists
    if not os.path.exists(fileName):
        print 'Error!!\nFile name {} not found'.format(fileName)
        return
    #creat puppet list to fill with atom objects
    atomList = [] 
    #open correct file name for reading
    fileOpen = open(fileName,'r') 
    #read 'ATOM' and 'HETATM' lines
    for line in fileOpen.readlines():
        #only select information from ATOM or HETATM lines
        if ('ATOM' in str(line[0:6])) or ('HETATM' in str(line[0:6])):
            y = atom() #make new 'atom' object here
            #get atom properties here
            y.atomNum   = int(line[6:11].strip())
            y.atomType  = str(line[12:16].strip())
            y.resiType  = str(line[17:20].strip())                       
            y.chainID   = str(line[21])                     
            y.resiNum   = int(line[22:26].strip())  
            y.xyzCoords = [float(line[30:38].strip()),
                           float(line[38:46].strip()),
                           float(line[46:54].strip())]    
            y.occupancy = str(line[54:60].strip())                                                    
            y.bfactor   = str(line[60:66].strip())
            y.atomID    = str(line[76:78].strip())  
            #append new 'atom' object to list
            atomList.append(y)
        else: 
            continue 
    fileOpen.close() #close .pdb file after reading
    #provide feedback to user
    print 'Finished reading in atoms --> {} atoms found in file'.format(len(atomList))
    #return list of atoms as output of function
    return atomList
#end