If you want to use Apache as a proxy for your WebStats instance, you can use
this sample configuration:
<VirtualHost 0.0.0.0:80>
        ServerName stats.supybot.fr.cr
        ServerAlias stats.supybot-fr.tk
        <Location />
                ProxyPass http://localhost:8080/
                SetEnv force-proxy-request-1.0 1
                SetEnv proxy-nokeepalive 1
        </Location>
</VirtualHost>
