import os
from datetime import date
from tkinter import *
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtextwindow
from language_code import get_language_code
from translate import *
from sentence import *
from autoread import *
from google_speech import Speech
from googletrans import Translator
import webbrowser
import urllib
import pickle # For saving and loading data
import subprocess # Used for text-to speak with Mac OS
import shlex # Used for text-to speak with Mac OS
import json # Used to read config file

# General settings
soundon = True # Pronounce word when looked up
macvoice = False # Use the text-to speak voice in Mac OS instead of Google
includearticle = True # Write out and pronounce article for nouns
uselemma = True # Use a lemmatizer to look up the lemma form of a word
startwindowsize = {'width': 1200, 'height': 700} # Set size of start window
mainwindowsize = {'width': 1200, 'height': 1000} # Set size of main window
considerexpressions = True # Allow expressions to be considered
alwaysshowactive = False # Always show active word in the side field (without translation)
savingon = True # Saves word lists when quitting
savestateon = True # Saves the current state (marked word or next word in queue)
usemessagebox = False # Uses message box to inform about saving, which has some bug on Mac OS
printwordlistsatstart = False # Prints word lists in terminal for debugging
newbrowsertab = True # Use a new browser tab the first time the browser is opened

# Fonts and colors
activecolor = 'orange'
learningcolor = '#fde367' #'yellow' macyellow:'#facd5a'
newcolor = '#cce6ff' #'#a3daf0'#'lightblue' macblue: '#69aff1'
knowncolor = 'lightgreen'

# Font
font = 'Avant Garde' #'Museo Sans Rounded', 'Bookman', 'Georgia', 'Helvetica', 'Avant Garde'

# Main window text settings
fontsize = 18
maintitlesize = 36
titlesize = 20
text_field_width = 60 # Text field width in number of characters
text_field_padx = 5
text_field_pady = 5

# Side field text settings
side_field_fonts = {'title': (font, 14),
							'field title background': 'darkgray',
							'field title text color': 'white',
							'word': (font, 20, 'bold'),
							'status': (font, 12, 'bold'),
							'translation': (font, 16),
							'google translate background': 'orange',
							'remark': (font, 14),
							'example': (font, 14, 'bold'),
							'example translation': (font, 14, 'italic')}
side_field_width = 30 # Side field width in number of characters
side_field_padx = 5
side_field_pady = 5









