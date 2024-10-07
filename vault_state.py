# Import python modul
import copy

import xml.dom.minidom as dom

# Import Debug Server for Eclipse
import os   
from os import *
import sys

import roslib
import rospy

from std_msgs.msg import String

class VaultState:

    def __init__(self,filename):
        # create an dictionary for name:pointer to save pointers of states, signals ...
        self.state=[]
        self.transition={}
        self.data={}

        self.importscxml(filename)
        self.currentstate="parent"
        self.abfolge=[]
        #rospy.init_node('mission_handler_statemachine')
        rospy.Subscriber('/mission_handler/Event',String,self.f_ros_event)
        self.compare = rospy.Subscriber
        self.comparevalue = "0"
        self.comparestate = "dummy"
        self.comparetopic = "dummy"
        self.abort = 0

    def _addstate(self,knoten):
        #print "lese state" 
        name = knoten.getAttribute("id")
        #print name
        self.state.append(name)
        #print knoten.childNodes
        for eintrag in knoten.childNodes:
          if eintrag.nodeName == "initial":
             for subeintrag in eintrag.childNodes:
               if subeintrag.nodeName == "transition":
                  #print "initial target "+subeintrag.getAttribute("target")
                  self.transition.update({knoten.getAttribute("id"):{"initial":[subeintrag.getAttribute("target"),0,0,0]}})
          if eintrag.nodeName == "state": 
             self._addstate(eintrag)
          if eintrag.nodeName == "datamodel":
             self._adddata(eintrag,name)
          if eintrag.nodeName == "transition":
             #print "transition from: "+name+" to: "+eintrag.getAttribute("target")+" event: "+eintrag.getAttribute("event")
             #zwischenspeichert={}
             zwischenspeichert=self.transition.get(name,{})
             eventnew=eintrag.getAttribute("event").split('|')
             if len(eventnew)==1:
               zwischenspeichert.update({eintrag.getAttribute("event"):[eintrag.getAttribute("target"),0,0,0]})
             else:
               zwischenspeichert.update({eventnew[0]:[eintrag.getAttribute("target"),eventnew[1],eventnew[2],eventnew[3]]})
             self.transition.update({name:zwischenspeichert})
             #print self.transition

    def get_abort(self):
        return self.abort

    def set_abort(self,number):
        self.abort = number
    
    def fcompare(self,msg):
        print msg
        if msg.data==self.comparevalue:
           if self.comparestate != "dummy":
              self.change_state(self.comparestate)
              self.comparestate = "dummy"
              self.comparetopic = "dummy"
              self.compare.unregister()
              #self.compare = rospy.Subscriber("/mission_handler/dummy",String,self.compare)

    def _adddata(self,knoten,state):
        #print "Daten auslesen"
        for eintrag in knoten.childNodes:
          if eintrag.nodeName == "data":
            #print "data id: "+eintrag.getAttribute("id")+"  | exp: "+eintrag.getAttribute("expr")
            #zwischenspeicher={}
            zwischenspeicherd=self.data.get(state,{})
            #print zwischenspeicher
            zwischenspeicherd.update({eintrag.getAttribute("id"):eintrag.getAttribute("expr")})
            #print zwischenspeicher
            self.data.update({state:zwischenspeicherd})

    def importscxml(self,filename):
        #filename="plan.scxml"
        baum = dom.parse(filename)
        erstesKind = baum.firstChild
        if erstesKind.getAttribute("initial"):
          #print erstesKind.getAttribute("initial")
          self.transition.update({"parent":{"initial":[erstesKind.getAttribute("initial"),0,0,0]}})
        for eintrag in baum.firstChild.childNodes: 
          if eintrag.nodeName == "state": 
             self._addstate(eintrag)
          if eintrag.nodeName == "datamodel":
             self._adddata(eintrag,"parent")
        #print self.state
        #print self.data
        #print self.transition

    def get_state(self):
        return self.currentstate

    def get_data(self):
        aktuellerstand = self.get_state()
        return self.get_data_state(aktuellerstand)
        
    def get_data_state(self,state):
        return self.data.get(state, "empty")

    def run(self):
        while self.event("initial") != "no_transition":
          i=1

    def f_ros_event(self,msg):
        print msg.data
        self.event(msg.data)

    def event(self,event):
        #print event
        aktuellerstand = self.get_state()
        #print aktuellerstand
        tmptransition = self.transition.get(aktuellerstand,{})
        #print tmptransition
        neuerstand = tmptransition.get(event, "empty")
        #print neuerstand
        if neuerstand == "empty":
           return "no_transition"
        else:
           if event == "abort":
              self.abort = 1
           #TODO abfragen ob neuerstate in self.state
           if self.state.count(neuerstand[0])==0:
              return "no state"
           if neuerstand[1]=="topic":
              self.comparevalue = neuerstand[3]
              self.comparestate = neuerstand[0]
              if neuerstand[2] != self.comparetopic:
                 self.comparetopic = neuerstand[2]
                 print "Subscribe Topic: "+str(neuerstand[2])+"  Value: "+str(neuerstand[3])
                 self.compare = rospy.Subscriber(neuerstand[2],String,self.fcompare)
           else:
              self.change_state(neuerstand[0])
           return "ok"

    def change_state(self,newstate):
        aktuellerstand = self.get_state()
        self.currentstate = newstate
        self.abfolge.append(aktuellerstand)
        self.run()
        rospy.set_param("/mission_handler/state_machine",self.currentstate)
        return "ok"

if __name__ == '__main__':
  #print "start"
  x = VaultState()
  x.run()
  print x.event("init_ok")
  print x.get_state()
  
