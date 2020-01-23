#!/usr/bin/env python3 

#############################################################
#                                                           #
# Genes and Health Contest Grader                           #
#                                                           #
# Jae Chan Hwang | hwangjc@umich.edu                        #
# 01/23/2020                                                #
#                                                           #
#############################################################

import argparse
import sys
import io

from io import StringIO


# CHANGE THIS IF THE FORMAT OF THE SIGN IN SHEET CHANGES!!!!!!!
# THE COLUMN INDICES FOR ITEMS IN THE SIGN IN SHEET, 0-indexed

TSTAMPPOS = 0 # timestamp 
EMAILPOS  = 1 # email
FIRSTPOS  = 2 # first name
LASTPOS   = 3 # last name
SCHOOLPOS = 4 # school
GRADEPOS  = 5 # grade
LOCPOS    = 6 # location

# CHANGE THIS IF THE FORMAT OF THE GRADE SHEET CHANGES!!!!!!!
# THE COLUMN INDICES FOR ITEMS IN THE GRADE SHEET, 0-indexed

EMAILPOS_G = 0 # email
FIRSTPOS_G = 1 # first name
LASTPOS_G  = 2 # last name
GRADEPOS_G = 3
WRITPOS_G  = 4 # written portion score
COMPPOS_G  = 5 # computational portion score

# DO NOT CHANGE

BEG = "Beginner"
ADV = "Advanced"

ALR = 0
WRT = 1
CMP = 2
UTR = 3
ITR = 4
WINNERTYPE = ["All Around", "Written", "Computational", "UTR", "Intron"]


def parseArgs():
    """Parse command line arguments in c style."""

    parser = argparse.ArgumentParser(
        description="""Finds the winners of the Genes and Health
                       contest."""
    )

    # optional arguments
    parser.add_argument('-w', '--writemax', required=False, type=int,
                        help="""The total number of possible points in the
                                written portion of the test. Default is 100.""")
    parser.add_argument('-c', '--compmax', required=False, type=int,
                        help="""The total number of possible points in the
                                computational portion of the test. Default
                                is 100.""")
    parser.add_argument('-b', '--begdst', required=False,
                        help="""The distribution of points allocated towards the 
                                written portion and the computational portion of
                                the test for the beginner section. Default is 
                                50/50.""")
    parser.add_argument('-a', '--advdst', required=False,
                        help="""The distrivution of points allocated towards the
                                written portion and the computational portion of
                                the test for the advanced section. Default is 
                                40/60.""")
    parser.add_argument('-A', '--advpath', required=False,
                        help="""The path to the score sheet for the advanced
                                section. If this argument is not specified, it
                                will grade everything as the beginner section using
                                the beginner section distribution. Cannot have both
                                -A and -G options.""")
    parser.add_argument('-G', '--gradesplit', required=False,
                        help="""Flag indicating that the competitors will be split
                                into different groups based on their grade - 
                                underclassmen and upperclassmen. The beginner 
                                distribution will be used for both groups. Cannot
                                have both -A and -G options.""",
                        action="store_true")

    # required arguments
    parser.add_argument('-s', '--signin', required=True,
                        help="The path to the sign-in sheet in CSV format.")

    parser.add_argument('grades', type=str,
                        help="The path to the grades sheet in CSV format.")

    return parser.parse_args()


def parseSignIn(args):
    """Parse sign in sheet as reference for the grades."""
    
    # create a dictionary of (email,first,last) -> score
    scores = {}

    # open sign in sheet
    signfile = open(args.signin, "r")
    # get the header
    header = signfile.readline()

    for line in signfile:
        # split line by commas
        fields = line.split(',')

        # create the tuple key of (email, firstname, lastname, grade)
        key = (fields[EMAILPOS], fields[FIRSTPOS], fields[LASTPOS], fields[GRADEPOS])
        # default score of 0
        scores[key] = 0

    return scores


def getDst(args, section):
    """Return the distribution for the written and computational portion
       of the exam for a specific section."""
    
    # set the default distributions
    wdst = 0.5 if section == BEG else 0.4
    cdst = 0.5 if section == BEG else 0.6

    # get the beginner distribution if it was specified
    if section == BEG and args.begdst:
        _dsts = args.begdst.split('/')
        
        # assert that the distributions total to 100
        if int(_dsts[0]) + int(_dsts[1]) != 100:
            raise Exception("Beginner distribution does not total to 100")

        wdst = float(_dsts[0]) / 100.0
        cdst = float(_dsts[1]) / 100.0
    # get the advanced distribution if it was specified
    elif section == ADV and args.advdst:
        _dsts = args.advdst.split('/')

        # assert that the distributions total to 100
        if int(_dsts[0]) + int(_dsts[1]) != 100:
            raise Exception("Advanced distribution does not total to 100")

        wdst = float(_dsts[0]) / 100.0
        cdst = float(_dsts[1]) / 100.0

    return (wdst, cdst)

        
def calcScores(scores, args, section, scorefile):
    """Calculate the total score for an individual based on their
       section corresponding distribution. Returns a list of keys
       of the competitors in this section."""

    # get the max score for the written and computational portion
    writemax = 100 if not args.writemax else args.writemax
    compmax  = 100 if not args.compmax else args.compmax

    # get the distribution for beginner and advanced sections
    dsts = getDst(args, section)
    wdst = dsts[0]
    cdst = dsts[1]

    # start calculating final scores
    header = scorefile.readline()

    keys = []

    for line in scorefile:
        # split line by commas
        fields = line.split(',')
        
        # create tuple key
        key = (fields[EMAILPOS_G], fields[FIRSTPOS_G], fields[LASTPOS_G], fields[GRADEPOS_G])
        keys.append(key)

        # calculate score
        if key in scores: 
            writescore = float(fields[WRITPOS_G]) / float(writemax)
            compscore = float(fields[COMPPOS_G]) / float(compmax)
            finalscore = ((writescore * wdst) + (compscore * cdst)) * 100

            scores[key] = [finalscore,writescore*100,compscore*100]

    return keys


