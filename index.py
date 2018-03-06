import nltk
import getopt
import os
import sys
from nltk.stem.porter import *
from nltk.tokenize import RegexpTokenizer
import math
import cPickle as pickle

stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

vocabulary = set()
docTermMapping = {}
docFreq = {}
	
def buildIndex(docDir):
	docIDs = []
	allDocs = os.listdir(docDir)
	allDocsSorted = sorted(allDocs, key=lambda x : int(x))
	
	for doc in allDocsSorted:
		docIDs.append(int(doc))
		docFile = os.path.join(docDir, doc)
		fDoc = open(docFile, 'r')
		contentList = fDoc.readlines()
		docContent = "".join(contentList)
		docSentList = nltk.sent_tokenize(docContent)
		# docSentWordList = [tokenizer.tokenize(sent) for sent in docSentList]
		docSentWordList = [nltk.word_tokenize(sent) for sent in docSentList]
		docWordList = [word for wordlist in docSentWordList for word in wordlist]
		for token in docWordList:
			token = token.lower()
			term = stemmer.stem(token)
			
			vocabulary.add(term)
			
			if term in docTermMapping:
				if int(doc) not in docTermMapping[term]:
					docFreq[term] += 1
					docTermMapping[term].append(int(doc))				
			else:
				docTermMapping[term] = []
				if term not in docFreq:
					docFreq[term] = 0
				if int(doc) not in docTermMapping[term]:
					docFreq[term] += 1
					docTermMapping[term].append(int(doc))

def outputData(dictFile, postingsFile, docDir):
	byteCtr = 0
	vocabPostingsMerged = {}

	fileP = open(postingsFile, 'w')
	fileD = open(dictFile, 'w')

	allDocs = os.listdir(docDir)
	allDocsSorted = sorted(allDocs, key=lambda x : int(x))

	for doc in allDocsSorted:
		fileP.write(str(doc))
		byteCtr += len(str(doc))
		fileP.write(' ')
		byteCtr += len(' ')

	fileP.write('\n')
	byteCtr += len('\n')
	
	for term in sorted(vocabulary):
		vocabPostingsMerged[term] = (docFreq[term], docTermMapping[term])
		# print term, docFreq[term], docTermMapping[term]

	for term in sorted(vocabulary):
		skipInterval = int(math.sqrt(docFreq[term]))
		postingsLen = 0

		fileD.write(term)
		fileD.write(' ')
		fileD.write(str(docFreq[term]))
		fileD.write(' ')
		fileD.write(str(byteCtr))
		fileD.write(' ')
				
		for i in range(len(docTermMapping[term])):
			
			fileP.write(str(docTermMapping[term][i]))
			byteCtr += len(str(docTermMapping[term][i]))
			postingsLen += len(str(docTermMapping[term][i]))
			
			if (int(skipInterval) > 1 and i+int(skipInterval) < docFreq[term] and i%skipInterval == 0):
				fileP.write('->')
				byteCtr += len('->')
				postingsLen += len('->')
				
				fileP.write(str(i+int(skipInterval)))
				byteCtr += len(str(i+int(skipInterval)))
				postingsLen += len(str(i+int(skipInterval)))
			
			elif (int(skipInterval) > 1 and i+int(skipInterval) >= docFreq[term] and i%skipInterval == 0 and docFreq[term] - 1 - i >= 2):
				fileP.write('->')
				byteCtr += len('->')
				postingsLen += len('->')
				
				fileP.write(str(docFreq[term]-1))
				byteCtr += len(str(docFreq[term]-1))
				postingsLen += len(str(docFreq[term]-1))
			
			fileP.write(' ')
			byteCtr += len(' ')
			postingsLen += len(' ')
		
		fileP.write('\n')
		byteCtr += len('\n')
		postingsLen += len('\n')

		fileD.write(str(postingsLen))
		fileD.write('\n')


def usage():
	print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

doc_directory = output_file_dict = output_file_postings = None
try:
	opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
	usage()
	sys.exit(2)

for command, arg in opts:
	if command == '-i':
		doc_directory = arg
	elif command == '-d':
		output_file_dict = arg
	elif command == '-p':
		output_file_postings = arg
	else:
		assert False, "unhandled option"

if doc_directory == None or output_file_dict == None or output_file_postings == None:
	usage()
	sys.exit(2)

buildIndex(doc_directory)
outputData(output_file_dict, output_file_postings, doc_directory)