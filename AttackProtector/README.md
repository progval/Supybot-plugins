This plugin aims to provide a highly configurable protection against flood
and spam.

AttackProtector
===============

Detection types
---------------

There are two kind of detections:

**Individual floods**: are the most common types of flood, involving floods
from one user. Options controlling these detections exist in the
configuration as the name of the flood type (e.g.
`config plugins.attackprotector.{join,message,etc.}`).

**grouped floods**: are floods from several nicks. Their names in the
configuration are the flood type, prepended by 'group' (e.g.
`config plugins.attackprotector.group{join,message,etc.}`).

Of course, the detection value of group floods should be greater than the
individual floods'.

Punishment types
----------------

For each flood type, you can define a punishment. More common are `ban`,
`kick`, or `kban`. You also can define modes, such as the default
punishment for group joins: `mode+i`, which sets the mode `+i`. You can
also remove a mode, with the syntax `mode-i`, or set/unset modes to the
user, with `mode-v' or 'mode+v`.
For a complete list of available modes, see your IRC network's help pages
or try `/quote help`.

For `ban` and `kban`, you can also add a timeout this way: `ban+X` and
`kban+X`, where `X` is the number of seconds.
