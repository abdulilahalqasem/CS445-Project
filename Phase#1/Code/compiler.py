import re
import sys
from tkinter import *

delimiters = [';', '.', ',', '(', ')', '[', ']', '{', '}', ' ', '\n']
re_delimiters = r"[\,|\s|\(|\)|\[|\]|\{|\}]"
re_operaters = r"[*|-|/|+|%|=|<|>|^<=$|^>=$]"
re_preemtive_types = r"^boolean$|^byte$|^char$|^short$|^int$|^long$|^float$|^double$"
re_non_preemtive_types = r"^string$|^array$|^class$"
re_keywords = r"^var$|^and$|^or$|^not$|^if$|^elif$|^else$|^for$|^to$|^step$|^while$|^fun$|^then$|^end$|^return$|^continue$|^break$|^print$"

re_float_number = r"[+-]?[0-9]+[.,][0-9]+"
re_integer_number = r"[+-]?[0-9]"
re_string = r"[A-Za-z0-9_./\-]*"
re_char = r"'[0-9]'|'[a-zA-Z]'"

#
##
###


def removeLeftRecursion(rulesDiction):
    # for rule: A->Aa|b
    # result: A->bA',A'->aA'|#

    # 'store' has new rules to be added
    store = {}
    # traverse over rules
    for lhs in rulesDiction:
        # alphaRules stores subrules with left-recursion
        # betaRules stores subrules without left-recursion
        alphaRules = []
        betaRules = []
        # get rhs for current lhs
        allrhs = rulesDiction[lhs]
        for subrhs in allrhs:
            if subrhs[0] == lhs:
                alphaRules.append(subrhs[1:])
            else:
                betaRules.append(subrhs)
        # alpha and beta containing subrules are separated
        # now form two new rules
        if len(alphaRules) != 0:
            # to generate new unique symbol
            # add ' till unique not generated
            lhs_ = lhs + "'"
            while (lhs_ in rulesDiction.keys()) \
                    or (lhs_ in store.keys()):
                lhs_ += "'"
            # make beta rule
            for b in range(0, len(betaRules)):
                betaRules[b].append(lhs_)
            rulesDiction[lhs] = betaRules
            # make alpha rule
            for a in range(0, len(alphaRules)):
                alphaRules[a].append(lhs_)
            alphaRules.append(['#'])
            # store in temp dict, append to
            # - rulesDiction at end of traversal
            store[lhs_] = alphaRules
    # add newly generated rules generated
    # - after removing left recursion
    for left in store:
        rulesDiction[left] = store[left]
    return rulesDiction


def LeftFactoring(rulesDiction):
    # for rule: A->aDF|aCV|k
    # result: A->aA'|k, A'->DF|CV

    # newDict stores newly generated
    # - rules after left factoring
    newDict = {}
    # iterate over all rules of dictionary
    for lhs in rulesDiction:
        # get rhs for given lhs
        allrhs = rulesDiction[lhs]
        # temp dictionary helps detect left factoring
        temp = dict()
        for subrhs in allrhs:
            if subrhs[0] not in list(temp.keys()):
                temp[subrhs[0]] = [subrhs]
            else:
                temp[subrhs[0]].append(subrhs)
        # if value list count for any key in temp is > 1,
        # - it has left factoring
        # new_rule stores new subrules for current LHS symbol
        new_rule = []
        # temp_dict stores new subrules for left factoring
        tempo_dict = {}
        for term_key in temp:
            # get value from temp for term_key
            allStartingWithTermKey = temp[term_key]
            if len(allStartingWithTermKey) > 1:
                # left factoring required
                # to generate new unique symbol
                # - add ' till unique not generated
                lhs_ = lhs + "'"
                while (lhs_ in rulesDiction.keys()) \
                        or (lhs_ in tempo_dict.keys()):
                    lhs_ += "'"
                # append the left factored result
                new_rule.append([term_key, lhs_])
                # add expanded rules to tempo_dict
                ex_rules = []
                for g in temp[term_key]:
                    ex_rules.append(g[1:])
                tempo_dict[lhs_] = ex_rules
            else:
                # no left factoring required
                new_rule.append(allStartingWithTermKey[0])
        # add original rule
        newDict[lhs] = new_rule
        # add newly generated rules after left factoring
        for key in tempo_dict:
            newDict[key] = tempo_dict[key]
    return newDict


