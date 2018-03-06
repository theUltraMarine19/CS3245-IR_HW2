import nltk
import getopt
import os
import sys
import re
import datetime
from nltk.stem.porter import *

start_time = datetime.datetime.now()
end_time = datetime.datetime.now()

stemmer = PorterStemmer()

docInfo = {}
vocabulary = set()
booleanPrecedence = {'AND' : 2, 'OR' : 1, 'NOT' : 3, '(' : 0}

fp = open('postings.txt','r')
docsStr = fp.readline().strip()
allDocs = docsStr.split(' ')

# print allDocs

def inMemoryDict(dictFile):
	with open(dictFile, 'r') as f:
		dictLines = f.readlines()
		for line in dictLines:
			line = line.strip()
			tokens = line.split(' ')
			vocabulary.add(tokens[0])
			docInfo[tokens[0]] = (int(tokens[1]), int(tokens[2]), int(tokens[3]))
			
def fetchPostings(term):
	retPostings = []
	startByte = docInfo[term][1]
	size = docInfo[term][2]
	fp.seek(startByte, 0)  
	postingStr = fp.read(size)
	# postingStr = fp.readline()
	postingStr = postingStr.strip()
	tokens = postingStr.split(' ')
	retPostings = tokens

	return retPostings

def inputQueries(queriesFile):
	queriesList = []
	with open(queriesFile, 'r') as fq:
		queries = fp.readlines()
		for line in fq:
			line = line.strip()
			tokens = nltk.word_tokenize(line)
			if tokens[-1] == '.':
				tokens.pop()
				tokens[-1] = tokens[-1] + '.'
			
			queryTerms = []
			for token in tokens:
				if (token != 'AND' and token != 'OR' and token != 'NOT' and token != '(' and token != ')'):
					token = token.lower()
					term = stemmer.stem(token)
					queryTerms.append(term)
				else:
					queryTerms.append(token)

			postfixQuery = shuntingYard(queryTerms)
			queriesList.append(postfixQuery)

	return queriesList

def refinePostings(pList):
	result = []

	for token in pList:
		if(len(token.split('->')) > 1):
			result.append(token.split('->')[0])
		else:
			result.append(token)

	return result

def handleQueries(queriesList):
	output = []
	operandStack = []

	for query in queriesList:
		if len(query) == 1:
			output.append(refinePostings(fetchPostings(query[0])))

		else:
			ind = 0
			while ind < len(query):
				token = query[ind]

				if (token != 'AND' and token != 'OR' and token != 'NOT'):
					operandStack.append(token)

				elif (token == 'NOT'):
					# a AND NOT b type queries
					if ((len(operandStack) > 1) and (query[ind + 1] == 'AND')):
						term_curr1 = operandStack.pop()
						if not(isinstance(term_curr1, (list,))):
							term_curr1 = fetchPostings(term_curr1)

						term_curr2 = operandStack.pop()
						if not(isinstance(term_curr2, (list,))):
							term_curr2 = fetchPostings(term_curr2)

						ans = OpANDNOT(term_curr2, term_curr1)
						operandStack.append(ans)
						ind+=1

					# simple NOT queries
					elif (len(operandStack) > 0):
						term_curr = operandStack.pop()
						if not(isinstance(term_curr, (list,))):
							term_curr = fetchPostings(term_curr)
						ans = OpNOT(term_curr)
						operandStack.append(ans)

				elif(token == 'AND'):
					if (len(operandStack) > 1):
						term_curr1 = operandStack.pop()
						if not(isinstance(term_curr1, (list,))):
							term_curr1 = fetchPostings(term_curr1)

						term_curr2 = operandStack.pop()
						if not(isinstance(term_curr2, (list,))):
							term_curr2 = fetchPostings(term_curr2)

						ans = OpAND(term_curr1, term_curr2)
						operandStack.append(ans)

				elif(token == 'OR'):
					if (len(operandStack) > 1):
						term_curr1 = operandStack.pop()
						if not(isinstance(term_curr1, (list,))):
							term_curr1 = fetchPostings(term_curr1)

						term_curr2 = operandStack.pop()
						if not(isinstance(term_curr2, (list,))):
							term_curr2 = fetchPostings(term_curr2)

						ans = OpOR(term_curr1, term_curr2)
						operandStack.append(ans)

				ind+=1

			output.append(operandStack.pop())

	return output

def outputResult(outputToPost, resultsFile):
	fileout = open(resultsFile, 'w')

	for line in outputToPost:
		for val in line:
			fileout.write(val)
			fileout.write(' ')
		fileout.write('\n')

def shuntingYard(infixQuery):
	output = []
	operatorStack = []

	for token in infixQuery:

		if token == '(':
			operatorStack.append(token)
		
		elif token == ')':
			while True:
				top = operatorStack.pop()
				if top == '(':
					break
				output.append(top)
		
		elif token in booleanPrecedence:
			if (operatorStack):
				currOp = operatorStack[-1]
				while (operatorStack and booleanPrecedence[currOp] > booleanPrecedence[token]):
					top = operatorStack.pop()
					output.append(top)
					if (operatorStack):
						currOp = operatorStack[-1]
			operatorStack.append(token)
		
		else:
			output.append(token)

	while (operatorStack):
		top = operatorStack.pop()
		output.append(top)

	return output


