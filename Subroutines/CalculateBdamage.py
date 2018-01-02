
# RABDAM
# Copyright (C) 2017 Garman Group, University of Oxford

# This file is part of RABDAM.

# RABDAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.

# RABDAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General
# Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.


class rabdam(object):
    def __init__(self, pathToInput, outputDir, batchRun, overwrite, PDT,
                 windowSize, protOrNA, HETATM, addAtoms, removeAtoms,
                 highlightAtoms, createOrigpdb, createAUpdb, createUCpdb,
                 createAUCpdb, createTApdb):
        self.pathToInput = pathToInput
        self.outputDir = outputDir
        self.batchRun = batchRun
        self.overwrite = overwrite
        self.PDT = PDT
        self.windowSize = windowSize
        self.protOrNA = protOrNA
        self.HETATM = HETATM
        self.addAtoms = addAtoms
        self.removeAtoms = removeAtoms
        self.highlightAtoms = highlightAtoms
        self.createOrigpdb = createOrigpdb
        self.createAUpdb = createAUpdb
        self.createUCpdb = createUCpdb
        self.createAUCpdb = createAUCpdb
        self.createTApdb = createTApdb

    def rabdam_dataframe(self, run):
        # Calculates BDamage for selected atoms within input PDB file and
        # writes output to DataFrame.

        prompt = '> '
        import sys
        import os
        import shutil
        import requests
        import copy
        duplicate = copy.copy
        import pickle

        from PDBCUR import (convert_cif_to_pdb, clean_pdb_file,
                            genPDBCURinputs, runPDBCUR)
        from parsePDB import (full_atom_list, b_damage_atom_list,
                              download_pdb_and_mmcif, copy_input)
        from translateUnitCell import convertToCartesian, translateUnitCell
        from trimUnitCellAssembly import getAUparams, convertParams, trimAtoms
        from makeDataFrame import makePDB, writeDataFrame
        from Bdamage import (calcBdam, get_xyz_from_objects,
                             calc_packing_density, write_pckg_dens_to_atoms)

        if run == 'rabdam':
            print '**************************** RABDAM ****************************\n'
        elif run == 'rabdam_dataframe':
            print '*********************** RABDAM DATAFRAME ***********************\n'

        print('\n****************************************************************\n'
              '***************** Program to calculate BDamage *****************\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '************************* Input Section ************************\n')
        # Prints the values of the program options to be used in the current
        # RABDAM run
        print 'Calculating BDamage for %s' % self.pathToInput
        print 'Writing output files to %s' % self.outputDir
        if self.PDT == 7:
            print 'Using default packing density threshold of 7 Angstroms'
        else:
            print 'Packing density threshold defined by user as %s Angstroms' % self.PDT
        if self.windowSize == 0.02:
            print 'Using default window size of 2%'
        else:
            print 'Window size defined by user as %s%%' % (self.windowSize*100)
        if self.HETATM is True:
            print 'Keeping HETATM'
        elif self.HETATM is False:
            print 'Removing HETATM'
        if self.protOrNA == 'protein':
            print 'Retaining protein atoms, discarding nucleic acid atoms'
        elif self.protOrNA in ['nucleicacid', 'na']:
            print 'Retaining nucleic acid atoms, discarding protein atoms'
        if len(self.addAtoms) == 0:
            print 'No atoms to be added'
        else:
            add_atoms_string = ''
            for value in self.addAtoms:
                value = value + ', '
                add_atoms_string = add_atoms_string + value
            add_atoms_string = add_atoms_string.strip(', ')
            print 'Atoms to be added: %s' % add_atoms_string
        if len(self.removeAtoms) == 0:
            print 'No atoms to be removed'
        else:
            remove_atoms_string = ''
            for value in self.removeAtoms:
                value = value + ', '
                remove_atoms_string = remove_atoms_string + value
            remove_atoms_string = remove_atoms_string.strip(', ')
            print 'Atoms to be removed: %s' % remove_atoms_string

        print('\n********************* End of Input Section *********************\n'
              '****************************************************************\n')

        # Changes directory to the specified location for the output 'Logfiles'
        # directory. The default location is the current working directory
        # (i.e. that in which the rabdam.py script is saved).
        cwd = os.getcwd()
        os.chdir('%s' % self.outputDir)

        print('****************************************************************\n'
              '********************** Process PDB Section *********************\n')
        # Creates a new directory named after the input PDB file (after
        # checking that this directory does not already exist) in the
        # 'Logfiles' directory. Then saves a copy of the input PDB file to the
        # new directory.

        # If 4 digit PDB accession code has been supplied:
        if len(self.pathToInput) == 4:
            print 'Accession code supplied\n'
            PDBcode = self.pathToInput.upper()
            window_name = 100*self.windowSize
            window_name = str(window_name).replace('.', '_')
            pdt_name = str(self.PDT).replace('.', '_')
            PDBdirectory = 'Logfiles/%s_window_%s_pdt_%s/' % (PDBcode, window_name, pdt_name)
            pdb_file_path = '%s%s' % (PDBdirectory, PDBcode)
            pathToInput = '%s%s.pdb' % (PDBdirectory, PDBcode)
            pathToCif = '%s%s.cif' % (PDBdirectory, PDBcode)

            # Checks whether accession code exists - if not, exit program
            # with error message
            urls = ['http://www.rcsb.org/pdb/files/%s.pdb' % PDBcode,
                    'http://www.rcsb.org/pdb/files/%s.cif' % PDBcode]
            for url in urls:
                header = requests.get(url)
                if header.status_code >= 300:
                    if self.batchRun is False:
                        sys.exit('ERROR: Failed to download %s file with '
                                 'accession code %s:\n'
                                 'check that a structure with this accession code '
                                 'exists.' % (url[-4:], PDBcode))
                    elif self.batchRun is True:
                        return

            # If directory with same name as PDBdirectory already exists in
            # 'Logfiles' directory, user input is requested ('Do you want to
            # overwrite the existing folder?'):
            # yes = old PDBdirectory is deleted, new PDBdirectory is created
            #       and copy of the PDB file is downloaded from the RSCB PDB
            #       website and saved to the new directory
            # no = old PDBdirectory is retained, exit program
            # If it doesn't already exist, new PDBdirectory is created and
            # copy of the PDB file is downloaded from the RSCB PDB website and
            # saved to the new directory.
            if os.path.isdir(PDBdirectory):
                print 'Folder %s already exists locally at %s' % (PDBcode,
                                                                  PDBdirectory)
                print('Do you want to overwrite the existing folder?\n'
                      '--USER INPUT-- type your choice and press RETURN\n'
                      'yes = overwrite this folder\n'
                      'no = do not overwrite this folder\n')
                owChoice = None
                while owChoice not in ['yes', 'no', 'y', 'n']:
                    if self.overwrite is True:
                        owChoice = 'yes'
                    elif self.overwrite is False:
                        owChoice = raw_input(prompt).lower()

                    if owChoice == 'yes' or owChoice == 'y':
                        print '\nOverwriting existing folder'
                        shutil.rmtree(PDBdirectory)
                        download_pdb_and_mmcif(PDBcode, PDBdirectory,
                                               pathToInput, pathToCif)
                        break
                    elif owChoice == 'no' or owChoice == 'n':
                        if self.batchRun is False:
                            sys.exit('\nKeeping original folder\n'
                                     'Exiting RABDAM')
                        elif self.batchRun is True:
                            return
                        break
                    else:
                        print 'Unrecognised input - please answer "yes" or "no"'
            else:
                download_pdb_and_mmcif(PDBcode, PDBdirectory, pathToInput,
                                       pathToCif)

            # Checks that PDB file has been successfully downloaded and saved to
            # the 'Logfiles' directory
            if not os.path.exists(pathToInput):
                shutil.rmtree('%s' % PDBdirectory)
                if self.batchRun is False:
                    sys.exit('ERROR: Failed to download and save PDB file - cause unknown')
                elif self.batchRun is True:
                    return

        # If filepath to PDB has been supplied:
        else:
            # Changes directory to allow input PDB file (a '.pdb' or '.txt'
            # file) to be read from any provided file path. If directory with
            # same name as PDBdirectory already exists in 'Logfiles' directory,
            # user input is requested ('Do you want to overwrite the existing
            # folder?'):
            # yes = old PDBdirectory is deleted, new PDBdirectory is created
            #       and copy of input PDB file is saved to the new directory
            # no = old PDBdirectory is retained, exit program
            # If it doesn't already exist, new PDBdirectory is created and copy
            # of input PDB file is saved to the new directory.
            owd = os.getcwd()
            pathToInput = self.pathToInput.replace('\\', '/')
            splitPath = pathToInput.split('/')
            disk = '%s/' % splitPath[0]
            os.chdir('/')
            os.chdir(disk)
            if not os.path.exists(pathToInput):
                if self.batchRun is False:
                    sys.exit('ERROR: Supplied filepath not recognised')
                elif self.batchRun is True:
                    return
            os.chdir(owd)

            if pathToInput[-4:] not in ['.pdb', '.cif']:
                if self.batchRun is False:
                    sys.exit('ERROR: Supplied input filepath is not a .pdb or '
                             '.cif file')
                elif self.batchRun is True:
                    return
            else:
                print('Filepath to %s file supplied\n' % pathToInput[-4])
                fileName = splitPath[len(splitPath)-1]
                splitFilename = fileName.split('.')
                PDBcode = splitFilename[-2].upper()
                fileName = PDBcode + '.' + splitFilename[len(splitFilename)-1]
                window_name = 100*self.windowSize
                window_name = str(window_name).replace('.', '_')
                pdt_name = str(self.PDT).replace('.', '_')
                PDBdirectory = 'Logfiles/%s_window_%s_pdt_%s/' % (PDBcode, window_name, pdt_name)
                pdb_file_path = '%s%s' % (PDBdirectory, PDBcode)
                newpathToInput = '%s%s' % (PDBdirectory, fileName)
                pathToCif = ''

                if os.path.isdir(PDBdirectory):
                    print 'Folder %s already exists locally at %s' % (
                        PDBcode, PDBdirectory)
                    print('Do you want to overwrite the existing folder?\n'
                          '--USER INPUT-- type your choice and press RETURN\n'
                          'yes = overwrite this folder\n'
                          'no = do not overwrite this folder\n')
                    owChoice = None
                    while owChoice not in ['yes', 'no', 'y', 'n']:
                        if self.overwrite is True:
                            owChoice = 'yes'
                        elif self.overwrite is False:
                            owChoice = raw_input(prompt).lower()

                        if owChoice == 'yes' or owChoice == 'y':
                            print '\nOverwriting existing folder'
                            shutil.rmtree(PDBdirectory)
                            copy_input(pathToInput, disk, newpathToInput, PDBdirectory)
                            break
                        elif owChoice == 'no' or owChoice == 'n':
                            if self.batchRun is False:
                                sys.exit('\nKeeping original folder\n'
                                         'Exiting RABDAM')
                            elif self.batchRun is True:
                                return
                            break
                        else:
                            print 'Unrecognised input - please answer "yes" or "no"'
                else:
                    copy_input(pathToInput, disk, newpathToInput, PDBdirectory)

                # Checks that PDB file has been successfully copied to the
                # 'Logfiles' directory
                if not os.path.exists(newpathToInput):
                    shutil.rmtree('%s' % PDBdirectory)
                    if self.batchRun is False:
                        sys.exit('ERROR: Failed to copy input cif / PDB file '
                                 'to the Logfiles directory.\n'
                                 'Check that supplied PDB file is not in use '
                                 'by another program')
                    elif self.batchRun is True:
                        return

                pathToInput = newpathToInput

        print('\nAll files generated by this program will be stored in:\n'
              '    %s\n' % PDBdirectory)

        # Processes the input PDB file to remove hydrogen atoms, anisotropic
        # B factor records, and atoms with zero occupancy, as well as
        # retaining only the most probable alternate conformations. The unit
        # cell assembly is then generated from the coordinates of the processed
        # PDB file and its associated symmetry operations. Note that unit cell
        # generation is currently performed by the PDBCUR program from the CCP4
        # software suite.
        print('\nProcessing input file to remove hydrogen atoms, anisotropic '
              '\nB factor records, and atoms with zero occupancy, as well as '
              '\nretaining only the most probable alternate conformations')

        if self.pathToInput[-4:] == '.cif':
            (pathToInput, cif_lines, cif_header_lines, cif_footer_lines,
             cif_column_labels) = convert_cif_to_pdb(pathToInput, True)
        elif len(self.pathToInput) == 4:
            (pathToCif, cif_lines, cif_header_lines, cif_footer_lines,
             cif_column_labels) = convert_cif_to_pdb(pathToCif, False)
        else:
            cif_lines = ''
            cif_header_lines = ''
            cif_footer_lines = ''
            cif_column_labels = ''

        (multi_model, clean_au_file, clean_au_list, header_lines, footer_lines,
         unit_cell_params) = clean_pdb_file(pathToInput, PDBdirectory,
                                            self.batchRun, pdb_file_path)
        if multi_model is True:
            shutil.rmtree('%s' % PDBdirectory)
            return

        # Deletes input file fed into the program unless createOrigpdb
        # is set equal to True in the input file (default=False).
        if not self.createOrigpdb:
            os.remove(pathToInput)
            if pathToCif != '':
                os.remove(pathToCif)

        print '\nGenerating unit cell\n'
        PDBCURinputFile = '%sPDBCURinput.txt' % pdb_file_path
        PDBCURlog = '%sPDBCURlog.txt' % pdb_file_path
        genPDBCURinputs(PDBCURinputFile)
        unit_cell_pdb = '%s_unit_cell.pdb' % pdb_file_path
        runPDBCUR(clean_au_file, unit_cell_pdb, PDBCURinputFile, PDBCURlog)

        if not os.path.exists(unit_cell_pdb):
            shutil.rmtree('%s' % PDBdirectory)
            if self.batchRun is False:
                sys.exit('ERROR: Error in running PDBCUR, failed to generate Unit'
                         'Cell PDB file')
            elif self.batchRun is True:
                return

        print('****************** End of Process PDB Section ******************\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '********************** Parsing PDB Section *********************\n')
        # Parses the newly generated unit cell PDB file into RABDAM, returning
        # a list of all atoms in the unit cell, plus the unit cell parameters.
        # The unit cell PDB file is then deleted unless createUCpdb is set
        # equal to True in the input file (default = False).
        print 'Reading in unit cell coordinates'
        ucAtomList = full_atom_list(unit_cell_pdb)

        # Halts program if no atoms selected for BDamage analysis
        if len(ucAtomList) < 1:
            shutil.rmtree('%s' % PDBdirectory)
            if self.batchRun is False:
                sys.exit('ERROR: No atoms selected for BDamage calculation')
            elif self.batchRun is True:
                return

        if self.createUCpdb is False:
            os.remove(unit_cell_pdb)

        print('\n****************** End of Parsing PDB Section ******************\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '****************** Translate Unit Cell Section *****************\n')
        # The unit cell parameters are converted into Cartesian vectors. These
        # vectors are then used to translate the unit cell -/+ 1 units in all
        # (3 - a, b and c) dimensions to generate a 3x3 parallelepiped. A PDB
        # file of this 3x3 parallelepiped is output if createAUCpdb is set
        # equal to True in the input file (default = False).

        transAtomList = duplicate(ucAtomList)
        cartesianVectors = convertToCartesian(unit_cell_params)
        for a in xrange(-1, 2):
            for b in xrange(-1, 2):
                for c in xrange(-1, 2):
                    if a == 0 and b == 0 and c == 0:
                        pass  # No identity translation
                    else:
                        transAtomList = translateUnitCell(ucAtomList,
                                                          transAtomList,
                                                          cartesianVectors,
                                                          a, b, c)

        if self.createAUCpdb is True:
            aucPDBfilepath = '%s_all_unit_cells.pdb' % pdb_file_path
            makePDB(header_lines, transAtomList, footer_lines, aucPDBfilepath,
                    'Bfactor')

        print('\n************** End of Translate Unit Cell Section **************\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '********************* Trim Crystal Section *********************\n')
        # Atoms in the 3x3 parallelepiped which are a distance greater than the
        # packing density threshold from the boundaries of the processed
        # asymmetric unit are discarded. A PDB file of the trimmed
        # parallelepiped is created if createTApdb is set equal to True
        # (default = False) in the input file. The PDB file of the processed
        # asymmetric unit is deleted unless createAUpdb is set equal to True
        # (default = False) in the input file.
        bdamAtomList = b_damage_atom_list(clean_au_list, self.HETATM,
                                          self.protOrNA, self.addAtoms,
                                          self.removeAtoms)

        # Halts program if no atoms selected for BDamage analysis
        if len(bdamAtomList) < 1:
            shutil.rmtree('%s' % PDBdirectory)
            if self.batchRun is False:
                sys.exit('ERROR: No atoms selected for BDamage calculation')
            elif self.batchRun is True:
                return

        if self.createAUpdb is False:
            os.remove(clean_au_file)

        auParams = getAUparams(bdamAtomList)
        print '\nObtained asymmetric unit parameters:'
        print 'xMin = %8.3f' % auParams[0]
        print 'xMax = %8.3f' % auParams[1]
        print 'yMin = %8.3f' % auParams[2]
        print 'yMax = %8.3f' % auParams[3]
        print 'zMin = %8.3f' % auParams[4]
        print 'zMax = %8.3f\n' % auParams[5]

        print 'Removing atoms outside of packing density threshold'
        keepParams = convertParams(auParams, self.PDT)
        trimmedAtomList = trimAtoms(transAtomList, keepParams)

        if self.createTApdb is True:
            taPDBfilepath = '%s_trimmed_atoms.pdb' % pdb_file_path
            makePDB(header_lines, trimmedAtomList, footer_lines, taPDBfilepath,
                    'Bfactor')

        print('\n****************** End of Trim Crystal Section *****************\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '*************** Calculate Packing Density Section **************\n')
        # Calculates the packing density (atomic contact number) of every atom
        # in the asymmetric unit.

        print 'Calculating packing density values\n'
        au_atom_xyz, trim_atom_xyz = get_xyz_from_objects(bdamAtomList,
                                                          trimmedAtomList)
        packing_density_array = calc_packing_density(au_atom_xyz,
                                                     trim_atom_xyz, self.PDT)
        write_pckg_dens_to_atoms(bdamAtomList, packing_density_array)

        print('*********** End of Calculate Packing Density Section ***********\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '****************** Calculate BDamage Section *******************\n')
        # Atoms in the asymmetric unit are ordered via their packing density
        # values; the BDamage value of each atom is then calculated as the
        # ratio of its Bfactor as compared to the average of the Bfactor values
        # of similarly (identified via sliding window) packed atoms.

        print 'Calculating BDamage values\n'
        window = int(round((len(bdamAtomList)*self.windowSize), 0))
        if window % 2 == 0:
            window = window + 1  # Window size must be an odd number.
        if window < 11:
            window = 11  # Minimum window size is 11.
        print 'Size of sliding window --> %s atoms\n' % window
        calcBdam(bdamAtomList, window)

        print('****************************************************************\n'
              '******************* Writing DataFrame Section ******************\n')
        # Writes properties of atoms to be considered for BDamage analysis to a
        # DataFrame. The DataFrame, plus additional variables and lists
        # required for subsequent analysis, are then pickled - this allows
        # multiple analysis runs to be performed from the same DataFrame,
        # thereby reducing their calculation time.

        print 'Writing BDamage data to DataFrame\n'
        df = writeDataFrame(bdamAtomList)
        print 'Saving DataFrame\n'
        storage = '%s/DataFrame' % PDBdirectory
        os.mkdir(storage)
        storage_file = '%s/%s' % (storage, PDBcode)
        df.to_pickle(storage_file + '_dataframe.pkl')
        with open(storage_file + '_variables.pkl', 'wb') as f:
            pickle.dump((pdb_file_path, PDBcode, bdamAtomList, cif_lines,
                         cif_header_lines, cif_footer_lines, cif_column_labels,
                         header_lines, footer_lines, window), f)

        print('****************************************************************\n'
              '*************** End Of Writing DataFrame Section ***************\n')

        # Changes directory back to the 'RABDAM' directory (that in which the
        # rabdam.py script is saved).
        os.chdir('%s' % cwd)

    def rabdam_analysis(self, run, output_options):
        # Uses values in DataFrame returned from calling the 'rabdam_dataframe'
        # function to write output analysis files.

        prompt = '> '
        import os
        import sys
        import pickle
        import pandas as pd
        from output import generate_output_files
        from makeDataFrame import makePDB

        if run == 'rabdam_analysis':
            print '************************ RABDAM ANALYSIS ***********************\n'

        # Changes directory to the specified location for the output 'Logfiles'
        # directory. The default location is the current working directory
        # (i.e. that in which the rabdam.py script is saved).
        cwd = os.getcwd()
        os.chdir('%s' % self.outputDir)

        print('\n****************************************************************\n'
              '***************** Processing DataFrame Section *****************\n')
        # Checks that pkl files output by 'rabdam_dataframe' function exist.
        # Then checks if output directory specified in input file (default =
        # current working directory) already contains any analysis output files
        # - if it does then user input is requested ('Do you want to overwrite
        # the existing analysis files?'):
        # yes = all old analysis files are removed and replaced by new analysis
        #       files
        # no = old analysis files are retained, exit program
        # Note that currently there is no option to replace only a subset of
        # the output analysis files.

        pathToInput = self.pathToInput.replace('\\', '/')
        splitPath = pathToInput.split('/')
        pathToInput = splitPath[len(splitPath)-1]
        PDBcode = pathToInput
        for file_name in ['.pdb', '.cif']:
            PDBcode = PDBcode.replace('%s' % file_name, '')
        PDBcode = PDBcode.upper()
        window_name = 100*self.windowSize
        window_name = str(window_name).replace('.', '_')
        pdt_name = str(self.PDT).replace('.', '_')
        PDBdirectory = 'Logfiles/%s_window_%s_pdt_%s' % (PDBcode, window_name,
                                                         pdt_name)
        PDB_analysis_file = '%s/%s' % (PDBdirectory, PDBcode)
        storage_directory = '%s/DataFrame' % PDBdirectory
        storage_file = '%s/%s' % (storage_directory, PDBcode)

        if not os.path.isdir(storage_directory):
            if self.batchRun is False:
                sys.exit('Folder %s not found\n'
                         'Exiting RABDAM analysis' % storage_directory)
            elif self.batchRun is True:
                return

        potential_analysis_files = ['_BDamage.csv', '_BDamage.html',
                                    '_BDamage.pdb', '_BDamage.cif',
                                    '_BDamage.svg', '_Bnet_Protein.svg',
                                    '_Bnet_NA.svg']
        actual_analysis_files = []
        for name in potential_analysis_files:
            if os.path.isfile(PDB_analysis_file + name):
                actual_analysis_files.append(PDB_analysis_file + name)
        if len(actual_analysis_files) > 0:
            print('There are one or more RABDAM analysis files already present\n'
                  'in folder %s' % PDBdirectory)
            print('Do you want to overwrite the existing analysis files?\n'
                  '--USER INPUT-- type your choice and press RETURN\n'
                  'yes = overwrite ALL analysis files\n'
                  'no = do not overwrite analysis files\n')
            owChoice = None
            while owChoice not in ['yes', 'no', 'y', 'n']:
                if self.overwrite is True:
                    owChoice = 'yes'
                elif self.overwrite is False:
                    owChoice = raw_input(prompt).lower()
                if owChoice == 'yes' or owChoice == 'y':
                    print '\nOverwriting existing analysis files\n'
                    for name in actual_analysis_files:
                        os.remove(name)
                    break
                elif owChoice == 'no' or owChoice == 'n':
                    if self.batchRun is False:
                        sys.exit('Keeping original analysis files\n'
                                 'Exiting RABDAM')
                    elif self.batchRun is True:
                        return
                    break
                else:
                    print 'Unrecognised input - please answer "yes" or "no"'

        # Pkl files unpickled
        print 'Unpickling DataFrame and variables\n'
        with open(storage_file + '_variables.pkl', 'rb') as f:
            (pdb_file_path, PDBcode, bdamAtomList, cif_lines,
             cif_header_lines, cif_footer_lines, cif_column_labels,
             header_lines, footer_lines, window) = pickle.load(f)
        df = pd.read_pickle(storage_file + '_dataframe.pkl')

        print('************** End Of Processing DataFrame Section *************\n'
              '****************************************************************\n')

        print('****************************************************************\n'
              '***************** Writing Output Files Section *****************\n')
        # Uses the values stored in the BDamage DataFrame to:
        # - write DataFrame values to a csv file (providing users with a copy
        #   of the raw data that they can manipulate for further analysis as
        #   they wish)
        # - write a PDB file in which the Bfactors are replaced by BDamage
        #   values (allowing users to e.g. colour the structure by BDamage
        #   when viewed with molecular graphics software)
        # - write a cif file in which a column listinf the calculated BDamage
        #   values has been appended to the ATOM (/HETATM) records
        # - plot a kernel density estimate of the complete (i.e. all analysed
        #   atoms) BDamage distribution
        # - plot a kernel density estimate of the BDamage values of the
        #   carboxyl group oxygens of Asp and Glu residues, this plot is then
        #   used to calculate the value of the Bnet summary metric

        output = generate_output_files(pdb_file_path=pdb_file_path, df=df)

        if 'csv' in output_options:
            print 'Writing csv file\n'
            output.make_csv(bdamAtomList, window)

        if 'bdam' in output_options:
            if (len(self.pathToInput) == 4 or self.pathToInput.split('.')[-1] == 'pdb'):
                print 'Writing PDB file with BDamage values replacing Bfactors'
                pdb_file_name = pdb_file_path + '_BDamage.pdb'
                makePDB(header_lines, bdamAtomList, footer_lines, pdb_file_name,
                        'BDamage')
            if (len(self.pathToInput) == 4 or self.pathToInput.split('.')[-1] == 'cif'):
                print '\nWriting cif file with BDamage column'
                output.write_output_cif(cif_lines, cif_header_lines,
                                        cif_footer_lines, cif_column_labels)

        if 'kde' in output_options or 'summary' in output_options:
            print '\nPlotting kernel density estimate\n'
            output.make_histogram(self.highlightAtoms)

        if 'bnet' in output_options or 'summary' in output_options:
            print 'Calculating Bnet\n'
            output.calculate_Bnet(window_name, pdt_name, window)

        if 'summary' in output_options:
            print 'Writing summary html file\n'
            output.write_html_summary(cwd, output_options, self.highlightAtoms)

        print('************** End of Writing Output Files Section *************\n'
              '****************************************************************\n')

        # Changes directory back to the 'RABDAM' directory (i.e. that in which
        # the rabdam.py script is saved).
        os.chdir('%s' % cwd)
