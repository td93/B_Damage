

def make_csv(bdamatomList, filename, window):
    # Returns a csv file containing a complete set of atom information
    # (including both that provided in the input PDB file and also the
    # B_damage values calculated by RABDAM) for all atoms considered for
    # B_damage analysis. (This provides the user with a copy of the raw data
    # which they can manipulate as they wish.)

    newFile = open(filename, 'w')

    # Defines column header abbreviations at top of file.
    newFile.write('REC = RECORD NAME\n'
                  'ATMNUM = ATOM SERIAL NUMBER\n'
                  'ATMNAME = ATOM NAME\n'
                  'RESNAME = RESIDUE NAME\n'
                  'CHAIN = CHAIN IDENTIFIER\n'
                  'RESNUM = RESIDUE SEQUENCE NUMBER\n'
                  'XPOS = ORTHOGONAL COORDINATES FOR X IN ANGSTROMS\n'
                  'YPOS = ORTHOGONAL COORDINATES FOR Y IN ANGSTROMS\n'
                  'ZPOS = ORTHOGONAL COORDINATES FOR Z IN ANGSTROMS\n'
                  'OCC = OCCUPANCY\n'
                  'BFAC = B FACTOR (TEMPERATURE FACTOR)\n'
                  'ELEMENT = ELEMENT SYMBOL\n'
                  'CHARGE = CHARGE ON ATOM\n'
                  'PD = PACKING DENSITY (ATOMIC CONTACT NUMBER)\n')
    newFile.write('AVRG_BF = AVERAGE B FACTOR FOR ATOMS IN A SIMILAR PACKING'
                  'DENSITY ENVIRONMENT (SLIDING WINDOW SIZE = %s)\n' % window)
    newFile.write('BDAM = BDAMAGE VALUE\n'
                  '\n')
    # Writes column headers to file
    newFile.write('REC' + ','
                  'ATMNUM' + ','
                  'ATMNAME' + ','
                  'RESNAME' + ','
                  'CHAIN' + ','
                  'RESNUM' + ','
                  'XPOS' + ','
                  'YPOS' + ','
                  'ZPOS' + ','
                  'OCC' + ','
                  'BFAC' + ','
                  'ELEMENT' + ','
                  'CHARGE' + ','
                  'PD' + ','
                  'AVRG_BF' + ','
                  'BDAM' + '\n')

    # Writes properties of each atom considered fpr B_damage analysis to file.
    for atm in bdamatomList:
        newFile.write(str(atm.lineID) + ',')
        newFile.write(str(atm.atomNum) + ',')
        newFile.write(str(atm.atomType) + ',')
        newFile.write(str(atm.resiType) + ',')
        newFile.write(str(atm.chainID) + ',')
        newFile.write(str(atm.resiNum) + ',')
        newFile.write(str(atm.xyzCoords[0][0]) + ',')
        newFile.write(str(atm.xyzCoords[1][0]) + ',')
        newFile.write(str(atm.xyzCoords[2][0]) + ',')
        newFile.write(str(atm.occupancy) + ',')
        newFile.write(str(atm.bFactor) + ',')
        newFile.write(str(atm.atomID) + ',')
        newFile.write(str(atm.charge) + ',')
        newFile.write(str(atm.pd) + ',')
        newFile.write(str(atm.avrg_bf) + ',')
        newFile.write(str(atm.bd) + '\n')

    newFile.close()