# calculation of first
# epsilon is denoted by '#' (semi-colon)

# pass rule in first function
def first(rule):
    global rules, nonterm_userdef, \
        term_userdef, diction, firsts
    # recursion base condition
    # (for terminal or epsilon)
    if len(rule) != 0 and (rule is not None):
        if rule[0] in term_userdef:
            return rule[0]
        elif rule[0] == '#':
            return '#'

    # condition for Non-Terminals
    if len(rule) != 0:
        if rule[0] in list(diction.keys()):
            # fres temporary list of result
            fres = []
            rhs_rules = diction[rule[0]]
            # call first on each rule of RHS
            # fetched (& take union)
            for itr in rhs_rules:
                indivRes = first(itr)
                if type(indivRes) is list:
                    for i in indivRes:
                        fres.append(i)
                else:
                    fres.append(indivRes)

            # if no epsilon in result
            # - received return fres
            if '#' not in fres:
                return fres
            else:
                # apply epsilon
                # rule => f(ABC)=f(A)-{e} U f(BC)
                newList = []
                fres.remove('#')
                if len(rule) > 1:
                    ansNew = first(rule[1:])
                    if ansNew != None:
                        if type(ansNew) is list:
                            newList = fres + ansNew
                        else:
                            newList = fres + [ansNew]
                    else:
                        newList = fres
                    return newList
                # if result is not already returned
                # - control reaches here
                # lastly if eplison still persists
                # - keep it in result of first
                fres.append('#')
                return fres


# calculation of follow
# use 'rules' list, and 'diction' dict from above

# follow function input is the split result on
# - Non-Terminal whose Follow we want to compute
def follow(nt):
    global start_symbol, rules, nonterm_userdef, \
        term_userdef, diction, firsts, follows
    # for start symbol return $ (recursion base case)

    solset = set()
    if nt == start_symbol:
        # return '$'
        solset.add('$')

    # check all occurrences
    # solset - is result of computed 'follow' so far

    # For input, check in all rules
    for curNT in diction:
        rhs = diction[curNT]
        # go for all productions of NT
        for subrule in rhs:
            if nt in subrule:
                # call for all occurrences on
                # - non-terminal in subrule
                while nt in subrule:
                    index_nt = subrule.index(nt)
                    subrule = subrule[index_nt + 1:]
                    # empty condition - call follow on LHS
                    if len(subrule) != 0:
                        # compute first if symbols on
                        # - RHS of target Non-Terminal exists
                        res = first(subrule)
                        # if epsilon in result apply rule
                        # - (A->aBX)- follow of -
                        # - follow(B)=(first(X)-{ep}) U follow(A)
                        if '#' in res:
                            newList = []
                            res.remove('#')
                            ansNew = follow(curNT)
                            if ansNew != None:
                                if type(ansNew) is list:
                                    newList = res + ansNew
                                else:
                                    newList = res + [ansNew]
                            else:
                                newList = res
                            res = newList
                    else:
                        # when nothing in RHS, go circular
                        # - and take follow of LHS
                        # only if (NT in LHS)!=curNT
                        if nt != curNT:
                            res = follow(curNT)

                    # add follow result in set form
                    if res is not None:
                        if type(res) is list:
                            for g in res:
                                solset.add(g)
                        else:
                            solset.add(res)
    return list(solset)


def computeAllFirsts():
    global rules, nonterm_userdef, \
        term_userdef, diction, firsts
    for rule in rules:
        k = rule.split("->")
        # remove un-necessary spaces
        k[0] = k[0].strip()
        k[1] = k[1].strip()
        rhs = k[1]
        multirhs = rhs.split('|')
        # remove un-necessary spaces
        for i in range(len(multirhs)):
            multirhs[i] = multirhs[i].strip()
            multirhs[i] = multirhs[i].split()
        diction[k[0]] = multirhs

    print(f"\nRules: \n")
    for y in diction:
        print(f"{y}->{diction[y]}")
    print(f"\nAfter elimination of left recursion:\n")

    diction = removeLeftRecursion(diction)
    for y in diction:
        print(f"{y}->{diction[y]}")
    print("\nAfter left factoring:\n")

    diction = LeftFactoring(diction)
    for y in diction:
        print(f"{y}->{diction[y]}")

    # calculate first for each rule
    # - (call first() on all RHS)
    for y in list(diction.keys()):
        t = set()
        for sub in diction.get(y):
            res = first(sub)
            if res != None:
                if type(res) is list:
                    for u in res:
                        t.add(u)
                else:
                    t.add(res)

        # save result in 'firsts' list
        firsts[y] = t

    print("\nCalculated firsts: ")
    key_list = list(firsts.keys())
    index = 0
    for gg in firsts:
        print(f"first({key_list[index]}) "
              f"=> {firsts.get(gg)}")
        index += 1


