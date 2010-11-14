This is a document that describe the SupyML language

Global syntax
=============

SupyML is a language based on the XML syntax. The official SupyML interpreter
uses the xml.dom.minidom parser. Minidom handles the format error; the
exceptions it raises are not handled by the SupyML parser.

Commands
========

SupyML is based on call to SupyBot commands. A command is call like that:
 <commandName>arg1 arg2 arg3</commandName>
If you want to call a command in a specific plugin, use this syntax:
 <pluginName>commandName arg1 arg2 arg3</pluginName>

Variables
=========

To get the value of a variable, type:
 <var name="variableName" />

To set the value, type:
 <set name="variableName">newValue</set>

Note that all variable are strings, because SupyML and SupyBot commands
processing both use only strings.
Some plugins, like Conditional provides different handlings for strings and
numerics, but it is their own problems.

Variable lifetime
-----------------

When creating/setting/editing a variable or its value, the changes are
available everywhere in the source code.

About the names
---------------

Because of/thanks to the syntax of the language, names can easily be anything,
even if things other language doesn't like, for example: special chars,
spaces, starting with a number, empty, etc.
But, this is highly deprecated, and it raises a warning.

Conditions
==========

SupyML has not (yet) conditions. Use the Conditional plugin to do that.

Loops
=====

Loops are the main feature provided by SupyML. Here is the global syntax:
 <loop><loopType>boolean</loopType>command arg1 arg2 arg3</loop>
Use conditions to have changing booleans ;)

While loop
----------

The syntax of the while loop is:
 <loop><while>boolean</while>command arg1 arg2 arg3</loop>
The command is run while the boolean is true.
