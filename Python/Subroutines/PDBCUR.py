

def genPDBCURinputs(PDBCURinputFile, asymmetricUnit):
    print 'Creating input file for PDBCUR at %s' % PDBCURinputFile
    # write input keywords to file for use with PDBCUR
    with open(PDBCURinputFile, 'w') as f:
        # delhydrogen keyword removes all hydrogen atoms from PDB
        f.write('delhydrogen\n')
        # cutocc keyword removes all atoms with occupancy of 0 from PDB
        f.write('cutocc\n')
        # mostprob keyword only keeps atoms from conformations with the highest occupancy
        # if equal occupancies then only one is retained (A)
        f.write('mostprob\n')
        # noanisou keyword removes all ANISOU information from PDB
        f.write('noanisou\n')

        if asymmetricUnit is False:
            # genunit keyword generates a unit cell
            f.write('genunit\n')
            f.close

        elif asymmetricUnit is True:
            f.close
# end genPDBCURinputs


def runPDBCUR(pathToPDB, PDBCURoutputPDB, PDBCURinputFile, PDBCURlog):
    import os
    # create a string for command line input to run PDBCUR
    runPDBCURcommand = 'pdbcur xyzin %s xyzout %s < %s > %s' % (pathToPDB, PDBCURoutputPDB, PDBCURinputFile, PDBCURlog)
    # run PDBCUR to specifications
    print 'Running PDBCUR (Winn et al. 2011) to process the PDB file'
    os.system(runPDBCURcommand)
    # inform user of generated PDBCUR output file
    print 'PDBCUR log is printed below\n'
    # print PDBCUR output to log file
    PDBCURlogText = open(PDBCURlog,'r')
    for line in PDBCURlogText:
        print line
    PDBCURlogText.close()
    # delete separate PDBCUR log file and input file
    os.remove(PDBCURlog)
    os.remove(PDBCURinputFile)
# end runPDBCUR
