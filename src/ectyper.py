#!/usr/bin/env python

import argparse
import os
import re
from Bio import SeqIO
from Bio.Blast.Applications import NcbiblastnCommandline



def parseCommandLine():
  """
  Initalizing the two main commands of the command line for the project.
  - input: refers to the location of the file(s) that will be processed
  - database: refers to the location of the BLAST database that will be used
  :return parser.parse_args():
  """

  parser = argparse.ArgumentParser()

  parser.add_argument("input", help="Location of new file(s). Can be a single file or a directory")
  parser.add_argument("database", help="Location of the BLAST database.")
  parser.add_argument("-out", "-output", help="", default="STDOUT")

  return parser.parse_args()


def getListGenomes(input_data):
  """
  Creating a list out of the files entered (where each file name is its absolute path). This creates a uniform
  format that works for both single files and directories.
  :param input_data:
  :return files:
  """

  filesList = []

  if os.path.isdir(input_data):
    #print("Using files from " + input_data)
    tmp = os.listdir(input_data)

    for root, dirs, files in os.walk(input_data):
     for filename in files:
       filesList.append(os.path.join(root,filename))

  else:
    # print("Using file " + input_data)
    filesList.append(os.path.abspath(input_data))

  return sorted(filesList)


def checkFiles(listGenomes):
  """
  Creating a list containig only valid .fasta files out of the previously formed list (from the getListGenomes method).
  If the newly created list is empty, the program exits with a warning.
  This filters out the invalid files.
  :param listGenomes:
  :return newListGenomes:
  """
  newListGenomes = []

  for filename in listGenomes:
    flag = 0
    print filename
    for seq_record in SeqIO.parse(filename, "fasta"):
      match = re.search('(^[a-zA-Z]+)', str(seq_record.seq))
      if not match:
        break
      else:
        flag = 1

    if flag>0:
      newListGenomes.append(filename)
    else:
      print("File " + filename+ " is in invalid format")

  if not newListGenomes:
    print("No valid fasta files")
    exit(1)

  else:
    return sorted(newListGenomes)


def initializeDB(database):

  if not os.path.isfile(database):


  # blastn_cline = NcbiblastnCommandline(cmd="blastn", db="ECTyperDB", outfmt=5, out="EcOH.xml")
  # print blastn_cline





if __name__=='__main__':
  args = parseCommandLine()
  roughListGenomes = getListGenomes(args.input)
  listGenomes = checkFiles(roughListGenomes)

  initializeDB(args.database)