# General function for saving files
def save(obj, name, directory):
	# Create directory if it doesn't exist
	if not os.path.exists(directory):
		os.makedirs(directory)

	with open(directory + '/' + name + '.pkl', 'wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

# General function for loading files
def load(name, directory):
    with open(directory + '/' + name + '.pkl', 'rb') as f:
    	return pickle.load(f)

# Save to .txt file
def savetotxt(title, text, filename, directory):
	# Create directory if it doesn't exist
	if not os.path.exists(directory):
		os.makedirs(directory)

	file = open(directory + '/' + filename,'w') 
	file.write(title)
	file.write('\n')
	file.write(text) 
	file.close()

# Save word list
def savelist(obj, name):
	save(obj, name, language + '/' + 'wordlists')

# Load word list
def loadlist(name):
	obj = load(name, language + '/' + 'wordlists')
	return obj

# Save word list as txt file
def savelistastxt(obj, name):
	savetotxt(name, str(obj), name + '.txt', language + '/' + 'txtwordlists')

# Load all the word lists
def loadall():
	global knownwords
	global learningwords
	global ignoredwords
	global expressions
	global lastopenedfiles

	try:
		knownwords = loadlist("knownwords")
		if printwordlistsatstart:
			print('')
			print('known words:')
			print(knownwords)
	except:
		knownwords = {}
	try:
		learningwords = loadlist("learningwords")
		if printwordlistsatstart:
			print('')
			print('learning words:')
			print(learningwords)
	except:
		learningwords = {}
	try:
		ignoredwords = loadlist("ignoredwords")
		if printwordlistsatstart:
			print('')
			print('ignored words:')
			print(ignoredwords)
	except:
		ignoredwords = []
	if considerexpressions:
		try:
			expressions = loadlist("expressions")
			if printwordlistsatstart:
				print('')
				print('expressions:')
				print(expressions)
		except:
			expressions = {}

# Save all the word lists and current state
def saveall():
	global savestateon
	savelist(knownwords, "knownwords")
	savelist(learningwords, "learningwords")
	savelist(ignoredwords, "ignoredwords")
	if considerexpressions:
		savelist(expressions, "expressions")
	savelist(lastopenedfiles, 'lastopenedfiles')
	if savestateon:
		savestate()
	if not usemessagebox:
		print("The wordlists were saved!")
		print(f"Number of known words: {len(knownwords)}")

# Save all the word lists as txt files
def saveallastxt():
	savelistastxt(knownwords, "knownwords")
	savelistastxt(learningwords, "learningwords")
	savelistastxt(ignoredwords, "ignoredwords")
	savelistastxt(learningwords.keys(), "learningwordlist")
	if considerexpressions:
		savelistastxt(expressions, "expressions")

# Save current state, i.e., current marked word or first word in queue
def savestate():
	global active
	global openedtextpath
	state = None
	wordinfo = None
	if active:
		wordinfo = active
	elif moreinqueue():
		wordinfo = nextword()

	if wordinfo:
		state = str(wordinfo['line']) + '.' + str(wordinfo['wordnum'])

		with open(openedtextpath) as file:
			lines = file.readlines()

		with open(openedtextpath, "w") as file:
			file.write('#state ' + state + '\n')
			for line in lines:
				file.write(line)

# Invoke saveall
def savelists(event):
	global w
	global text
	saveall()
	if usemessagebox:
		ans = messagebox.showinfo("Saved", "The wordlists were saved!")
	deactivateexpressionmode(event)
	text.focus()
	unfocus()

# Invoke saveallastxt
def savelistsastxt(event):
	global w
	global text
	saveallastxt()
	if usemessagebox:
		ans = messagebox.showinfo("Saved", "The wordlists were saved as txt files!")
	else:
		print("The wordlists were saved as txt files!")
	deactivateexpressionmode(event)
	text.focus()
	unfocus()

# Handles active word when another word is clicked
def handleactivewordsatclick():
	global active
	global activelookedup
	global wordqueue
	global removedfromqueue
	if active and activelookedup:
		info = getwordinfo()
		addtolearning(active['word'], info)
		active['status'] = 'learning'
		removedfromqueue.append(active)
		markallinstances(active['word'], 'learning')
		unset_active_word()
	elif active:
		putbackinqueue(active)
		unset_active_word()

# Handles active expression when another word/expression is clicked
def handleactiveexpressionsatclick():
	global activeexpression
	global expressions
	if activeexpression:
		info = getexpressioninfo()
		addtoexpressions(activeexpression, info)
		markexpression(activeexpression['line'], activeexpression['startwordnum'], 'ordinary')
		markallexpressioninstances(activeexpression['expressionwords'], 'ordinary')
		activeexpression = None
		clearsidefield()

# Find old expression from tag
def findoldexpression(tag):
	global expressions
	startindex = text.tag_ranges(tag)[0]
	endindex = text.tag_ranges(tag)[1]
	lineandstartword = tag.split('.')

	line = int(lineandstartword[0][1:])
	wordnum1 = int(lineandstartword[1])
	expression = text.get(startindex,endindex)
	expressionwords = expression.translate(str.maketrans("""'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„""", "                                     "))
	expressionwords = expressionwords.lower().split()
	wordnum2 = wordnum1 + len(expressionwords)
	firstword = expressionwords[0]

	info = None

	# Search for expression
	if firstword in expressions:
		expressionslist = expressions[firstword]

		for expnum, exp in enumerate(expressionslist):
			expressionwords2 = exp['expressionwords']
			if len(expressionwords) == len(expressionwords2):
				if str(expressionwords) == str(expressionwords2):
					# Expressions are matching
					info = expressionslist[expnum]
					break
	return (expression, info, line, wordnum1, wordnum2)

# Handle mouse click in text field
def mouseclick(event):
	global active
	global activelookedup
	global activeexpression
	global expressionmode
	global selectedexpressionwords
	# For expression mode:
	if expressionmode:
		wordtags = text.tag_names(text.index(CURRENT))
		isoldexpression = False
		for tag in wordtags:
			if 'e' in tag:
				isoldexpression = True
		# If old expression
		if isoldexpression:
			selectedexpressionwords = [] # Cancel selection of new expression
			# Mark and save previous expression
			if activeexpression:
				handleactiveexpressionsatclick()
				activeexpression = False
			# Put back active word in queue and clear side field
			if active:
				if activelookedup:
					handleactivewordsatclick()
				else:
					putbackinqueue(active)
					unset_active_word()

			# Show old expression
			for tag in wordtags:
				if 'e' in tag:
					expressiontag = tag

			(expression, info, line, wordnum1, wordnum2) = findoldexpression(expressiontag)

			activeexpression = {'expressionwords' : info['expressionwords'], 'line' : line, 'startwordnum' : wordnum1, 'endwordnum' : wordnum2}
			markexpression(activeexpression['line'], activeexpression['startwordnum'], 'active')
			sidefieldshow(expression, info)
			printstatus('learning expression')

		# If new expression
		else: 
			# Choose tag for word, not for expression:
			for tag in wordtags:
				if 'e' not in tag and 'l' not in tag:
					wordtag = tag

			selectedexpressionwords.append(wordtag)
			# If two words are selected so that a new expression can be created
			if len(selectedexpressionwords) > 1:
				# Mark and save previous expression
				if activeexpression:
					handleactiveexpressionsatclick()
				activeexpression = False
				if active:
					if activelookedup:
						handleactivewordsatclick()
					else:
						putbackinqueue(active)
						unset_active_word()
				newexpression(selectedexpressionwords[0], selectedexpressionwords[1])
				selectedexpressionwords = [] # Restore selected expression words list
		return

	# If not in expression mode:
	if considerexpressions:
		wordtags = text.tag_names(text.index(CURRENT))
		# Choose tag for word, not for expression:
		for tag in wordtags:
			if 'e' not in tag and 'l' not in tag:
				wordtag = tag
				break
	else:
		wordtag = text.tag_names(text.index(CURRENT))[0]

	skip_to_word(wordtag)
	lookup(active['word'], active['status'])
	printstatus(active['status'])

# Skip to word with word tag `wordtag`
def skip_to_word(wordtag):
	global active
	global wordqueue
	global removedfromqueue

	lineandwordnum = wordtag.split(".")
	line = int(lineandwordnum[0])
	wordnum = int(lineandwordnum[1])
	wordstoremove = []
	# Handle active expression
	if activeexpression:
		handleactiveexpressionsatclick()
	# Handle active word
	if active:
		handleactivewordsatclick()

	# Mark all prev. new words as ignored and clicked word as active, 
	# and remove all previous words from queue
	clickedwordinqueue = False
	for worddict in wordqueue:
		if worddict['line'] < line or (worddict['line'] == line and worddict['wordnum'] < wordnum):
			if worddict['status'] == 'new':
				worddict['status'] = 'ignored'
				addtoignored(worddict['word'])
				markallinstances(worddict['word'],'ignored')
				wordstoremove.append(worddict)
			elif worddict['status'] == 'known':
				worddict['status'] = 'ignored'
				addtoignored(worddict['word'])
				markallinstances(worddict['word'],'known')
				wordstoremove.append(worddict)
			elif worddict['status'] == 'ignored':
				markallinstances(worddict['word'],'ignored')
				wordstoremove.append(worddict)
			elif worddict['status'] == 'learning':
				markallinstances(worddict['word'],'learning')
				wordstoremove.append(worddict)

		elif worddict['line'] == line and worddict['wordnum'] == wordnum:
			clickedwordinqueue = True
			wordstoremove.append(worddict)
			set_to_active(worddict)
			break

	if not clickedwordinqueue:
		for worddict in removedfromqueue:
			if worddict['line'] == line and worddict['wordnum'] == wordnum:
				set_to_active(worddict)
				break

	for word in wordstoremove:
		removedfromqueue.append(word)
		wordqueue.remove(word)

# Mark words
def markword(line, wordnum, status):
	if status == 'new':
		text.tag_config(str(line) + "." + str(wordnum), background=newcolor)
	elif status == 'learning':
		text.tag_config(str(line) + "." + str(wordnum), background=learningcolor)
	elif status == 'known':
		text.tag_config(str(line) + "." + str(wordnum), background="white")
	elif status == 'ignored':
		text.tag_config(str(line) + "." + str(wordnum), background="white")
	elif status == 'active':
		text.tag_config(str(line) + "." + str(wordnum), background=activecolor)

# Mark all instances of a word
def markallinstances(word, status):
	alltextwords = removedfromqueue + wordqueue
	for worddict in alltextwords:
		if word == worddict['word']:
			worddict['status'] = status
			line = worddict['line']
			wordnum = worddict['wordnum']
			markword(line,wordnum,status)

# Mark expression
def markexpression(line, startwordnum, status):
	global text

	istitleline = False
	linetags = text.tag_names(str(line) + '.0')
	for tag in linetags:
		if 'l' in tag:
			istitleline = True
	expressionfontsize = fontsize
	if line == 1 and istitleline:
		expressionfontsize = maintitlesize
	elif istitleline:
		expressionfontsize = titlesize

	if status == 'ordinary':
		if istitleline:
			fontsettings = (font, expressionfontsize, "underline", "bold")
		else:
			fontsettings = (font, expressionfontsize, "underline")
		text.tag_config("e" + str(line) + "." + str(startwordnum), font = fontsettings)
	elif status == 'none':
		if istitleline:
			fontsettings = (font, expressionfontsize, "bold")
		else:
			fontsettings = (font, expressionfontsize)
		text.tag_config("e" + str(line) + "." + str(startwordnum), font = fontsettings)
	elif status == 'active':
		if istitleline:
			fontsettings = (font, expressionfontsize, "underline", "italic", "bold")
		else:
			fontsettings = (font, expressionfontsize, "underline", "italic")
		text.tag_config("e" + str(line) + "." + str(startwordnum), font = fontsettings)

# Mark all instances of an expression
def markallexpressioninstances(expressionwords, status):
	global textwords
	global text

	firstword = expressionwords[0]
	for i in range(len(textwords)):
		linewords = textwords[i]
		for j, word in enumerate(linewords):
			if firstword == word and len(expressionwords) <= len(linewords)-j:
				if str(linewords[j:j+len(expressionwords)]) == str(expressionwords):
					if status == 'none':
						text.tag_delete("e" + str(i+1) + "." + str(j))
						markexpression(i+1, j, 'none')
					elif status == 'ordinary':
						text.tag_add('e' + str(i+1) + "." + str(j), wordstart[i][j], wordend[i][j+len(expressionwords)-1])
						markexpression(i+1, j, 'ordinary')

# Set word referred to by `worddict` as `active` and mark it
def set_to_active(worddict):
	global active
	global alwaysshowactive
	active = worddict
	markword(active['line'], active['wordnum'], 'active')
	if alwaysshowactive:
		show_active_word_in_sidefield()

# Unset active word and remove the viewing of it from the side field
def unset_active_word():
	global active
	global activelookedup
	markword(active['line'], active['wordnum'], active['status'])
	active = None
	activelookedup = False
	clearsidefield()

# Remove possible focus on text fields
def unfocus():
	w.focus()

# Get gender of noun from word type info
def getgender(wordtype):
	global language
	gender = ""
	if 'noun' in wordtype:
		if language == 'french' or language == 'italian' or language == 'german' or language == 'russian':
			if 'masculine' in wordtype:
				gender = gender + 'm'
			if 'feminine' in wordtype:
				gender = gender + 'f'
		if language == 'german' or language == 'russian':
			if 'neuter' in wordtype:
				gender = gender + 'n'
	return gender

# Returns the article of a word (or an empty string if article is not unique)
def getarticle(word, gender, language):
	if language == 'french':
		vowels = 'aeiouyáéèéœôù'
		# If first letter isn't a vowel
		if word[0] not in vowels:
			if gender == 'm':
				return 'le'
			elif gender == 'f':
				return 'la'
			else:
				return ''
		# If first letter is a vowel
		else:
			if gender == 'm':
				return 'un'
			elif gender == 'f':
				return 'une'
			else:
				return ''
	elif language == 'german':
		if gender == 'm':
			return 'der'
		elif gender == 'f':
			return 'die'
		elif gender == 'n':
			return 'das'
		else:
			return ''
	elif language == 'italian': # Remains to be implemented
		vowels = 'aeiouy'
		consonants = 'bcdfghjklmnpqrstvwxz'
		if gender == 'm':
			if len(word) > 0:
				if word[0] in ['x','y','z']:
					return 'lo'
				if word[0] in vowels:
					return 'un'
			if len(word) > 1:
				if word[0:2] in ['gn', 'pn', 'ps']:
					return 'lo'
				if word[0] == 's':
					if word[1] in consonants:
						return 'lo'
			return 'il'
		elif gender == 'f':
			if len(word) > 0:
				if word[0] in vowels:
					return "un'"
				else:
					return 'la'
		else:
			return ''
	else:
		return ''

# Color word in side field according to gender
def gendercolor(gender):
	global language
	global textword
	if language == 'french' or language == 'italian':
		if 'm' in gender and 'f' not in gender:
			textword.configure(fg="blue")
		elif 'f' in gender and 'm' not in gender:
			textword.configure(fg="red")
		else:
			textword.configure(fg="black")
	if language == 'german' or language == 'russian':
		verb = False
		word = textword.get('1.0','end')
		if ',' in word:
			verb = True
		if not verb:
			if 'm' in gender and 'f' not in gender and 'n' not in gender:
				textword.configure(fg="blue")
			elif 'f' in gender and 'm' not in gender and 'n' not in gender:
				textword.configure(fg="red")
			elif 'n' in gender and 'm' not in gender and 'f' not in gender:
				textword.configure(fg="green")
			else:
				textword.configure(fg="black")
		else:
			nounandverb = word.split(',')
			nounlength = len(nounandverb[0])
			textword.configure(fg="black")
			textword.tag_add("noun", "1.0", "1." + str(nounlength))
			if 'm' in gender and 'f' not in gender and 'n' not in gender:
				textword.tag_configure("noun", foreground="blue")
			elif 'f' in gender and 'm' not in gender and 'n' not in gender:
				textword.tag_configure("noun", foreground="red")
			elif 'n' in gender and 'm' not in gender and 'f' not in gender:
				textword.tag_configure("noun", foreground="green")
			else:
				textword.tag_configure("noun", foreground="black")
			

# Insert example sentence
def insertsentence(sentence, sentencetrans):
	textexample.delete("1.0", "end")
	textexample.insert("1.0", sentence + "\n")
	textexample.insert("3.0", sentencetrans)
	textexample.tag_add("sentence", "1.0", "1." + str(len(sentence)))
	textexample.tag_config("sentence", font = side_field_fonts['example'])

# Insert formated translation into translation field
def inserttranslation(info):
	# Define tags for formatting
	(translation_font, translation_font_size) = side_field_fonts['translation']
	texttrans.tag_configure("word", font=(translation_font, translation_font_size, "bold"))
	texttrans.tag_configure("normal", font=(translation_font, translation_font_size))
	texttrans.tag_configure("parenthesis", font=(translation_font, translation_font_size))
	texttrans.tag_configure("type_and_gender", font=(translation_font, translation_font_size, "italic"))
	texttrans.tag_configure("google_translate", font=(translation_font, translation_font_size),
						 background=side_field_fonts['google translate background'])
	texttrans.tag_configure("definitions", font=(translation_font, translation_font_size), lmargin1=20, spacing1=5)
	texttrans.tag_configure("synonyms", font=(translation_font, translation_font_size-2, "bold"), lmargin1=40, spacing1=2)

	for i, item in enumerate(info):
		if 'source' in item and item['source'] == 'Google Translate':
			if 'definitions' in item:
				definition = item['definitions'][0]
				if 'definition' in definition:
					def_def = definition['definition'] 
					texttrans.insert(END, def_def, 'google_translate')
					texttrans.insert(END, '\n\n', 'normal')
		else: # If source is Wiktionary
			if 'word' in item:
				texttrans.insert(END, item['word'], 'word')
			if 'part_of_speech' in item:
				texttrans.insert(END, ' (', 'parenthesis')
				texttrans.insert(END, item['part_of_speech'], 'type_and_gender')
				if 'gender' in item:
					texttrans.insert(END, ' — ' + item['gender'], 'type_and_gender')
				texttrans.insert(END, ')', 'parenthesis')
				if 'qualifier' in item:
					texttrans.insert(END, ' (', 'parenthesis')
					texttrans.insert(END, item['qualifier'], 'type_and_gender')
					texttrans.insert(END, ')', 'parenthesis')

			if 'definitions' in item:
				for j, definition in enumerate(item['definitions']):
					if 'definition' in definition:
						def_def = definition['definition']
						texttrans.insert(END, f'\n{j+1}. {def_def}', 'definitions')
					if 'synonyms' in definition:
						synonyms = definition['synonyms']
						texttrans.insert(END, f'\n≈ {synonyms}', 'synonyms')
					if 'antonyms' in definition:
						antonyms = definition['antonyms']
						texttrans.insert(END, f'\n≠ {antonyms}', 'synonyms')
			if i < len(info)-1:
				texttrans.insert(END, '\n\n', 'normal')

# View in side field
def sidefieldshow(word, info):
	global language
	global infoforshowedword
	infoforshowedword = info
	trans = info['trans']
	wordtype = None
	if 'wordtype' in info:
		wordtype = info['wordtype']
	if not wordtype == 'expression':
		equaltodictword = False
		# The word is a variant of some other word if there are lemmas
		word_is_variant = 'lemmas' in info

	# Write german nouns with initial capital letter and article
	if language == 'german' and 'noun' in wordtype and len(word) > 0:
		if not 'verb' in wordtype:
			word = word[0].upper() + word[1:]
		else:
			word = word[0].upper() + word[1:] + ', ' + word

	has_unique_gender = False
	if 'gender' in info:
		gender = info['gender']
		if len(gender) == 1:
			has_unique_gender = True

	if not wordtype == 'expression':
		# Write nouns with article if in dictionary form
		if has_unique_gender:
			if includearticle and len(word) > 0 and not word_is_variant:
				article = getarticle(word, gender, language)
				if language == 'italian':
					if len(article) > 0:
						if not article == "un'":
							word = article + ' ' + word
						else:
							word = article + word
				else:
					if len(article) > 0:
						word = article + ' ' + word

	editsidefield()
	textword.insert("1.0", word)
	if has_unique_gender:
		gendercolor(gender)
	else:
		textword.configure(fg="black")
	if not wordtype == 'expression':
		inserttranslation(trans)
	else:
		texttrans.tag_configure("expression_trans",
						  font=side_field_fonts['translation'],
						  background=side_field_fonts['google translate background'])

		texttrans.insert("1.0", trans, "expression_trans")
	has_text_in_remark = False
	if 'remark' in info:
		textremark.insert(END, info['remark'])
		has_text_in_remark = True
	if 'sentence' in info and 'sentencetrans' in info:
		insertsentence(info['sentence'], info['sentencetrans'])
	freezesidefield()

	# Pronunciation
	if soundon:
		pronounce(word, language)

# Show active word and its status in the side field, but no other information
def show_active_word_in_sidefield():
	if active:
		clearsidefield()
		editsidefield()
		textword.insert('1.0', active['word'])
		textword.configure(fg='black')
		freezesidefield()
		printstatus(active['status'])

# Add info in side field
def lookup(word, status):
	global textword
	global activelookedup
	if status == 'new' or status == 'ignored':
		info = legilotranslator.get_info(word)
		sentence = ""
		(sentence, sentencetrans) = getfirstsentence(word, language)
		if len(sentence) > 0:
			info['sentence'] = sentence
			info['sentencetrans'] = sentencetrans
	elif status == 'learning':
		info = learningwords[word]
	else: # status == 'known'
		info = knownwords[word]

	sidefieldshow(word, info)
	activelookedup = True

# Enable input of text in sidebar
def editsidefield():
	textword.configure(state="normal")
	texttrans.configure(state="normal")
	textremark.configure(state="normal")
	textexample.configure(state="normal")

# Disable input of text in sidebar
def freezesidefield():
	textword.configure(state="disabled")
	texttrans.configure(state="disabled")
	textremark.configure(state="disabled")
	textexample.configure(state="disabled")

def removenewlineatend(string):
	if len(string) > 0:
		if string[-1:] == '\n':
			string = string[:-1]
	return string

# Collect word info from side field and infoforshowedword variable
def getwordinfo():
	global infoforshowedword
	editsidefield()
	wordtype = None
	if 'wordtype' in infoforshowedword:
		wordtype = infoforshowedword['wordtype']
		wordtype = removenewlineatend(wordtype)
	remark = textremark.get("1.0",END)
	remark = removenewlineatend(remark)
	sentence = textexample.get("1.0","1.end")
	sentence = removenewlineatend(sentence)
	sentencetrans = textexample.get("2.0","2.end")
	sentencetrans = removenewlineatend(sentencetrans)
	if wordtype == 'expression':
		trans = texttrans.get("1.0",END)
		trans = removenewlineatend(trans)
		info = {'trans' : trans, 'wordtype' : wordtype, 'remark' : remark,
		  		'sentence' : sentence, 'sentencetrans' : sentencetrans}
	else:
		info = infoforshowedword
		info['remark'] = remark
		info['sentence'] = sentence
		info['sentencetrans'] = sentencetrans

	freezesidefield()
	return info

def getexpressioninfo():
	editsidefield()
	expression = textword.get("1.0",END)
	trans = texttrans.get("1.0",END)
	remark = textremark.get("1.0",END)
	sentence = '' #textexample.get("1.0","1.end")
	sentencetrans = '' #textexample.get("3.0","3.end")

	# Remove newline at end
	expression = removenewlineatend(expression)
	trans = removenewlineatend(trans)
	remark = removenewlineatend(remark)
	sentence = removenewlineatend(sentence)
	sentencetrans = removenewlineatend(sentencetrans)

	expressionwords = expression.translate(str.maketrans("""'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„""", "                                     "))
	expressionwords = expressionwords.lower().split()

	info = {'expressionwords': expressionwords, 'word' : expression, 'trans' : trans, 'wordtype' : 'expression', 'remark' : remark, 'sentence' : sentence, 'sentencetrans' : sentencetrans}
	freezesidefield()
	return info

# Add word to learning words
def addtolearning(word, info):
	# Remove from ignored or known words
	if word in ignoredwords:
		ignoredwords.remove(word)
	elif word in knownwords:
		del knownwords[word]
	learningwords[word] = info

# Add to ignored words
def addtoignored(word):
	ignoredwords.append(word)

# Add word to known words
def addtoknown(word, info):
	# Remove from ignored or learning words
	if word in ignoredwords:
		ignoredwords.remove(word)
	elif word in learningwords:
		del learningwords[word]
	knownwords[word] = info

# Add expression to expressions
def addtoexpressions(expression, info):
	i = expression['line']-1
	wordnum1 = expression['startwordnum']
	expressionwords = []
	firstword = textwords[i][wordnum1]

	# Add expression to expressions
	if firstword in expressions:
		expressions[firstword].append(info)
	else:
		expressions[firstword] = [info]

# Empty the side field
def clearsidefield():
	global textstatus
	global textword
	global textremark
	global texttrans
	global textexampletitle
	global textexample

	textstatus.configure(state="normal")
	textstatus.delete("1.0", "end")
	textstatus.configure(bg="white")
	textstatus.configure(state="disabled")

	textword.configure(state="normal")
	textword.delete('1.0', "end")
	textword.configure(state="disabled")

	textremark.configure(state="normal")
	textremark.delete('1.0', "end")
	textremark.configure(state="disabled")

	texttrans.configure(state="normal")
	texttrans.delete('1.0', "end")
	texttrans.configure(state="disabled")

	textexample.configure(state="normal")
	textexample.delete('1.0', "end")
	textexample.configure(state="disabled")

# Check if more words in the queue
def moreinqueue():
	global wordqueue
	ans = False
	for i in range(len(wordqueue)):
		word = wordqueue[i]
		if not (word['status'] == 'ignored' or word['status'] == 'known'):
			ans = True
			break
	return ans

# Return next word from queue
def nextword():
	global wordqueue
	nextword = None
	for i in range(len(wordqueue)):	
		word = wordqueue.pop(0)
		if not (word['status'] == 'ignored' or word['status'] == 'known'):
			nextword = word
			break
	return nextword

# Put back a word in the word queue
def putbackinqueue(word):
	global wordqueue
	wordqueue.insert(0,word)

# Put back a word in the word queue sorted according to word index
def putbackinqueuesorted(word):
	global wordqueue
	insertindex = None
	wordindex = word['index']
	for i, queueword in enumerate(wordqueue):
		if queueword['index'] > wordindex:
			insertindex = i
			break
	wordqueue.insert(insertindex,word)

# Checks if the text word is already in the queue based on its index
def wordinqueue(wordindex):
	global wordqueue
	ans = False
	for word in wordqueue:
		if word['index'] == wordindex:
			ans = True
			break
	return ans

# Show word status in side field
def printstatus(status):
	textstatus.configure(state="normal")
	if status == 'ignored':
		status = 'new'
	textstatus.insert("1.0", status) # Insert text at line i and character 0
	if status == 'new' or status == 'ignored':
		textstatus.configure(bg=newcolor)
	elif status == 'learning':
		textstatus.configure(bg=learningcolor)
	elif status == 'known':
		textstatus.configure(bg=knowncolor)
	elif status == 'learning expression':
		textstatus.configure(bg=learningcolor)
	elif status == 'new expression':
		textstatus.configure(bg=newcolor)
	else:
		textstatus.configure(bg="white")
	textstatus.configure(state="disabled")

# Center window on the screen
def center_window(window, width, height):
	# Get the screen width and height
	screen_width = window.winfo_screenwidth()
	screen_height = window.winfo_screenheight()
	
	# Calculate the position to center the window
	x = (screen_width // 2) - (width // 2)
	y = (screen_height // 2) - (height // 2)
	
	# Set the position of the window
	window.geometry(f'{width}x{height}+{x}+{y}')

# When pressing space
def space(event):
	global active
	global activelookedup
	global wordqueue
	global removedfromqueue

	if not editing:
		unfocus()

		if activeexpression:
			handleactiveexpressionsatclick()

		if active and not activelookedup:
			if active['status'] == 'learning':
				removedfromqueue.append(active)
				unset_active_word()
				if moreinqueue():
					new_active = nextword()
					set_to_active(new_active)
			else: # active['status'] == 'new'
				ignore(event)
		elif active:
			info = getwordinfo()
			active['status'] = 'learning'
			addtolearning(active['word'], info)
			removedfromqueue.append(active)
			markallinstances(active['word'], 'learning')
			unset_active_word()
			if moreinqueue():
				new_active = nextword()
				set_to_active(new_active)
		else:
			if moreinqueue():
				new_active = nextword()
				set_to_active(new_active)
				activelookedup = False


def enter(event):
	global active
	global activelookedup
	global wordqueue
	global removedfromqueue
	global editing
	if not editing:
		if active and activelookedup:
				info = getwordinfo()
				active['status'] = 'learning'
				addtolearning(active['word'], info)
				removedfromqueue.append(active)
				markallinstances(active['word'], 'learning')
				unset_active_word()
				if moreinqueue():
					new_active = nextword()
					set_to_active(new_active)
		elif active:
			lookup(active['word'], active['status'])
			printstatus(active['status'])
		else:
			if moreinqueue():
				new_active = nextword()
				set_to_active(new_active)
				activelookedup = False

def ignore(event):
	global active
	global activelookedup
	global wordqueue
	global removedfromqueue
	global activeexpression
	global expressions

	if active and not editing:
		word = active['word']
		status = active['status']
		active['status'] = 'ignored'
		addtoignored(word)

		# Remove word from kown words and learning words
		if status == 'known':
			del knownwords[word]
		elif status == 'learning':
			del learningwords[word]

		#Remove all instances of word in queue
		removedfromqueue.append(active)
		wordstoremove = []
		for worddict in wordqueue:
			if worddict['word'] == word:
				wordstoremove.append(worddict)

		for word in wordstoremove:
			removedfromqueue.append(word)
			wordqueue.remove(word)

		markallinstances(active['word'], 'ignored')
		unset_active_word()
		if moreinqueue():
			new_active = nextword()
			set_to_active(new_active)
			activelookedup = False

	if activeexpression and not editing:
		markallexpressioninstances(activeexpression['expressionwords'], 'none')
		expressionwords = activeexpression['expressionwords']
		firstword = expressionwords[0]
		if firstword in expressions:
			expressionswithsamefirstword = expressions[firstword]
			for expnum, exp in enumerate(expressionswithsamefirstword):
				if str(exp['expressionwords']) == str(expressionwords):
					del expressionswithsamefirstword[expnum]
					if len(expressionswithsamefirstword) == 0:
						expressions.pop(firstword)
		activeexpression = False
		clearsidefield()

def known(event):
	global active
	global activelookedup
	global wordqueue
	global removedfromqueue

	if active and not editing:
		status = active['status']
		# Allow only words that have been looked up (now or before) to become known
		if status == 'learning' or activelookedup:
			word = active['word']
			info = getwordinfo()
			active['status'] = 'known'
			addtoknown(word, info)

			#Remove all instances of word in queue
			removedfromqueue.append(active)
			wordstoremove = []
			for worddict in wordqueue:
				if worddict['word'] == word:
					wordstoremove.append(worddict)

			for word in wordstoremove:
				removedfromqueue.append(word)
				wordqueue.remove(word)

			markallinstances(active['word'], 'known')
			unset_active_word()
			if moreinqueue():
				new_active = nextword()
				set_to_active(new_active)
				activelookedup = False

	if activeexpression and not editing:
		ignore(event)

# Put back all learning words in the queue to go through them from start
def iteratelearningwords(event):
	global wordqueue
	global removedfromqueue
	global editing
	if not editing:
		handleactiveexpressionsatclick()
		handleactivewordsatclick()
		removefromremoved = []
		for i, word in enumerate(removedfromqueue):
			if word['status'] == 'learning':
				if not wordinqueue(word['index']):
					putbackinqueuesorted(word)
				removefromremoved.append(word)
		for word in removefromremoved:
			removedfromqueue.remove(word)

def pronounce(word, language):
	global active
	global activelookedup
	global textword
	global lastpronounced
	global macvoice

	# Mac OS text-to-speak
	if macvoice:
		word = word.replace("'","´")
		voice = None
		if language == 'croatian':
			voice = 'Lana'
		elif language == 'french':
			voice = 'Thomas'
		elif language == 'german':
			voice = 'Petra'
		elif language == 'italian':
			voice = 'Alice'
		elif language == 'russian':
			voice = 'Milena'
		elif language == 'spanish':
			voice = 'Mónica'
		elif language == 'swedish':
			voice = 'Alva'
		
		if voice:
			if active and activelookedup: # Pronounce nouns with article
				sidefieldword = textword.get('1.0','end')
				sidefieldword = sidefieldword.split(',')
				sidefieldword = sidefieldword[0]
				sidefieldword = sidefieldword.replace("'","´")
				subprocess.call(shlex.split('say -v ' + voice + ' ' + str(sidefieldword)))
			else:
				subprocess.call(shlex.split('say -v ' + voice + ' ' + str(word)))
		
	# Google
	else:
		if lastpronounced:
			if lastpronounced['word'] == word:
				sound = lastpronounced['sound']
			elif active and activelookedup:
				sidefieldword = textword.get('1.0','end')
				sidefieldword = sidefieldword.split(',')
				sidefieldword = sidefieldword[0]
				sound = Speech(sidefieldword, get_language_code(language))
				lastpronounced = {'word': word, 'sound': sound}
			else:
				sound = Speech(word, get_language_code(language))
		else:
			if active and activelookedup:
				sidefieldword = textword.get('1.0','end')
				sidefieldword = sidefieldword.split(',')
				sidefieldword = sidefieldword[0]
				sound = Speech(sidefieldword, get_language_code(language))
				lastpronounced = {'word': word, 'sound': sound}
			else:
				sound = Speech(word, get_language_code(language))
		sound.play()

def pronounceactiveword(event):
	global active
	global textword
	global language
	if active and not editing:
		pronounce(active['word'], language)

	if activeexpression and not editing:
		pronounce(textword.get('1.0','end'), language)

def pronouncenext(event):
	space(event)
	pronounceactiveword(event)

def changeremark(event):
	global editing
	if not editing:
		editing = True
		textremark.configure(state="normal")
		textremark.focus()

def changesentence(event):
	global editing
	if not editing:
		editing = True
		#textremark.configure(state="normal")
		#textremark.focus()

def opendictionary(event):
	global active
	global editing
	global language
	if active and not editing:
		word = active["word"]
		if not language == 'russian':
			link = "https://www.collinsdictionary.com/dictionary/" + language + "-english/" + word
			link = urllib.parse.quote(link, safe='/:')
			#webbrowser.get('chrome').open(link)
			openurlinoldtab(link)
		else: # language == 'russian'
			if language == 'russian':
				word = removerussianaccents(word)
			link = "https://en.openrussian.org/ru/" + word
			link = urllib.parse.quote(link, safe='/:')
			openurlinoldtab(link)
	if activeexpression and not editing:
		expressionwords = activeexpression['expressionwords']
		expressionstr = ''
		for word in expressionwords:
			expressionstr = expressionstr + word + '-'
		expressionstr = expressionstr[0:-1] # Remove last +
		link = "https://www.collinsdictionary.com/dictionary/" + language + "-english/" + expressionstr
		openurlinoldtab(link)

def openverbconjugation(event):
	global active
	global editing
	if active and not editing:
		word = active["word"]
		if language == 'french':
			link = "https://leconjugueur.lefigaro.fr/conjugaison/verbe/" + word
		elif language == 'german':
			link = "https://www.verbformen.de/konjugation/?w=" + word
		elif language == 'italian':
			link = "https://www.italian-verbs.com/italian-verbs/conjugation.php?parola=" + word
		elif language == 'russian':
			word = removerussianaccents(word)
			link = 'https://conjugator.reverso.net/conjugation-russian-verb-' + word + '.html'
		else:
			link = "http://www.google.se"
		#link = urllib.parse.quote(link, safe='/:')
		#webbrowser.get('chrome').open(link)
		openurlinoldtab(link)

def openwiktionary(event):
	global active
	global editing
	if active and not editing:
		word = active["word"]
		if language == 'russian':
			word = removerussianaccents(word)
		link = "https://en.wiktionary.org/wiki/" + word + "#" + language[0].upper() + language[1:]
		#link = urllib.parse.quote(link, safe='/:')
		#webbrowser.get('chrome').open(link)
		openurlinoldtab(link)
	if activeexpression and not editing:
		expressionwords = activeexpression['expressionwords']
		expressionstr = ''
		for word in expressionwords:
			expressionstr = expressionstr + word + '_'
		expressionstr = expressionstr[0:-1] # Remove last +
		link = "https://en.wiktionary.org/wiki/" + expressionstr + "#" + language[0].upper() + language[1:]
		openurlinoldtab(link)

def opencontextreverso(event):
	global active
	global editing
	if active and not editing:
		word = active["word"]
		link = "https://context.reverso.net/translation/" + language + "-english/" + word
		openurlinoldtab(link)
	if activeexpression and not editing:
		expressionwords = activeexpression['expressionwords']
		expressionstr = ''
		for word in expressionwords:
			expressionstr = expressionstr + word + '+'
		expressionstr = expressionstr[0:-1] # Remove last +
		link = "https://context.reverso.net/translation/" + language + "-english/" + expressionstr
		openurlinoldtab(link)

def opengoogle(event):
	global active
	global editing
	if active and not editing:
		word = active["word"]
		link = "https://www.google.com/search?q=" + word
		#link = urllib.parse.quote(link, safe='/:')
		#webbrowser.get('chrome').open(link)
		openurlinoldtab(link)
	if activeexpression and not editing:
		expressionwords = activeexpression['expressionwords']
		expressionstr = ''
		for word in expressionwords:
			expressionstr = expressionstr + word + '+'
		expressionstr = expressionstr[0:-1] # Remove last +
		link = "https://www.google.com/search?q=" + expressionstr
		openurlinoldtab(link)

def opengoogleimages(event):
	global active
	global editing
	if active and not editing:
		word = active["word"]
		link = "https://www.google.com/search?q=" + word + "&tbm=isch"
		#link = urllib.parse.quote(link, safe='/:')
		#webbrowser.get('chrome').open(link)
		openurlinoldtab(link)
	if activeexpression and not editing:
		expressionwords = activeexpression['expressionwords']
		expressionstr = ''
		for word in expressionwords:
			expressionstr = expressionstr + word + '+'
		expressionstr = expressionstr[0:-1] # Remove last +
		link = "https://www.google.com/search?q=" + expressionstr + "&tbm=isch"
		openurlinoldtab(link)

def openwikipedia(event):
	global active
	global editing
	if active and not editing:
		word = active["word"]
		link = "https://en.wikipedia.org/wiki/" + word
		#link = urllib.parse.quote(link, safe='/:')
		#webbrowser.get('chrome').open(link)
		openurlinoldtab(link)
	if activeexpression and not editing:
		expressionwords = activeexpression['expressionwords']
		expressionstr = ''
		for word in expressionwords:
			expressionstr = expressionstr + word + '_'
		expressionstr = expressionstr[0:-1] # Remove last +
		link = "https://en.wikipedia.org/wiki/" + expressionstr
		openurlinoldtab(link)

def openurlinoldtab(url):
	global newbrowsertab
	newbrowsertab = False # This was added when the function with Chrome stopped working
	if not newbrowsertab:
		script = '''tell application "Google Chrome"
	                    tell front window
	                        set URL of active tab to "%s"
	                    end tell
	                end tell ''' % url.replace('"', '%22')
		osapipe = os.popen("osascript", "w")
		if osapipe is None:
			return False

		osapipe.write(script)
		rc = osapipe.close()
		return not rc
	else:
		webbrowser.get('chrome').open(url)
		newbrowsertab = False

remarkwithoutswedish = False
lastwordtranslatedtoswedish = ''
def addswedishtrans(event):
	global textword
	global texttrans
	global textremark
	global remarkwithoutswedish
	global lastwordtranslatedtoswedish
	global active
	global activeexpression
	global editing

	if (active or activeexpression) and not editing:
		engtrans = texttrans.get('1.0','end')
		word = textword.get('1.0','end')
		editsidefield()
		# Remove translation if already added
		if remarkwithoutswedish and word == lastwordtranslatedtoswedish:
			textremark.delete('1.0','end')
			textremark.insert('1.0',remarkwithoutswedish)
			remarkwithoutswedish = False
		# Otherwise, get the Swedish translation
		else:
			remarkwithoutswedish = textremark.get('1.0','end')
			textremark.tag_configure('swedish_header', font=(font, side_field_fonts['remark'][1], 'italic'))
			if len(remarkwithoutswedish) > 1:
				textremark.insert('end', '\n\n' + 'Swedish translations:', 'swedish_header')
				textremark.insert('end', '\n\n' + translatetoswedish(word, engtrans))
			else:
				textremark.insert('end', 'Swedish translations:', 'swedish_header')
				textremark.insert('end', '\n\n' + translatetoswedish(word, engtrans))
			lastwordtranslatedtoswedish = word
		freezesidefield()

def quitprogram():
	if usemessagebox:
		if savingon:
			ans = messagebox.askyesnocancel("Quit", "Do you want to save the changes?")
		else:
			ans = False
	elif savingon:
		ans = True
	if ans is not None:
		if ans:
			saveall()
		w.destroy()
		start()

def quitwithoutsaving(event):
	w.destroy()
	print('Quitted without saving progress.')
	start()

# Find word from index
def wordfromindex(index):
	lineandchar = index.split(".")
	i = int(lineandchar[0])-1
	character = int(lineandchar[1])
	endindex = None
	wordnum = None
	line = None
	for j in wordend[i]: # Compare index with word end indices to find the word's end index
		if int((j.split("."))[1]) > int((index.split("."))[1]):
			endindex = j
			break
	if endindex:
		j = wordend[i].index(endindex)
		# Check that index is larger than or equal to the word's start index
		if int((wordstart[i][j].split("."))[1]) <= int((index.split("."))[1]):
			line = i+1
			wordnum = j
	return line, wordnum

# If a word is clicked
def clickedword(event):
	if considerexpressions:
		wordtags = text.tag_names(text.index(CURRENT))
		# Choose tag for word, not for expression:
		for tag in wordtags:
			if 'e' not in tag and 'l' not in tag:
				wordtag = tag
	else:
		wordtag = text.tag_names(text.index(CURRENT))[0]

# Pressing enter in info field to stop editing
def enterininfofield(event):
	global editing
	global textword
	global wordtype
	unfocus()
	editing = False
	freezesidefield()
	return 'break'

# Pressing shift + enter in info field to get new line
def newline1(event):
	global texttrans
	index = texttrans.index(INSERT)
	texttrans.insert(index,"\n")
	return 'break'
def newline2(event):
	global textremark
	index = textremark.index(INSERT)
	textremark.insert(index,"\n")
	return 'break'

# Select example sentence
sentenceword = "" # Last word for which example sentences were downloaded
sentencelist = [] # List with last downloaded collection of example sentences (for one word)
sentencetranslist = [] # Corresponding translations to the sentences above
sentencechoice = 1 # Which of the sentences is chosen
def selectsentence(event):
	global sentenceword
	global sentencelist
	global sentencetranslist
	global sentencechoice
	global text
	global editing
	global language
	if event.char in ['1','2','3','4','5','6','7','8','9','0']:
		n = int(event.char) # Sentence number
		sentencechoice = n
	else:
		sentencechoice += 1
		if sentencechoice > 9:
			sentencechoice = 0
		n = sentencechoice

	# If active word
	if active and not editing:
		# Get example sentences for word if not already downloaded
		if not sentenceword == active['word']:
			(sentencelist, sentencetranslist) = getsentences(active['word'], language, 7)
		if n > 0 and n < 8: # Choose example sentence from web
			sentence = sentencelist[n-1]
			sentencetrans = sentencetranslist[n-1]
		elif n == 0: # Remove example sentence
			sentence = ''
			sentencetrans = ''
		else: # n == 8 or n == 9: Take text sentence as example sentence
			line = active['line']
			wordnum = active['wordnum']
			tag = str(line) + "." + str(wordnum)
			wordstart = int(str(text.tag_ranges(tag)[0]).split('.')[1])
			wordend = int(str(text.tag_ranges(tag)[1]).split('.')[1])
			textline = text.get(str(line)+".0", str(line)+".end")
			sentencestart = 0
			sentenceend = len(textline)
			for sign in ['.', '?', '!']:
				i = textline[:wordstart].rfind(sign)
				if i > sentencestart:
					sentencestart = i
				j = textline.find(sign, wordend)
				if j >= 0 and j < sentenceend:
					sentenceend = j
			# Include end sign if available
			if len(textline) > sentenceend:
				sentenceend += 1
			sentence = textline[sentencestart:sentenceend]
			initialsigntoremove = True
			signs = [' ','.','!','?']
			while initialsigntoremove and len(sentence) > 0:
				allsignschecked = False
				for signnbr, sign in enumerate(signs):
					if sign == sentence[0]:
						sentence = sentence[1:]
						break
					if signnbr == len(signs)-1:
						allsignschecked = True
				if allsignschecked:
					initialsigntoremove = False
			# Get translation from Google
			if n == 8:
				translator = Translator()
				sentencetrans = translator.translate(sentence, src=get_language_code(language), dest='en').text
			# Don't use a translation
			else: # n == 9
				sentencetrans = ""

		editsidefield()
		insertsentence(sentence, sentencetrans)
		freezesidefield()

# Get Swedish translations from string of english translations
includetransoforiginalword = True
def translatetoswedish(word, trans):
	global includetransoforiginalword
	translator = Translator()
	# Remove new line from end of word
	if len(word) > 0:
		if word[-1] == '\n':
			word = word[:-1]
	translationstring = ""
	# Translate the original word directly to Swedish
	if includetransoforiginalword:
		swedishtrans = translator.translate(word, src=get_language_code(language), dest='sv').text
		translationstring = word + ' = ' + swedishtrans + '\n\n'
	# Remove new line from end of translations string
	if len(trans) > 0:
		if trans[-1] == '\n':
			trans = trans[:-1]
	# Translate the English translations to Swedish
	translationstring += translator.translate(trans, src='en', dest='sv').text

	return translationstring

def activateexpressionmode(event):
	global editing
	global text
	global expressionmode
	global considerexpressionmode
	global expressionclickbinding

	if considerexpressions and not editing:
		global expressionmode
		expressionmode = True
		text.config(cursor='dot')
		selectedexpressionwords = []

def deactivateexpressionmode(event):
	global editing
	global text
	global expressionmode
	global considerexpressionmode
	global expressionclickbinding
	global selectedexpressionwords

	if considerexpressions and not editing:
		global expressionmode
		text.config(cursor='arrow')
		selectedexpressionwords = []
		expressionmode = False

def newexpression(wordtag1, wordtag2):
	global active
	global activelookedup
	global activeexpression

	lineandwordnum1 = wordtag1.split(".")
	lineandwordnum2 = wordtag2.split(".")
	wordnum1 = lineandwordnum1[1]
	wordnum2 = lineandwordnum2[1]

	# Sort words in right order
	if int(wordnum1) > int(wordnum2):
		temp = lineandwordnum1
		lineandwordnum1 = lineandwordnum2
		lineandwordnum2 = temp
		temp = wordtag1
		wordtag1 = wordtag2
		wordtag2 = temp
	line = int(lineandwordnum1[0])

	firstwordstart = str(text.tag_ranges(wordtag1)[0])
	lastwordend = str(text.tag_ranges(wordtag2)[1])
	expression = text.get(firstwordstart, lastwordend)

	line1 = int(lineandwordnum1[0])
	wordnum1 = int(lineandwordnum1[1])
	line2 = int(lineandwordnum2[0])
	wordnum2 = int(lineandwordnum2[1])
	if line1 == line2:
		linewords = textwords[line1-1]
		expressionwords = []
		for wordnum in range(min(wordnum1,wordnum2), max(wordnum1,wordnum2)+1):
			expressionwords.append(linewords[wordnum])

		translator = Translator()
		trans = translator.translate(expression, src=get_language_code(language), dest='en').text
		info = {'expressionwords': expressionwords, 'word' : expression, 'trans' : trans, 'wordtype' : 'expression'}
		(sentence, sentencetrans) = getfirstsentence(expression, language)
		if len(sentence) > 0:
			info['sentence'] = sentence
			info['sentencetrans'] = sentencetrans
		active = None
		activelookedup = False
		activeexpression = {'expressionwords': expressionwords, 'line': line1, 'startwordnum': wordnum1, 'endwordnum': wordnum2, 'status': 'learning'}

		# Add tag to new expression
		expressionstart = wordstart[activeexpression['line']-1][activeexpression['startwordnum']]
		expressionend = wordend[activeexpression['line']-1][activeexpression['endwordnum']]
		text.tag_add('e' + str(line1) + "." + str(activeexpression['startwordnum']), expressionstart, expressionend)
		markexpression(activeexpression['line'], activeexpression['startwordnum'], 'active')

		printstatus('new expression')
		sidefieldshow(expression, info)
	else: 
		expressionwords = []
	selectedexpressionwords = []

def removerussianaccents(oldstring):
	newstring = oldstring.replace('а́','а')
	newstring = newstring.replace('е́','е')
	newstring = newstring.replace('и́','и')
	newstring = newstring.replace('о́','о')
	newstring = newstring.replace('у́','у')
	newstring = newstring.replace('ы́','ы')
	newstring = newstring.replace('э́','э')
	newstring = newstring.replace('ю́','ю')
	newstring = newstring.replace('я́','я')
	return newstring










def start():
	global config
	global startwindow
	global starttext
	global selection_key_to_language
	
	# Load config file
	config_file_path = 'config.json'
	try:
		with open(config_file_path, 'r') as file:
			config = json.load(file)
	except FileNotFoundError:
		print(f"Error: The config file '{config_file_path}' was not found.")
	except json.JSONDecodeError:
		print(f"Error: The config file '{config_file_path}' contains invalid JSON.")

	startwindow = Tk()
	startwindow.title("Legilo")
	width = startwindowsize['width']
	height = startwindowsize['height']
	center_window(startwindow, width, height)

	# Create frames
	leftframe = Frame(startwindow, width=450, height=height, background="black")
	leftframe.pack(side=LEFT)
	leftframe.pack_propagate(0)

	centerframe = Frame(startwindow, width=300, height=height, background="black")
	centerframe.pack(side=LEFT)
	centerframe.pack_propagate(0)

	rightframe = Frame(startwindow, width=450, height=height, background="black")
	rightframe.pack(side=LEFT)
	rightframe.pack_propagate(0)

	# Add text field
	starttext = Text(centerframe, width=50, height=100, wrap='word', background="black", foreground="white", font=(font,20))
	starttext.config(highlightbackground='black')
	starttext.pack(side=TOP)
	starttext.config(cursor='arrow')

	# Show text
	starttext.insert("end", "\n\n\nLegilo")
	starttext.tag_add("legilo", "4.0", "4.end")
	starttext.tag_configure("legilo", font=(font,80), justify='center')
	starttext.insert("end", "\n\nChoose language and option: ")
	starttext.tag_add("choice", "6.0", "6.end")
	starttext.tag_configure("choice", font=(font, 20, 'italic'))
	starttext.insert("end", "\n\n")
	selection_key_to_language = {}
	if 'languages' in config:
		for language in config['languages']:
			lang_settings = config['languages'][language]
			if 'menu_entry' in lang_settings and 'selection_key' in lang_settings:
				menu_entry = lang_settings['menu_entry']
				selection_key = lang_settings['selection_key']
				selection_key_to_language[selection_key] = language
				starttext.insert("end", menu_entry + '\n')
				startwindow.bind(selection_key, langchoice)
	starttext.insert("end", "\n")
	starttext.insert("end", "📄 [N]ew\n")
	starttext.insert("end", "📂 [O]pen\n")
	starttext.configure(state="disabled")

	startwindow.bind("<n>", optionchoice)
	startwindow.bind("<o>", optionchoice)
	startwindow.bind("<Return>", confirm)

	startwindow.mainloop()

def langchoice(event):
	global config
	global selection_key_to_language
	global language
	global option
	global optionandlang
	global starttext
	global macvoice

	choice = event.char
	language = selection_key_to_language[choice]

	# Set option for text to speech voice if specified
	lang_config = config['languages'][language]
	if 'text_to_speech_voice' in lang_config:
		text_to_speech_voice = lang_config['text_to_speech_voice']
		if text_to_speech_voice == 'mac':
			macvoice = True
		elif text_to_speech_voice == 'google':
			macvoice = False

	if language and option:
		languagetext = language[0].upper() + language[1:]
		optiontext = option[0].upper() + option[1:]
		if optionandlang == False:
			starttext.configure(state="normal")
			starttext.insert("end", "\nChoice: " + optiontext + " " + languagetext)
			starttext.insert("end", "\nPress [enter] to continue\n")
			starttext.configure(state="disabled")
			optionandlang = True
		else:
			starttext.configure(state="normal")
			starttext.delete("end -3 lines", "end")
			starttext.insert("end", "\nChoice: " + optiontext + " " + languagetext)
			starttext.insert("end", "\nPress [enter] to continue\n")
			starttext.configure(state="disabled")

option = None
language = None
optionandlang = False
def optionchoice(event):
	global language
	global option
	global optionandlang
	global starttext
	choice = event.char
	if choice == 'n':
		option = 'new'
	elif choice == 'o':
		option = 'open'

	if language and option:
		languagetext = language[0].upper() + language[1:]
		optiontext = option[0].upper() + option[1:]
		if optionandlang == False:
			starttext.configure(state="normal")
			starttext.insert("end", "\nChoice: " + optiontext + " " + languagetext)
			starttext.insert("end", "\nPress [enter] to continue\n")
			starttext.configure(state="disabled")
			optionandlang = True
		else:
			starttext.configure(state="normal")
			starttext.delete("end -3 lines", "end")
			starttext.insert("end", "\nChoice: " + optiontext + " " + languagetext)
			starttext.insert("end", "\nPress [enter] to continue\n")
			starttext.configure(state="disabled")

def confirm(event):
	global startwindow
	if option and language:
		startwindow.destroy()
		if option == 'new':
			createnew(language)
		elif option == 'open':
			openold(language)

def createnew(language):
	global newtext
	global newtitle
	global newwindow
	global editingnewtitle
	global editingnewtext
	global lastopenedfiles
	editingnewtitle = True
	editingnewtext = False

	newwindow = Tk()
	newwindow.title("Legilo")
	width = startwindowsize['width']
	height = startwindowsize['height']
	center_window(newwindow, width, height)

	# Create frames
	topframe = Frame(newwindow, width=1200, height=50, background="lightgray")
	topframe.pack(side=TOP)
	topframe.pack_propagate(0)

	bottomframe = Frame(newwindow, width=1200, height=50, background="lightgray")
	bottomframe.pack(side=BOTTOM)
	bottomframe.pack_propagate(0)

	mainframe = Frame(newwindow, width=1200, height=700, background="lightgray")
	mainframe.pack(side=LEFT)
	mainframe.pack_propagate(0)

	# Add title field
	newtitle = Text(mainframe, width=65, height=2, wrap='word', font=(font,20))
	newtitle.pack(side=TOP)
	newtitle.focus()

	# Add text field
	newtext = scrolledtextwindow.ScrolledText(
	    master = mainframe,
	    wrap   = 'word',  # wrap text at full words only
	    width  = 100,      # characters
	    height = 100,      # text lines
	    bg='white',        # background color of edit area
	    font=(font, 14)
	)
	newtext.pack(side=TOP)

	# Load list of last opened files
	try:
		lastopenedfiles = loadlist("lastopenedfiles")
	except:
		lastopenedfiles = []

	newtext.bind("<Return>", confirmnew)
	newtitle.bind("<Return>", confirmnew)
	newwindow.bind("<Return>", confirmnew)
	newtext.bind("<Shift-Return>", newlinenewtext)
	newtitle.bind("<Tab>", switchfocusnewtext)
	newtitle.bind("<Button-1>", clickednewtextfield)
	newtext.bind("<Button-1>", clickednewtextfield)

	newwindow.mainloop()

def confirmnew(event):
	global newtext
	global newtitle
	global newwindow
	global editingnewtitle
	global editingnewtext
	global lastopenedfiles
	if editingnewtext:
		newwindow.focus()
		editingnewtext = False
	elif editingnewtitle:
		newwindow.focus()
		editingnewtitle = False
		title = newtitle.get('1.0','end')
		if 'http://' in title or 'https://' in title:
			(title, text) = autoread(title)
			# Remove strange space-like sign to not get new lines
			title = title.replace(' ',' ')
			text = text.replace(' ',' ')
			newtitle.delete('1.0','end')
			newtitle.insert('1.0',title)
			newtext.delete('1.0','end')
			newtext.insert('1.0',text)
	else:
		title = newtitle.get('1.0','end')
		if len(title) == 0 or title == '\n': # If there is no title
			title = newtext.get('1.0','1.end')
			text = newtext.get('2.0','end')
		else:
			text = newtext.get('1.0','end')
		filename = createfilename(title) + '.txt'
		directory = language + '/texts'
		savetotxt(title, text, filename, directory)
		newwindow.destroy()
		run(language, directory + '/' + filename)
	return 'break'

def createfilename(filename):
	charstoremove = """\n'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„"""
	filename = filename.translate(str.maketrans(" ", "-", charstoremove))
	# Add date:
	filename = str(date.today()) + '-' + filename
	return filename

def clickednewtitlefield(event):
	global newwindow
	global editingnewtext
	global editingnewtext
	editingnewtext = False
	editingnewtitle = True

def clickednewtextfield(event):
	global newwindow
	global editingnewtext
	global editingnewtext
	editingnewtext = True
	editingnewtitle = False

def newlinenewtext(event):
	global newtext
	index = newtext.index(INSERT)
	newtext.insert(index,"\n")
	return 'break'

def switchfocusnewtext(event):
	global newtitle
	global newtext
	global editingnewtitle
	global editingnewtext
	editingnewtitle = False
	editingnewtext = True
	newtext.focus()
	return 'break'

def openold(language):
	global oldwindow
	global oldtext
	global lastopenedfiles
	global oldpath
	global editing

	editing = False # Used for removing files from list

	oldwindow = Tk()
	oldwindow.title("Legilo")
	width = startwindowsize['width']
	height = startwindowsize['height']
	center_window(oldwindow, width, height)

	# Create frames
	topframe = Frame(oldwindow, width=1200, height=50, background="lightgray")
	topframe.pack(side=TOP)
	topframe.pack_propagate(0)

	bottomframe = Frame(oldwindow, width=1200, height=50, background="lightgray")
	bottomframe.pack(side=BOTTOM)
	bottomframe.pack_propagate(0)

	mainframe = Frame(oldwindow, width=1200, height=700, background="lightgray")
	mainframe.pack(side=LEFT)
	mainframe.pack_propagate(0)

	texttitlefield = Text(mainframe, width=65, height=1, wrap='word', font=(font,30))
	texttitlefield.pack(side=TOP)
	texttitlefield.insert('1.0','Open file')
	texttitlefield.tag_add("windowtitle", "1.0", "end")
	texttitlefield.tag_configure("windowtitle", font=(font,30), justify='center')
	texttitlefield.configure(state="disabled", background="lightgray", highlightbackground='lightgray')

	textfield1 = Text(mainframe, width=65, height=1, wrap='word', font=(font,20))
	textfield1.pack(side=TOP)
	textfield1.insert('1.0','Write file path: ')
	textfield1.configure(state="disabled", background="lightgray", highlightbackground='lightgray')

	oldpath = Text(mainframe, width=65, height=1, wrap='word', font=(font,20))
	oldpath.pack(side=TOP)

	textfield1 = Text(mainframe, width=65, height=1, wrap='word', font=(font,20))
	textfield1.pack(side=TOP)
	textfield1.insert('1.0','Choose one of the latest files: ')
	textfield1.configure(state="disabled", background="lightgray", highlightbackground='lightgray')

	oldtext = Text(mainframe, width=65, height=50, wrap='word', font=(font,20))
	oldtext.pack(side=TOP)
	oldtext.configure(state="disabled")

	# Load list of last opened files
	try:
		lastopenedfiles = loadlist("lastopenedfiles")
	except:
		lastopenedfiles = []

	oldtext.configure(state="normal")
	for i, f in reversed(list(enumerate(lastopenedfiles))):
		oldtext.insert('end', '[' + str(len(lastopenedfiles)-i) + '] ' + f['title'])
		filename = f['filename']
	oldtext.configure(state="disabled")

	oldpath.bind("<Return>", openoldfrompath)
	oldwindow.bind("1", openoldfromnumber)
	oldwindow.bind("2", openoldfromnumber)
	oldwindow.bind("3", openoldfromnumber)
	oldwindow.bind("4", openoldfromnumber)
	oldwindow.bind("5", openoldfromnumber)
	oldwindow.bind("6", openoldfromnumber)
	oldwindow.bind("7", openoldfromnumber)
	oldwindow.bind("8", openoldfromnumber)
	oldwindow.bind("9", openoldfromnumber)
	oldwindow.bind("r", removeoldfromlist)

	oldwindow.mainloop()

def openoldfrompath(event):
	global oldpath
	if not editing:
		#lastopenedfiles.append({'title': title, 'filename': filename})
		filename = oldpath.get('1.0','end')
		filename = removenewlineatend(filename)
		if len(filename) < 4:
			filename = filename + '.txt'
		elif not filename[:-4] == '.txt':
			filename = filename + '.txt'
		oldwindow.destroy()
		directory = language + '/texts'
		run(language, directory + '/' + filename)

def openoldfromnumber(event):
	global lastopenedfiles
	global oldtext
	global editing
	n = int(event.char)
	if n >= 1 and n <= len(lastopenedfiles):
		i = len(lastopenedfiles) - n
	if not editing:
		filename = lastopenedfiles[i]['filename']
		oldwindow.destroy()
		run(language, filename)
	else: # If editing
		del lastopenedfiles[i]
		oldtext.configure(state="normal")
		oldtext.delete('1.0','end')
		for i, f in reversed(list(enumerate(lastopenedfiles))):
			oldtext.insert('end', '[' + str(len(lastopenedfiles)-i) + '] ' + f['title'])
			filename = f['filename']
		oldtext.configure(state="disabled")
		editing = False



def removeoldfromlist(event):
	global lastopenedfiles
	global oldtext
	global editing
	if not editing:
		editing = True
		oldtext.configure(state="normal", font=(font,20))
		oldtext.delete('1.0','end')
		oldtext.insert('1.0','Remove from list: \nEnter number to remove or press [r] again to cancel.\n')
		for i, f in reversed(list(enumerate(lastopenedfiles))):
			oldtext.insert('end', '[' + str(len(lastopenedfiles)-i) + '] ' + f['title'])
			filename = f['filename']
		oldtext.configure(state="disabled")
	else:
		editing = False
		oldtext.configure(state="normal", font=(font,20))
		oldtext.delete('1.0','end')
		for i, f in reversed(list(enumerate(lastopenedfiles))):
			oldtext.insert('end', '[' + str(len(lastopenedfiles)-i) + '] ' + f['title'])
			filename = f['filename']
		oldtext.configure(state="disabled")









# Main window
def run(language, textfile):
	global w
	global text
	global lastopenedfiles
	global textwords
	global wordstart
	global wordend
	global textstatus
	global textword
	global texttrans
	global textremark
	global textexampletitle
	global textexample

	global openedtextpath
	global knownwords
	global learningwords
	global ignoredwords
	global expressions
	global active
	global activelookedup
	global activeexpression
	global lastpronounced
	global editing
	global expressionmode
	global selectedexpressionwords
	global wordqueue
	global removedfromqueue
	global textexpressions

	global legilotranslator

	legilotranslator = LegiloTranslator(language, use_lemma=uselemma)

	# Word lists
	knownwords = None
	learningwords = None
	ignoredwords = None
	expressions = None

	active = None # Current active word
	activelookedup = False # Gives whether the active word has been looked up
	activeexpression = False # Current active expression
	lastpronounced = False # Last pronounced word
	editing = False # Editing text fields
	expressionmode = False # Expression mode active
	selectedexpressionwords = [] # List of selected expression words

	wordqueue = [] # Word queue
	removedfromqueue = [] # Words removed from queue
	textexpressions = [] # Expressions in text

	# Load word lists from file
	loadall()

	# Create main window
	w = Tk()
	w.title("Legilo")
	width = mainwindowsize['width']
	height = mainwindowsize['height']
	center_window(w, width, height)

	# Create frames
	topframe = Frame(w, width=1200, height=50, background="lightgray")
	topframe.pack(side=TOP)
	topframe.pack_propagate(0)

	bottomframe = Frame(w, width=1200, height=50, background="lightgray")
	bottomframe.pack(side=BOTTOM)
	bottomframe.pack_propagate(0)

	mainframe = Frame(w, width=800, height=2000, background="lightgray")
	mainframe.pack(side=LEFT)
	mainframe.pack_propagate(0)

	sideframe = Frame(w, width=400, height=2000, background="lightgray")
	sideframe.pack(side=TOP)
	sideframe.pack_propagate(0)

	# Add text field
	text = scrolledtextwindow.ScrolledText(
	    master=mainframe,
		padx=text_field_padx,
		pady=text_field_pady,
	    wrap='word',  # wrap text at full words only
	    width=text_field_width,      # characters
	    height=100,      # text lines
	    bg='white',        # background color of edit area
		highlightthickness=0,
		borderwidth=0, 
	    font=(font, fontsize)
	)

	#text = Text(mainframe, width=50, height=30, wrap='word', font=("Helvetica",20))
	text.pack(side=TOP)
	text.config(cursor='arrow')
	#text.grid(row=0, column=0)

	# Read text
	openedtextpath = textfile
	with open(textfile) as file:
		lines = file.readlines()

	# Get saved state and remove state info from text
	state = None
	if len(lines) > 0 and '#state' in lines[0]:
		stateinfo = lines[0].split(' ')
		if len(stateinfo) > 1:
			state = stateinfo[1]
		lines = lines[1:]
		with open(openedtextpath, "w") as file:
			for line in lines:
				file.write(line)

	nbrlines = len(lines)

	# Show text
	for i in range(nbrlines): # Go through the lines
		line = lines[i]
		# Fix issue with scrolling when the character ’ is in the text
		line = line.translate(str.maketrans("’", "'"))
		text.insert(str(i+1) + ".0", line) # Insert text at line i and character 0
		# Mark headlines
		hastitles = False
		lastlinechar = '.'
		newlinesremoved = False
		checkiftitle = line
		while len(checkiftitle) > 0 and not newlinesremoved:
			if checkiftitle[-1] == '\n' or checkiftitle[-1] == ' ':
				checkiftitle = checkiftitle[0:-1]
			else:
				newlinesremoved = True
		if len(checkiftitle) > 0:
			lastlinechar = checkiftitle[-1]
		previouslineempty = False
		if i > 0:
			if len(lines[i-1]) < 3:
				previouslineempty = True
		# Main title
		if not lastlinechar in '.?!:,]*-' and i == 0 and len(line) < 200:
			text.tag_add('l' + str(i+1), str(i+1) + '.' + str(0), str(i+1) + '.' + 'end')
			text.tag_config('l' + str(i+1), font=(font, maintitlesize, "bold"))
		# Other titles
		if not lastlinechar in '.?!:,])}*-' and previouslineempty and len(line) < 200 and i < nbrlines-1:
			hastitles = True
			text.tag_add('l' + str(i+1), str(i+1) + '.' + str(0), str(i+1) + '.' + 'end')
			text.tag_config('l' + str(i+1), font=(font, titlesize, "bold"))
		# Mark preamble
		if hastitles:
			for i in range(min(3,nbrlines)):
				line = lines[i]
				if i > 0 and len(line) < 400:
					text.tag_add('l' + str(i+1), str(i+1) + '.' + str(0), str(i+1) + '.' + 'end')
					text.tag_config('l' + str(i+1), font=(font, titlesize, "bold"))
	text.configure(state="disabled")

	# Add opened text to last opened files list and limit its length to 9
	if len(lines[0]) > 0:
		titleoftext = lines[0]
	else:
		titleoftext = 'Unknown Title'
	# Delete in last opened files
	title = None
	for i, file in enumerate(lastopenedfiles):
		if textfile == file['filename']:
			title = file['title']
			del lastopenedfiles[i]
	lastopenedfiles.append({'title': titleoftext, 'filename': textfile})
	if len(lastopenedfiles) > 9:
		lastopenedfiles.pop(0)

	# Get words
	textwords = [None]*nbrlines
	wordstart = [None]*nbrlines
	wordend = [None]*nbrlines
	wordcount = 0
	for i in range(nbrlines): # Go through the lines
		line = lines[i]
		line = line.lower()
		restofline = line
		charstoremove = "" #"""!"#$%&()*+,./:;<=>?@[]^_`{|}~"""
		line = line.translate(str.maketrans("""'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„""", "                                     ", charstoremove))
		restofline = line
		linewords = line.split()
		numlinewords = len(linewords)
		textwords[i] = [None]*numlinewords
		wordstart[i] = [None]*numlinewords
		wordend[i] = [None]*numlinewords
		charcount = 0
		lineexpressions = []
		for j, word in enumerate(linewords):
			index = restofline.find(word)
			restofline = restofline[index+len(word):]
			charcount = charcount + index
			textwords[i][j] = word
			wordstart[i][j] = str(i+1) + "." + str(charcount)
			wordend[i][j] = str(i+1) + "." + str(charcount + len(word))
			charcount = charcount + len(word)
			wordqueue.append({'index' : wordcount, 'word' : word, 'line' : i+1, 'wordnum' : j})
			text.tag_add(str(i+1) + "." + str(j), wordstart[i][j], wordend[i][j])
			text.tag_bind(str(i+1) + "." + str(j), "<Button-1>", mouseclick)

			# If word is in start of an expression:
			if considerexpressions:
				if word in expressions:
					expressionslist = expressions[word]
					for expression in expressionslist:
						expressionwords = expression['expressionwords']
						if len(expressionwords) <= numlinewords - j:
							for k, expword in enumerate(expressionwords):
								if expword == linewords[j+k]:
									matchingexpression = True
								else:
									matchingexpression = False
									break
							if matchingexpression:
								textexpressions.append({'expressionwords' : expressionwords, 'line' : i+1,
								'startwordnum' : j, 'endwordnum' : j+len(expressionwords)-1})
								lineexpressions.append({'expressionwords' : expressionwords, 'line' : i+1,
								'startwordnum' : j, 'endwordnum' : j+len(expressionwords)-1})
								break
			wordcount += 1

		# Add tags to expressions on the line
		if considerexpressions:
			for expression in lineexpressions:
				expressionstart = wordstart[i][expression['startwordnum']]
				expressionend = wordend[i][expression['endwordnum']]
				text.tag_add('e' + str(i+1) + "." + str(expression['startwordnum']), expressionstart, expressionend)

	# Set word status
	wordstoremove = []
	for i, worddict in enumerate(wordqueue):
		word = worddict['word']
		if word in ignoredwords:
			wordqueue[i]['status'] = 'ignored'
			wordstoremove.append(worddict)
		elif word in knownwords:
			wordqueue[i]['status'] = 'known'
			wordstoremove.append(worddict)
		elif word in learningwords:
			wordqueue[i]['status'] = 'learning'
		else:
			wordqueue[i]['status'] = 'new'

	# Remove known and ignored words from queue
	for word in wordstoremove:
		removedfromqueue.append(word)
		wordqueue.remove(word)

	# Mark words in queue
	for word in wordqueue:
		markword(word['line'], word['wordnum'] , word['status'])

	# Mark expressions in text
	for expression in textexpressions:
		markexpression(expression['line'], expression['startwordnum'], 'ordinary')

	# Add text fields in side field
	textstatus = Text(sideframe, width=side_field_width, height=1, padx=side_field_padx, pady=side_field_pady,
				   wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['status'])
	textstatus.pack(fill='x')
	textword = Text(sideframe, width=side_field_width, height=1, padx=side_field_padx, pady=side_field_pady,
				 wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['word'])
	textword.pack(fill='x')
	texttranstitle = Text(sideframe, width=side_field_width, height=1, padx=side_field_padx, pady=side_field_pady,
					   wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['title'],
					   background=side_field_fonts['field title background'],
					   foreground=side_field_fonts['field title text color'])
	texttranstitle.pack(fill='x')
	texttranstitle.insert('1.0', 'Translations: ')
	texttrans = Text(sideframe, width=side_field_width, height=20, padx=side_field_padx, pady=side_field_pady,
				  wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['translation'])
	texttrans.pack(fill='x')
	textremarktitle = Text(sideframe, width=side_field_width, height=1, padx=side_field_padx, pady=side_field_pady,
							 wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['title'],
							 background=side_field_fonts['field title background'],
							 foreground=side_field_fonts['field title text color'])
	textremarktitle.pack(fill='x')
	textremarktitle.insert('1.0', 'Notes & Remarks: ')
	textremark = Text(sideframe, width=side_field_width, height=12, padx=side_field_padx, pady=side_field_pady,
				   wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['remark'])
	textremark.pack(fill='x')
	textexampletitle = Text(sideframe, width=side_field_width, height=1, padx=side_field_padx, pady=side_field_pady,
						 wrap='word', highlightthickness=0, borderwidth=0,
						 font=side_field_fonts['title'], background=side_field_fonts['field title background'],
						 foreground=side_field_fonts['field title text color'])
	textexampletitle.pack(fill='x')
	textexampletitle.insert('1.0', 'Example Sentence: ')
	textexample = Text(sideframe, width=side_field_width, height=50, padx=side_field_padx, pady=side_field_pady,
					wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['example translation'])
	textexample.pack(fill='x')

	# Set program to saved state
	if state:
		skip_to_word(state)

	# Set what to de when closing window
	w.protocol("WM_DELETE_WINDOW", quitprogram)

	# Add key bindings
	w.bind("<space>", space)
	w.bind("<Return>", enter)
	w.bind("<Right>", space)
	w.bind("<Up>", enter)
	w.bind("<Down>", known)
	w.bind("<Left>", pronounceactiveword)
	w.bind("<a>", enter)
	w.bind("<k>", known)
	w.bind("<p>", ignore)
	w.bind("<BackSpace>", ignore)
	w.bind("<h>", pronounceactiveword)
	w.bind("<.>", pronounceactiveword)
	w.bind("<e>", space)
	w.bind("<r>", changeremark)
	w.bind("<b>", iteratelearningwords)
	w.bind("<s>", addswedishtrans)
	w.bind("<d>", opendictionary)
	w.bind("<v>", openverbconjugation)
	w.bind("<w>", openwiktionary)
	w.bind("<c>", opencontextreverso)
	w.bind("<g>", opengoogle)
	w.bind("<i>", opengoogleimages)
	w.bind("<l>", openwikipedia)
	w.bind("<Meta_L>", activateexpressionmode)
	w.bind("<KeyRelease-Meta_L>", deactivateexpressionmode)
	w.bind("<Command-Key-s>", savelists)
	w.bind("<Command-Key-t>", savelistsastxt)
	w.bind("<Command-Key-x>", quitwithoutsaving)
	w.bind("<z>", pronouncenext)

	textremark.bind("<Button-1>", changeremark)

	texttrans.bind("<Return>", enterininfofield)
	textremark.bind("<Return>", enterininfofield)

	texttrans.bind("<Shift-Return>", newline1)
	textremark.bind("<Shift-Return>", newline2)

	w.bind("1", selectsentence)
	w.bind("2", selectsentence)
	w.bind("3", selectsentence)
	w.bind("4", selectsentence)
	w.bind("5", selectsentence)
	w.bind("6", selectsentence)
	w.bind("7", selectsentence)
	w.bind("8", selectsentence)
	w.bind("9", selectsentence)
	w.bind("0", selectsentence)

	w.mainloop()











# Open start window and get options
start()