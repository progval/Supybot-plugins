This plugin aims to provide a highly configurable protection against flood
and spam.

AttackProtector
===============

Detection types
---------------

There are two kind of detections:

**individual**: they are the most common flood, so there name in configuration
   is the name of the flood type

**groupped**: it's a flood from several nicks. There name in the configuration
   is the flood type, prepended by 'group'.

Of course, detection value of group flood should be greater than the
individual flood's.

Punishment types
----------------

For each flood type, you can define a punishment. More common are 'ban',
'kick', 'kban'. You also can define modes, such as the default punishment
for group joins: 'mode+i' (it defines the mode +i). You also can remove
a mode, with the syntax 'mode-i', or set/unset modes to the user, with
'mode-v' or 'mode+v'.
For a complete list of available modes, checkout the network's help pages.