def make_histogram(df, fileName, PDBcode, threshold, highlightAtoms):  # Need to increase speed
    # Returns a kernel density plot of the B_damage values of every atom
    # considered for B_damage analysis. The area under the kernel density
    # plot (which is equal to 1) is then calculated, and a boundary is drawn
    # at the B_damage value above which a particular % (equal to the value
    # of the 'threshold' argument as defined in INPUT.txt, default value is
    # 2%) of the area under the curve lies. Those atoms which lie above this
    # threshold are listed in an html file. Any atom numbers listed in
    # highlightAtoms argument as defined in INPUT.txt will be marked on the
    # kernel density plot.

    import matplotlib.pyplot as plt
    import numpy  # Required for seaborn and pandas functionality
    import seaborn as sns
    import pandas as pd

    # Generates kernel density plot
    plt.clf()  # Prevents kernel density plots of all atoms considered for
    # B_damage analysis, and the subset of atoms considered for calculation
    # of the global B_damage metric, from being plotted on the same axes.
    line1 = sns.distplot(df.BDAM.values, hist=False, rug=True)

    # Extracts an array of (x, y) coordinate pairs evenly spaced along the
    # x(B_damage)-axis. These coordinate pairs are used to calculate the
    # area under the curve via the trapezium rule. Concomitantly, the (x, y)
    # coordinate pair values are separated depending upon whether they lie
    # below or above the threshold area defined in INPUT.txt or not. The
    # threshold B_damage boundary is then taken as the smallest x coordinate
    # of the (x, y) pairs which lie above the threshold area.
    xy_values = line1.get_lines()[0].get_data()
    x_values = xy_values[0]
    y_values = xy_values[1]

    total_area = 0
    for index, value in enumerate(y_values):
        if index != len(y_values) - 1:
            area = (((y_values[int(index)] + y_values[int((index)+1)]) / 2)
                    * (float(x_values[len(x_values)-1] - x_values[0]) / float(len(x_values)-1)))
            total_area = total_area + area

    area_LHS = 0
    atoms_list = []
    for index, value in enumerate(y_values):
        if area_LHS <= (1-float(threshold)) * total_area:
            atoms_list.append(value)
            area = (((y_values[int(index)] + y_values[int((index)+1)]) / 2)
                    * (float(x_values[len(x_values)-1] - x_values[0]) / float(len(x_values)-1)))
            if area_LHS + area <= (1-float(threshold)) * total_area:
                area_LHS = area_LHS + area
            else:
                break

    x_values_RHS = x_values[len(atoms_list):]
    RHS_Bdam_values = []
    for value in df.BDAM.values:
        if value >= x_values_RHS[0]:
            RHS_Bdam_values.append(value)

    # Those atoms considered for B_damage analysis with an associated
    # B_damage value greater than the threshold boundary are listed in an
    # html file.
    df_ordered = df.sort_values(by='BDAM', ascending=False)
    df_trunc = df_ordered.head(len(RHS_Bdam_values))
    decimals = pd.Series([2, 2, 2], index=['BFAC', 'AVRG BF', 'BDAM'])
    df_trunc = df_trunc.round(decimals)
    df_trunc.to_html(str(fileName) + 'Bdamage.html', index=False,
                     float_format='%11.3f')

    # Marks the position of the threshold boundary, plus the positions of any
    # atoms whose numbers are listed in highlightAtoms argument as defined in
    # INPUT.txt, on the kernel density plot.
    highlighted_atoms = [None]

    boundary_line = plt.plot([x_values_RHS[0], x_values_RHS[0]],
                             [0, max(y_values)], linewidth=2, color='black',
                             label=' boundary = {:.2f}\n (threshold = {:})'.format(x_values_RHS[0],
                             threshold))
    highlighted_atoms.append(boundary_line)

    if len(highlightAtoms) != 0:
        lines = [None]
        for atm in highlightAtoms:
            for index, value in enumerate(df.ATMNUM.values):
                if float(atm) == value:
                    lines[0] = index
            for line in lines:
                for index, value in enumerate(df.BDAM.values):
                    if line == index:
                        m = plt.plot([value, value], [0, max(y_values)],
                                     linewidth=2, label=' atom ' + str(atm)
                                     + '\n B_damage = {:.2f}'.format(value))
                        highlighted_atoms.append(m)

    plt.legend(handles=highlighted_atoms[0])
    plt.xlabel('B Damage')
    plt.ylabel('Frequency')
    plt.title(str(PDBcode) + ' kernel density plot')
    plt.savefig(str(fileName)+"Bdamage.png")

    return x_values_RHS


