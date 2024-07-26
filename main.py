#!/usr/bin/env python3

import os
import re
import regex
from datetime import date
from tkinter import *
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtextwindow
from language_code import get_language_code
from translate import LegiloTranslator
from sentence import get_first_sentence, get_sentences
from autoread import autoread
from google_speech import Speech
from googletrans import Translator
import webbrowser
import urllib
import pickle # For saving and loading data
import subprocess # Used for text-to speak with Mac OS
import shlex # Used for text-to speak with Mac OS
import json # Used to read config file

# General settings
sound_on = True # Pronounce word when looked up
mac_voice = False # Use the text-to speak voice in Mac OS instead of Google
include_article = True # Write out and pronounce article for nouns
use_lemma = True # Use a lemmatizer to look up the lemma form of a word
third_lang = 'swedish' # Third language (e.g. native language) for extra translations
start_window_size = {'width': 1200, 'height': 700} # Set size of start window
main_window_size = {'width': 1200, 'height': 1000} # Set size of main window
consider_phrases = True # Allow phrases to be considered
always_show_active = False # Always show active word in the side field (without translation)
move_back_when_clicking_previous = True # Put back learning words after clicked word in queue
saving_on = True # Saves word lists when quitting
save_state_on = True # Saves the current state (marked word or next word in queue)
use_message_box = False # Uses message box to inform about saving, which has some bug on Mac OS
print_word_lists_at_start = False # Prints word lists in terminal for debugging
new_browser_tab = True # Use a new browser tab the first time the browser is opened
data_dir = 'data' # Directory where data (texts and word lists etc.) is saved

# Fonts and colors
window_background_color = 'lightgray'
active_color = 'orange'
learning_color = '#fde367' #'yellow' macyellow:'#facd5a'
new_color = '#cce6ff' #'#a3daf0'#'lightblue' macblue: '#69aff1'
known_color = '#b0fc81', #'#9ffa66' #'lightgreen'
selection_color = '#b0fc81' # Color for selector in phrase mode

# Font
font = 'Avant Garde' #'Museo Sans Rounded', 'Bookman', 'Georgia', 'Helvetica', 'Avant Garde'

# Main window text settings
font_size = 18
main_title_size = 36
title_size = 20
text_field_width = 60 # Text field width in number of characters
text_field_padx = 5
text_field_pady = 5

# Side field text settings
side_field_fonts = {'title': (font, 14),
							'field_title_background': 'darkgray',
							'field_title_text_color': 'white',
							'word': (font, 20, 'bold'),
							'status': (font, 12, 'bold'),
							'translation': (font, 16),
							'personal_translation_background': 'orange',
							'google_translate_background': '#b0fc81',
							'remark': (font, 14),
							'example': (font, 14, 'bold'),
							'example_translation': (font, 14, 'italic')}
side_field_width = 40 # Side field width in number of characters
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
def save_to_txt(title, text, file_name, directory):
	# Create directory if it doesn't exist
	if not os.path.exists(directory):
		os.makedirs(directory)

	file = open(directory + '/' + file_name,'w') 
	file.write(title)
	file.write('\n')
	file.write(text) 
	file.close()

# Save word list
def save_list(obj, name):
	save(obj, name, data_dir + '/' + language + '/' + 'history')

# Load word list
def load_list(name):
	obj = load(name, data_dir + '/' + language + '/' + 'history')
	return obj

# Save word list as txt file
def save_list_as_txt(obj, name):
	save_to_txt(name, str(obj), name + '.txt', data_dir + '/' + language + '/' + 'txt_word_lists')

# Load all the word lists
def load_all():
	global known_words
	global learning_words
	global ignored_words
	global phrases
	global last_opened_files

	try:
		known_words = load_list("known_words")
		if print_word_lists_at_start:
			print('')
			print('known words:')
			print(known_words)
	except:
		known_words = {}
	try:
		learning_words = load_list("learning_words")
		if print_word_lists_at_start:
			print('')
			print('learning words:')
			print(learning_words)
	except:
		learning_words = {}
	try:
		ignored_words = load_list("ignored_words")
		if print_word_lists_at_start:
			print('')
			print('ignored words:')
			print(ignored_words)
	except:
		ignored_words = []
	if consider_phrases:
		try:
			phrases = load_list("phrases")
			if print_word_lists_at_start:
				print('')
				print('phrases:')
				print(phrases)
		except:
			phrases = {}

# Save all the word lists and current state
def save_all():
	global save_state_on
	save_list(known_words, "known_words")
	save_list(learning_words, "learning_words")
	save_list(ignored_words, "ignored_words")
	if consider_phrases:
		save_list(phrases, "phrases")
	save_list(last_opened_files, 'last_opened_files')
	if save_state_on:
		save_state()
	if not use_message_box:
		print("The history was saved!")
		print(f"Number of known words: {len(known_words)}")

# Save all the word lists as txt files
def save_all_as_txt():
	save_list_as_txt(known_words, "known_words")
	save_list_as_txt(learning_words, "learning_words")
	save_list_as_txt(ignored_words, "ignored_words")
	save_list_as_txt(learning_words.keys(), "learningwordlist")
	if consider_phrases:
		save_list_as_txt(phrases, "phrases")

# Save current state, i.e., current marked word or first word in queue
def save_state():
	global active
	global opened_text_path
	state = None
	word_info = None
	if active:
		word_info = active
	elif more_in_queue():
		word_info = next_word()

	if word_info:
		state = str(word_info['line']) + '.' + str(word_info['word_num'])

		with open(opened_text_path) as file:
			lines = file.readlines()

		with open(opened_text_path, "w") as file:
			file.write('#state ' + state + '\n')
			for line in lines:
				if not '#state' in line:
					file.write(line)

# Invoke save_all
def save_lists(event):
	global w
	global text
	save_all()
	if use_message_box:
		ans = messagebox.showinfo("Saved", "The history was saved!")
	deactivate_phrase_mode(event)
	text.focus()
	unfocus()

# Invoke save_all_as_txt
def save_listsastxt(event):
	global w
	global text
	save_all_as_txt()
	if use_message_box:
		ans = messagebox.showinfo("Saved", "The word lists were saved as txt files!")
	else:
		print("The word lists were saved as txt files!")
	deactivate_phrase_mode(event)
	text.focus()
	unfocus()

# Handles active word when another word or phrase is selected
def handle_active_words(unqueue_looked_up=True):
	global active
	global active_looked_up
	global word_queue
	global removed_from_queue
	if active:
		if active_looked_up:
			info = get_word_info()
			add_to_learning(active['word'], info)
			active['status'] = 'learning'
			if unqueue_looked_up:
				removed_from_queue.append(active)
			else:
				put_back_in_queue(active)
			mark_all_instances(active['word'], 'learning')
		else:
			put_back_in_queue(active)
		unset_active_word()

# Handles active phrase when another word or phrase is selected.
# Saves a new active phrase if `save_new` is True
def handle_active_phrases(save_new=False):
	global info_for_showed_word
	global active_phrase
	global active_phrase_is_new
	global phrases
	if active_phrase:
		if active_phrase_is_new and not save_new:
			mark_phrase(active_phrase['line'], active_phrase['startword_num'], 'none')
			mark_all_phrase_instances(active_phrase['phrase_words'], 'none')
		else:
			add_to_phrases(active_phrase, info_for_showed_word)
			mark_phrase(active_phrase['line'], active_phrase['startword_num'], 'ordinary')
			mark_all_phrase_instances(active_phrase['phrase_words'], 'ordinary')
		active_phrase = False
		active_phrase_is_new = False
		clear_side_field()

# Find old phrase from tag
def find_old_phrase(tag):
	global phrases
	start_index = text.tag_ranges(tag)[0]
	end_index = text.tag_ranges(tag)[1]
	line_and_start_word = tag.split('.')

	line = int(line_and_start_word[0][1:])
	word_num1 = int(line_and_start_word[1])
	phrase = text.get(start_index,end_index)
	phrase_words = phrase.translate(str.maketrans("""'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„""", "                                     "))
	phrase_words = phrase_words.lower().split()
	word_num2 = word_num1 + len(phrase_words)
	first_word = phrase_words[0]

	info = None

	# Search for phrase
	if first_word in phrases:
		phrases_list = phrases[first_word]

		for phrase_num, p in enumerate(phrases_list):
			phrase_words2 = p['phrase_words']
			if len(phrase_words) == len(phrase_words2):
				if str(phrase_words) == str(phrase_words2):
					# phrases are matching
					info = phrases_list[phrase_num]
					break
	return (phrase, info, line, word_num1, word_num2)

# Handle mouse click in text field
def mouse_click(event):
	global active
	global phrase_mode

	if phrase_mode:
		handle_selected_phrase_word(selected_by_mouse=True)
	else:
		if consider_phrases:
			word_tags = text.tag_names(text.index(CURRENT))
			# Choose tag for word, not for phrase:
			for tag in word_tags:
				if 'p' not in tag and 'l' not in tag:
					word_tag = tag
					break
		else:
			word_tag = text.tag_names(text.index(CURRENT))[0]

		if move_back_when_clicking_previous:
			handle_active_phrases()
			handle_active_words()
			go_to_start()

		skip_to_word(word_tag)
		look_up(active['word'], active['status'])

def handle_selected_phrase_word(selected_by_mouse=False):
	global text
	global active_phrase
	global selected_phrase_words
	global selected_tag1
	global selected_tag2

	if selected_by_mouse:
		word_tags = text.tag_names(text.index(CURRENT))
	else:
		if len(selected_phrase_words) == 0:
			word_tags = get_containing_tags(selected_tag1) + [selected_tag1]
		else:
			word_tags = get_containing_tags(selected_tag2) + [selected_tag2]
	is_old_phrase = False
	for tag in word_tags:
		if 'p' in tag:
			is_old_phrase = True
	
	# If old phrase
	if is_old_phrase:
		selected_phrase_words = [] # Cancel selection of new phrase
		# Mark and save previous phrase
		handle_active_phrases()
		# Put back active word in queue and clear side field
		handle_active_words()

		# Show old phrase
		for tag in word_tags:
			if 'p' in tag:
				phrase_tag = tag

		(phrase, info, line, word_num1, word_num2) = find_old_phrase(phrase_tag)

		active_phrase = {'phrase_words' : info['phrase_words'], 'line' : line, 'startword_num' : word_num1, 'endword_num' : word_num2}
		mark_phrase(active_phrase['line'], active_phrase['startword_num'], 'active')
		deactivate_phrase_mode()
		side_field_show(phrase, info, 'learning phrase')

	# If new phrase
	else: 
		# Choose tag for word, not for phrase:
		for tag in word_tags:
			if 'p' not in tag and 'l' not in tag:
				word_tag = tag

		selected_phrase_words.append(word_tag)
		# If two words are selected so that a new phrase can be created
		if len(selected_phrase_words) > 1:
			# Mark and save previous phrase
			handle_active_phrases()
			handle_active_words()
			first_phrase_word = selected_phrase_words[0]
			second_phrase_word = selected_phrase_words[1]
			deactivate_phrase_mode()
			new_phrase(first_phrase_word, second_phrase_word)

