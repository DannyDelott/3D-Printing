"""Tied rim clips for an exposed top core. Only the rear clip takes a wood screw."""
def build(r):
 ex=r.extr; C=r.circle
 def clip(back):
  zone=r.box(-9,37,9,49);cap=(C(46.4)-C(39.8))^zone
  jaws=((C(46.4)-C(44.55))+(C(40.9)-C(39.8)))^zone
  pad=r.rnd(-7.4,43.65,7.4,61.8 if back else 51.5,2.35)
  m=ex(cap+pad,-r.lip,0)+ex(jaws,0,4.2)+ex(pad-C(44.55),0,1.25)
  for x in [-3.6,3.6]:m-=ex(r.rnd(x-.95,48.4-1.6,x+.95,48.4+1.6,.4),-2,9)
  if back:
   m+=ex(C(4.9,0,56.5),0,2.8);m-=ex(C(2.4,0,56.5),-3,9)
   m-=ex(r.rnd(-4.8,46.7,4.8,50.1,.5),-r.lip-.02,-r.lip+1.08)
  return m
 l=r.rnd(-r.lip-1.1,-4.05,r.L+r.lip-.08,4.05,.44)
 tie=ex(l-l.offset(-.9),48.4-1.25,48.4+1.25).transform([[0,1,0,0],[0,0,1,0],[1,0,0,0]])
 return clip,tie
