# -*- coding: utf-8 -*
#
# This file is in public domain.
# Its author's email is nemaanjaa@gmail.com

import libxml2
import math
from math import ceil

import types 


class Citizen:
    def loadByName(self, name):
        if name.isdigit():
            return self.loadById(name)
        import supybot.utils.web as web
        lines = filter(lambda x:'<id>' in x, web.getUrl('http://api.erpk.org/citizen/search/' + name + '/1.xml?key=nIKh0F7U').split('\n'))
        if not lines:
            return None
        line = lines[0]
        id = line.split('>')[1].split('<')[0]
        return self.loadById(id)

    def loadById(self, id):
        try:
            self.doc = libxml2.parseFile('http://api.erpk.org/citizen/profile/' + str(id) + '.xml?key=nIKh0F7U')
        except:
            return None
        self.ctxt = self.doc.xpathNewContext()
        return self

    def getName(self):
        return self.ctxt.xpathEval('//citizen/name/text()')[0].getContent()

    def getId(self):
        return int(self.ctxt.xpathEval('//citizen/id/text()')[0].getContent())
    
    def getDamage(self):
        try:
            return float(self.ctxt.xpathEval('//military-skill/points')[0].getContent())
        except:
            return 0

    def getStrength(self):
        try:
            return float(self.ctxt.xpathEval('//id')[0].getContent())
        except:
            return 0.0

    def getRank11(self):
        try:
            return self.ctxt.xpathEval('//military-skill/level')[0].getContent()
        except:
            return "Private"

    def getRankAsNumber(self, rank = None):
        if rank == None:
            rank = self.getRank()
        rank = rank.lower()

        if rank == 'private':
            return 1
        elif rank == 'corporal':
            return 2
        elif rank == 'sergeant':
            return 3
        elif rank == 'lieutenant':
            return 4
        elif rank == 'captain':
            return 5
        elif rank == 'colonel':
            return 6
        elif rank == 'general':
            return 7
        else: # if rank == 'field marshall'
            return 8
    
    def getFights(self):
        try:
            return int(self.ctxt.xpathEval('//fight-count')[0].getContent())
        except:
            return 0

    def getWellness(self):
        try:
            return float(self.ctxt.xpathEval('//wellness')[0].getContent())
        except:
            return 0.0

    def getHappiness(self):
        try:
            return float(self.ctxt.xpathEval('//happiness')[0].getContent())
        except:
            return 0.0


    def getVestinu(self):
        try:
            return float(self.ctxt.xpathEval('//work-skill-points')[0].getContent())
        except:
            return 0.0
    def getRank(self):
        try:
            return float(self.ctxt.xpathEval('//military/rank-points')[0].getContent())
        except:
            return 0.0
    def getExperience(self):
        try:
            return int(self.ctxt.xpathEval('//experience-points')[0].getContent())
        except:
            return 0

    def getLevel(self):
        try:
            return int(self.ctxt.xpathEval('//level')[0].getContent())
        except:
            return 1

    def getCitizenship(self):
        try:
            return self.ctxt.xpathEval('//citizenship/country/name')[0].getContent()
        except:
            return 'Error'

    def getCitizenshipId(self):
        try:
            return int(self.ctxt.xpathEval('//citizenship/country/id')[0].getContent())
        except:
            return 0

    def getEmployer(self):
        expr = self.ctxt.xpathEval('//employer/name')
        if len(expr) == 0:
            return 'N/A'
        else:
            return expr[0].getContent()

    def getEmployerId(self):
        try:
            return int(self.ctxt.xpathEval('//employer/id')[0].getContent())
        except:
            return 0

    def isUnemployed(self):
        return len(self.ctxt.xpathEval('//employer/id')) == 0

    def getManufacturing(self):
        expr = self.ctxt.xpathEval('//skills/skill/name')
        if len(expr) == 0:
            return 0.0
        return float(expr[0].getContent())

    def getLand(self):
        expr = self.ctxt.xpathEval('//citizen/skills/skill[domain="land"]/value/text()')
        if len(expr) == 0:
            return 0.0
        return float(expr[0].getContent())

   
    def getRegion(self):
        return self.ctxt.xpathEval('//residence/region/name')[0].getContent()

    def getRegionId(self):
        return int(self.ctxt.xpathEval('//residence/region/id')[0].getContent())

    def getCountry(self):
        return self.ctxt.xpathEval('//residence/country/name')[0].getContent()

    def getCountryId(self):
        return int(self.ctxt.xpathEval('//residence/country/id')[0].getContent())

    def isPartyMember(self):
        return self.ctxt.xpathEval('//citizen/is-party-member/text()')[0].getContent() == 'true'

    def pointsToLevel(self, points):
        levels = [0, 20, 100, 500, 2000, 5000, 10000, 20000, 40000, 80000, 160000, 320000, 640000, 1280000, 2560000]
        idx = 0
        level = -1
        while(level == -1 and idx < len(levels)):
            if(levels[idx] > points):
                level = idx
            idx += 1
        return level

    def getSkills(self):
        list = ''
        idx = 0
        skills = self.ctxt.xpathEval('//citizen/skills/skill/name/text()')
        while(idx < len(skills)):
            skill = skills[idx].getContent()
            points = int(self.ctxt.xpathEval('//citizen/skills/skill/points/text()')[idx].getContent())
            if(points > 0):
                level = self.pointsToLevel(points)
                list = list + str(skill) + ': ' + str(level) + ' (' + str(points) + ') '
            idx += 1
        list = list.replace('Commodities Worker', 'Harvester')
        return list

    def militaryPointsToLevel(self, points):
        levels = [0, 40, 200, 1000, 4000, 10000, 20000, 40000, 80000, 160000, 320000, 640000, 1280000, 2560000]
        idx = 0
        level = -1
        while(level == -1 and idx < len(levels)):
            if(levels[idx] > points):
                level = idx
            idx += 1
        return level

    def getMilitary(self):
        list = ''
        idx = 0
        skills = self.ctxt.xpathEval('//citizen/military-skills/military-skill/name/text()')
        while(idx < len(skills)):
            skill = skills[idx].getContent()
            points = int(self.ctxt.xpathEval('//citizen/military-skills/military-skill/points/text()')[idx].getContent())
            if(points > 0):
                level = self.militaryPointsToLevel(points)
                list = list + skill + ': ' + str(level) + ' (' + str(points) + ') '
            idx += 1
        return list



    def rankPointsToLevel(self, points):
        levels = [0, 4, 9, 19 , 31, 46, 91, 179, 296, 426, 676, 1001, 1401, 1851, 2351, 3001, 3751, 5001, 6501, 9001, 12001, 15501, 20001, 25001, 31001, 40001, 52001, 67001, 85001, 110001, 140001, 180001, 225001, 285001, 355001, 435001, 540001, 660001, 800001, 950001, 1140001, 1350001, 1600000, 1875001, 2185001, 2550001, 3000001, 3500001, 4150001, 4900001, 5800001, 7000001, 9000001, 11500001, 14500001, 18000001, 23000001, 30000001, 40000001, 55000001, 80000001, 110000001, 150000001]
        idx = 0
        level = -1
        while(level == -1 and idx < len(levels)):
            if(levels[idx] > points):
                level = idx
            idx += 1
        return level

    def getRanklvl(self):
        list = ''
        idx = 0
       
        points = float(self.ctxt.xpathEval('//military/rank-points')[idx].getContent())
        if(points > 0):
            level = self.rankPointsToLevel(points)
         
           
        return level


    def getMedals(self):
        list = ''
        idx = 0
        skills = self.ctxt.xpathEval('//citizen/medals/medal/type/text()')
        while(idx < len(skills)):
            skill = skills[idx].getContent()
            points = int(self.ctxt.xpathEval('//citizen/medals/medal/amount/text()')[idx].getContent())
            if(points > 0):
                list = list + ' \x02 ' + skill + '\x02[' + str(points) + ']: '
            idx += 1
        
        return list

    def toString(self):
        return (
            ' \x02 ' + self.getName() + ': Location: \x02' +
            self.getCountry() + ', ' + self.getRegion() +
            ';\x02 Wellness: \x02' + str(self.getWellness()) + ';\x02 Rank: \x02' + str(self.getRank()) +
            ';\x02 Experience: \x02' + str(self.getExperience()) +
             ';\x02 Employed at: \x02' + self.getEmployer() +
            ';\x02 Citizenship: \x02' + self.getCitizenship() +  ';\x02 Work Skill: \x02' + str(self.getVestinu()) +
            ';\x02 Strenght: \x02' + str(self.getDamage()) 
            
            )
    def toDict(self):
        return {
            'name'        : self.getName(),
            'strenght'    : self.getDamage(),
            'manu'        : self.getVestinu(),
            'land'        : self.getExperience(),
           

            }


    





























    def fightCalc1(self, wellness, rank=None, strength=None):
        if rank == None:
            rank = self.getRanklvl()
        if strength == None:
            strength = self.getDamage()
        dmg = (((float (rank-1) / 20) + 0.3) * ((strength / 10) +40)*38)
      

        return map(lambda x: float(ceil(dmg * x)), (1, 1.2, 1.4, 1.6, 1.8, 2.0))

    def fightCalcStr1(self, wellness):
        fc = self.fightCalc1(wellness)

        res = ''
        for i in range(0,6):
            res += 'Q%s: %s, ' % (str(i), str(fc[i]))
        return res[:-2]







    

    def fightCalc(self, wellness, rank=None, strength=None):
        if rank == None:
            rank = self.getRanklvl()
        if strength == None:
            strength = self.getDamage()
        dmg = (((float (rank-1) / 20) + 0.3) * ((strength / 10) +40))
      

        return map(lambda x: float(ceil(dmg * x)), (1, 1.2, 1.4, 1.6, 1.8, 2.0))

    def fightCalcStr(self, wellness):
        fc = self.fightCalc(wellness)

        res = ''
        for i in range(0,6):
            res += 'Q%s: %s, ' % (str(i), str(fc[i]))
        return res[:-2]