# Skip to word with word tag `word_tag`
def skip_to_word(word_tag, scroll_to_word=False):
	global active
	global word_queue
	global removed_from_queue

	line_and_word_num = word_tag.split(".")
	line = int(line_and_word_num[0])
	word_num = int(line_and_word_num[1])
	words_to_remove = []
	# Handle active phrase
	handle_active_phrases()
	# Handle active word
	handle_active_words()

	# Mark all prev. new words as known and clicked word as active, 
	# and remove all previous words from queue
	clicked_word_in_queue = False
	for word_dict in word_queue:
		if word_dict['line'] < line or (word_dict['line'] == line and word_dict['word_num'] < word_num):
			if word_dict['status'] == 'new':
				word_dict['status'] = 'known'
				add_to_known(word_dict['word'], None)
				mark_all_instances(word_dict['word'],'known')
				words_to_remove.append(word_dict)
			elif word_dict['status'] == 'ignored':
				mark_all_instances(word_dict['word'],'ignored')
				words_to_remove.append(word_dict)
			elif word_dict['status'] == 'learning':
				mark_all_instances(word_dict['word'],'learning')
				words_to_remove.append(word_dict)

		elif word_dict['line'] == line and word_dict['word_num'] == word_num:
			clicked_word_in_queue = True
			words_to_remove.append(word_dict)
			set_to_active(word_dict)
			break

	if not clicked_word_in_queue:
		for word_dict in removed_from_queue:
			if word_dict['line'] == line and word_dict['word_num'] == word_num:
				removed_from_queue.remove(word_dict)
				set_to_active(word_dict)
				break

	for word in words_to_remove:
		removed_from_queue.append(word)
		word_queue.remove(word)

	if scroll_to_word and active:
		active_word_tag = str(active['line']) + '.' + str(active['word_num'])
		text.see(active_word_tag)

# Mark words
def mark_word(line, word_num, status):
	if status == 'new':
		text.tag_config(str(line) + "." + str(word_num), background=new_color)
	elif status == 'learning':
		text.tag_config(str(line) + "." + str(word_num), background=learning_color)
	elif status == 'known':
		text.tag_config(str(line) + "." + str(word_num), background="white")
	elif status == 'ignored':
		text.tag_config(str(line) + "." + str(word_num), background="white")
	elif status == 'active':
		text.tag_config(str(line) + "." + str(word_num), background=active_color)
	elif status == 'selection':
		text.tag_config(str(line) + "." + str(word_num), background=selection_color)

# Mark all instances of a word
def mark_all_instances(word, status):
	all_text_words = removed_from_queue + word_queue
	for word_dict in all_text_words:
		if word == word_dict['word']:
			word_dict['status'] = status
			line = word_dict['line']
			word_num = word_dict['word_num']
			mark_word(line, word_num, status)

# Mark phrase
def mark_phrase(line, startword_num, status):
	global text

	is_title_line = False
	line_tags = text.tag_names(str(line) + '.0')
	for tag in line_tags:
		if 'l' in tag:
			is_title_line = True
	phrasefont_size = font_size
	if line == 1 and is_title_line:
		phrasefont_size = main_title_size
	elif is_title_line:
		phrasefont_size = title_size

	if status == 'ordinary':
		if is_title_line:
			font_settings = (font, phrasefont_size, "underline", "bold")
		else:
			font_settings = (font, phrasefont_size, "underline")
		text.tag_config("p" + str(line) + "." + str(startword_num), font = font_settings)
	elif status == 'none':
		if is_title_line:
			font_settings = (font, phrasefont_size, "bold")
		else:
			font_settings = (font, phrasefont_size)
		text.tag_config("p" + str(line) + "." + str(startword_num), font = font_settings)
	elif status == 'active':
		if is_title_line:
			font_settings = (font, phrasefont_size, "underline", "italic", "bold")
		else:
			font_settings = (font, phrasefont_size, "underline", "italic")
		text.tag_config("p" + str(line) + "." + str(startword_num), font = font_settings)

# Mark all instances of an phrase
def mark_all_phrase_instances(phrase_words, status):
	global text_words
	global text

	first_word = phrase_words[0]
	for i in range(len(text_words)):
		line_words = text_words[i]
		for j, word in enumerate(line_words):
			if first_word == word and len(phrase_words) <= len(line_words)-j:
				if str(line_words[j:j+len(phrase_words)]) == str(phrase_words):
					if status == 'none':
						text.tag_delete("p" + str(i+1) + "." + str(j))
						mark_phrase(i+1, j, 'none')
					elif status == 'ordinary':
						text.tag_add('p' + str(i+1) + "." + str(j), word_start[i][j], word_end[i][j+len(phrase_words)-1])
						mark_phrase(i+1, j, 'ordinary')

# Set word referred to by `word_dict` as `active` and mark it
def set_to_active(word_dict):
	global active
	global always_show_active
	active = word_dict
	mark_word(active['line'], active['word_num'], 'active')
	if always_show_active:
		show_active_word_in_sidefield()

# Set next word in the queue (if there are more words) to active
def set_next_to_active():
	global active_looked_up
	if more_in_queue():
		new_active = next_word()
		set_to_active(new_active)
		active_looked_up = False

# Unset active word and remove the viewing of it from the side field
def unset_active_word():
	global active
	global active_looked_up
	mark_word(active['line'], active['word_num'], active['status'])
	active = None
	active_looked_up = False
	clear_side_field()

# Retrieve tag configuration and convert it to a dictionary
def save_tag_config(tag_name):
	global text
	config = text.tag_configure(tag_name)
	tag_config = {option: config[option][4] for option in config}
	return tag_config

# Apply the saved tag configuration to the specified tag
def apply_tag_config(tag_name, tag_config):
	global text
	for option, value in tag_config.items():
		text.tag_configure(tag_name, **{option: value})

# Get a list with all other tags that contain a tag
def get_containing_tags(word_tag):
	global text
	# Get the range of the specific tag
	word_tag_ranges = text.tag_ranges(word_tag)

	if len(word_tag_ranges) < 2:
		return []  # If the specific tag has no range, return an empty list
    
	word_tag_start = word_tag_ranges[0]
	word_tag_end = word_tag_ranges[1]

	# Get all tags in the text widget
	all_tags = text.tag_names()

	# List to store tags that contain the specific tag
	containing_tags = []

	for tag in all_tags:
		if tag == word_tag:
			continue  # Skip the specific tag itself

		# Get the ranges of the current tag
		tag_ranges = text.tag_ranges(tag)
		for i in range(0, len(tag_ranges), 2):
			tag_start = tag_ranges[i]
			tag_end = tag_ranges[i+1]

			# Check if specific tag is fully contained within the current tag
			if (text.compare(tag_start, '<=', word_tag_start) and
				text.compare(tag_end, '>=', word_tag_end)):
				containing_tags.append(tag)
				break  # No need to check further ranges for this tag

	return containing_tags

# Remove possible focus on text fields
def unfocus():
	w.focus()

# Returns the article of a word (or an empty string if article is not unique)
def get_article(word, gender, language):
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
	elif language == 'spanish':
		if gender == 'm':
			return 'el'
		elif gender == 'f':
			return 'la'
		else:
			return ''
	elif language == 'swedish':
		if gender in ['c', 'm', 'f']:
			return 'en'
		elif gender == 'n':
			return 'ett'
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
def gender_color(gender):
	global language
	global text_word

	gender_colors = {'m': 'blue', 'f': 'red', 'n': 'green', 'c': 'purple'}
	# Only set gender color if gender is unique and gender_color is defined
	if not gender in gender_colors:
		text_word.configure(foreground='black')
		return

	text_word.configure(state='normal')
	if language in ['croatian', 'french', 'italian', 'spanish', 'swedish', 'russian']:
		text_word.configure(foreground=gender_colors[gender])
	if language in ['german']:
		verb = False
		word = text_word.get('1.0','end')
		if ',' in word:
			verb = True
		if not verb:
			text_word.configure(foreground=gender_colors[gender])
		else:
			noun_and_verb = word.split(',')
			noun_length = len(noun_and_verb[0])
			text_word.configure(foreground='black')
			text_word.tag_add('noun', '1.0', '1.' + str(noun_length))
			text_word.tag_configure('noun', foreground=gender_colors[gender])
	text_word.configure(state='disabled')

# Insert example sentence
def insert_remark(remark):
	text_remark.configure(state='normal')
	text_remark.insert(END, remark)
	text_remark.configure(state='disabled')

# Insert example sentence
def insert_sentence(sentence, sentence_trans):
	text_example.configure(state='normal')
	text_example.delete("1.0", "end")
	text_example.insert("1.0", sentence + "\n")
	text_example.insert("3.0", sentence_trans)
	text_example.tag_add("sentence", "1.0", "1." + str(len(sentence)))
	text_example.tag_config("sentence", font = side_field_fonts['example'])
	text_example.configure(state='disabled')

# Insert formated translation into translation field
def insert_translation(trans):
	text_trans.configure(state='normal')
	# Define tags for formatting
	(translation_font, translation_font_size) = side_field_fonts['translation']
	text_trans.tag_configure("word", font=(translation_font, translation_font_size, "bold"))
	text_trans.tag_configure("normal", font=(translation_font, translation_font_size))
	text_trans.tag_configure("parenthesis", font=(translation_font, translation_font_size))
	text_trans.tag_configure("type_and_gender", font=(translation_font, translation_font_size, "italic"))
	text_trans.tag_configure("personal_translation", font=(translation_font, translation_font_size),
						 background=side_field_fonts['personal_translation_background'])
	text_trans.tag_configure("google_translate", font=(translation_font, translation_font_size),
						 background=side_field_fonts['google_translate_background'])
	text_trans.tag_configure("definitions", font=(translation_font, translation_font_size), lmargin1=20, spacing1=5)
	text_trans.tag_configure("synonyms", font=(translation_font, translation_font_size-2, "bold"), lmargin1=40, spacing1=2)

	personal_trans = None
	google_trans = None
	for i, item in enumerate(trans):
		if 'source' in item and item['source'] == 'personal translation':
			if 'definitions' in item:
				definition = item['definitions'][0]
				if 'definition' in definition:
					personal_trans = definition['definition']

		elif 'source' in item and item['source'] == 'Google Translate':
			if 'definitions' in item:
				definition = item['definitions'][0]
				if 'definition' in definition:
					google_trans = definition['definition']

		elif 'source' in item and item['source'] == 'Wiktionary':
			if 'word' in item:
				text_trans.insert(END, item['word'], 'word')
			if 'part_of_speech' in item:
				text_trans.insert(END, ' (', 'parenthesis')
				text_trans.insert(END, item['part_of_speech'], 'type_and_gender')
				if 'gender' in item:
					text_trans.insert(END, ' — ' + item['gender'], 'type_and_gender')
				text_trans.insert(END, ')', 'parenthesis')
				if 'qualifier' in item:
					text_trans.insert(END, ' (', 'parenthesis')
					text_trans.insert(END, item['qualifier'], 'type_and_gender')
					text_trans.insert(END, ')', 'parenthesis')

			if 'definitions' in item:
				for j, definition in enumerate(item['definitions']):
					if 'definition' in definition:
						def_def = definition['definition']
						text_trans.insert(END, f'\n{j+1}. {def_def}', 'definitions')
					if 'synonyms' in definition:
						synonyms = definition['synonyms']
						text_trans.insert(END, f'\n≈ {synonyms}', 'synonyms')
					if 'antonyms' in definition:
						antonyms = definition['antonyms']
						text_trans.insert(END, f'\n≠ {antonyms}', 'synonyms')
			if i < len(trans)-1:
				text_trans.insert(END, '\n\n', 'normal')

	if google_trans:
		text_trans.insert('1.0', '\n\n', 'normal')
		text_trans.insert('1.0', google_trans, 'google_translate')
	
	if personal_trans:
		text_trans.insert('1.0', '\n\n', 'normal')
		text_trans.insert('1.0', personal_trans, 'personal_translation')

	text_trans.configure(state='disabled')

def replace_phrase_translation(trans, color):
	global text_trans
	global side_field_fonts
	text_trans.configure(state='normal')
	text_trans.delete('1.0', "end")
	text_trans.tag_configure("phrase_trans",
						  font=side_field_fonts['translation'],
						  background=color)
	text_trans.insert("1.0", trans, "phrase_trans")
	text_trans.configure(state='disabled')

# Get personal translation from a translations list, if available
def get_personal_translation(trans_list):
	for item in trans_list:
		if 'source' in item and item['source'] == 'personal translation':
			if 'definitions' in item:
				return item['definitions'][0]['definition']
	return None

