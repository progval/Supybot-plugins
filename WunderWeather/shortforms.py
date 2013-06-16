# coding=utf-8
###
# Copyright (c) 2009 Michael Tughan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

encoding = 'utf-8'

# Provinces.  (Province being a metric state measurement mind you. :D)
_shortforms = {
    # Canadian provinces
    'ab': 'alberta', 
    'bc': 'british columbia', 
    'mb': 'manitoba', 
    'nb': 'new brunswick', 
    'nf': 'newfoundland', 
    'ns': 'nova scotia', 
    'nt': 'northwest territories',
    'nwt':'northwest territories',
    'nu': 'nunavut', 
    'on': 'ontario', 
    'pe': 'prince edward island', 
    'pei':'prince edward island', 
    'qc': 'quebec', 
    'sk': 'saskatchewan', 
    'yk': 'yukon',
    
    # Countries
    'ad': 'andorra',
    'ae': 'united arab emirates',
    'af': 'afghanistan',
    'ag': 'antigua and barbuda',
    'ai': 'anguilla',
    'am': 'armenia',
    'an': 'netherlands antilles',
    'ao': 'angola',
    'aq': 'antarctica',
    'as': 'american samoa',
    'at': 'austria',
    'au': 'australia',
    'aw': 'aruba',
    'ax': u'åland islands',
    'ba': 'bosnia and herzegovina',
    'bb': 'barbados',
    'bd': 'bangladesh',
    'be': 'belgium',
    'bf': 'burkina faso',
    'bg': 'bulgaria',
    'bh': 'bahrain',
    'bi': 'burundi',
    'bj': 'benin',
    'bl': 'saint barthélemy',
    'bm': 'bermuda',
    'bn': 'brunei darussalam',
    'bo': 'bolivia',
    'br': 'brazil',
    'bs': 'bahamas',
    'bt': 'bhutan',
    'bv': 'bouvet island',
    'bw': 'botswana',
    'by': 'belarus',
    'bz': 'belize',
    'cc': 'cocos (keeling) islands',
    'cd': 'congo, the democratic republic of the',
    'cf': 'central african republic',
    'cg': 'congo',
    'ch': 'switzerland',
    'ci': 'côte d\'ivoire',
    'ck': 'cook islands',
    'cl': 'chile',
    'cm': 'cameroon',
    'cn': 'china',
    'cr': 'costa rica',
    'cu': 'cuba',
    'cv': 'cape verde',
    'cx': 'christmas island',
    'cy': 'cyprus',
    'cz': 'czech republic',
    'dj': 'djibouti',
    'dk': 'denmark',
    'dm': 'dominica',
    'do': 'dominican republic',
    'dz': 'algeria',
    'ec': 'ecuador',
    'ee': 'estonia',
    'eg': 'egypt',
    'eh': 'western sahara',
    'er': 'eritrea',
    'es': 'spain',
    'et': 'ethiopia',
    'fi': 'finland',
    'fj': 'fiji',
    'fk': 'falkland islands',
    'fm': 'micronesia',
    'fo': 'faroe islands',
    'fr': 'france',
    'gb': 'united kingdom',
    'gd': 'grenada',
    'ge': 'georgia',
    'gf': 'french guiana',
    'gg': 'guernsey',
    'gh': 'ghana',
    'gi': 'gibraltar',
    'gl': 'greenland',
    'gm': 'gambia',
    'gn': 'guinea',
    'gp': 'guadeloupe',
    'gq': 'equatorial guinea',
    'gr': 'greece',
    'gs': 'south georgia and the south sandwich islands',
    'gt': 'guatemala',
    'gu': 'guam',
    'gw': 'guinea-bissau',
    'gy': 'guyana',
    'hk': 'hong kong',
    'hm': 'heard island and mcdonald islands',
    'hn': 'honduras',
    'hr': 'croatia',
    'ht': 'haiti',
    'hu': 'hungary',
    'ie': 'ireland',
    'im': 'isle of man',
    'io': 'british indian ocean territory',
    'iq': 'iraq',
    'ir': 'iran, islamic republic of',
    'is': 'iceland',
    'it': 'italy',
    'je': 'jersey',
    'jm': 'jamaica',
    'jo': 'jordan',
    'jp': 'japan',
    'ke': 'kenya',
    'kg': 'kyrgyzstan',
    'kh': 'cambodia',
    'ki': 'kiribati',
    'km': 'comoros',
    'kn': 'saint kitts and nevis',
    'kp': 'north korea',
    'kr': 'south korea',
    'kw': 'kuwait',
    'kz': 'kazakhstan',
    'lb': 'lebanon',
    'lc': 'saint lucia',
    'li': 'liechtenstein',
    'lk': 'sri lanka',
    'lr': 'liberia',
    'ls': 'lesotho',
    'lt': 'lithuania',
    'lu': 'luxembourg',
    'lv': 'latvia',
    'ly': 'libyan arab jamahiriya',
    'mc': 'monaco',
    'mf': 'saint martin',
    'mg': 'madagascar',
    'mh': 'marshall islands',
    'mk': 'macedonia, the former yugoslav republic of',
    'ml': 'mali',
    'mm': 'myanmar',
    'mp': 'northern mariana islands',
    'mq': 'martinique',
    'mr': 'mauritania',
    'mu': 'mauritius',
    'mv': 'maldives',
    'mw': 'malawi',
    'mx': 'mexico',
    'my': 'malaysia',
    'mz': 'mozambique',
    'na': 'namibia',
    'nf': 'norfolk island',
    'ng': 'nigeria',
    'ni': 'nicaragua',
    'nl': 'netherlands',
    'no': 'norway',
    'np': 'nepal',
    'nr': 'nauru',
    'nu': 'niue',
    'nz': 'new zealand',
    'om': 'oman',
    'pe': 'peru',
    'pf': 'french polynesia',
    'pg': 'papua new guinea',
    'ph': 'philippines',
    'pk': 'pakistan',
    'pl': 'poland',
    'pm': 'saint pierre and miquelon',
    'pn': 'pitcairn',
    'pr': 'puerto rico',
    'ps': 'palestinian territory',
    'pt': 'portugal',
    'pw': 'palau',
    'py': 'paraguay',
    'qa': 'qatar',
    're': 'réunion',
    'ro': 'romania',
    'rs': 'serbia',
    'ru': 'russian federation',
    'rw': 'rwanda',
    'sa': 'saudi arabia',
    'sb': 'solomon islands',
    'se': 'sweden',
    'sg': 'singapore',
    'sh': 'saint helena',
    'si': 'slovenia',
    'sj': 'svalbard and jan mayen',
    'sk': 'slovakia',
    'sl': 'sierra leone',
    'sm': 'san marino',
    'sn': 'senegal',
    'so': 'somalia',
    'sr': 'suriname',
    'st': 'sao tome and principe',
    'sv': 'el salvador',
    'sy': 'syrian arab republic',
    'sz': 'swaziland',
    'tc': 'turks and caicos islands',
    'td': 'chad',
    'tf': 'french southern territories',
    'tg': 'togo',
    'th': 'thailand',
    'tj': 'tajikistan',
    'tk': 'tokelau',
    'tl': 'timor-leste',
    'tm': 'turkmenistan',
    'to': 'tonga',
    'tr': 'turkey',
    'tt': 'trinidad and tobago',
    'tv': 'tuvalu',
    'tw': 'taiwan',
    'tz': 'tanzania',
    'ua': 'ukraine',
    'ug': 'uganda',
    'um': 'united states minor outlying islands',
    'uy': 'uruguay',
    'uz': 'uzbekistan',
    'vc': 'saint vincent and the grenadines',
    've': 'venezuela, bolivarian republic of',
    'vg': 'virgin islands, british',
    'vi': 'virgin islands, u.s.',
    'vn': 'viet nam',
    'vu': 'vanuatu',
    'wf': 'wallis and futuna',
    'ws': 'samoa',
    'ye': 'yemen',
    'yt': 'mayotte',
    'za': 'south africa',
    'zm': 'zambia',
    'zw': 'zimbabwe'
}