def findWinners(scores, args, section, keys):
    """Find the winners of this section. The participants of this section
       are passed through the list 'keys'."""
    
    # partition participants into two groups if splitting by grade
    if args.gradesplit:
        under = []
        upper = []
        
        # split into underclassmen and upperclassmen
        for key in keys:
            if int(key[3]) < 11:
                under.append(key)
            else:
                upper.append(key)

        # find winners
        print("-------- Underclassmen Winners --------\n")
        findWinnersHelper(scores, args, under)
        print("-------- Upperclassmen Winners --------\n")
        findWinnersHelper(scores, args, upper)
    else:
        print(f"-------- {section} section winners --------\n")
        findWinnersHelper(scores, args, keys)
      

def findWinnersHelper(scores, args, keys):
    """Does the real work to find section winners."""
    
    # get the top 3 all around winners
    getTopScore(scores, keys, ALR, 3)
    # get the top 3 computational and written section winners
    getTopWrtCmp(scores, keys, 3)
    # get the UTR section winner
    getTopScore(scores, keys, UTR, 1)
    # get the Intron section winner
    getTopScore(scores, keys, ITR, 1)


def getTopWrtCmp(scores, keys, numwinners):
    """Find the top scores for written and computational."""

    writewinners = []
    compwinners = []

    counter = 1
    while len(writewinners) != numwinners or len(compwinners) != numwinners:
        # keep track of ties
        writeties = []
        compties = []
        writetop = 0.0
        comptop = 0.0
        
        for key in keys:
            if key in scores:
                writescore = round(scores[key][WRT], 5)
                compscore = round(scores[key][CMP], 5)

                # see if they are the top for written portion
                if writescore > writetop:
                    writetop = writescore
                    writeties = [(key, writescore)]
                elif writescore == writetop:
                    writeties.append((key, writescore))

                # see if they are the top for computational portion
                if compscore > comptop:
                    comptop = compscore
                    compties = [(key, compscore)]
                elif compscore == comptop:
                    compties.append((key, compscore))

        wonboth = []
        # see if anybody won both portions 
        for winner_w in writeties:
            for winner_c in compties:
                if winner_w[0] == winner_c[0]:
                    # remove them if they did
                    wonboth.append(winner_c)

        # alternate between the portions to remove as leader
        for winner in wonboth:
            if (counter % 2) == 1:
                compties.remove(winner)
            else:
                writeties.remove(winner)
            counter += 1

        # remove them from the score so they cant win again
        for winner in writeties:
            if len(writewinners) < numwinners:
                del scores[winner[0]] 
        for winner in compties:
            if len(compwinners) < numwinners:
                del scores[winner[0]]

        if len(writeties) != 0 and len(writewinners) <  numwinners:
            writewinners.append(writeties)
        if len(compties) != 0 and len(compwinners) < numwinners:
            compwinners.append(compties)

    # print the winners
    for i in range(0,numwinners):
        for winner in writewinners[i]:
            print(f" -- #{i+1} {WINNERTYPE[WRT]} Winner: {winner[0][1]} {winner[0][2]}, {winner[0][0]}, score={winner[1]}") 
    print("")

    for i in range(0,numwinners):
        for winner in compwinners[i]:
            print(f" -- #{i+1} {WINNERTYPE[CMP]} Winner: {winner[0][1]} {winner[0][2]}, {winner[0][0]}, score={winner[1]}") 
    print("")


def getTopScore(scores, keys, session, numwinners):
    """Find the top score for all around scores."""

    _session = session
    if session == UTR or session == ITR:
        _session = 0 

    winners = []
    for i in range(0,numwinners):
        # keep track of ties
        ties = []
        topscore = 0.0
        
        # find the person(s) with the highest score
        for key in keys: 
            if key in scores:
                currscore = round(scores[key][_session], 5)
                if currscore > topscore:
                    topscore = currscore
                    ties = [(key, currscore)]
                elif currscore == topscore:
                    ties.append((key, currscore))

        # remove winners for other prizes ie can only win once
        for winner in ties:
            del scores[winner[0]] 

        winners.append(ties) 

    for i in range(0,numwinners):
        for winner in winners[i]:
            print(f" -- #{i+1} {WINNERTYPE[session]} Winner: {winner[0][1]} {winner[0][2]}, {winner[0][0]}, score={winner[1]}") 
    print("")
    

def main():

    args = parseArgs()

    if args.gradesplit and args.advpath:
        print("error: Cannot have an advanced section AND split by grade. For help, type:")
        print(f"\t{sys.argv[0]} -h")
        exit(1)

    # parse sign in sheet
    scores = parseSignIn(args)

    # calculate scores for beginner section
    grades = open(args.grades, "r")
    begkeys = calcScores(scores, args, BEG, grades)

    # calculate scores for advanced section
    if args.advpath:
        advgrades = open(args.advpath, "r")
        advkeys = calcScores(scores, args, ADV, advgrades)

    # find winners for the beginner section
    findWinners(scores, args, BEG, begkeys)

    # find winners for the advanced section
    if args.advpath:
        findWinners(scores, args, ADV, advkeys)

main()