# Check if word translations list contains a personal translation
def has_personal_translation(trans_list):
	for item in trans_list:
		if 'source' in item and item['source'] == 'personal translation':
			return True
	return False

# Check if word translations list contains a Google translation
def has_google_translation(trans_list):
	for item in trans_list:
		if 'source' in item and item['source'] == 'Google Translate':
			return True
	return False

# Delete personal translation from translations list, if available
def delete_personal_translation(trans_list):
	if has_personal_translation(trans_list):
		for i, item in enumerate(trans_list):
			if 'source' in item and item['source'] == 'personal translation':
				translation_index_to_remove = i
				break
		del trans_list[translation_index_to_remove]

# Delete Google translation from translations list, if available
def delete_google_translation(trans_list):
	if has_google_translation(trans_list):
		for i, item in enumerate(trans_list):
			if 'source' in item and item['source'] == 'Google Translate':
				translation_index_to_remove = i
				break
		del trans_list[translation_index_to_remove]

# View in side field
def side_field_show(word, info, status, do_pronounce=True):
	global language
	global info_for_showed_word
	info_for_showed_word = info
	trans = info['trans']
	word_type = None
	if 'word_type' in info:
		word_type = info['word_type']
	if not word_type == 'phrase':
		# The word is a variant of some other word if there are lemmas
		word_is_variant = 'lemmas' in info

	# Write german nouns with initial capital letter and article
	if language == 'german' and word_type and 'noun' in word_type:
		if not 'verb' in word_type:
			word = word.capitalize()
		else:
			word = word.capitalize() + ', ' + word

	has_unique_gender = False
	if 'gender' in info:
		gender = info['gender']
		if len(gender) == 1:
			has_unique_gender = True

	if not word_type == 'phrase':
		# Write nouns with article if in dictionary form
		if has_unique_gender:
			if include_article and len(word) > 0 and not word_is_variant:
				article = get_article(word, gender, language)
				if language == 'italian':
					if len(article) > 0:
						if not article == "un'":
							word = article + ' ' + word
						else:
							word = article + word
				else:
					if len(article) > 0:
						word = article + ' ' + word

	print_status(status)
	text_word.configure(state='normal')
	text_word.insert("1.0", word)
	text_word.configure(state='disabled')

	if has_unique_gender:
		gender_color(gender)
	else:
		text_word.configure(state='normal')
		text_word.configure(fg="black")
		text_word.configure(state='disabled')
	insert_translation(trans)
	if 'remark' in info:
		insert_remark(info['remark'])
	if 'sentence' in info and 'sentence_trans' in info:
		insert_sentence(info['sentence'], info['sentence_trans'])

	# Pronunciation
	if sound_on and do_pronounce:
		w.update_idletasks()
		w.after(100, pronounce(word, language))

# Show active word and its status in the side field, but no other information
def show_active_word_in_sidefield():
	if active:
		clear_side_field()
		text_word.configure(state='normal')
		text_word.insert('1.0', active['word'])
		text_word.configure(fg='black')
		text_word.configure(state='disabled')
		print_status(active['status'])

# Add info in side field
def look_up(word, status):
	global text_word
	global active_looked_up
	known_without_info = (status == 'known' and not known_words[word])
	if status in ['new', 'ignored'] or known_without_info:
		info = legilo_translator.get_info(word)
		(sentence, sentence_trans) = get_first_sentence(word, language)
		if len(sentence) > 0:
			info['sentence'] = sentence
			info['sentence_trans'] = sentence_trans
	elif status == 'learning':
		info = learning_words[word]
	else: # status == 'known' and word has info
		info = known_words[word]

	side_field_show(word, info, status)
	active_looked_up = True

def update_translation_for_showed_word():
	global active_looked_up
	global active_phrase
	global info_for_showed_word
	if active_looked_up or active_phrase:
		clear_translation_field()
		insert_translation(info_for_showed_word['trans'])

# Enable input of text in sidebar
def edit_side_field():
	text_status.configure(state="normal")
	text_word.configure(state="normal")
	text_trans.configure(state="normal")
	text_remark.configure(state="normal")
	text_example.configure(state="normal")

# Disable input of text in sidebar
def freeze_side_field():
	text_status.configure(state="disabled")
	text_word.configure(state="disabled")
	text_trans.configure(state="disabled")
	text_remark.configure(state="disabled")
	text_example.configure(state="disabled")

def remove_new_line_at_end(string):
	if len(string) > 0:
		if string[-1:] == '\n':
			string = string[:-1]
	return string

# Collect word info from side field and info_for_showed_word variable
def get_word_info():
	global info_for_showed_word
	edit_side_field()
	word_type = None
	if 'word_type' in info_for_showed_word:
		word_type = info_for_showed_word['word_type']
		word_type = remove_new_line_at_end(word_type)
	remark = text_remark.get("1.0",END)
	remark = remove_new_line_at_end(remark)
	sentence = text_example.get("1.0","1.end")
	sentence = remove_new_line_at_end(sentence)
	sentence_trans = text_example.get("2.0","2.end")
	sentence_trans = remove_new_line_at_end(sentence_trans)

	info = info_for_showed_word
	info['remark'] = remark
	info['sentence'] = sentence
	info['sentence_trans'] = sentence_trans

	freeze_side_field()
	return info

# Add personal translation to info_for_showed_word
def add_personal_translation_info_to_showed_word():
	global info_for_showed_word
	global text_word
	global text_personal_trans
	trans = remove_new_line_at_end(text_personal_trans.get('1.0', END))
	word = remove_new_line_at_end(text_word.get("1.0",END))
	delete_personal_translation(info_for_showed_word['trans'])
	if len(trans) > 0:
		info_for_showed_word['trans'].append({'word': word, 'definitions': [{'definition': trans}], 'source': 'personal translation'})
	update_translation_for_showed_word()
	text_personal_trans.delete("1.0", "end")

# Add word to learning words
def add_to_learning(word, info):
	# Remove from ignored or known words
	if word in ignored_words:
		ignored_words.remove(word)
	elif word in known_words:
		del known_words[word]
	learning_words[word] = info

# Add to ignored words
def add_to_ignored(word):
	ignored_words.append(word)

# Add word to known words
def add_to_known(word, info):
	# Remove from ignored or learning words
	if word in ignored_words:
		ignored_words.remove(word)
	elif word in learning_words:
		del learning_words[word]
	known_words[word] = info

# Add phrase to phrases
def add_to_phrases(phrase, info):
	global phrases
	i = phrase['line']-1
	word_num1 = phrase['startword_num']
	first_word = text_words[i][word_num1]

	if not is_in_phrases(phrase['phrase_words']):
		if first_word in phrases:
			phrases[first_word].append(info)
		else:
			phrases[first_word] = [info]

def is_in_phrases(phrase_words):
	global phrases
	if len(phrase_words) > 0:
		first_word = phrase_words[0]
		if first_word in phrases:
			for phrase in phrases[first_word]:
				if phrase['phrase_words'] == phrase_words:
					return True
	return False

# Empty the side field
def clear_side_field():
	global info_for_showed_word
	global text_status
	global text_word
	global text_remark
	global text_trans
	global text_example_title
	global text_example

	info_for_showed_word = None

	text_status.configure(state="normal")
	text_status.delete("1.0", "end")
	text_status.configure(bg="white")
	text_status.configure(state="disabled")

	text_word.configure(state="normal")
	text_word.delete('1.0', "end")
	text_word.configure(state="disabled")

	text_remark.configure(state="normal")
	text_remark.delete('1.0', "end")
	text_remark.configure(state="disabled")

	text_trans.configure(state="normal")
	text_trans.delete('1.0', "end")
	text_trans.configure(state="disabled")

	text_example.configure(state="normal")
	text_example.delete('1.0', "end")
	text_example.configure(state="disabled")

# Empty the translation field
def clear_translation_field():
	global text_trans
	text_trans.configure(state="normal")
	text_trans.delete('1.0', "end")
	text_trans.configure(state="disabled")

# Check if more words in the queue
def more_in_queue():
	global word_queue
	ans = False
	for i in range(len(word_queue)):
		word = word_queue[i]
		if not (word['status'] == 'ignored' or word['status'] == 'known'):
			ans = True
			break
	return ans

# Return next word from queue
def next_word():
	global word_queue
	next_word = None
	for i in range(len(word_queue)):	
		word = word_queue.pop(0)
		if not (word['status'] == 'ignored' or word['status'] == 'known'):
			next_word = word
			break
	return next_word

# Put back a word in the word queue
def put_back_in_queue(word):
	global word_queue
	word_queue.insert(0,word)

# Put back a word in the word queue sorted according to word index
def put_back_in_queue_sorted(word):
	global word_queue
	insert_index = 0
	word_index = word['index']
	for i, queue_word in enumerate(word_queue):
		if queue_word['index'] > word_index:
			insert_index = i
			break
	word_queue.insert(insert_index, word)

# Checks if the text word is already in the queue based on its index
def word_in_queue(word_index):
	global word_queue
	ans = False
	for word in word_queue:
		if word['index'] == word_index:
			ans = True
			break
	return ans

# Show word status in side field
def print_status(status):
	text_status.configure(state="normal")
	if status == 'ignored':
		status = 'new'
	text_status.insert("1.0", status) # Insert text at line i and character 0
	if status == 'new' or status == 'ignored':
		text_status.configure(bg=new_color)
	elif status == 'learning':
		text_status.configure(bg=learning_color)
	elif status == 'known':
		text_status.configure(bg=known_color)
	elif status == 'learning phrase':
		text_status.configure(bg=learning_color)
	elif status == 'new phrase':
		text_status.configure(bg=new_color)
	else:
		text_status.configure(bg="white")
	text_status.configure(state="disabled")

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
def go_to_next(event):
	global editing
	global active
	global active_looked_up
	global word_queue
	global removed_from_queue

	if not editing:
		unfocus()
		handle_active_phrases()
		if active and not active_looked_up:
			if active['status'] == 'learning':
				removed_from_queue.append(active)
				unset_active_word()
				set_next_to_active()
			else: # active['status'] == 'new'
				known(event)
		else:
			handle_active_words()
			set_next_to_active()

def enter(event):
	global active
	global active_looked_up
	global word_queue
	global removed_from_queue
	global editing
	global phrase_mode
	if not editing:
		if phrase_mode:
			enter_in_phrase_mode()
		else:
			if active and not active_looked_up:
				look_up(active['word'], active['status'])
			else:
				handle_active_phrases(save_new=True)
				handle_active_words()
				set_next_to_active()

def ignore(event):
	global active
	global active_looked_up
	global word_queue
	global removed_from_queue
	global active_phrase
	global phrases

	if active and not editing:
		word = active['word']
		status = active['status']
		active['status'] = 'ignored'
		add_to_ignored(word)

		# Remove word from kown words and learning words
		if status == 'known':
			del known_words[word]
		elif status == 'learning':
			del learning_words[word]

		# Remove all instances of word in queue
		removed_from_queue.append(active)
		words_to_remove = []
		for word_dict in word_queue:
			if word_dict['word'] == word:
				words_to_remove.append(word_dict)

		for word in words_to_remove:
			removed_from_queue.append(word)
			word_queue.remove(word)

		mark_all_instances(active['word'], 'ignored')
		unset_active_word()
		set_next_to_active()

	if active_phrase and not editing:
		mark_all_phrase_instances(active_phrase['phrase_words'], 'none')
		phrase_words = active_phrase['phrase_words']
		first_word = phrase_words[0]
		if first_word in phrases:
			phrases_with_same_first_word = phrases[first_word]
			for phrase_num, p in enumerate(phrases_with_same_first_word):
				if str(p['phrase_words']) == str(phrase_words):
					del phrases_with_same_first_word[phrase_num]
					if len(phrases_with_same_first_word) == 0:
						phrases.pop(first_word)
		active_phrase = False
		clear_side_field()

