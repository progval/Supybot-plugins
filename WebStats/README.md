WebStats is a plugin that provide a web access to channel based statistics.

**This plugin requires Limnoria.**

It is designed to be used on active channels, so it implements a cache system.
Don't worry if you have enabled statistics and nothing happens on the Web
interface in the following hour.

You need pygraphviz (python-pygraphviz in Debian) for the "links" graph.

## Reverse proxies

### apache

If you want to use Apache as a proxy for your WebStats instance, you can
use this sample configuration:

```apache
<VirtualHost 0.0.0.0:80>
        ServerName stats.supybot.fr.cr
        ServerAlias stats.supybot-fr.tk
        <Location />
                ProxyPass http://localhost:8080/
                SetEnv force-proxy-request-1.0 1
                SetEnv proxy-nokeepalive 1
        </Location>
</VirtualHost>
```

### nginx

Create a new site for your bot `/etc/nginx/sites-enabled/bot`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name stats.supybot.fr.cr;

    location / {
        proxy_pass http://localhost:8080/;
    }
}
```
