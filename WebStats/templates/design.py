try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('WebStats')
except:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

content = \
"""/*
Copyright (c) 2010, Valentin Lorentz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice,
    this list of conditions, and the following disclaimer.
  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions, and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
  * Neither the name of the author of this software nor the name of
    contributors to this software may be used to endorse or promote products
    derived from this software without specific prior written consent.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/

body, html {
    text-align: center;
}

li {
    list-style-type: none;
}

#header {
    width: 100%;
    font-size: 1.2em;
    text-align: center;
}

#menu {
    width: 100%;
    font-size: 0.8em;
    text-align: center;
    margin: 0;
    padding: 0;
}

#menu:before {
    content: \"""" + _('Menu:') + """\";
}

#menu li {
    display: inline;
}

#footer {
    width: 100%;
    font-size: 0.6em;
    text-align: right;
}

h1 {
    text-align: center;
}

.chanslist li a:visited {
    color: blue;
}

table {
    margin-left: auto;
    margin-right: auto;
}
.progressbar {
    border: orange 1px solid;
    height: 20px;
}
.progressbar .color {
    background-color: orange;
    height: 20px;
    text-align: center;
    -moz-border-radius: 10px;
    -webkit-border-radius: 10px;
}
.progressbar .text {
    position: absolute;
    width: 150px;
    text-align: center;
    margin-top: auto;
    margin-bottom: auto;
}
"""

def get(useSkeleton=True):
    return content