def known(event):
	global active
	global active_looked_up
	global word_queue
	global removed_from_queue

	if active and not editing:
		word = active['word']
		info = None
		if active_looked_up:
			info = get_word_info()
		active['status'] = 'known'
		add_to_known(word, info)

		#Remove all instances of word in queue
		removed_from_queue.append(active)
		words_to_remove = []
		for word_dict in word_queue:
			if word_dict['word'] == word:
				words_to_remove.append(word_dict)

		for word in words_to_remove:
			removed_from_queue.append(word)
			word_queue.remove(word)

		mark_all_instances(active['word'], 'known')
		unset_active_word()
		set_next_to_active()

	if active_phrase and not editing:
		ignore(event)

# Repeat learning words from the beginning of the text
def repeat_learning_words(event):
	global editing
	if not editing:
		go_to_start()
		set_next_to_active()
		if active:
			active_word_tag = str(active['line']) + '.' + str(active['word_num'])
			text.see(active_word_tag)

# Put back all learning words in the queue to go through them from start
def go_to_start():
	global word_queue
	global removed_from_queue
	global editing
	if not editing:
		handle_active_phrases()
		handle_active_words()
		remove_from_removed = []
		for word in removed_from_queue:
			if word['status'] == 'learning':
				if not word_in_queue(word['index']):
					put_back_in_queue_sorted(word)
				remove_from_removed.append(word)
		for word in remove_from_removed:
			removed_from_queue.remove(word)

def go_to_previous_learning_word(event):
	global word_queue
	global removed_from_queue
	global editing
	global active_looked_up
	if not editing:
		if active:
			current_index = active['index']
			closest_index = -1
			previous_word = None
			for word in removed_from_queue:
				word_index = word['index']
				if (word_index < current_index and
					word_index > closest_index and
					word['status'] == 'learning'):
					closest_index = word_index
					previous_word = word
			if previous_word:
				handle_active_phrases()
				handle_active_words(unqueue_looked_up=False)
				put_back_in_queue_sorted(previous_word)
				removed_from_queue.remove(previous_word)
				set_next_to_active()

def mark_sentence_as_phrase(event):
	global active
	global editing
	global sentences
	if active and not editing:
		line = active['line']
		sentence_indices = sentences[line]
		word_index = active['word_num']
		for (start_index, end_index) in sentence_indices:
			if word_index >= start_index and word_index <= end_index:
				word_tag1 = str(line) + '.' + str(start_index)
				word_tag2 = str(line) + '.' + str(end_index)
				handle_active_phrases()
				handle_active_words()
				# Since sentences tend to be long, they are not
				# pronounced by default
				new_phrase(word_tag1, word_tag2, do_pronounce=False)
				break

def pronounce(word, language):
	global active
	global active_looked_up
	global text_word
	global last_pronounced
	global mac_voice

	# Mac OS text-to-speak
	if mac_voice:
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
			if active and active_looked_up: # Pronounce nouns with article
				side_field_word = text_word.get('1.0','end')
				side_field_word = side_field_word.split(',')
				side_field_word = side_field_word[0]
				side_field_word = side_field_word.replace("'","´")
				subprocess.call(shlex.split('say -v ' + voice + ' ' + str(side_field_word)))
			else:
				subprocess.call(shlex.split('say -v ' + voice + ' ' + str(word)))
		
	# Google
	else:
		if last_pronounced:
			if last_pronounced['word'] == word:
				sound = last_pronounced['sound']
			elif active and active_looked_up:
				side_field_word = text_word.get('1.0','end')
				side_field_word = side_field_word.split(',')
				side_field_word = side_field_word[0]
				sound = Speech(side_field_word, get_language_code(language))
				last_pronounced = {'word': word, 'sound': sound}
			else:
				sound = Speech(word, get_language_code(language))
		else:
			if active and active_looked_up:
				side_field_word = text_word.get('1.0','end')
				side_field_word = side_field_word.split(',')
				side_field_word = side_field_word[0]
				sound = Speech(side_field_word, get_language_code(language))
				last_pronounced = {'word': word, 'sound': sound}
			else:
				sound = Speech(word, get_language_code(language))
		sound.play()

def pronounce_active_word(event):
	global active
	global text_word
	global language
	if active and not editing:
		pronounce(active['word'], language)

	if active_phrase and not editing:
		pronounce(text_word.get('1.0','end'), language)

def pronounce_next(event):
	global w
	go_to_next(event)
	w.update_idletasks()
	w.after(100, pronounce_active_word(event))

def edit_personal_translation(event):
	global w
	global editing
	global active_looked_up
	global active_phrase
	global text_trans
	global text_personal_trans
	global info_for_showed_word
	if not editing and (active_looked_up or active_phrase):
		editing = True
		text_personal_trans.grid(row=3, column=0, sticky='nswe')
		text_personal_trans.focus()

		current_personal_trans = get_current_personal_trans()
		if current_personal_trans:
			text_personal_trans.insert('1.0', current_personal_trans)

			# Temporarily delete the personal translation while editing
			# Forcing the order below gives a feeling of less flickering
			current_trans_num_lines = current_personal_trans.count('\n')
			num_lines_to_delete = current_trans_num_lines + 1
			index2 = str(num_lines_to_delete + 1) + '.0'
			text_trans.configure(state='normal')
			w.update_idletasks()
			w.after(100, text_trans.delete('1.0', index2))
			text_trans.configure(state='disabled')

def get_current_personal_trans():
	global active_looked_up
	global active_phrase
	global info_for_showed_word
	if active_looked_up or active_phrase:
		if 'trans' in info_for_showed_word:
			return get_personal_translation(info_for_showed_word['trans'])
	return None

def delete_current_personal_trans():
	global active_looked_up
	global active_phrase
	global info_for_showed_word
	if active_looked_up or active_phrase:
		if 'trans' in info_for_showed_word:
			delete_personal_translation(info_for_showed_word['trans'])
	return None

def change_remark(event):
	global editing
	global active_looked_up
	global active_phrase
	if not editing and (active_looked_up or active_phrase):
		editing = True
		text_remark.configure(state="normal")
		text_remark.focus()

def scroll_up(event):
    scroll_lines(-10, text)

def scroll_down(event):
    scroll_lines(10, text)

def scroll_up_translation(event):
    scroll_lines(-10, text_trans)

def scroll_down_translation(event):
    scroll_lines(10, text_trans)

def scroll_up_remark(event):
    scroll_lines(-10, text_remark)

def scroll_down_remark(event):
    scroll_lines(10, text_remark)

def scroll_lines(num_lines, text_field):
	global editing
	if not editing:
		# Number of small scroll steps for animation
		steps = 10
		# Amount to scroll per step
		step_size = num_lines / steps
		for i in range(steps):
			w.after(i * 20, lambda step_size=step_size: text_field.yview_scroll(int(step_size), "units"))

def open_external(event):
	global active
	global editing
	global external_resources

	if not editing and (active or active_phrase):
		pressed_key = event.keysym
		url = None
		phrase_word_delimiter = None
		for key, resource_info in external_resources.items():
			if pressed_key == key and 'url' in resource_info:
				url = resource_info['url']
				if 'phrase_word_delimiter' in resource_info:
					phrase_word_delimiter = resource_info['phrase_word_delimiter']
				break
		
		if not url:
			return
		
		url_parts = url.split('%s')
		if not len(url_parts) == 2:
			error_string = ('Could not open the external resource due to incorrect formating. '
				+ f'The url {url} should contain exactly one %s as a word placeholder.')
			return

		lookup_text = None
		if active:
			lookup_text = active["word"]
		elif active_phrase and phrase_word_delimiter:
			lookup_text = phrase_word_delimiter.join(active_phrase["phrase_words"])

		if language == 'russian':
			lookup_text = remove_russian_accents(lookup_text)
			
		if lookup_text:
			url = url_parts[0] + lookup_text + url_parts[1]
			open_url_in_old_tab(url)

def open_url_in_old_tab(url):
	global new_browser_tab
	new_browser_tab = False # This was added when the function with Chrome stopped working
	if not new_browser_tab:
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
		new_browser_tab = False

remark_without_third_lang = False
last_word_translated_to_third_lang = ''
def add_third_lang_trans(event):
	global text_word
	global text_trans
	global text_remark
	global remark_without_third_lang
	global last_word_translated_to_third_lang
	global active_looked_up
	global active_phrase
	global editing
	global info_for_showed_word

	if (active_looked_up or active_phrase) and not editing:
		word = info_for_showed_word['dict_word']
		trans = info_for_showed_word['trans']
		text_remark.configure(state='normal')
		# Remove translation if already added
		if remark_without_third_lang and word == last_word_translated_to_third_lang:
			text_remark.delete('1.0','end')
			remark_without_third_lang = remove_new_line_at_end(remark_without_third_lang)
			text_remark.insert('1.0',remark_without_third_lang)
			remark_without_third_lang = False
		# Otherwise, get the third_lang translation
		else:
			remark_without_third_lang = text_remark.get('1.0','end')
			text_remark.tag_configure('third_lang_header', font=(font, side_field_fonts['remark'][1], 'italic'))
			if len(remark_without_third_lang) > 1:
				title_string = '\n\n' + f'{third_lang.capitalize()} translations: '
				text_remark.insert('end', title_string, 'third_lang_header')
				text_remark.insert('end', '\n' + translate_to_third_lang(word, trans))
			else:
				title_string = f'{third_lang.capitalize()} translations: '
				text_remark.insert('end', title_string, 'third_lang_header')
				text_remark.insert('end', '\n' + translate_to_third_lang(word, trans))
			last_word_translated_to_third_lang = word
		text_remark.configure(state='disabled')

# Add a Google translation to the definitions of the word and show in the side field.
# Reverse if Google translation already is added.
def add_google_trans(event):
	global active_looked_up
	global active_phrase
	global info_for_showed_word
	global editing
	if (active_looked_up or active_phrase) and not editing:
		has_google_trans = has_google_translation(info_for_showed_word['trans'])
		trans_list = info_for_showed_word['trans']
		if not has_google_trans:
			google_trans = legilo_translator.get_google_translation(info_for_showed_word['dict_word'])
			trans_list += google_trans
		else:
			delete_google_translation(trans_list)
		update_translation_for_showed_word()

def quit_program():
	if use_message_box:
		if saving_on:
			ans = messagebox.askyesnocancel("Quit", "Do you want to save the changes?")
		else:
			ans = False
	elif saving_on:
		ans = True
	if ans is not None:
		if ans:
			save_all()
		w.destroy()
		start()

def quit_without_saving(event):
	w.destroy()
	print('Quitted without saving progress.')
	start()

# Find word from index
def word_from_index(index):
	lineandchar = index.split(".")
	i = int(lineandchar[0])-1
	character = int(lineandchar[1])
	end_index = None
	word_num = None
	line = None
	for j in word_end[i]: # Compare index with word end indices to find the word's end index
		if int((j.split("."))[1]) > int((index.split("."))[1]):
			end_index = j
			break
	if end_index:
		j = word_end[i].index(end_index)
		# Check that index is larger than or equal to the word's start index
		if int((word_start[i][j].split("."))[1]) <= int((index.split("."))[1]):
			line = i+1
			word_num = j
	return line, word_num

# Pressing enter in personal translation field to stop editing
def enter_in_personal_translation_field(event):
	global editing
	global text_personal_trans
	global w
	unfocus()
	editing = False
	add_personal_translation_info_to_showed_word()
	# Forcing the order below gives a feeling of less flickering
	w.update_idletasks()
	w.after(100, text_personal_trans.grid_forget())
	return 'break'

# Pressing enter in remark field to stop editing
def enter_in_remark_field(event):
	global editing
	unfocus()
	editing = False
	freeze_side_field()
	return 'break'

# Pressing shift + enter in info field to get new line
def new_line1(event):
	global text_personal_trans
	index = text_personal_trans.index(INSERT)
	text_personal_trans.insert(index,"\n")
	return 'break'