def computeAllFollows():
    global start_symbol, rules, nonterm_userdef,\
        term_userdef, diction, firsts, follows
    for NT in diction:
        solset = set()
        sol = follow(NT)
        if sol is not None:
            for g in sol:
                solset.add(g)
        follows[NT] = solset

    print("\nCalculated follows: ")
    key_list = list(follows.keys())
    index = 0
    for gg in follows:
        print(f"follow({key_list[index]})"
              f" => {follows[gg]}")
        index += 1


# create parse table
def createParseTable():
    import copy
    global diction, firsts, follows, term_userdef
    print("\nFirsts and Follow Result table\n")

    # find space size
    mx_len_first = 0
    mx_len_fol = 0
    for u in diction:
        k1 = len(str(firsts[u]))
        k2 = len(str(follows[u]))
        if k1 > mx_len_first:
            mx_len_first = k1
        if k2 > mx_len_fol:
            mx_len_fol = k2

    print(f"{{:<{10}}} "
          f"{{:<{mx_len_first + 5}}} "
          f"{{:<{mx_len_fol + 5}}}"
          .format("Non-T", "FIRST", "FOLLOW"))
    for u in diction:
        print(f"{{:<{10}}} "
              f"{{:<{mx_len_first + 5}}} "
              f"{{:<{mx_len_fol + 5}}}"
              .format(u, str(firsts[u]), str(follows[u])))

    # create matrix of row(NT) x [col(T) + 1($)]
    # create list of non-terminals
    ntlist = list(diction.keys())
    terminals = copy.deepcopy(term_userdef)
    terminals.append('$')

    # create the initial empty state of ,matrix
    mat = []
    for x in diction:
        row = []
        for y in terminals:
            row.append('')
        # of $ append one more col
        mat.append(row)

    # Classifying grammar as LL(1) or not LL(1)
    grammar_is_LL = True

    # rules implementation
    for lhs in diction:
        rhs = diction[lhs]
        for y in rhs:
            res = first(y)
            # epsilon is present,
            # - take union with follow
            if '#' in res:
                if type(res) == str:
                    firstFollow = []
                    fol_op = follows[lhs]
                    if fol_op is str:
                        firstFollow.append(fol_op)
                    else:
                        for u in fol_op:
                            firstFollow.append(u)
                    res = firstFollow
                else:
                    res.remove('#')
                    res = list(res) +\
                        list(follows[lhs])
            # add rules to table
            ttemp = []
            if type(res) is str:
                ttemp.append(res)
                res = copy.deepcopy(ttemp)
            for c in res:
                xnt = ntlist.index(lhs)
                yt = terminals.index(c)
                if mat[xnt][yt] == '':
                    mat[xnt][yt] = mat[xnt][yt] \
                        + f"{lhs}->{' '.join(y)}"
                else:
                    # if rule already present
                    if f"{lhs}->{y}" in mat[xnt][yt]:
                        continue
                    else:
                        grammar_is_LL = False
                        mat[xnt][yt] = mat[xnt][yt] \
                            + f",{lhs}->{' '.join(y)}"

    # final state of parse table
    print("\nGenerated parsing table:\n")
    frmt = "{:>12}" * len(terminals)
    print(frmt.format(*terminals))

    j = 0
    for y in mat:
        frmt1 = "{:>12}" * len(y)
        print(f"{ntlist[j]} {frmt1.format(*y)}")
        j += 1

    return (mat, grammar_is_LL, terminals)


