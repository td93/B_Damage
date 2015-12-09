# Copyright Thomas Dixon 2015

#calculate the distance between two atoms
def calcDist(atomA, atomB):
    from parsePDB import atom as a #for utilising the 'atom' class
    import math #for obtaining the square root
    #obtain two sets of atom coordinates for the atoms
    Acoords = atomA.xyzCoords
    Bcoords = atomB.xyzCoords
    #find the linear displaements of the atoms from each other along the three Cartesian axes
    x = Acoords[0][0] - Bcoords[0][0]
    y = Acoords[1][0] - Bcoords[1][0]
    z = Acoords[2][0] - Bcoords[2][0]
    #find the distance between the two atoms 
    d = math.sqrt(x**2 + y**2 + z**2)
    return d
#end calcDist


def countInRadius(atm, atomList, r):
    from parsePDB import atom as a #for utilising the 'atom' class
    from Bdamage import calcDist #calcualtes the distance between two atoms in 3D space
    #set packing density counter to 0
    PD = 0
    #for every retained atom
    for atm in atomList:
        #calcualte the distance between the two atoms
        if calcDist(atm, atm) < r:
            #if the distance is less than the PDT, increment the counter
            PD = PD + 1
    #return packing density of the atom once all comparisons have been made
    atm.PD = PD
    return atm.PD
        
#Calculate packing density for all atoms in the original PDB file
def calcPDT(auAtomList, atomList, PDT):
    from parsePDB import atom as a #for utilising the 'atom' class
    from Bdamage import countInRadius #counts atoms within PDT
    #set initial values for min/maxPD
    firstPD = countInRadius(auAtomList[0], atomList, PDT)
    minPD = firstPD
    maxPD = firstPD
    #for every atom in the asymmetric unit
    for atm in xrange (1,len(auAtomList)):
        auAtm = auAtomList[atm]
        auAtm.PD = countInRadius(auAtm, atomList, PDT)
        #update min/maxPD if necessary
        if auAtm.PD < minPD:
            minPD = auAtm.PD
        elif auAtm.PD > maxPD:
            maxPD = auAtm.PD
    return auAtomList, minPD, maxPD
#end calcPackingDensity
    
#Segregate atoms into bins based on PD
def binAtoms(atomList, binSize):
    from parsePDB import atom as a #for utilising the 'atom' class
    
#end binAtoms