def new_line2(event):
	global text_remark
	index = text_remark.index(INSERT)
	text_remark.insert(index,"\n")
	return 'break'

# Pressing cmd + backspace in info field to empty it
def empty_text_field1(event):
	global text_personal_trans
	text_personal_trans.delete('1.0', 'end')
	return 'break'
def empty_text_field2(event):
	global text_remark
	text_remark.delete('1.0', 'end')
	return 'break'

# Select example sentence
sentence_word = "" # Last word for which example sentences were downloaded
sentence_list = [] # List with last downloaded collection of example sentences (for one word)
sentence_trans_list = [] # Corresponding translations to the sentences above
sentence_choice = 1 # Which of the sentences is chosen
def select_sentence(event):
	global sentence_word
	global sentence_list
	global sentence_trans_list
	global sentence_choice
	global text
	global editing
	global language
	if event.char in ['1','2','3','4','5','6','7','8','9','0']:
		n = int(event.char) # Sentence number
		sentence_choice = n
	else:
		sentence_choice += 1
		if sentence_choice > 9:
			sentence_choice = 0
		n = sentence_choice

	# If active word
	if active and not editing:
		# Get example sentences for word if not already downloaded
		if not sentence_word == active['word']:
			(sentence_list, sentence_trans_list) = get_sentences(active['word'], language, 7)
		if n > 0 and n < 8: # Choose example sentence from web
			sentence = sentence_list[n-1]
			sentence_trans = sentence_trans_list[n-1]
		elif n == 0: # Remove example sentence
			sentence = ''
			sentence_trans = ''
		else: # n == 8 or n == 9: Take text sentence as example sentence
			line = active['line']
			word_num = active['word_num']
			tag = str(line) + "." + str(word_num)
			word_start = int(str(text.tag_ranges(tag)[0]).split('.')[1])
			word_end = int(str(text.tag_ranges(tag)[1]).split('.')[1])
			text_line = text.get(str(line)+".0", str(line)+".end")
			sentence_start = 0
			sentence_end = len(text_line)
			for sign in ['.', '?', '!']:
				i = text_line[:word_start].rfind(sign)
				if i > sentence_start:
					sentence_start = i
				j = text_line.find(sign, word_end)
				if j >= 0 and j < sentence_end:
					sentence_end = j
			# Include end sign if available
			if len(text_line) > sentence_end:
				sentence_end += 1
			sentence = text_line[sentence_start:sentence_end]
			initial_sign_to_remove = True
			signs = [' ','.','!','?']
			while initial_sign_to_remove and len(sentence) > 0:
				all_signs_checked = False
				for signnbr, sign in enumerate(signs):
					if sign == sentence[0]:
						sentence = sentence[1:]
						break
					if signnbr == len(signs)-1:
						all_signs_checked = True
				if all_signs_checked:
					initial_sign_to_remove = False
			# Get translation from Google
			if n == 8:
				translator = Translator()
				sentence_trans = translator.translate(sentence, src=get_language_code(language), dest='en').text
			# Don't use a translation
			else: # n == 9
				sentence_trans = ""
		insert_sentence(sentence, sentence_trans)

# Get third_lang translations from string of english translations
include_trans_of_original_word = True
def translate_to_third_lang(word, trans):
	global include_trans_of_original_word
	translator = Translator()
	translations = []
	
	# Translate the original word directly to third_lang
	if include_trans_of_original_word:
		third_lang_trans = translator.translate(word,
										  src=get_language_code(language),
										  dest=get_language_code(third_lang)).text
		translations.append(word + ' = ' + third_lang_trans)
	
	# Translate the English translations to third_lang
	definitions = definitions_to_list(trans)
	for definition in definitions:
		third_lang_trans = translator.translate(definition,
										  src='en',
										  dest=get_language_code(third_lang)).text
		translations.append(definition + ' = ' + third_lang_trans)

	if len(translations) == 0:
		return ''
	
	return ', '.join(translations)

# Get definitions as a list with only definition strings
# Skips definitions that have several lines
def definitions_to_list(translations):
	def_strings = []
	for translation in translations:
		if 'definitions' in translation:
			for definition_entry in translation['definitions']:
				if 'definition' in definition_entry:
					definition = definition_entry['definition']
					# Don't use multiple-line definitions and skip definitions
					# of type "masculine plural of ..."
					if not definition.count('\n') > 1 and not ' of ' in definition:
						# Remove words in parentheses
						definition = re.sub(r'\([^)]*\)', '', definition)
						definition = definition.replace(';',',')
						definition_parts = definition.split(', ')
						for part in definition_parts:
							def_strings.append(part.strip())
	
	return def_strings

def activate_general_word_selection_mode():
	global editing
	global general_word_selection_mode
	global selected_tag1
	global saved_tag_config1
	if active and not editing:
		general_word_selection_mode = True
		selected_tag1 = str(active['line']) + '.' + str(active['word_num'])
		mark_word(active['line'], active['word_num'], active['status'])
		saved_tag_config1 = {'tag': selected_tag1, 'config': save_tag_config(selected_tag1)}
		mark_word(active['line'], active['word_num'], 'active')

def deactivate_general_word_selection_mode(event):
	global general_word_selection_mode
	global selected_tag1
	global saved_tag_config1
	if general_word_selection_mode:
		general_word_selection_mode = False
		if move_back_when_clicking_previous:
			handle_active_phrases()
			handle_active_words()
			go_to_start()
		skip_to_word(selected_tag1)
		selected_tag1 = None
		saved_tag_config1 = None

def general_word_selection_left(event):
	global editing
	global general_word_selection_mode
	global selected_tag1
	global saved_tag_config1
	if not editing:
		if not general_word_selection_mode:
			activate_general_word_selection_mode()
		prev_tag = get_previous_tag(selected_tag1)
		if prev_tag:
			apply_tag_config(saved_tag_config1['tag'], saved_tag_config1['config'])
			selected_tag1 = prev_tag
			line, word_num = [int(i) for i in selected_tag1.split('.')]
			saved_tag_config1 = {'tag': selected_tag1, 'config': save_tag_config(selected_tag1)}
			mark_word(line, word_num, 'active')

def general_word_selection_right(event):
	global editing
	global general_word_selection_mode
	global selected_tag1
	global saved_tag_config1
	if not editing:
		if not general_word_selection_mode:
			activate_general_word_selection_mode()
		next_tag = get_next_tag(selected_tag1)
		if next_tag:
			apply_tag_config(saved_tag_config1['tag'], saved_tag_config1['config'])
			selected_tag1 = next_tag
			line, word_num = [int(i) for i in selected_tag1.split('.')]
			saved_tag_config1 = {'tag': selected_tag1, 'config': save_tag_config(selected_tag1)}
			mark_word(line, word_num, 'active')

def activate_phrase_mode(event):
	global editing
	global text
	global phrase_mode
	global phrase_click_binding
	global selected_phrase_words
	global selected_tag1
	global saved_tag_config1

	if consider_phrases and not editing:
		global phrase_mode
		phrase_mode = True
		text.config(cursor='dot')
		selected_phrase_words = []

		if active:
			selected_tag1 = str(active['line']) + '.' + str(active['word_num'])
			mark_word(active['line'], active['word_num'], active['status'])
			saved_tag_config1 = {'tag': selected_tag1, 'config': save_tag_config(selected_tag1)}
			mark_word(active['line'], active['word_num'], 'selection')

def deactivate_phrase_mode(event=None):
	global editing
	global text
	global active
	global phrase_mode
	global phrase_click_binding
	global selected_phrase_words
	global selected_tag1
	global selected_tag2
	global saved_tag_config1
	global saved_tag_config2

	if consider_phrases and not editing:
		global phrase_mode
		text.config(cursor='arrow')
		selected_phrase_words = []
		if saved_tag_config1:
			apply_tag_config(saved_tag_config1['tag'], saved_tag_config1['config'])
			saved_tag_config1 = None
		if saved_tag_config2:
			apply_tag_config(saved_tag_config2['tag'], saved_tag_config2['config'])
			saved_tag_config2 = None
		if active:
			mark_word(active['line'], active['word_num'], 'active')
		selected_tag1 = None
		selected_tag2 = None
		phrase_mode = False

def phrase_word_selection_left(event):
	global active
	global selected_phrase_words
	if active:
		if len(selected_phrase_words) == 0:
			move_selection_to_prev(1)
		else:
			move_selection_to_prev(2)

def phrase_word_selection_right(event):
	global active
	global selected_phrase_words
	if active:
		if len(selected_phrase_words) == 0:
			move_selection_to_next(1)
		else:
			move_selection_to_next(2)

def move_selection_to_prev(selection_num):
	global selected_tag1
	global selected_tag2
	global saved_tag_config1
	global saved_tag_config2
	if selection_num == 1:
		prev_tag = get_previous_tag(selected_tag1)
		if prev_tag:
			apply_tag_config(saved_tag_config1['tag'], saved_tag_config1['config'])
			selected_tag1 = prev_tag
			line, word_num = [int(i) for i in selected_tag1.split('.')]
			saved_tag_config1 = {'tag': selected_tag1, 'config': save_tag_config(selected_tag1)}
			mark_word(line, word_num, 'selection')
	elif selection_num == 2:
		prev_tag = get_previous_tag(selected_tag2)
		if prev_tag:
			apply_tag_config(saved_tag_config2['tag'], saved_tag_config2['config'])
			selected_tag2 = prev_tag
			line, word_num = [int(i) for i in selected_tag2.split('.')]
			saved_tag_config2 = {'tag': selected_tag2, 'config': save_tag_config(selected_tag2)}
			mark_word(line, word_num, 'selection')

def move_selection_to_next(selection_num):
	global selected_tag1
	global selected_tag2
	global saved_tag_config1
	global saved_tag_config2
	if selection_num == 1:
		next_tag = get_next_tag(selected_tag1)
		if next_tag:
			apply_tag_config(saved_tag_config1['tag'], saved_tag_config1['config'])
			selected_tag1 = next_tag
			line, word_num = [int(i) for i in selected_tag1.split('.')]
			saved_tag_config1 = {'tag': selected_tag1, 'config': save_tag_config(selected_tag1)}
			mark_word(line, word_num, 'selection')
	elif selection_num == 2:
		next_tag = get_next_tag(selected_tag2)
		if next_tag:
			apply_tag_config(saved_tag_config2['tag'], saved_tag_config2['config'])
			selected_tag2 = next_tag
			line, word_num = [int(i) for i in selected_tag2.split('.')]
			saved_tag_config2 = {'tag': selected_tag2, 'config': save_tag_config(selected_tag2)}
			mark_word(line, word_num, 'selection')

def get_previous_tag(tag):
	global ordered_word_tags
	prev_index = ordered_word_tags.index(tag) - 1
	if prev_index >= 0 and prev_index < len(ordered_word_tags):
		return ordered_word_tags[prev_index]
	return None

def get_next_tag(tag):
	global ordered_word_tags
	next_index = ordered_word_tags.index(tag) + 1
	if next_index >= 0 and next_index < len(ordered_word_tags):
		return ordered_word_tags[next_index]
	return None

def enter_in_phrase_mode():
	global active
	global selected_phrase_words
	global selected_tag1
	global selected_tag2
	global saved_tag_config2
	handle_selected_phrase_word()
	if active and len(selected_phrase_words) == 1:
		line1, word_num1 = [int(i) for i in selected_tag1.split('.')]
		mark_word(line1, word_num1, 'selection')
		selected_tag2 = str(active['line']) + '.' + str(active['word_num'])
		if not selected_tag2 == selected_tag1:
			mark_word(active['line'], active['word_num'], active['status'])
		saved_tag_config2 = {'tag': selected_tag2, 'config': save_tag_config(selected_tag2)}
		mark_word(active['line'], active['word_num'], 'selection')