def make_colourbyBdam_pdb(df, bof, eof, fileName, atomList, x_values_RHS):
    # Writes pdb files in which B factor values are replaced by B_damage
    # values to allow structure when viewed with molecular graphics software
    # to be coloured by B_damage.

    import numpy as np

    # Writes PDB file in which every atom can be coloured by its B_damage
    # values.
    newPDBfile = open(str(fileName) + 'Bdamage.pdb', 'a')

    for line in bof:
        newPDBfile.write(line)

    for atm in atomList:
        a = str(atm.lineID)
        b = int(atm.atomNum)
        c = str(atm.atomType)
        d = str(atm.resiType)
        e = str(atm.chainID)
        f = int(atm.resiNum)
        g = float(atm.xyzCoords[0][0])
        h = float(atm.xyzCoords[1][0])
        j = float(atm.xyzCoords[2][0])
        k = float(atm.occupancy)
        l = float(np.log(atm.bd))  # Converts log normal B_damage distribution
        # to a linear distribution such that a fixed change in colour will
        # represent a fixed change in B_damage.
        m = str(atm.atomID)
        n = str(atm.charge)
        newLine = '%-6s%5d  %-3s %3s %1s%4d    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s%2s\n' % (a, b, c, d, e, f, g, h, j, k, l, m, n)
        newPDBfile.write(newLine)

    for line in eof:
        newPDBfile.write(line)

    newPDBfile.close()

    # Writes PDB file which highlights only those atoms with B damage values
    # which lie above the threshold boundary (as calculated when writing the
    # B_damage kernel density plot).
    newPDBfile = open(str(fileName) + 'Bdamage_above_boundary.pdb', 'a')

    for line in bof:
        newPDBfile.write(line)

    for atm in atomList:
        if float(atm.bd) >= x_values_RHS[0]:
            a = str(atm.lineID)
            b = int(atm.atomNum)
            c = str(atm.atomType)
            d = str(atm.resiType)
            e = str(atm.chainID)
            f = int(atm.resiNum)
            g = float(atm.xyzCoords[0][0])
            h = float(atm.xyzCoords[1][0])
            j = float(atm.xyzCoords[2][0])
            k = float(atm.occupancy)
            l = float(np.log(atm.bd))  # Converts log normal B_damage
            # distribution to a linear distribution such that a fixed change
            # in colour will represent a fixed change in B_damage.
            m = str(atm.atomID)
            n = str(atm.charge)
            newLine = '%-6s%5d  %-3s %3s %1s%4d    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s%2s\n' % (a, b, c, d, e, f, g, h, j, k, l, m, n)
            newPDBfile.write(newLine)
        else:
            a = str(atm.lineID)
            b = int(atm.atomNum)
            c = str(atm.atomType)
            d = str(atm.resiType)
            e = str(atm.chainID)
            f = int(atm.resiNum)
            g = float(atm.xyzCoords[0][0])
            h = float(atm.xyzCoords[1][0])
            j = float(atm.xyzCoords[2][0])
            k = float(atm.occupancy)
            l = np.log(x_values_RHS[0]) - 1  # Sets the B_damage values of all
            # atoms which lie below the threshold boundary to 1 less than
            # the smallest B_damage value which lies above the threshold, in
            # order that these atoms are not highlighted.
            m = str(atm.atomID)
            n = str(atm.charge)
            newLine = '%-6s%5d  %-3s %3s %1s%4d    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s%2s\n' % (a, b, c, d, e, f, g, h, j, k, l, m, n)
            newPDBfile.write(newLine)

    for line in eof:
        newPDBfile.write(line)

    newPDBfile.close()

	