def validateStringUsingStackBuffer(parsing_table, grammarll1,
                                   table_term_list, input_string,
                                   term_userdef, start_symbol):

    print(f"\nValidate String => {input_string}\n")

    # for more than one entries
    # - in one cell of parsing table
    if grammarll1 == False:
        return f"\nInput String = " \
            f"\"{input_string}\"\n" \
            f"Grammar is not LL(1)"

    # implementing stack buffer

    stack = [start_symbol, '$']
    buffer = []

    # reverse input string store in buffer
    input_string = input_string.split()
    input_string.reverse()
    buffer = ['$'] + input_string

    print("{:>20} {:>20} {:>20}".
          format("Buffer", "Stack", "Action"))

    while True:
        # end loop if all symbols matched
        if stack == ['$'] and buffer == ['$']:
            print("{:>20} {:>20} {:>20}"
                  .format(' '.join(buffer),
                          ' '.join(stack),
                          "Valid"))
            return "\nValid String!"
        elif stack[0] not in term_userdef:
            # take font of buffer (y) and tos (x)
            x = list(diction.keys()).index(stack[0])
            y = table_term_list.index(buffer[-1])
            if parsing_table[x][y] != '':
                # format table entry received
                entry = parsing_table[x][y]
                print("{:>20} {:>20} {:>25}".
                      format(' '.join(buffer),
                             ' '.join(stack),
                             f"T[{stack[0]}][{buffer[-1]}] = {entry}"))
                lhs_rhs = entry.split("->")
                lhs_rhs[1] = lhs_rhs[1].replace('#', '').strip()
                entryrhs = lhs_rhs[1].split()
                stack = entryrhs + stack[1:]
            else:
                return f"\nInvalid String! No rule at " \
                    f"Table[{stack[0]}][{buffer[-1]}]."
        else:
            # stack top is Terminal
            if stack[0] == buffer[-1]:
                print("{:>20} {:>20} {:>20}"
                      .format(' '.join(buffer),
                              ' '.join(stack),
                              f"Matched:{stack[0]}"))
                buffer = buffer[:-1]
                stack = stack[1:]
            else:
                return "\nInvalid String! " \
                    "Unmatched terminal symbols"


sample_input_string = None

rules = ["S -> Float",
         "Sign -> + | - ",
         "Float -> Sign Digit Dot Digit | Digit Dot Digit",
         "Digit -> 0 Digit | 1 Digit | 2 Digit | 3 Digit | 4 Digit | 5 Digit | 6 Digit | 7 Digit | 8 Digit | 9 Digit | #",
         "Dot -> ."]

nonterm_userdef = ['S', 'Sign', 'Integer', 'Digit', 'Float', 'Dot']
term_userdef = ['+', '-', '.', '0', '1', '2',
                '3', '4', '5', '6', '7', '8', '9', '#']
sample_input_string = "+ 1 2 . 0"

diction = {}
firsts = {}
follows = {}

# computes all FIRSTs for all non terminals
computeAllFirsts()
# assuming first rule has start_symbol
# start symbol can be modified in below line of code
start_symbol = list(diction.keys())[0]
# computes all FOLLOWs for all occurrences
computeAllFollows()
# generate formatted first and follow table
# then generate parse table

(parsing_table, result, tabTerm) = createParseTable()

# validate string input using stack-buffer concept
if sample_input_string != None:
    validity = validateStringUsingStackBuffer(parsing_table, result,
                                              tabTerm, sample_input_string,
                                              term_userdef, start_symbol)
    print(validity)
else:
    print("\nNo input String detected")


###
##
#


def ifOperator(word):
    if re.match(re_operaters, word):
        return True
    return False


def ifPreemtiveType(word):
    if re.match(re_preemtive_types, word, re.IGNORECASE):
        return True
    return False


def ifNonPreemtiveType(word):
    if re.match(re_non_preemtive_types, word, re.IGNORECASE):
        return True
    return False


def ifKeyword(word):
    if re.match(re_keywords, word, re.IGNORECASE):
        return True
    return False


def ifFloat(word):
    if re.match(re_float_number, word):
        return True
    return False


def ifInteger(word):
    if re.match(re_integer_number, word):
        # if re.search(r"[a-zA-Z]|\W[0-9]\W",word):
        # return False
        return True
    return False


def ifString(word):
    if re.match(re_string, word):
        return True
    return False


def ifChar(word):
    if re.match(re_char, word):
        return True
    return False


