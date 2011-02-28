This plugin is a packages downloadeder and installer.
It handles basic dependencies, based on tags.

Repositories must have a root JSON file, that uses the fellowing
format:
{
    "repository": {
        "maintainers": {
            "ProgVal": "progval@gmail.com",
        },
        "repo-name": "Main packages repository",
        "repo-url": "http://packages.supybot.fr.cr",
        "project-name": "Supybot-fr",
        "project-url": "http://supybot.fr.cr"
    }
    "packages": [
        {
            "name": "Trigger",
            "version": "0.1",
            "author": [
                "Valentin Lorentz",
                "ProgVal",
                "progval@gmail.com"
            ],
            "info-url": "http://supybot.fr.cr/Trigger",
            "download-url": "./Trigger-0.1.tar",
            "requires": {
                "package-installer": "0.1"
            },
            "suggests": {
                "i18n": "0.1",
                "conditional": "0.1"
            },
            "provides": {
                "trigger": "0.1"
            }
        }
    ]
}
