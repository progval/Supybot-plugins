.. _plugin-RelayedCommands:

Documentation for the RelayedCommands plugin for Supybot
========================================================

Purpose
-------

RelayedCommands: Recognizes commands sent through a relay bot and runs them

Usage
-----

Recognizes commands sent through a relay bot and runs them

.. _conf-RelayedCommands:

Configuration
-------------

.. _conf-supybot.plugins.RelayedCommands.bots:


supybot.plugins.RelayedCommands.bots
  This is a group of:

  .. _conf-supybot.plugins.RelayedCommands.bots.nicks:


  supybot.plugins.RelayedCommands.bots.nicks
    This config variable defaults to " ", is network-specific, and is channel-specific.

    Nick names of relay bots to recognize.

  .. _conf-supybot.plugins.RelayedCommands.bots.self:


  supybot.plugins.RelayedCommands.bots.self
    This config variable defaults to "False", is network-specific, and is channel-specific.

    Whether to recognize this bot itself as a relay bot.

.. _conf-supybot.plugins.RelayedCommands.public:


supybot.plugins.RelayedCommands.public
  This config variable defaults to "True", is not network-specific, and is not channel-specific.

  Determines whether this plugin is publicly visible.

.. _conf-supybot.plugins.RelayedCommands.replaceNick:


supybot.plugins.RelayedCommands.replaceNick
  This config variable defaults to "False", is network-specific, and is channel-specific.

  Whether to run commands as the relayed user's nick instead of the relay bot's. This allows $nick to work as expected, makes the bot reply to the right nick, and makes rate-limits work per-relayed user instead of applying to all relayed messages as if coming to a single user (the relay bot). This means that it effectively exempts malicious relay bots from rate-limits.