class Region:
    def __init__(self, id):
        self.doc = libxml2.parseFile('http://api.erepublik.com/v1/feeds/regions/' + str(id))
        self.ctxt = self.doc.xpathNewContext()

    def getName(self):
        return self.ctxt.xpathEval('//region/name/text()')[0].getContent()

    def getId(self):
        return int(self.ctxt.xpathEval('//region/id/text()')[0].getContent())

    def getCitizens(self):
        ret = []
        for a in self.ctxt.xpathEval('//region/citizens/citizen/id/text()'):
            ret = ret + [int(a.getContent())]
        return ret


class Stats:

    
    def loadByName(self,name,id=None):
        try:
            if name == None:
                if id == None:
                    self.doc = libxml2.parseFile('http://genzard.net/erepublik/stats/unit.php?limit=3')
                else:
                    self.doc = libxml2.parseFile('http://genzard.net/erepublik/stats/unit.php?unit_id=' + str(id) + '&limit=3')
            else:
                try:
                    test = int(name)
                    self.doc = libxml2.parseFile('http://genzard.net/erepublik/stats/unit.php?battle_id=' + name + '&limit=1')
                except:
                    self.doc = libxml2.parseFile('http://genzard.net/erepublik/stats/unit.php?region=' + name + '&limit=3')
        except:
            return None
        self.ctxt = self.doc.xpathNewContext()
        return self

    def getIme(self):
        return self.ctxt.xpathEval('//battle-1/region')[0].getContent()

    def getSteta(self):
        return float(self.ctxt.xpathEval('//battle-1/damage')[0].getContent())
    
    def getBorba(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/fights')[0].getContent())
        except:
            return 0

    def getUbistvo(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/deaths')[0].getContent())
        except:
            return 0.0




    def getIme1(self):
        return self.ctxt.xpathEval('//battle-2/region')[0].getContent()

    def getSteta1(self):
        return float(self.ctxt.xpathEval('//battle-2/damage')[0].getContent())
    
    def getBorba1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/fights')[0].getContent())
        except:
            return 0

    def getUbistvo1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/deaths')[0].getContent())
        except:
            return 0.0

    def getIme2(self):
        return self.ctxt.xpathEval('//battle-3/region')[0].getContent()

    def getSteta2(self):
        return float(self.ctxt.xpathEval('//battle-3/damage')[0].getContent())
    
    def getBorba2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/fights')[0].getContent())
        except:
            return 0

    def getUbistvo2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/deaths')[0].getContent())
        except:
            return 0.0
    def getBorci(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/fighters')[0].getContent())
        except:
            return 0.0
    def getBorci1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/fighters')[0].getContent())
        except:
            return 0.0
    def getBorci2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/fighters')[0].getContent())
        except:
            return 0.0

    def toString(self, name='Skorpioni'):
        return (
             '; ' + name + ' statistika: ' + self.getIme() + ': Naneta steta: ' +
            str(self.getSteta()) + ': Broj borbi: ' + str(self.getBorba()) +
            '; Broj ubistava: ' + str(self.getUbistvo()) + '; Broj pogibija: '
             +  str(self.getSmrt()) + '; Broj vojnika: ' + str(self.getBorci())


            )

    def toString1(self, name='Skorpioni'):
        return (
             '; ' + name + ' statistika: ' + self.getIme1() + ': Naneta steta: ' +
            str(self.getSteta1()) + ': Broj borbi: ' + str(self.getBorba1()) +
            '; Broj ubistava: ' + str(self.getUbistvo1()) + '; Broj pogibija: '
             +  str(self.getSmrt1())  + '; Broj vojnika: ' + str(self.getBorci1())


            )
    def toString2(self, name='Skorpioni'):
        return (
             '; ' + name + ' statistika: ' + self.getIme2() + ': Naneta steta: ' +
            str(self.getSteta2()) + ': Broj borbi: ' + str(self.getBorba2()) +
            '; Broj ubistava: ' + str(self.getUbistvo2()) + '; Broj pogibija: '
             +  str(self.getSmrt2())  + '; Broj vojnika: ' + str(self.getBorci2())


            )





class Vojnik:
    def loadByName(self, name):
        try:
            self.doc = libxml2.parseFile('http://genzard.net/erepublik/stats/citizen.php?nick=' +
                                         name + '&limit=3')
        except:
            return None
        self.ctxt = self.doc.xpathNewContext()
        return self


    def getIme(self):
        return self.ctxt.xpathEval('//battle-1/region')[0].getContent()

    def getSteta(self):
        return float(self.ctxt.xpathEval('//battle-1/damage')[0].getContent())
    
    def getBorba(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/fights')[0].getContent())
        except:
            return 0

    def getUbistvo(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt(self):
        try:
            return int(self.ctxt.xpathEval('//battle-1/deaths')[0].getContent())
        except:
            return 0.0


    def getIme3(self):
        return self.ctxt.xpathEval('//citizen/name')[0].getContent()

    def getIme1(self):
        return self.ctxt.xpathEval('//battle-2/region')[0].getContent()

    def getSteta1(self):
        return float(self.ctxt.xpathEval('//battle-2/damage')[0].getContent())
    
    def getBorba1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/fights')[0].getContent())
        except:
            return 0

    def getUbistvo1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt1(self):
        try:
            return int(self.ctxt.xpathEval('//battle-2/deaths')[0].getContent())
        except:
            return 0.0

    def getIme2(self):
        return self.ctxt.xpathEval('//battle-3/region')[0].getContent()

    def getSteta2(self):
        return float(self.ctxt.xpathEval('//battle-3/damage')[0].getContent())
    
    def getBorba2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/fights')[0].getContent())
        except:
            return 0

    def getUbistvo2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt2(self):
        try:
            return int(self.ctxt.xpathEval('//battle-3/deaths')[0].getContent())
        except:
            return 0.0



        
    def getSteta3(self):
        return float(self.ctxt.xpathEval('//all-battles/damage')[0].getContent())
    
    def getBorba3(self):
        try:
            return int(self.ctxt.xpathEval('//all-battles/fights')[0].getContent())
        except:
            return 0

    def getBorba4(self):
        try:
            return float(self.ctxt.xpathEval('//all-battles/kill-ratio')[0].getContent())
        except:
            return 0

    def getUbistvo3(self):
        try:
            return int(self.ctxt.xpathEval('//all-battles/kills')[0].getContent())
        except:
            return 0.0

    def getSmrt3(self):
        try:
            return int(self.ctxt.xpathEval('//all-battles/deaths')[0].getContent())
        except:
            return 0.0

    def toString(self):
        return (
             '; Statistika za igraca: ' + self.getIme3() + ' ' + self.getIme() + '  <||>  Naneta steta:  ' +
            str(self.getSteta()) + '  <||>  Broj borbi: ' + str(self.getBorba()) +
            '  <||>  Broj ubistava: ' + str(self.getUbistvo()) + '  <||>  Broj pogibija: '
             +  str(self.getSmrt()) 


            )

    def toString1(self):
        return (
             '; Statistika za igraca: ' + self.getIme3() + ' ' + self.getIme1() + '  <||>  Naneta steta: ' +
            str(self.getSteta1()) + '  <||>  Broj borbi: ' + str(self.getBorba1()) +
            '  <||>  Broj ubistava: ' + str(self.getUbistvo1()) + '  <||>  Broj pogibija: '
             +  str(self.getSmrt1()) 


            )
    def toString2(self):
        return (
             '; Statistika za igraca: ' + self.getIme3() + ' ' + self.getIme2() + '  <||>  Naneta steta: ' +
            str(self.getSteta2()) + '  <||>  Broj borbi: ' + str(self.getBorba2()) +
            '  <||>  Broj ubistava: ' + str(self.getUbistvo2()) + '  <||>  Broj pogibija: '
             +  str(self.getSmrt2()) 


            )
    def toString3(self):
        return (
             'Erepovac:  ' + self.getIme3() + ' ' '  <||>  Ukupna steta: ' +
            str(self.getSteta3()) + '  <||> Ukupan broj borbi: ' + str(self.getBorba3()) +
            '  <||> Ukupan  broj ubistava: ' + str(self.getUbistvo3()) + '  <||> Ukupan broj pogibija: '
             +  str(self.getSmrt3()) + '  <||> Odnos ubistva/smrti: ' + str(self.getBorba4())


            )

class Ekonomija:
    def loadByName(self, name):
        try:
            self.doc2 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/' + name + '/gold')
        except:
            return None
        self.ctxt2 = self.doc2.xpathNewContext()
        return self



    def getMedals(self):
        list = ''
        idx = 0
    
       
       
        points = float(self.ctxt2.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
           
     

        return points

    def getRon(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/ron/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        
        return points

    def getRonk(self):
        srb = self.getMedals()
    
        valuta = self.getRon()
        dmg = srb/valuta

        return dmg
        #dmg = (((float (rank-1) / 20) + 0.3) * ((strength / 10) +40)*38)
      

        #return map(lambda x: float(ceil(dmg * x)), (1, 1.2, 1.4, 1.6, 1.8, 2.0))
    def getBrl(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/brl/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getBrlk(self):
        srb = self.getMedals()
    
        valuta = self.getBrl()
        dmg = srb/valuta

        return dmg
    
    def getFrf(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/frf/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getFrfk(self):
        srb = self.getMedals()
    
        valuta = self.getFrf()
        dmg = srb/valuta

        return dmg

    def getDem(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/dem/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getDemk(self):
        srb = self.getMedals()
    
        valuta = self.getDem()
        dmg = srb/valuta

        return dmg

    def getHuf(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/huf/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getHufk(self):
        srb = self.getMedals()
    
        valuta = self.getHuf()
        dmg = srb/valuta

        return dmg

    def getCny(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/cny/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getCnyk(self):
        srb = self.getMedals()
    
        valuta = self.getCny()
        dmg = srb/valuta

        return dmg

    def getEsp(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/esp/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getEspk(self):
        srb = self.getMedals()
    
        valuta = self.getEsp()
        dmg = srb/valuta

        return dmg

    def getCad(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/Cad/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getCadk(self):
        srb = self.getMedals()
    
        valuta = self.getCad()
        dmg = srb/valuta

        return dmg

    def getUsd(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/usd/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
        return points

    def getUsdk(self):
        srb = self.getMedals()
    
        valuta = self.getUsd()
        dmg = srb/valuta

        return dmg

    def getGbp(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/gbp/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getGbpk(self):
        srb = self.getMedals()
    
        valuta = self.getGbp()
        dmg = srb/valuta

        return dmg

    def getPln(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/pln/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())


        return points

    def getPlnk(self):
        srb = self.getMedals()
    
        valuta = self.getPln()
        dmg = srb/valuta

        return dmg

    def getRub(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/rub/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getRubk(self):
        srb = self.getMedals()
    
        valuta = self.getRub()
        dmg = srb/valuta

        return dmg

    
    def getBgn(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/bgn/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getBgnk(self):
        srb = self.getMedals()
    
        valuta = self.getBgn()
        dmg = srb/valuta

        return dmg
    
    def getTry(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/try/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getTryk(self):
        srb = self.getMedals()
    
        valuta = self.getTry()
        dmg = srb/valuta

        return dmg

    def getGrd(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/grd/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getGrdk(self):
        srb = self.getMedals()
    
        valuta = self.getGrd()
        dmg = srb/valuta

        return dmg

    def getIdr(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/idr/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getIdrk(self):
        srb = self.getMedals()
    
        valuta = self.getIdr()
        dmg = srb/valuta

        return dmg

    def getIep(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/iep/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getIepk(self):
        srb = self.getMedals()
    
        valuta = self.getIep()
        dmg = srb/valuta

        return dmg

    def getIrr(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/irr/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getIrrk(self):
        srb = self.getMedals()
    
        valuta = self.getIrr()
        dmg = srb/valuta

        return dmg

    def getSit(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/sit/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getSitk(self):
        srb = self.getMedals()
    
        valuta = self.getSit()
        dmg = srb/valuta

        return dmg

    def getPkr(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/pkr/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getPkrk(self):
        srb = self.getMedals()
    
        valuta = self.getPkr()
        dmg = srb/valuta

        return dmg

    def getHrk(self):
        list = ''
        idx = 0
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/exchange/hrk/gold')
        self.ctxt = self.doc.xpathNewContext()
        points = float(self.ctxt.xpathEval('//offers/offer/exchange-rate/text()')[1].getContent())
     

        return points

    def getHrkk(self):
        srb = self.getMedals()
    
        valuta = self.getHrk()
        dmg = srb/valuta

        return dmg
    
    def getName(self):
        return self.ctxt.xpathEval('//citizen/name/text()')[0].getContent()


    def getVestinu(self):
        try:
            return float(self.ctxt.xpathEval('//work-skill-points')[0].getContent())
        except:
            return 0.0


    def toString(self):
        return (
             str(self.getMedals())  )
    def toString1(self):
        return (
             str(self.getRonk())  )
    def toString2(self):
        return (
             str(self.getBrlk())  )
    def toString3(self):
        return (
             str(self.getFrfk())  )
    def toString4(self):
        return (
             str(self.getDemk())  )
    def toString5(self):
        return (
             str(self.getHufk())  )
    def toString6(self):
        return (
             str(self.getCnyk())  )
    def toString7(self):
        return (
             str(self.getEspk())  )
    def toString8(self):
        return (
             str(self.getCadk())  )
    def toString9(self):
        return (
             str(self.getUsdk())  )
    def toString10(self):
        return (
             str(self.getGbpk())  )
    def toString11(self):
        return (
             str(self.getPlnk())  )
    def toString12(self):
        return (
             str(self.getRubk())  )
    def toString13(self):
        return (
             str(self.getBgnk())  )
    def toString14(self):
        return (
             str(self.getTryk())  )
    def toString15(self):
        return (
             str(self.getGrdk())  )
    def toString16(self):
        return (
             str(self.getIdrk())  )
    def toString17(self):
        return (
             str(self.getIepk())  )
    def toString18(self):
        return (
             str(self.getIrrk())  )
    def toString19(self):
        return (
             str(self.getSitk())  )
    def toString20(self):
        return (
             str(self.getPkrk())  )
    def toString21(self):
        return (
             str(self.getHrkk())  )
   

    







class Firme:
    def loadByName(self, name):
        try:
            self.doc2 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/' + name )
        except:
            return None
        self.ctxt2 = self.doc2.xpathNewContext()
        return self



    def getRifleRaw(self):
        #q5 rifles
     
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/210268')
        self.ctxt = self.doc.xpathNewContext()
        raw = float(self.ctxt.xpathEval('//company/raw-materials-in-stock/text()')[0].getContent())
        ime = self.ctxt.xpathEval('//company/name/text()')[0].getContent()
        if(raw < 2000):
            list = '\x02 '+ ime + '(' + str(raw) + '); \x02'
        
            return list
        
        list = '\x02 ' + '\x02  '
     

        return list

    def getFood2Raw(self):
        #q5 food
     
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/200584')
        self.ctxt = self.doc.xpathNewContext()
        raw = float(self.ctxt.xpathEval('//company/raw-materials-in-stock/text()')[0].getContent())
        ime = self.ctxt.xpathEval('//company/name/text()')[0].getContent()
        if(raw < 2000):
            list = '\x02 '+ ime + '(' + str(raw) + '); \x02'
        
            return list
        
        list = '\x02 ' + '\x02  '
     

        return list

    def getFoodRaw(self):
        #q5 Cd i kaseta
     
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/244751')
        self.ctxt = self.doc.xpathNewContext()
        raw = float(self.ctxt.xpathEval('//company/raw-materials-in-stock/text()')[0].getContent())
        ime = self.ctxt.xpathEval('//company/name/text()')[0].getContent()
        if(raw < 2000):
            list = '\x02 '+ ime + '(' + str(raw) + '); \x02'
        
            return list
        
        list = '\x02 ' + '\x02  '
     

        return list
    def getKarteRaw(self):
        #q2 karte
     
    
        
        self.doc = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/212301')
        self.ctxt = self.doc.xpathNewContext()
        raw = float(self.ctxt.xpathEval('//company/raw-materials-in-stock/text()')[0].getContent())
        ime = self.ctxt.xpathEval('//company/name/text()')[0].getContent()
        if(raw < 2000):
            list = '\x02 '+ ime + '(' + str(raw) + '); \x02'
        
            return list
        
        list = '\x02 ' + '\x02  '
     

        return list



    def toString(self):
        return (
            ' Firme sa kriticnom kolicinom raw-a su:' + self.getRifleRaw() + self.getFood2Raw()+ self.getFoodRaw() + self.getKarteRaw()
            
            )


    def getBrojPuca(self):
        
     
    
        
        self.doc1 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/210268')
        self.ctxt1 = self.doc1.xpathNewContext()
        raw1 = int(self.ctxt1.xpathEval('//company/stock/text()')[0].getContent())
        self.doc2 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/237552')
        self.ctxt2 = self.doc2.xpathNewContext()
        raw2 = int(self.ctxt2.xpathEval('//company/stock/text()')[0].getContent())
        self.doc3 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/192952')
        self.ctxt3 = self.doc3.xpathNewContext()
        raw3 = int(self.ctxt3.xpathEval('//company/stock/text()')[0].getContent())
        ukupno = raw1 + raw2 + raw3

        list = 'Trenutni stek puca je:\x02 Q5 RIFLES[' + str(raw1) + '] + Q5 HELIKOPTERI[' + str(raw2) + '] + Q5 ARTILJERIJA[' + str(raw3) + '] = ' +str(ukupno) + ' \x02 '
        
       
     

        return list

    def getBrojHleba(self):
        
     
    
        
        self.doc1 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/200584')
        self.ctxt1 = self.doc1.xpathNewContext()
        raw1 = int(self.ctxt1.xpathEval('//company/stock/text()')[0].getContent())
        self.doc2 = libxml2.parseFile('http://api.erepublik.com/v2/feeds/companies/244751')
        self.ctxt2 = self.doc2.xpathNewContext()
        raw2 = int(self.ctxt2.xpathEval('//company/stock/text()')[0].getContent())
        
        ukupno = raw1 + raw2

        list = 'Trenutni stek q5 hrane je:\x02 Skorpioni Food 2[' + str(raw1) + '] + Skorpionska CD i kaseta[' + str(raw2) + '] = ' + str(ukupno) + ' \x02 '
        
       
     

        return list
    
    #krece stock

