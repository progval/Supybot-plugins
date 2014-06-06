Advanced trivia plugin.

Config file format
==================

P QUESTION
---
X RESPONSE 1
X RESPONSE 2
---
Y CLUE 1
Y CLUE 2
Y CLUE 3
=== Z

Where P, X, Y, and Z are integers. P is the number of points the question
is worth of, X the type of response (a single char: 'r' for raw answer, and
'm' for a match (regexp)), Y is the time waited before giving a clue,
and Z is the time waited before the question timeout.

Y and Z are relative to the time of the previous clue.

Example config file
===================

2 Who wrote this plugin?
---
r ProgVal
---
5 P***V**
5 Pr**Va*
2 Pro*Val
=== 5

4 What is the name of this bot?
---
r Limnoria
r Supybot
---
5 L******a
2 Li****ia
2 Lim**ria
=== 5

3 Who is the original author of Supybot?
---
r jemfinch
---
1 j*******
1 jem*****
=== 1

1 Give a number.
---
r 42
m [0-9]+
---
=== 2

1 Give another number.
---
r 42
m [0-9]+
---
=== 2
