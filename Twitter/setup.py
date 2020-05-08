from supybot.setup import plugin_setup

plugin_setup(
    'Twitter',
    install_requires=[
        'oauth2',
        'python-twitter',
    ]
)