def new_phrase(word_tag1, word_tag2, do_pronounce=True):
	global active
	global active_looked_up
	global active_phrase
	global active_phrase_is_new
	global legilo_translator

	active_phrase_is_new = True

	lineandword_num1 = word_tag1.split(".")
	lineandword_num2 = word_tag2.split(".")
	word_num1 = lineandword_num1[1]
	word_num2 = lineandword_num2[1]

	# Sort words in right order
	if int(word_num1) > int(word_num2):
		temp = lineandword_num1
		lineandword_num1 = lineandword_num2
		lineandword_num2 = temp
		temp = word_tag1
		word_tag1 = word_tag2
		word_tag2 = temp

	first_word_start = str(text.tag_ranges(word_tag1)[0])
	lastword_end = str(text.tag_ranges(word_tag2)[1])
	phrase = text.get(first_word_start, lastword_end)

	line1 = int(lineandword_num1[0])
	word_num1 = int(lineandword_num1[1])
	line2 = int(lineandword_num2[0])
	word_num2 = int(lineandword_num2[1])
	if line1 == line2:
		line_words = text_words[line1-1]
		phrase_words = []
		for word_num in range(min(word_num1, word_num2), max(word_num1, word_num2)+1):
			phrase_words.append(line_words[word_num])

		info = legilo_translator.get_info(phrase, is_phrase=True)
		info['word_type'] = 'phrase'
		info['phrase_words'] = phrase_words
		(sentence, sentence_trans) = get_first_sentence(phrase, language)
		if len(sentence) > 0:
			info['sentence'] = sentence
			info['sentence_trans'] = sentence_trans
		active = None
		active_looked_up = False
		active_phrase = {'phrase_words': phrase_words, 'line': line1, 'startword_num': word_num1, 'endword_num': word_num2, 'status': 'learning'}

		# Add tag to new phrase
		phrase_start = word_start[active_phrase['line']-1][active_phrase['startword_num']]
		phrase_end = word_end[active_phrase['line']-1][active_phrase['endword_num']]
		text.tag_add('p' + str(line1) + "." + str(active_phrase['startword_num']), phrase_start, phrase_end)
		mark_phrase(active_phrase['line'], active_phrase['startword_num'], 'active')

		side_field_show(phrase, info, 'new phrase', do_pronounce=do_pronounce)
	else: 
		phrase_words = []
	selected_phrase_words = []

def remove_russian_accents(old_string):
	new_string = old_string.replace('а́','а')
	new_string = new_string.replace('е́','е')
	new_string = new_string.replace('и́','и')
	new_string = new_string.replace('о́','о')
	new_string = new_string.replace('у́','у')
	new_string = new_string.replace('ы́','ы')
	new_string = new_string.replace('э́','э')
	new_string = new_string.replace('ю́','ю')
	new_string = new_string.replace('я́','я')
	return new_string










def start():
	global config
	global start_window
	global start_text
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
	set_config_params()

	start_window = Tk()
	start_window.title("Legilo")
	width = start_window_size['width']
	height = start_window_size['height']
	center_window(start_window, width, height)

	# Create frames
	left_frame = Frame(start_window, width=450, height=height, background="black")
	left_frame.pack(side=LEFT)
	left_frame.pack_propagate(0)

	center_frame = Frame(start_window, width=300, height=height, background="black")
	center_frame.pack(side=LEFT)
	center_frame.pack_propagate(0)

	right_frame = Frame(start_window, width=450, height=height, background="black")
	right_frame.pack(side=LEFT)
	right_frame.pack_propagate(0)

	# Add text field
	start_text = Text(center_frame, width=50, height=100, wrap='word', background="black", foreground="white", font=(font,20))
	start_text.config(highlightbackground='black')
	start_text.pack(side=TOP)
	start_text.config(cursor='arrow')

	# Show text
	start_text.insert("end", "\n\n\nLegilo")
	start_text.tag_add("legilo", "4.0", "4.end")
	start_text.tag_configure("legilo", font=(font,80), justify='center')
	start_text.insert("end", "\n\nChoose language and option: ")
	start_text.tag_add("choice", "6.0", "6.end")
	start_text.tag_configure("choice", font=(font, 20, 'italic'))
	start_text.insert("end", "\n\n")
	selection_key_to_language = {}
	if 'languages' in config:
		for language in config['languages']:
			lang_settings = config['languages'][language]
			if 'menu_entry' in lang_settings and 'selection_key' in lang_settings:
				menu_entry = lang_settings['menu_entry']
				selection_key = lang_settings['selection_key']
				selection_key_to_language[selection_key] = language
				start_text.insert("end", menu_entry + '\n')
				start_window.bind(selection_key, lang_choice)
	start_text.insert("end", "\n")
	start_text.insert("end", "📄 [N]ew\n")
	start_text.insert("end", "📂 [O]pen\n")
	start_text.configure(state="disabled")

	start_window.bind("<n>", option_choice)
	start_window.bind("<o>", option_choice)
	start_window.bind("<Return>", confirm)

	start_window.mainloop()

# Set parameters to values specified in config
def set_config_params():
	global third_lang
	if 'third_language' in config:
		third_lang = config['third_language']

def lang_choice(event):
	global config
	global selection_key_to_language
	global language
	global option
	global option_and_lang
	global start_text
	global mac_voice

	choice = event.char
	language = selection_key_to_language[choice]

	# Set option for text to speech voice if specified
	lang_config = config['languages'][language]
	if 'text_to_speech_voice' in lang_config:
		text_to_speech_voice = lang_config['text_to_speech_voice']
		if text_to_speech_voice == 'mac':
			mac_voice = True
		elif text_to_speech_voice == 'google':
			mac_voice = False

	if language and option:
		language_text = language[0].upper() + language[1:]
		option_text = option[0].upper() + option[1:]
		if option_and_lang == False:
			start_text.configure(state="normal")
			start_text.insert("end", "\nChoice: " + option_text + " " + language_text)
			start_text.insert("end", "\nPress [enter] to continue\n")
			start_text.configure(state="disabled")
			option_and_lang = True
		else:
			start_text.configure(state="normal")
			start_text.delete("end -3 lines", "end")
			start_text.insert("end", "\nChoice: " + option_text + " " + language_text)
			start_text.insert("end", "\nPress [enter] to continue\n")
			start_text.configure(state="disabled")

option = None
language = None
option_and_lang = False
def option_choice(event):
	global language
	global option
	global option_and_lang
	global start_text
	choice = event.char
	if choice == 'n':
		option = 'new'
	elif choice == 'o':
		option = 'open'

	if language and option:
		language_text = language[0].upper() + language[1:]
		option_text = option[0].upper() + option[1:]
		if option_and_lang == False:
			start_text.configure(state="normal")
			start_text.insert("end", "\nChoice: " + option_text + " " + language_text)
			start_text.insert("end", "\nPress [enter] to continue\n")
			start_text.configure(state="disabled")
			option_and_lang = True
		else:
			start_text.configure(state="normal")
			start_text.delete("end -3 lines", "end")
			start_text.insert("end", "\nChoice: " + option_text + " " + language_text)
			start_text.insert("end", "\nPress [enter] to continue\n")
			start_text.configure(state="disabled")

def confirm(event):
	global start_window
	if option and language:
		start_window.destroy()
		if option == 'new':
			create_new(language)
		elif option == 'open':
			open_old(language)

def create_new(language):
	global new_text
	global new_title
	global new_window
	global editing_new_title
	global editing_new_text
	global last_opened_files
	editing_new_title = True
	editing_new_text = False

	new_window = Tk()
	new_window.title("Legilo")
	width = start_window_size['width']
	height = start_window_size['height']
	center_window(new_window, width, height)
	new_window.configure(bg=window_background_color)

	# Create frames
	top_frame = Frame(new_window, width=1200, height=50, background=window_background_color)
	top_frame.pack(side=TOP)
	top_frame.pack_propagate(0)

	bottom_frame = Frame(new_window, width=1200, height=50, background=window_background_color)
	bottom_frame.pack(side=BOTTOM)
	bottom_frame.pack_propagate(0)

	main_frame = Frame(new_window, width=1200, height=700, background=window_background_color)
	main_frame.pack(side=LEFT)
	main_frame.pack_propagate(0)

	# Add title field
	new_title = Text(main_frame, width=65, height=2, wrap='word', font=(font,20))
	new_title.pack(side=TOP)
	new_title.focus()

	# Add text field
	new_text = scrolledtextwindow.ScrolledText(
	    master = main_frame,
	    wrap   = 'word',  # wrap text at full words only
	    width  = 100,      # characters
	    height = 100,      # text lines
	    bg='white',        # background color of edit area
	    font=(font, 14)
	)
	new_text.pack(side=TOP)

	# Load list of last opened files
	try:
		last_opened_files = load_list("last_opened_files")
	except:
		last_opened_files = []

	new_text.bind("<Return>", confirm_new)
	new_title.bind("<Return>", confirm_new)
	new_window.bind("<Return>", confirm_new)
	new_text.bind("<Shift-Return>", new_line_new_text)
	new_title.bind("<Tab>", switch_focus_new_text)
	new_title.bind("<Button-1>", clicked_new_text_field)
	new_text.bind("<Button-1>", clicked_new_text_field)

	new_window.mainloop()

def confirm_new(event):
	global new_text
	global new_title
	global new_window
	global editing_new_title
	global editing_new_text
	global last_opened_files
	if editing_new_text:
		new_window.focus()
		editing_new_text = False
	elif editing_new_title:
		new_window.focus()
		editing_new_title = False
		title = new_title.get('1.0','end')
		if 'http://' in title or 'https://' in title:
			(title, text) = autoread(title)
			# Remove strange space-like sign to not get new lines
			title = title.replace(' ',' ')
			text = text.replace(' ',' ')
			new_title.delete('1.0','end')
			new_title.insert('1.0',title)
			new_text.delete('1.0','end')
			new_text.insert('1.0',text)
	else:
		title = new_title.get('1.0','end')
		if len(title) == 0 or title == '\n': # If there is no title
			title = new_text.get('1.0','1.end')
			text = new_text.get('2.0','end')
		else:
			text = new_text.get('1.0','end')
		file_name = create_file_name(title) + '.txt'
		directory = data_dir + '/' + language + '/texts'
		save_to_txt(title, text, file_name, directory)
		new_window.destroy()
		run(language, directory + '/' + file_name)
	return 'break'

def create_file_name(file_name):
	chars_to_remove = """\n'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„"""
	file_name = file_name.translate(str.maketrans(" ", "-", chars_to_remove))
	# Add date:
	file_name = str(date.today()) + '-' + file_name
	return file_name

def clicked_new_title_field(event):
	global new_window
	global editing_new_text
	global editing_new_title
	editing_new_text = False
	editing_new_title = True

def clicked_new_text_field(event):
	global new_window
	global editing_new_text
	global editing_new_title
	editing_new_text = True
	editing_new_title = False

def new_line_new_text(event):
	global new_text
	index = new_text.index(INSERT)
	new_text.insert(index,"\n")
	return 'break'

def switch_focus_new_text(event):
	global new_title
	global new_text
	global editing_new_title
	global editing_new_text
	editing_new_title = False
	editing_new_text = True
	new_text.focus()
	return 'break'

