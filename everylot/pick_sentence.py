
import csv, random

def generateRandomSentence(treeInfo):
	"""
	randomly selects a sentence appropriate to the species and health status
	  spc_latin, health, steward, spc_common
	"""

	pickedSentence = ""

	# pick a sentence
	with open('data/EveryTreeNYC_Phrases.csv', 'rU') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

		sentenceList = []
		for row in spamreader:
			sentenceList.append(row)

		random.shuffle(sentenceList)

		for row in sentenceList:
			if len(row[0]) > 0 and not row[0] == treeInfo['spc_latin']:
				continue
			if len(row[1]) > 0 and not row[1] == treeInfo['health']:
				continue
			if len(row[2]) > 0 and not row[2] == treeInfo['steward']:
				continue
			pickedSentence = row[3]
			break

	# do replacements
	return pickedSentence.format(**treeInfo)


	#coord = {'latitude': '37.24N', 'longitude': '-115.81W'}
	#'Coordinates: {latitude}, {longitude}'.format(**coord)	


if __name__ == "__main__":

	treeInfo = {'spc_latin' : "Quercus palustris", 'health' : "", 'steward' : "", "spc_common" : "My Tree Name"}
	print generateRandomSentence(treeInfo)