_conflictingShortforms = {
    'al': 'albania',
    'ar': 'argentina',
    'az': 'azerbaijan',
    'ca': 'canada',
    'co': 'colombia',
    'de': 'germany',
    'ga': 'gabon',
    'id': 'indonesia',
    'il': 'israel',
    'in': 'india',
    'ky': 'cayman islands',
    'la': 'laos',
    'ma': 'morocco',
    'md': 'moldova',
    'me': 'montenegro',
    'mn': 'mongolia',
    'mo': 'macao',
    'ms': 'montserrat',
    'mt': 'malta',
    'nc': 'new caledonia',
    'ne': 'niger',
    'pa': 'panama',
    'sc': 'seychelles',
    'sd': 'sudan',
    'tn': 'tunisia',
    'va': 'vatican city'
}

def checkShortforms(query): # being Canadian, I often use something like "Toronto, ON"
                            # but wunderground needs "Toronto, Ontario"
    if ' ' not in query and ',' not in query:
        return query # if there's no spaces or commas, it's one word, no need to check for provinces
    
    lastWord = query.split()[-1].lower() # split by spaces, see if the last word is a province shortform
    if lastWord in _shortforms:
        return (query[0:0 - len(lastWord)] + _shortforms[lastWord]).encode(encoding)
    
    lastWord = query.split(',')[-1].lower() # if it's not separated by spaces, maybe commas
    if lastWord in _shortforms:
        return (query[0:0 - len(lastWord)] + _shortforms[lastWord]).encode(encoding)
    
    return query # nope, probably not a province name, return original query

def checkConflictingShortforms(query):
    if ' ' not in query and ',' not in query:
        return None
    
    lastWord = query.split()[-1].lower()
    if lastWord in _conflictingShortforms:
        return (query[0:0 - len(lastWord)] + _conflictingShortforms[lastWord]).encode(encoding)
    
    lastWord = query.split(',')[-1].lower()
    if lastWord in _conflictingShortforms:
        return (query[0:0 - len(lastWord)] + _conflictingShortforms[lastWord]).encode(encoding)
    
    return None
