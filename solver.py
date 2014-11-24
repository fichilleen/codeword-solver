import sys
import re
from copy import deepcopy

debug = False

word_classes = []
dict_words = {}
puzzle = []
known = {}

VALID_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

class Word ( object ):
    ''' Instance per word, ie unbroken row or column of letters
    Take a subset of the dictionary matching the length of the word,
    and narrow down from there, by finding duplicated letters, regular
    expression, etc
    '''

    def __init__ ( self, word, len_dict ):
        self.word = word
        self.psuedo_word = deepcopy ( word )
        self.local_dict = len_dict
        self.solved = False

        # Look for duplicate letters
        letters = {}
        for i, char in enumerate(word):
            if letters.get ( char ):
                letters[char].append (i)
            else:
                letters[char] = [i]

        new_list = []
        keys_over_one = [k for k,v in letters.items() if len(v) > 1]
        for word in self.local_dict:
            match = True
            for k in keys_over_one:
                new_set = set()
                vals = letters[k]
                for x in vals:
                    new_set.add (word[x])
                if len(new_set) > 1:
                    match = False
                    break
            if match:
                new_list.append ( word )

        if len ( new_list ) > 0:
            self.local_dict = set(new_list)

        # Do the normal check for known letters
        self.narow_down()


    def narow_down ( self ):
        ''' Check if any num/letter pairs we know about are in the word,
        then narrow down from there '''

        if self.solved:
            return True
        if len(self.local_dict) == 1:
            self.solved = True
            return True

        if debug:
            starting_len = len(self.local_dict)

        # Build a "psuedo word" where we replace ints with known letters
        # this will be used for regex later.
        # Additionally, filter out words which contain known letters,
        # that we don't have
        found_known_letters = False
        no_match = []
        for num, char in known.items():
            if num not in self.psuedo_word:
                no_match.append ( char )
                continue
            found_known_letters = True
            while num in self.psuedo_word:
                i = self.psuedo_word.index ( num )
                self.psuedo_word[i] = char

        new_dict = []
        for local_word in self.local_dict:
            if any(char in local_word for char in no_match):
                continue
            new_dict.append ( local_word )
        if new_dict:
            self.local_dict = new_dict

        if found_known_letters:
            regex_str = []
            for i in self.psuedo_word:
                if type(i) == int:
                    regex_str.append('.')
                else:
                    regex_str.append(i)
            regex_str = ''.join(regex_str)
            matches = []
            for x in self.local_dict:
                match = re.match ( regex_str, x )
                if match:
                    matches.append ( match.string )
            if matches:
                self.local_dict = matches
            else:
                print ("Couldn't find a matching word for - %s" % self.word)
                return

        if debug:
            end_len = len(self.local_dict)
            if end_len != starting_len:
                print "Reduced length from %d to %d" % (starting_len, end_len)


    def only_possible_letter ( self ):
        ''' Check if all of the words in our local dictionary has a char
        that appears in the same position every time. If so, we know
        that the number matches the character
        '''
        if len(self.local_dict) == 1:
            self.solved = True
            for i,x in enumerate(self.local_dict[0]):
                known[self.word[i]] = x
            return True

        start = list(self.local_dict[0])
        for word in self.local_dict[1:]:
            for i, char in enumerate(word):
                if char != start[i]:
                    start[i] = None
        for i,x in enumerate(start):
            if x:
                known[self.word[i]] = x



# Import puzzle into mem
with open (sys.argv[2]) as puzzle_f:
    line_width = 0
    for line in puzzle_f:
        if line.startswith('#'):
            continue
        line = line.strip()
        if '=' in line:
            line = line.split('=')
            known [int(line[0])] = line[1]
            continue

    # Zero terminate lines, so the word builder finds a zero and
    # terminates the word. Means that a few things that iterate over the
    # puzzle have to stop at [-1], but removes code checking whether a
    # word is finished or not after each line
        if ',' in line:
            nums = line.split(',')
            line_width = len(nums)
            nums.append ('0')
            puzzle.append (map(int, nums))
    puzzle.append ([0]*line_width)


# Homogenise a dictionary file
with open (sys.argv[1]) as dictionary:
    for line in dictionary:
        line = line.upper().strip().replace("'",'')
        for char in line:
            if char not in VALID_CHARS:
                break
            word_len = len ( line )
            if not dict_words.get ( word_len ):
                dict_words[word_len] = set()
                dict_words[word_len].add ( line )
            else:
                dict_words[word_len].add ( line )

def build_words ( num, cur_word ):
    ''' Keep adding digit by digit each word-shape in the puzzle,
    until we hit a 0 '''
    if num == 0:
        word_len = len(cur_word)
        if word_len > 1:
            word_classes.append (Word(cur_word, dict_words[word_len]))
        cur_word = []
    else:
        cur_word.append ( num )
    return cur_word

cur_word = []
# Find words going down first
for i in range(len(puzzle[0])-1):
    for line in puzzle:
        cur_word = build_words ( line[i], cur_word )

for line in puzzle:
    for char in line:
        cur_word = build_words ( char, cur_word )


cur_known = 0
now_known = 1
passes = 0
while now_known != cur_known:
    passes += 1
    cur_known = len(known)
    print 'NEW PASS'

    for x in word_classes:
        x.only_possible_letter()

    for x in word_classes:
        x.narow_down()

    now_known = len(known)
    print '-'*80

print "Performed %d passes" % passes

if not all([x.solved for x in word_classes]):
    print "Couldn't solve puzzle"

for line in puzzle[:-1]:
    out = []
    for char in line[:-1]:
        if char == 0:
            out.append ('\x1b[40;1m   ')
            out.append('\x1b[0m')
        else:
            letter = '?'
            if known.get(char):
                letter = known[char]
            out.append ('\x1b[47;1m\x1b[30;1m %s ' % letter)
    out.append('\x1b[0m')
    print ''.join(out)