def OpANDNOT(pList1, pList2):
	ans = []
	index1 = 0
	index2 = 0
	while index1 < len(pList1):
		docID1 = pList1[index1].split('->')[0]

		if index2 == len(pList2):
			ans.append(docID1)
			index1 += 1
			continue
		
		docID2 = pList2[index2].split('->')[0]
		
		if (int(docID1) == int(docID2)):
			index1 += 1
			index2 += 1

		elif (int(docID1) < int(docID2)):
			ans.append(docID1)
			index1 += 1

		else:
			if ('->' in pList2[index2] and pList2[int(pList2[index2].split('->')[1])] < int(docID1)):
				while ('->' in pList2[index2] and pList2[int(pList2[index2].split('->')[1])] < int(docID1)):
					index2 = pList2[index2].split('->')[1]
			else:
				index2 += 1

	return ans


def OpAND(pList1, pList2):
	ans = []
	index1 = 0
	index2 = 0
	while index1 < len(pList1) and index2 < len(pList2):
		docID1 = pList1[index1].split('->')[0]
		docID2 = pList2[index2].split('->')[0]
		
		# hasSkip1 = '->' in pList1[index1]
		# hasSkip2 = '->' in pList2[index2]
		
		# if hasSkip1:
		# 	skip1 = pList1[index1].split('->')[1]
		# if hasSkip2:
		# 	skip1 = pList2[index2].split('->')[1]
		
		if (int(docID1) == int(docID2)):
			ans.append(docID1)
			index1 += 1
			index2 += 1

		elif (int(docID1) < int(docID2)):
			if ('->' in pList1[index1] and pList1[int(pList1[index1].split('->')[1])] < int(docID2)):
				while ('->' in pList1[index1] and pList1[int(pList1[index1].split('->')[1])] < int(docID2)):
					# regex = re.compile('^'+docID1+'*')
					index1 = pList1[index1].split('->')[1]   # Skip jump needs improvement
					# print index1 
			else:
				index1 += 1

		else:
			if ('->' in pList2[index2] and pList2[int(pList2[index2].split('->')[1])] < int(docID1)):
				while ('->' in pList2[index2] and pList2[int(pList2[index2].split('->')[1])] < int(docID1)):
					# regex = re.compile('^'+docID2+'*')
					index2 = pList2[index2].split('->')[1]   # Skip jump needs improvement
					# print index2 
			else:
				index2 += 1

	return ans

def OpOR(pList1, pList2):
	ans = []
	index1 = 0
	index2 = 0
	
	while True:
		
		if (index1 == len(pList1) and index2 == len(pList2)):
			break

		elif (index1 < len(pList1) and index2 < len(pList2)):
			docID1 = pList1[index1].split('->')[0]
			docID2 = pList2[index2].split('->')[0]
		
			if (int(docID1) == int(docID2)):
				ans.append(docID1)
				index1 += 1
				index2 += 1

			elif (int(docID1) < int(docID2)):
				ans.append(docID1)
				index1 += 1

			else:
				ans.append(docID2)
				index2 += 1
		
		elif (index1 == len(pList1) and index2 < len(pList2)):
			docID2 = pList2[index2].split('->')[0]
			ans.append(docID2)
			index2 += 1			

		elif (index1 < len(pList1) and index2 == len(pList2)):
			docID1 = pList1[index1].split('->')[0]
			ans.append(docID1)
			index1 += 1

	return ans

def OpNOT(pList):
	ans = []
	index1 = 0
	index2 = 0

	while True:

		if (index1 == len(pList) and index2 == len(allDocs)):
			break

		elif (index1 < len(pList) and index2 < len(allDocs)):
			docID1 = pList[index1].split('->')[0]
			docID2 = allDocs[index2].split('->')[0]
		
			if (int(docID1) == int(docID2)):
				index1 += 1
				index2 += 1

			elif (int(docID1) < int(docID2)):
				index1 += 1

			else:
				ans.append(docID2)
				index2 += 1
		
		elif (index1 == len(pList) and index2 < len(allDocs)):
			docID2 = allDocs[index2].split('->')[0]
			ans.append(docID2)
			index2 += 1			

		elif (index1 < len(pList) and index2 == len(allDocs)):
			index1 += 1

	return ans


def usage():
	print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

dictFile = postingsFile = queriesFile = resultsFile = None
try:
	opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
	usage()
	sys.exit(2)

for command, arg in opts:
	if command == '-q':
		queriesFile = arg
	elif command == '-d':
		dictFile = arg
	elif command == '-p':
		postingsFile = arg
	elif command == '-o':
		resultsFile = arg
	else:
		assert False, "unhandled option"

if dictFile == None or postingsFile == None or queriesFile == None or resultsFile == None:
	usage()
	sys.exit(2)

inMemoryDict(dictFile)

start_time = datetime.datetime.now()
allQueries = inputQueries(queriesFile)
outputToPost = handleQueries(allQueries)
end_time = datetime.datetime.now()

outputResult(outputToPost, resultsFile)

delta = end_time - start_time
print("Time taken in miliseconds = " + str(delta.total_seconds() * 1000)) # Time in miliseconds


# print fetchPostings('&')
# print OpNOT(fetchPostings('&'))
# print OpAND(fetchPostings('shut'), fetchPostings('shutdown'))
# print OpOR(fetchPostings('shut'), fetchPostings('shutdown'))


fp.close()