def open_old(language):
	global old_window
	global old_text
	global last_opened_files
	global old_path
	global editing

	editing = False # Used for removing files from list

	old_window = Tk()
	old_window.title("Legilo")
	width = start_window_size['width']
	height = start_window_size['height']
	center_window(old_window, width, height)
	old_window.configure(bg=window_background_color)

	# Create frames
	top_frame = Frame(old_window, width=1200, height=50, background=window_background_color)
	top_frame.pack(side=TOP)
	top_frame.pack_propagate(0)

	bottom_frame = Frame(old_window, width=1200, height=50, background=window_background_color)
	bottom_frame.pack(side=BOTTOM)
	bottom_frame.pack_propagate(0)

	main_frame = Frame(old_window, width=1200, height=700, background=window_background_color)
	main_frame.pack(side=LEFT)
	main_frame.pack_propagate(0)

	text_title_field = Text(main_frame, width=65, height=1, wrap='word', font=(font,30))
	text_title_field.pack(side=TOP)
	text_title_field.insert('1.0','Open file')
	text_title_field.tag_add("windowtitle", "1.0", "end")
	text_title_field.tag_configure("windowtitle", font=(font,30), justify='center')
	text_title_field.configure(state="disabled", background=window_background_color, highlightbackground=window_background_color)

	text_field1 = Text(main_frame, width=65, height=1, wrap='word', font=(font,20))
	text_field1.pack(side=TOP)
	text_field1.insert('1.0',f'Write name of file in {data_dir}/{language}/texts: ')
	text_field1.configure(state="disabled", background=window_background_color, highlightbackground=window_background_color)

	old_path = Text(main_frame, width=65, height=1, wrap='word', font=(font,20))
	old_path.pack(side=TOP)

	text_field1 = Text(main_frame, width=65, height=1, wrap='word', font=(font,20))
	text_field1.pack(side=TOP)
	text_field1.insert('1.0','Choose one of the latest files: ')
	text_field1.configure(state="disabled", background=window_background_color, highlightbackground=window_background_color)

	old_text = Text(main_frame, width=65, height=50, wrap='word', font=(font,20))
	old_text.pack(side=TOP)
	old_text.configure(state="disabled")

	# Load list of last opened files
	try:
		last_opened_files = load_list("last_opened_files")
	except:
		last_opened_files = []

	remove_deleted_text_files(last_opened_files)

	old_text.configure(state="normal")
	for i, f in reversed(list(enumerate(last_opened_files))):
		old_text.insert('end', '[' + str(len(last_opened_files)-i) + '] ' + f['title'])
	old_text.configure(state="disabled")

	old_path.bind("<Return>", open_old_from_path)
	old_window.bind("1", open_old_from_number)
	old_window.bind("2", open_old_from_number)
	old_window.bind("3", open_old_from_number)
	old_window.bind("4", open_old_from_number)
	old_window.bind("5", open_old_from_number)
	old_window.bind("6", open_old_from_number)
	old_window.bind("7", open_old_from_number)
	old_window.bind("8", open_old_from_number)
	old_window.bind("9", open_old_from_number)
	old_window.bind("r", remove_old_from_list)

	old_window.mainloop()

# Remove deleted files from list of recently opened files
def remove_deleted_text_files(last_opened_files):
	items_to_remove = []
	for item in last_opened_files:
		if not os.path.exists(item['file_name']):
			items_to_remove.append(item)
	for item in items_to_remove:
		last_opened_files.remove(item)

def open_old_from_path(event):
	global old_path
	if not editing:
		#last_opened_files.append({'title': title, 'path': path})
		file_name = old_path.get('1.0','end')
		file_name = remove_new_line_at_end(file_name)
		if len(file_name) < 4:
			file_name = file_name + '.txt'
		elif not file_name[:-4] == '.txt':
			file_name = file_name + '.txt'
		old_window.destroy()
		directory = data_dir + '/' + language + '/texts'
		run(language, directory + '/' + file_name)

def open_old_from_number(event):
	global last_opened_files
	global old_text
	global editing
	n = int(event.char)
	if n >= 1 and n <= len(last_opened_files):
		i = len(last_opened_files) - n
	if not editing:
		file_name = last_opened_files[i]['file_name']
		old_window.destroy()
		run(language, file_name)
	else: # If editing
		del last_opened_files[i]
		old_text.configure(state="normal")
		old_text.delete('1.0','end')
		for i, f in reversed(list(enumerate(last_opened_files))):
			old_text.insert('end', '[' + str(len(last_opened_files)-i) + '] ' + f['title'])
		old_text.configure(state="disabled")
		editing = False



def remove_old_from_list(event):
	global last_opened_files
	global old_text
	global editing
	if not editing:
		editing = True
		old_text.configure(state="normal", font=(font,20))
		old_text.delete('1.0','end')
		old_text.insert('1.0','Remove from list: \nEnter number to remove or press [r] again to cancel.\n')
		for i, f in reversed(list(enumerate(last_opened_files))):
			old_text.insert('end', '[' + str(len(last_opened_files)-i) + '] ' + f['title'])
		old_text.configure(state="disabled")
	else:
		editing = False
		old_text.configure(state="normal", font=(font,20))
		old_text.delete('1.0','end')
		for i, f in reversed(list(enumerate(last_opened_files))):
			old_text.insert('end', '[' + str(len(last_opened_files)-i) + '] ' + f['title'])
		old_text.configure(state="disabled")









