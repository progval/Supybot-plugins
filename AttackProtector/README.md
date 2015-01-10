This plugin aims to provide a highly configurable protection against flood
and spam.

AttackProtector
===============

Detection types
---------------

There are two kind of detections:

**individual**: they are the most common type of flood, so their names in the configuration
   are the name of the flood type.

**grouped**: it's a flood from several nicks. Their names in the configuration
   are the flood type, prepended by 'group'.

Of course, the detection value of group floods should be greater than the
individual floods'.

Punishment types
----------------

For each flood type, you can define a punishment. More common are `ban`,
`kick`, or `kban`. You also can define modes, such as the default punishment
for group joins: `mode+i`, which sets the mode `+i`. You also can remove
a mode, with the syntax `mode-i`, or set/unset modes to the user, with
`mode-v' or 'mode+v`.
For a complete list of available modes, see your IRC network's help pages.
