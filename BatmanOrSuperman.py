from __future__ import division
import urllib2
from stemming.porter2 import stem
from bs4 import BeautifulSoup
import string
from collections import Counter
import math
import json
import easygui

minste = 0
def acceptWord(word):

    list=["for","and","nor","but","or","yet","so","after","although","as",
          "because","before","even","if","once","that","since","though",
          "unless","until","when","where","while","such","than","i","the",
          "a","to","of","in","is","was","it","he","with","are"]

    if(word in list):
        return False
    else:
        return True

def getPages(film,sider=1):

    if(film == "batman"):
        url = "http://www.imdb.com/title/tt2975590/reviews?start="
        filename = "batComments.txt"
    else:
        url = "http://www.imdb.com/title/tt0109830/reviews?start="
        filename = "otherComments.txt"

    for i in range(0,sider):
        url = url+str(i*10)
        html = urllib2.urlopen(url)

        soup = BeautifulSoup(html,"html.parser")

        [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
        visible_text = soup.getText()
        email= visible_text.lower().replace('\n',' ')
        email = email.replace('\r',' ')
        for p in string.punctuation:
            email = email.replace(p," ")
        email = email.encode('utf-8')

        if(i == 0):
            file=open(filename,"w")
        else:
            file=open(filename,"a")

        file.write(email)
        file.close()

def getMap(filename,handling):

    if(handling == "create map"):
        file = open(filename+".txt","r")
        text = file.read()
        file.close()

        emails = filter(None,[stem(word) for word in text.split(" ") if(acceptWord(word))])
        map = (Counter(emails))
        a = dict(map)
        save(a,filename)

        return a

    elif(handling=="load map"):
        a = load(filename)
        return a

def calcProb(spamMap,hamMap,spamNr,hamNr):

    probs = {}
    for key in spamMap:
        if(spamMap[key]>minste):
            if key in hamMap:
                if(hamMap[key]>minste):
                    spamFreq = spamMap[key]
                    hamFreq = hamMap[key]
                    prob = (spamFreq/spamNr)/((spamFreq/spamNr)+(hamFreq/hamNr))
                    probs[key] = prob
                else:
                    probs[key] = 0.99
            else:
                probs[key] = 0.99

    for key in hamMap:
        if(hamMap[key]>minste):
            if key in spamMap:
                if(spamMap[key]<minste+1):
                    probs[key] = 0.01
            else:
                probs[key] = 0.01

    save(probs,"probabilities")
    return probs

def updateProb(filenameSpam,filenameHam,antall,map,probs):

    a = load(filenameSpam)
    b = load(filenameHam)
    c = load(antall)

    for key in map:
        if key in a:
            if a[key]>minste:
                if key in b:
                    if b[key]>minste:
                        spamFreq = a[key]
                        hamFreq = b[key]
                        prob = (spamFreq/c["spam"])/((spamFreq/c["spam"])+(hamFreq/c["ham"]))
                        probs[key] = prob
                    else:
                        probs[key] = 0.99
                else:
                    probs[key] = 0.99
            elif key in b:
                if b[key] > minste:
                    probs[key] = 0.1
        elif key in b:
            if b[key] > minste:
                probs[key] = 0.1

    save(probs,"probabilities")

def classify(text, probs):

    map = {}
    diffMap = {}
    neutral = 0.5
    xlist = [None]*20
    list = filter(None,[stem(word.lower()) for word in text.split(" ") if(acceptWord(word))])
    a = (Counter(list))
    mapNr = dict(a)

    for word in list:
        if word in probs:
            map[word] = probs[word]
            if(map[word]<neutral):
                diffMap[word] = neutral - map[word]
            else:
                diffMap[word] = map[word] - neutral
        else:
            map[word] = 0.5
            diffMap[word] = 0.1

    biggest = ""
    for i in range(0,20):
        for key in diffMap:
            if biggest in diffMap:
                if(diffMap[biggest] < diffMap[key]):
                    biggest = key

            else:
                biggest = key

        xlist[i] = map[biggest]
        if(mapNr[biggest]>1):
            mapNr[biggest] -=1
        else:
            diffMap[biggest] = -1

        if(i >= len(list)-1):
            break

    prob1 = 0.0
    prob2 = 0.0
    for k in range(0,20):
        if(xlist[k]== None):
            break

        prob1 +=math.log(xlist[k],10)
        prob2 +=math.log(1-xlist[k],10)
    prob1 = math.pow(10,prob1)
    prob2 = math.pow(10,prob2)
    p = (prob1)/(prob1+prob2)
    print p
    print map
    if(p>0.5):
        return True
    else:
        return False

def updateTable(review,filename,type):

    emails = filter(None,[stem(word) for word in review.split(" ") if(acceptWord(word))])
    map = (Counter(emails))
    a = dict(map)

    b = load(filename)
    for key in a:
        if key in b:
            b[key] += a[key]
        else:
            b[key] = a[key]

    save(b,filename)

    c = load("Antall")
    if(type == "spam"):
        c["spam"] +=1
    elif(type=="ham"):
        c["ham"] +=1

    save(c,"Antall")

    return a

def program():

    a = easygui.ynbox('Load or restart?', 'Spamfilter', ('Load', 'Restart'))

    if(a==True):
        Spam = getMap("batComments","load map")
        Ham = getMap("otherComments","load map")
        antall = load("Antall")
        prob = load("probabilities")

    else:
        b = easygui.ynbox('Get reviews from ibdm? Press yes if these are not '
                          'already present in your computer','Spamfilter',('Yes','No'))
        if(b):
            getPages("ba",10)
            getPages("batman",10)

        Spam = getMap("batComments","create map")
        Ham = getMap("otherComments","create map")
        antall = {"spam":30,"ham":30}
        save(antall,"Antall")
        prob = calcProb(Spam,Ham,antall["spam"],antall["ham"])

    review = easygui.textbox(msg='Write your review:', title='Spamfilter', text='', codebox=0)

    if(classify(review,prob)):
        x = easygui.ynbox('Was this a Batman Vs Superman review?','Spamfilter',('Yes','No'))
        if(x):
            a=updateTable(review,"batComments","spam")
            updateProb("batComments","otherComments","Antall",a,prob)
        else:
            a=updateTable(review,"otherComments","ham")
            updateProb("batComments","otherComments","Antall",a,prob)

    else:
        x = easygui.ynbox('Was this a Forrest Gump review?','Spamfilter',('Yes','No'))
        if(x):
            a=updateTable(review,"otherComments","ham")
            updateProb("batComments","otherComments","Antall",a,prob)
        else:
            a=updateTable(review,"batComments","spam")
            updateProb("batComments","otherComments","Antall",a,prob)

def save(map,filename):

    with open(filename+'.json', 'w') as f:
        json.dump(map, f)

def load(filename):

    with open(filename+'.json') as f:
        d = json.load(f)
    return d

program()