# Main window
def run(language, text_file):
	global w
	global text
	global sentences
	global last_opened_files
	global text_words
	global word_start
	global word_end
	global ordered_word_tags

	global text_status
	global text_word
	global text_personal_trans
	global text_trans
	global text_remark
	global text_example_title
	global text_example

	global opened_text_path
	global known_words
	global learning_words
	global ignored_words
	global phrases
	global active
	global active_looked_up
	global active_phrase
	global active_phrase_is_new
	global last_pronounced
	global editing
	global external_resources
	global general_word_selection_mode
	global phrase_mode
	global selected_phrase_words
	global word_queue
	global removed_from_queue
	global text_phrases
	global selected_tag1
	global selected_tag2
	global saved_tag_config1
	global saved_tag_config2

	global legilo_translator

	legilo_translator = LegiloTranslator(language, use_lemma=use_lemma)

	# Word lists
	known_words = None
	learning_words = None
	ignored_words = None
	phrases = None

	active = None # Current active word
	active_looked_up = False # Gives whether the active word has been looked up
	active_phrase = False # Current active phrase
	active_phrase_is_new = False # The active phrase is new (not yet saved)
	last_pronounced = False # Last pronounced word
	editing = False # Editing text fields
	general_word_selection_mode = False # General word selection mode active
	phrase_mode = False # Phrase mode active
	selected_phrase_words = [] # List of selected phrase words
	selected_tag1 = None # First keyboard selected word tag in phrase mode
	selected_tag2 = None # Second keyboard selected word tag in phrase mode
	saved_tag_config1 = None # Saved original tag config for selected_tag1
	saved_tag_config2 = None # Saved original tag config for selected_tag2

	word_queue = [] # Word queue
	removed_from_queue = [] # Words removed from queue
	text_phrases = [] # phrases in text

	# Load word lists from file
	load_all()

	# Create main window
	w = Tk()
	w.title("Legilo")
	w.configure(bg=window_background_color)
	width = main_window_size['width']
	height = main_window_size['height']
	center_window(w, width, height)

	# Create frames
	container = Frame(w) # Main container frame to hold all other frames
	container.pack(fill=BOTH, expand=True)
	container.grid_rowconfigure(0, weight=1)
	container.grid_columnconfigure(0, weight=1)
	container.grid_columnconfigure(1, weight=0)
	container.grid_columnconfigure(2, weight=1)

	left_margin_frame = Frame(container, background=window_background_color)
	left_margin_frame.grid(row=0, column=0, sticky='nswe')
	
	main_frame = Frame(container, background=window_background_color)
	main_frame.grid(row=0, column=1, sticky='nswe')

	main_frame.grid_rowconfigure(0, weight=1)
	main_frame.grid_columnconfigure(0, weight=1)
	
	right_margin_frame = Frame(container, background=window_background_color)
	right_margin_frame.grid(row=0, column=2, sticky='nswe')

	text_frame = Frame(main_frame, background=window_background_color)
	text_frame.grid(row=0, column=0, padx=20, pady=20, sticky='nswe')

	text_frame.grid_rowconfigure(0, weight=1)
	text_frame.grid_columnconfigure(0, weight=1)

	side_frame = Frame(main_frame, background=window_background_color)
	side_frame.grid(row=0, column=1, padx=20, pady=20, sticky='nswe')

	side_frame.grid_rowconfigure(0, weight=0)
	side_frame.grid_rowconfigure(1, weight=0)
	side_frame.grid_rowconfigure(2, weight=0)
	side_frame.grid_rowconfigure(3, weight=0)
	side_frame.grid_rowconfigure(4, weight=1)
	side_frame.grid_rowconfigure(5, weight=0)
	side_frame.grid_rowconfigure(6, weight=0)
	side_frame.grid_rowconfigure(7, weight=0)
	side_frame.grid_rowconfigure(8, weight=0)
	side_frame.grid_columnconfigure(0, weight=1)

	# Add text field
	text = scrolledtextwindow.ScrolledText(
	    master=text_frame,
		padx=text_field_padx,
		pady=text_field_pady,
	    wrap='word',  # wrap text at full words only
		width=text_field_width,
	    bg='white',        # background color of edit area
		highlightthickness=0,
		borderwidth=0, 
	    font=(font, font_size),
		cursor='arrow'
	)
	text.grid(row=0, column=0, sticky='nswe')

	# Add text fields in side field
	text_status = Text(side_frame, height=1, width=0, padx=side_field_padx, pady=side_field_pady,
				   wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['status'])
	text_status.grid(row=0, column=0, sticky='nswe')
	
	text_word = Text(side_frame, height=1, width=0, padx=side_field_padx, pady=side_field_pady,
				 wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['word'])
	text_word.grid(row=1, column=0, sticky='nswe')
	
	text_trans_title = Text(side_frame, height=1, width=0, padx=side_field_padx, pady=side_field_pady,
					   wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['title'],
					   background=side_field_fonts['field_title_background'],
					   foreground=side_field_fonts['field_title_text_color'])
	text_trans_title.grid(row=2, column=0, sticky='nswe')
	text_trans_title.insert('1.0', 'Translations: ')
	text_trans_title.configure(state="disabled")
	
	text_personal_trans = Text(side_frame, width=side_field_width, height=5, padx=side_field_padx, pady=side_field_pady,
				  wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['translation'],
				  background='orange')
	text_personal_trans.grid(row=3, column=0, sticky='nswe')
	text_personal_trans.grid_forget()
	
	text_trans = Text(side_frame, width=side_field_width, height=20, padx=side_field_padx, pady=side_field_pady,
				  wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['translation'])
	text_trans.grid(row=4, column=0, sticky='nswe')
	
	text_remark_title = Text(side_frame, height=1, width=0, padx=side_field_padx, pady=side_field_pady,
							 wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['title'],
							 background=side_field_fonts['field_title_background'],
							 foreground=side_field_fonts['field_title_text_color'])
	text_remark_title.grid(row=5, column=0, sticky='nswe')
	text_remark_title.insert('1.0', 'Notes & Remarks: ')
	text_remark_title.configure(state="disabled")

	text_remark = Text(side_frame, height=10, width=0, padx=side_field_padx, pady=side_field_pady,
				   wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['remark'])
	text_remark.grid(row=6, column=0, sticky='nswe')
	
	text_example_title = Text(side_frame, height=1, width=0, padx=side_field_padx, pady=side_field_pady,
						 wrap='word', highlightthickness=0, borderwidth=0,
						 font=side_field_fonts['title'], background=side_field_fonts['field_title_background'],
						 foreground=side_field_fonts['field_title_text_color'])
	text_example_title.grid(row=7, column=0, sticky='nswe')
	text_example_title.insert('1.0', 'Example Sentence: ')
	text_example_title.configure(state="disabled")
	
	text_example = Text(side_frame, height=4, width=0, padx=side_field_padx, pady=side_field_pady,
					wrap='word', highlightthickness=0, borderwidth=0, font=side_field_fonts['example_translation'])
	text_example.grid(row=8, column=0, sticky='nswe')
	freeze_side_field()

	# Read text
	opened_text_path = text_file
	with open(text_file) as file:
		lines = file.readlines()

	# Get saved state and remove state info from text
	state = None
	if len(lines) > 0 and '#state' in lines[0]:
		stateinfo = lines[0].split(' ')
		if len(stateinfo) > 1:
			state = stateinfo[1]
		lines = lines[1:]
		with open(opened_text_path, "w") as file:
			for line in lines:
				file.write(line)

	nbr_lines = len(lines)

	# Show text
	for i in range(nbr_lines): # Go through the lines
		line = lines[i]
		# Fix issue with scrolling when the character ’ is in the text
		line = line.translate(str.maketrans("’", "'"))
		text.insert(str(i+1) + ".0", line) # Insert text at line i and character 0
		# Mark headlines
		has_titles = False
		last_line_char = '.'
		new_lines_removed = False
		check_if_title = line
		while len(check_if_title) > 0 and not new_lines_removed:
			if check_if_title[-1] == '\n' or check_if_title[-1] == ' ':
				check_if_title = check_if_title[0:-1]
			else:
				new_lines_removed = True
		if len(check_if_title) > 0:
			last_line_char = check_if_title[-1]
		previous_line_empty = False
		if i > 0:
			if len(lines[i-1]) < 3:
				previous_line_empty = True
		# Main title
		if not last_line_char in '.?!:,]*-' and i == 0 and len(line) < 200:
			text.tag_add('l' + str(i+1), str(i+1) + '.' + str(0), str(i+1) + '.' + 'end')
			text.tag_config('l' + str(i+1), font=(font, main_title_size, "bold"))
		# Other titles
		if (not last_line_char in '.?!:,])}*-;"' and previous_line_empty
	  		and len(line) < 200 and i < nbr_lines-1 and not '.' in line):
			has_titles = True
			text.tag_add('l' + str(i+1), str(i+1) + '.' + str(0), str(i+1) + '.' + 'end')
			text.tag_config('l' + str(i+1), font=(font, title_size, "bold"))
		# Mark preamble
		if has_titles:
			for i in range(min(3,nbr_lines)):
				line = lines[i]
				if i > 0 and len(line) < 400:
					text.tag_add('l' + str(i+1), str(i+1) + '.' + str(0), str(i+1) + '.' + 'end')
					text.tag_config('l' + str(i+1), font=(font, title_size, "bold"))
	text.configure(state="disabled")

	# Add opened text to last opened files list and limit its length to 9
	if len(lines[0]) > 0:
		title_of_text = lines[0]
	else:
		title_of_text = 'Unknown Title'
	# Delete in last opened files
	title = None
	for i, file in enumerate(last_opened_files):
		if text_file == file['file_name']:
			title = file['title']
			del last_opened_files[i]
	last_opened_files.append({'title': title_of_text, 'file_name': text_file})
	if len(last_opened_files) > 9:
		last_opened_files.pop(0)

	# Get words
	text_words = [None]*nbr_lines
	word_start = [None]*nbr_lines
	word_end = [None]*nbr_lines
	ordered_word_tags = []
	word_count = 0
	for i in range(nbr_lines): # Go through the lines
		line = lines[i]
		line = line.lower()
		rest_of_line = line
		chars_to_remove = "" #"""!"#$%&()*+,./:;<=>?@[]^_`{|}~"""
		line = line.translate(str.maketrans("""'´’!"#$%&()*+,./:;<=>?@[]^_`{|}~«»“”„""", "                                     ", chars_to_remove))
		rest_of_line = line
		line_words = line.split()
		num_line_words = len(line_words)
		text_words[i] = [None]*num_line_words
		word_start[i] = [None]*num_line_words
		word_end[i] = [None]*num_line_words
		char_count = 0
		line_phrases = []
		for j, word in enumerate(line_words):
			index = rest_of_line.find(word)
			rest_of_line = rest_of_line[index+len(word):]
			char_count = char_count + index
			text_words[i][j] = word
			word_start[i][j] = str(i+1) + "." + str(char_count)
			word_end[i][j] = str(i+1) + "." + str(char_count + len(word))
			char_count = char_count + len(word)
			word_queue.append({'index' : word_count, 'word' : word, 'line' : i+1, 'word_num' : j})
			word_tag = str(i+1) + "." + str(j)
			ordered_word_tags.append(word_tag)
			text.tag_add(word_tag, word_start[i][j], word_end[i][j])
			text.tag_configure(word_tag, wrap='word')
			text.tag_bind(word_tag, "<Button-1>", mouse_click)

			# If word is in start of an phrase:
			if consider_phrases:
				if word in phrases:
					phrases_list = phrases[word]
					for phrase in phrases_list:
						phrase_words = phrase['phrase_words']
						if len(phrase_words) <= num_line_words - j:
							for k, exp_word in enumerate(phrase_words):
								if exp_word == line_words[j+k]:
									matching_phrases = True
								else:
									matching_phrases = False
									break
							if matching_phrases:
								text_phrases.append({'phrase_words' : phrase_words, 'line' : i+1,
								'startword_num' : j, 'endword_num' : j+len(phrase_words)-1})
								line_phrases.append({'phrase_words' : phrase_words, 'line' : i+1,
								'startword_num' : j, 'endword_num' : j+len(phrase_words)-1})
								break
			word_count += 1

		# Add tags to phrases on the line
		if consider_phrases:
			for phrase in line_phrases:
				phrase_start = word_start[i][phrase['startword_num']]
				phrase_end = word_end[i][phrase['endword_num']]
				text.tag_add('p' + str(i+1) + "." + str(phrase['startword_num']), phrase_start, phrase_end)

	# Get sentences from text
	sentences = {}
	for i, line in enumerate(lines):
		sentences[i+1] = get_sentence_word_indices(line)

	# Set word status
	words_to_remove = []
	for i, word_dict in enumerate(word_queue):
		word = word_dict['word']
		if word in ignored_words:
			word_queue[i]['status'] = 'ignored'
			words_to_remove.append(word_dict)
		elif word in known_words:
			word_queue[i]['status'] = 'known'
			words_to_remove.append(word_dict)
		elif word in learning_words:
			word_queue[i]['status'] = 'learning'
		else:
			word_queue[i]['status'] = 'new'

	# Remove known and ignored words from queue
	for word in words_to_remove:
		removed_from_queue.append(word)
		word_queue.remove(word)

	# Mark words in queue
	for word in word_queue:
		mark_word(word['line'], word['word_num'] , word['status'])

	# Mark phrases in text
	for phrase in text_phrases:
		mark_phrase(phrase['line'], phrase['startword_num'], 'ordinary')

	# Set program to saved state
	if state:
		skip_to_word(state, scroll_to_word=True)

	# Set what to de when closing window
	w.protocol("WM_DELETE_WINDOW", quit_program)

	# Add key bindings
	## General
	w.bind("<Right>", go_to_next)
	w.bind("<space>", go_to_next)
	w.bind("<n>", go_to_next)
	w.bind("<Up>", enter)
	w.bind("<Return>", enter)
	w.bind("<Down>", known)
	w.bind("<k>", known)
	w.bind("<Left>", go_to_previous_learning_word)
	w.bind("<BackSpace>", ignore)
	w.bind("<x>", ignore)
	w.bind("<i>", edit_personal_translation)
	w.bind("<r>", change_remark)
	w.bind("<p>", pronounce_active_word)
	w.bind("<.>", pronounce_active_word)
	w.bind("<s>", add_third_lang_trans)
	w.bind("<t>", add_google_trans)
	w.bind("<a>", mark_sentence_as_phrase)
	w.bind("<b>", repeat_learning_words)

	## Scrolling
	w.bind("<Command-Key-Down>", scroll_down)
	w.bind("<Command-Key-Up>", scroll_up)
	w.bind("<Shift-Down>", scroll_down_translation)
	w.bind("<Shift-Up>", scroll_up_translation)
	w.bind("<Option-Down>", scroll_down_remark)
	w.bind("<Option-Up>", scroll_up_remark)

	## Phrase mode
	w.bind("<Meta_L>", activate_phrase_mode)
	w.bind("<KeyRelease-Meta_L>", deactivate_phrase_mode)
	w.bind("<Command-Key-Left>", phrase_word_selection_left)
	w.bind("<Command-Key-Right>", phrase_word_selection_right)

	## General word selection
	w.bind("<Shift-Left>", general_word_selection_left)
	w.bind("<Shift-Right>", general_word_selection_right)
	w.bind("<KeyRelease-Shift_L>", deactivate_general_word_selection_mode)

	## Saving
	w.bind("<Command-Key-s>", save_lists)
	w.bind("<Command-Key-t>", save_listsastxt)
	w.bind("<Command-Key-x>", quit_without_saving)

	## Open external resources
	common_resources = get_common_external_resources()
	configure_external_resources(config, common_resources)

	## Edit personal translation and remark
	text_remark.bind("<Button-1>", change_remark)

	text_personal_trans.bind("<Return>", enter_in_personal_translation_field)
	text_remark.bind("<Return>", enter_in_remark_field)

	text_personal_trans.bind("<Shift-Return>", new_line1)
	text_remark.bind("<Shift-Return>", new_line2)

	text_personal_trans.bind("<Command-Key-BackSpace>", empty_text_field1)
	text_remark.bind("<Command-Key-BackSpace>", empty_text_field2)

	## Select example sentence
	w.bind("1", select_sentence)
	w.bind("2", select_sentence)
	w.bind("3", select_sentence)
	w.bind("4", select_sentence)
	w.bind("5", select_sentence)
	w.bind("6", select_sentence)
	w.bind("7", select_sentence)
	w.bind("8", select_sentence)
	w.bind("9", select_sentence)
	w.bind("0", select_sentence)

	w.mainloop()

# Get external resources that are common for all languages
def get_common_external_resources():
	global language

	wiktionary_url = 'https://en.wiktionary.org/wiki/%s#' + language.capitalize()
	if language == 'croatian':
		wiktionary_url = 'https://en.wiktionary.org/wiki/%s#Serbo-Croatian'

	common_resources = [
		{'open_key': 'w',
   		'url': wiktionary_url,
   		'phrase_word_delimiter': '_'},
		{'open_key': 'g',
   		'url': 'https://www.google.com/search?q=%s',
   		'phrase_word_delimiter': '+'},
		{'open_key': 'f',
   		'url': 'https://www.google.com/search?q=%s&tbm=isch',
   		'phrase_word_delimiter': '+'},
		{'open_key': 'l',
   		'url': 'https://en.wikipedia.org/wiki/%s',
   		'phrase_word_delimiter': '_'}
	]

	external_resources = {}
	for resource in common_resources:
		external_resources[resource['open_key']] = resource
	return external_resources

def configure_external_resources(config, common_resources):
	global w
	global language
	global external_resources
	external_resources = common_resources
	if 'languages' in config and language in config['languages']:
		lang_config = config['languages'][language]
		if 'external_resources' in lang_config:
			for resource in lang_config['external_resources']:
				if 'open_key' in resource and 'url' in resource:
					external_resources[resource['open_key']] = resource
	
	for key, resource in external_resources.items():
		if key in w.bind():
			url = resource['url']
			used_keys = [i for i in w.bind() if not '<' in i]
			used_keys.sort()
			error_string = ('Error: Could not set external resource '
				   + f'{url}, to be opened by key {key}, '
				   + 'since the key already is used. Please choose '
				   + f'a key that is not in this list: {used_keys}.')
			print(error_string)
		else:
			w.bind(key, open_external)

# Split a line into sentences and get index of first and last word in each sentence
def get_sentence_word_indices(line):
	# This regular expression captures sentence-ending punctuation followed by a space or end of string.
    # It considers periods, exclamation marks, question marks, and ellipses as sentence-ending characters.
    sentence_endings = regex.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!|\.\.\.)\s+')
    word_splitter = regex.compile(r'\s+')
    
    sentences = sentence_endings.split(line)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    
    word_index = 0
    word_indices = []

    for sentence in sentences:
        words = word_splitter.split(sentence)
        num_words = len(words)
        if num_words > 0:
            first_word_index = word_index
            last_word_index = word_index + num_words - 1
            word_indices.append((first_word_index, last_word_index))
            word_index += num_words

    return word_indices








if __name__ == "__main__":
	start() # Open start window and get options