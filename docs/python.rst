Python Primer
==================

Think of python as a program. what it does is takes
human readable source code (.py) and parses, compiles and executes in real time.

`Python 2.7 Documentation <https://docs.python.org/2.7>`_

Best place to start. `Python Tutorial <http://docs.python.org/tutorial/index.html>`_

You can run python in 2 ways. (there is actually many ways to run from the command line but
	only 2 are used frequently)
Open terminal

1. with no arguments. opens the python interpreter

>>> python

2. with a path to python script (absolute or relative path). executes the script
>>> python hello_world.py

Using Python Interpreter
Zen of Python

>>> import this

you can use the command line as a powerful calculator
see http://docs.python.org/tutorial/introduction.html

>>> x=1
>>> y=2
>>> x+y
3
>>> x=50

Use the up and down arrows to cycle thru previous commands

>>> x+y
53
>>> y=x+y
>>> x+y
103
>>> i=0
>>> i+=1    #same as i = i+1 works for all math operators i -=1, i*=2 etc...

strings are defined using \', \", or \'\'\' blocks. \' and \" are equivalent. convenient when needing to nest quotes.

>>> s='foo'
>>> b='bar'
>>> print s,b
foo bar
>>> s
'foo'
>>> b
'bar'
>>> "foo" == 'foo' == '''foo'''
True

to make a list of items use a list or tuple
see http://docs.python.org/tutorial/datastructures.html

>>> l1=[1,2,3,4]
>>> l2=['foo','bar']
>>> t1=(1,2,3)
>>> t2=('foo','bar')

lists are mutable, tuples are immutable

>>> l1[0]=10
>>> l1
[10,2,3,4]
>>> t1[0]=10
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'tuple' object does not support item assignment

get the length of the sequence use builtin len

>>> len(l1)
4

to generate a list of numbers use builtin range

>>> range(10)
[0,1,2,3,4,5,6,7,8,9]


>>> range(0,10,2)
[0,2,4,6,8]

get item from list

>>> l1[0]
1

get the last item

>>> l1[-1]
9

get a sublist

>>> l1[0:2]    #list[startindex:stopindex:step]
                #each parameter is optional but at least needs to be set
                #startindex defaults to 0
                #stopindex defaults to the last index
                #step defaults to 1
                #l1[0:2] same as l1[0:2:1] and l1[:2] (preferred)

same slicing operations work on strings. just think of them as a list of characters

>>> s= 'hello world'
>>> s[:5]
'hello'
>>> s[6:]
'world'
>>> s[-5:]
'world'

you can split and join strings easily

>>> s.split(' ') #str.list(character to  split on) returns a list
['hello', 'world']
>>> ', '.join(s.split(' ')) #join_str.join(list of strings to join)
hello, world
>>> '\n'.join(['this is a good','way to write multi','line text'])
this is a good
way to write multi
line text

Dictionaries are key:value containers. There are two syntaxes for creating a dictionary

>>> d=dict(name='Jake', office=316, building='MSEC')
>>> d2 = {'name':'Jake','office':316, 'building':'MSEC'} #convenient when the keys are variables as well
>>> key1='person'
>>> key2='id'
>>> val1='John'
>>> val2=10394303
>>> d3 = {key1:val1, key2:val2}

to get a value from the dictionary you specifiy a key. To get the definition of a word you find the
word (key) in are dictionary and read the associated entry

>>> d['name']
Jake

entries can be modified

>>> d['name']='Jake Ross'
>>> d['name']
Jake Ross

String formating is awesome in python. Lets say you want to display some text with your results

>>> 'the result of {} plus {} is {}'.format(x,y,x+y)
'the result of 50 plus 53 is 103'
>>> 'the result of {1} plus {0} is {2}'.format(x,y,x+y)
'the result of 53 plus 50 is 103'

you can use pass in a key:pairs

>>> "{name}'s office is {building} {office}".format(name='Jake',building='MSEC',office=316)

or better

>>> "{name}'s office is {building} {office}".format(**d2)
"Jake's office is MSEC 316"
