.. _plugin-NickTracker:

Documentation for the NickTracker plugin for Supybot
====================================================

Purpose
-------

NickTracker: Keeps track of the nicknames used by people connecting from the same hosts

Usage
-----

Keeps track of the nicknames used by people connecting from the same hosts

This relies on the ChannelLogger plugin being loaded and enabled to
remember past nicknames after the bot restarts.

.. _conf-NickTracker:

Configuration
-------------

.. _conf-supybot.plugins.NickTracker.announce:


supybot.plugins.NickTracker.announce
  This is a group of:

  .. _conf-supybot.plugins.NickTracker.announce.nicks:


  supybot.plugins.NickTracker.announce.nicks
    This is a group of:

    .. _conf-supybot.plugins.NickTracker.announce.nicks.lines:


    supybot.plugins.NickTracker.announce.nicks.lines
      This config variable defaults to "2", is network-specific, and is channel-specific.

      Number of lines to announce when someone joins.

    .. _conf-supybot.plugins.NickTracker.announce.nicks.separator:


    supybot.plugins.NickTracker.announce.nicks.separator
      This config variable defaults to " ", is network-specific, and is channel-specific.

      Separator between two items in the list of nicks.

.. _conf-supybot.plugins.NickTracker.patterns:


supybot.plugins.NickTracker.patterns
  This config variable defaults to "*!$user@$host", is network-specific, and is channel-specific.

  Space-separated list of patterns to use to find matches. For example, '$user@$host' finds all people with the same user and host, and '$host' finds all people with the same host. The following variables are available: $nick, $user, and $host.

.. _conf-supybot.plugins.NickTracker.public:


supybot.plugins.NickTracker.public
  This config variable defaults to "True", is not network-specific, and is not channel-specific.

  Determines whether this plugin is publicly visible.

.. _conf-supybot.plugins.NickTracker.targets:


supybot.plugins.NickTracker.targets
  This config variable defaults to " ", is network-specific, and is channel-specific.

  Space-separated list of channels and/or nicks to announce joins to.