def calculate_global_BDam(df, PDBcode, fileName):
    # Plots a kernel density estimate of Cys S, Glu O and Asp O atoms from
    # the subset of atoms considered for B_damage analysis. The global
    # B_damage metric is then calculated as the ratio of the areas under
    # the curve either side of 1.

    import matplotlib.pyplot as plt
    import numpy as np  # Required for seaborn and pandas functionality
    import seaborn as sns
    import pandas as pd

    # Selects Cys S, Glu O and Asp O atoms from complete DataFrame.
    a = df[df.RESNAME.isin(["CYS"])][df.ATMNAME.isin(["SG"])]
    b = df[df.RESNAME.isin(["GLU"])][df.ATMNAME.isin(["OE1", "OE2"])]
    c = df[df.RESNAME.isin(["ASP"])][df.ATMNAME.isin(["OD1", "OD2"])]
    dataframes = [a, b, c]
    x = pd.concat(dataframes)

    if x.empty:
        print('\nNo Cys S, Glu O or Asp O in structure to calculate global\n'
              'B_damage\n')
        pass

    else:
        plt.clf()  # Prevents kernel density plots of all atoms considered for
        # B_damage analysis, and the subset of atoms considered for calculation
        # of the global B_damage metric, from being plotted on the same axes.
        plot = sns.distplot(x.BDAM.values, hist=False, rug=True)
        plt.xlabel("B Damage")
        plt.ylabel("Frequency")
        plt.title(str(PDBcode) + 'kernel density plot')

        # Extracts an array of (x, y) coordinate pairs evenly spaced along
        # the x(B_damage)-axis from the kernel density plot. These coordinate
        # pairs are used to calculate, via the trapezium rule, the area under
        # the curve between the smallest value of x and 1 (= area LHS), and
        # the area under the curve between 1 and the largest value of x
        # (= area RHS). The global B_damage metric is then calculated as the
        # ratio of area RHS to area LHS.
        xy_values = plot.get_lines()[0].get_data()
        x_values = xy_values[0]
        y_values = xy_values[1]

        # Calculates area RHS
        x_values_RHS = x_values[x_values >= 1]
        x_min_index = len(x_values) - len(x_values_RHS)
        y_values_RHS = y_values[x_min_index:]

        x_max_RHS = int(len(x_values_RHS) - 1)
        x_distance_RHS = x_values_RHS[x_max_RHS] - x_values_RHS[0]

        total_area_RHS = 0

        for index, value in enumerate(y_values_RHS):
            if float(index) != (len(y_values_RHS) - 1):
                area_RHS = (((y_values_RHS[int(index)] + y_values_RHS[int((index) + 1)]) / 2)
                            * (float(x_distance_RHS) / float(x_max_RHS)))
                total_area_RHS = total_area_RHS + area_RHS

        # Calculates area LHS
        x_values_LHS = x_values[x_values <= 1]
        x_max_index = len(x_values_LHS) - 1
        y_values_LHS = y_values[:x_max_index]

        x_max_LHS = int(len(x_values_LHS) - 1)
        x_distance_LHS = x_values_LHS[x_max_index] - x_values_LHS[0]

        total_area_LHS = 0

        for index, value in enumerate(y_values_LHS):
            if float(index) != (len(y_values_LHS) - 1):
                area_LHS = (((y_values_LHS[int(index)] + y_values_LHS[int((index) + 1)]) / 2)
                            * (float(x_distance_LHS) / float(x_max_LHS)))
                total_area_LHS = total_area_LHS + area_LHS

        # Calculates area ratio ( = global B_damage metric)
        ratio = total_area_RHS / total_area_LHS

        plt.annotate('globalBdamage = {:.2f}'.format(ratio),
                     xy=((max((plot.get_lines()[0].get_data())[0])*0.65),
                     (max(y_values)*0.9)))  # Need to fix annotation position
        plt.savefig(str(fileName)+"globalBdamage.png")
