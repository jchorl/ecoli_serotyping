#!/usr/bin/env python

from flask import *
from formatresults import *
from compareresults import *

TEST= False
GENOMES = {}

def runProgram():

  logging.basicConfig(filename='ectyper.log',level=logging.INFO)

  args = parseCommandLine()

  roughGenomesList = getFilesList(args.input)
  genomesList = checkFiles(roughGenomesList)

  if isinstance(genomesList, list):
    if initializeDB() == 0:
      resultsList = runBlastQuery(genomesList, 'ECTyperDB')
      genomesDict = parseResults(resultsList)
      predictionDict = filterPredictions(genomesDict, args.pi, args.pl)
      matchDict = sortMatches(predictionDict)
      GENOMES = findTopMatches(matchDict)
      logging.info('Top matches are ' + str(GENOMES))

      if TEST == True:
        compareResults(roughGenomesList, GENOMES)

      if args.csv == 'true':
        toCSV(GENOMES, args.v)

      print formatResults(GENOMES, args.v)

    else:
      logging.error('There was an error while generating the database.')
  else:
    print genomesList



if __name__=='__main__':
  runProgram()