def ifDelimiter(word):
    if re.match(re_delimiters, word):
        return True
    return False


def ifEndStatement(word):
    if ';' in word:
        return True
    return False


def dfa(word, index_of_word, line_number):
    global flag_datatype
    global flag_identifier
    global flag_keyword
    if index_of_word == 0:
        if ifKeyword(word):
            tokens.append(['KEYWORD', word])
            tokens_list.append((word, line_number, 'KEYWORD'))
            flag_keyword = True
            return
        if ifPreemtiveType(word):
            tokens.append(['DATATYPE', word])
            tokens_list.append((word, line_number, 'DATATYPE'))
            return
        if ifNonPreemtiveType(word):
            tokens.append(['DATATYPE', word])
            tokens_list.append((word, line_number, 'DATATYPE'))
            return
        flag_datatype = True
        errors_list.append(
            ["ERORR at line #{}: TYPO[DATATYPE, KEYWORD]. [{}]".format(i+1, word)])
        return
        # sys.exit("ERORR at line #{}: TYPO. [{}]".format(i+1, word))

    # identify identifiers.
    # if the last token was a datatype and was a typo then the next token must be an IDENTIFIER.
    if flag_datatype == True:
        if re.match("[a-zA-Z]([a-zA-Z]|[0-9])*", word):
            tokens.append(['IDENTIFIER', word])
            tokens_list.append((word, line_number, 'IDENTIFIER'))
            flag_datatype = False
            return
        else:
            flag_identifier = True
            errors_list.append(
                ["ERORR at line #{}: INVALID IDENTIFIER NAME[IDENTIFIER]. [{}]".format(i+1, word)])
            return
            # sys.exit("ERORR at line #{}: INVALID IDENTIFIER NAME. [{}]".format(i+1, word))

    if flag_identifier == True:
        if ifOperator(word) == True:
            tokens.append(['OPERATOR', word])
            tokens_list.append((word, line_number, 'OPERATOR'))
            flag_identifier == False
            return

    if tokens[len(tokens) - 1][0] == 'DATATYPE':
        if re.match("[a-z]|[A-Z]", word):
            tokens.append(['IDENTIFIER', word])
            tokens_list.append((word, line_number, 'IDENTIFIER'))
            return
        else:
            flag_identifier = True
            errors_list.append(
                ["ERORR at line #{}: INVALID IDENTIFIER NAME[IDENTIFIER]. [{}]".format(i+1, word)])
            return
            # sys.exit("ERORR at line #{}: INVALID IDENTIFIER NAME. [{}]".format(i+1, word))

    if flag_keyword == True:
        if ifDelimiter(word) == True:
            tokens.append(['DELIMITER', word])
            tokens_list.append((word, line_number, 'DELIMITER'))
            flag_keyword == False
            return
        # keyword -> identifier.
        if re.match("[a-z]|[A-Z]", word):
            tokens.append(['IDENTIFIER', word])
            tokens_list.append((word, line_number, 'IDENTIFIER'))
            flag_keyword == False
            return

    # DELIMITER.
    if ifDelimiter(word) == True:
        tokens.append(['DELIMITER', word])
        tokens_list.append((word, line_number, 'DELIMITER'))
        return

    # identify END STATEMENTS.
    if ifEndStatement(word) == True:
        tokens.append(['END STATEMENT', word])
        tokens_list.append((word, line_number, 'END STATEMENT'))
        return

    # identify operators.
    if ifOperator(word) == True:
        tokens.append(['OPERATOR', word])
        tokens_list.append((word, line_number, 'OPERATOR'))
        return

    # identify FLOAT.
    if ifFloat(word):
        tokens.append(["FLOAT", word])
        tokens_list.append((word, line_number, 'FLOAT'))
        return

 # identify integer.
    if ifInteger(word):
        tokens.append(["INTEGER", word])
        tokens_list.append((word, line_number, 'INTEGER'))
        return

    # identify Character.
    if ifChar(word):
        tokens.append(["CHARACTER", word])
        tokens_list.append((word, line_number, 'CHARACTER'))
        return

 # identify STRING
    if ifString(word):
        tokens.append(["STRING", word])
        tokens_list.append((word, line_number, 'STRING'))
        return

    errors_list.append(
        ["ERORR at line #{}: ILLEGAL CHARACTER. [{}]".format(i+1, word)])
    return True


