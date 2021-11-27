This is a document that describe the SupyML language

Global syntax
=============

SupyML is a language based on the XML syntax. The official SupyML interpreter
uses the xml.dom.minidom parser. Minidom handles the format error; the
exceptions it raises are not handled by the SupyML parser.

Commands
========

SupyML is based on call to SupyBot commands. A command is call like that:

```
 <commandName>arg1 arg2 arg3</commandName>
```

If you want to call a command in a specific plugin, use this syntax:

```
 <pluginName>commandName arg1 arg2 arg3</pluginName>
```

Variables
=========

To get the value of a variable, type:

```
<var name="variableName" />
```

To set the value, type:

```
<set name="variableName">newValue</set>
```

Note that all variable are strings, because SupyML and SupyBot commands
processing both use only strings.
Some plugins, like Conditional provides different handlings for strings and
numerics, but it is their own problems.

Variable scope and lifetime
-----------------

When creating/setting/editing a variable or its value, the changes are
available only within the current eval script.

About the names
---------------

Because of/thanks to the syntax of the language, names can easily be anything,
even if things other language doesn't like, for example: special chars,
spaces, starting with a number, empty, etc.
But, this is highly deprecated, and it raises a warning.

Conditions
==========

SupyML uses the onceif loop type to implement conditional execution. Please use the Conditional and Math modules for expressing conditions.

Loops
=====

Loops are the main feature provided by SupyML. Here is the global syntax:

```
<loop><loopType>expression</loopType>statement</loop>
```

Where expression and statement are strings. If executed, the loop becomes equivalent to zero, one or multiple calls of the form:

```
<echo>statement</echo> 
<echo>statement</echo> 
...
<echo>statement</echo> 
```

The maximum number of iterations is limited by the Plugins.SupyML.maxnodes config variable just like the maximum length of SupyML scripts.

While loop
----------

The syntax of the while loop is:

```
<loop><while>boolean expression</while>statement</loop>
```

The statement is repeated while the boolean expression evaluates to true.

OnceIf loop
----------

The syntax of the onceif statement is:

```
<loop><onceif>boolean expression</onceif>statement</loop>
```

The statement is expressed exactly once iff the boolean expression evaluates to true.

Range loop
----------

The syntax of the range loop is:

```
<loop><range>integer expression</range>statement</loop>
```

The statement is repeated integer expression times or never if the integer expression evaluates to zero or less.
The iterator value during any iteration is accessible through the loop variable. Example:

```
<loop><range>3</range>iteration <var name="loop"/>.</loop>
```

ForEach loop
----------

The syntax of the foreach loop is:

```
<loop><foreach>token expression</foreach>statement</loop>
```

The statement is repeated once for each token in the token expression, or never if the expression is empty.
The current tokene during any iteration is accessible through the loop variable. Example:

```
<loop><foreach>foo bar baz</foreach>I have <var name="loop"/>.</loop>
```

Quote escaping
==============

For some commands, escape sequences are important, in order to return useful strings from loops.
The XML is parsed before execution, so variable names do typically not need escaping.
However, quotation marks in text are parsed and converted in tokenization at each nested level of execution of the eval statement.
As such a large amount of escaping might be needed depending on nesting level.

Examples:

```
eval <utilities>last <loop><range>3</range>This is iteration <var name="loop"/></loop></utilities>
```

outputs '2'


one would likely prefer:

```
eval <utilities>last <loop><range>3</range>"\"This is iteration <var name="loop"/>\""</loop></utilities>
```

which outputs 'This is iteration 2'


If the loop is nested deeper, more escaping is needed:

```
eval <utilities>last <echo><loop><range>3</range>"\"<echo>This is iteration <var name="loop"/></echo>\""</loop></echo></utilities>
```

outputs '2' since the echo command strips the then unescaped quotation mark during execution. The correct escaping would be:

```
eval <utilities>last <echo><loop><range>3</range>"\"\\\"<echo>This is iteration <var name="loop"/></echo>\\\"\""</loop></echo></utilities>
```

which outputs 'This is iteration 2'.

This needs to be taken in mind also in combination with the Alias or Aka or other modules, for example in:

```
aka add repeat "eval <utilities>last <loop><range>$1</range>\"\\\"<echo>This is iteration <var name=\"loop\"/></echo>\\\"\"</loop></utilities>"
repeat 3
``` 

the quotation marks in the XML also require escaping.

If you need to have XML tags in strings, they need to be escaped with HTML syntax, for example for a nested eval:

```
eval <echo>first level <eval>&lt;echo&gt;second level&lt;/echo&gt;</eval></echo>
```

Functions
=========

It is recommended to use the Aka module to write custom functions. Aliases can be used in SupyML and SupyML eval can be used in Aliases. For example:

```
aka add runcmd "eval <echo><$1>$*</$1></echo>"
aka add foreach "eval <echo><loop><foreach>$*</foreach>\"\\\"<runcmd>$1 <var name=\"loop\" /></runcmd>\\\"\"</loop></echo>"
foreach "echo I am" foo bar baz
```

Will output "I am foo I am bar I am baz"

Note that the foreach type in the loop is a special keyword that will not be affected by an Alias of the same name.

Further examples:

```
aka add escapenicks "re \"s/ and|,//g\" $*"
foreach "voice #mychannel" [ escapenicks [ nicks #mychannel ] ]
```