def writeFile():
    file = open('Editor.txt', 'w+')
    file.write(text.get('1.0', 'end') + '\n')
    file.close()
    gui.destroy()


gui = Tk()
gui.title("Pseudocode Editor - [Lexical Analyzer]")
gui.geometry("1000x750+250+25")

text = Text(gui, wrap=WORD, font=('Courier 15 bold'))
text.pack(side=LEFT, expand=True, fill=BOTH)
text.place(x=10, y=10, width=980, height=680)

button = Button(gui)
button.config(text='Write To File', command=writeFile)
button.place(x=475, y=700)

gui.mainloop()

f = open('Editor.txt', 'r')
contents = f.readlines()
f.close()

global flag_identifier
flag_identifier = False
global flag_datatype
flag_datatype = False
global flag_keyword
flag_keyword = False

end_at_line = len(contents)

for i in range(len(contents)):
    if contents[i] != "":
        if "Do:" not in contents[i]:
            sys.exit("ERROR: Must start with 'Do:'")
        else:
            break

errors_list = []
tokens = []
tokens_list = []
counter = 0

for i in range(len(contents)):
    count = 0
    content_at_line = contents[i]
    temp_line = list(content_at_line)
    new_line = []
    string = ''
    for singchar in temp_line:
        if singchar in delimiters:
            if not string == '':
                new_line.append(string)
            new_line.append(singchar)
            string = ''
        else:
            string = string + singchar
    temp = " ".join(new_line)
    contents[i] = temp

flag_end = False
for i in range(len(contents)):
    if flag_end == True and contents[i] != "\n":  # كلام عقب ال END
        sys.exit("ERROR: END IS NOT THE LAST.")
    if flag_end == True and contents[i] == "\n":  # سطور فاضية عقب ال END
        continue
    if "End" in contents[i]:
        flag_end = True

if flag_end == False:
    sys.exit("ERROR: NO END KEYWORD.")

for i in range(end_at_line):
    if i == 0:
        continue
    contents_at_line = contents[i].split()
    for word in contents_at_line:
        #print("THE WORD= ", word, contents_at_line.index(word), i+1)
        if word == "End":
            continue
        dfa(word, contents_at_line.index(word), i+1)

    print('--> Line #{}:'.format(i+1), end=' ')
    print(tokens[counter:])
    counter = len(tokens)

print("PROGRAM FINISHED...")


class TableForTokens:
    def __init__(self, root):
        # code for creating table
        for i in range(1):
            for j in range(3):
                self.e = Entry(root, width=20, fg='white',
                               bg='#131E3A', font=('Arial', 16, 'bold'))
                self.e.grid(row=i, column=j)
                self.e.insert(END, token_table_headers[j])
        for i in range(token_table_total_rows):
            for j in range(token_table_total_columns):
                self.e = Entry(root, width=20, fg='white',
                               bg='#95C8D8', font=('Arial', 16, 'bold'))
                self.e.grid(row=i+1, column=j)
                self.e.insert(END, tokens_list[i][j])


class TableForErrors:
    def __init__(self, root):
        # code for creating table
        for i in range(1):
            for j in range(1):
                self.e = Entry(root, width=70, fg='white',
                               bg='#131E3A', font=('Arial', 16, 'bold'))
                self.e.grid(row=i, column=j)
                self.e.insert(END, error_table_headers[j])
        for i in range(error_table_total_rows):
            for j in range(error_table_total_columns):
                self.e = Entry(root, width=70, fg='white',
                               bg='#95C8D8', font=('Arial', 16, 'bold'))
                self.e.grid(row=i+1, column=j)
                self.e.insert(END, errors_list[i][j])


token_table_headers = ['Token', 'Line Number', 'Type']
token_table_total_rows = len(tokens_list)
token_table_total_columns = len(tokens_list[0])

root = Tk()
root.title("Tokens Table")
root.geometry("+350+180")
table = TableForTokens(root)

if len(errors_list) != 0:
    error_table_headers = ['Error']
    error_table_total_rows = len(errors_list)
    error_table_total_columns = len(errors_list[0])

    root = Tk()
    root.title("Tokens Error Table")
    root.geometry("+350+0")
    table = TableForErrors(root)

root.mainloop()
