from __future__ import division
import numpy as np
import itertools
try:
    from wx.lib.pubsub import Publisher as pub
except ImportError:
    from wx.lib.pubsub import pub


class UserPrograms(object):
    """
    UserPrograms:
        A class to contain all the custom user programs.
        Insert your own functions here :)
    """

    def __init__(self, controller):
        self.m = controller.model
        self.v = controller.view
        self.list = [method for method in dir(self) if (not '__' in method) and callable(getattr(self,method))]
        self.Vset = 0.0



    ######################## Hidden Functions 


    def __ChangePulse(self, type_='Reset', lead=5, width=50, tail=5, amp=3.0, nano=True):
        if nano:
            lead, width, tail = np.array([lead, width, tail]) * 1e-9

        ind = ['Set', 'Reset', 'Gate'].index(type_)
        plist = [self.m.set_pulse, self.m.reset_pulse, self.m.gate_pulse]
        pulse = plist[ind]
        pdict = dict(LEADING=lead, WIDTH=width, TRAILING=tail, HIGH=amp)

        for key, value in pdict.items():
            pulse[key] = value

        self.m.hardware_changed = True
        pub.sendMessage('RefreshControls')


    def __abort(self):
        if self.m.want_to_abort:
            pub.sendMessage("Abort")
            return True



    def __blwl(self, bl, wl):
        self.m.bl = bl
        self.m.wl = wl
        pub.sendMessage('RefreshControls')



    ######################## Base Functions 



    def test(self):
        self.__ChangePulse('Reset', 500, 500, 5000, 3.0)
        # self.__Pulse('Reset')
        self.__ChangePulse('Set', 5, 300, 5, 1.0)
        # self.__Pulse('Set')


        # self.m.reset_pulse['HIGH']=1.9
        # print self.m.reset_pulse

        # self.m.Vread = 0.4
        # print self.m.Vread


        # pub.sendMessage('RefreshHardware')
        # pub.sendMessage('RefreshControls')

        # print self.m.reset_pulse
        # print self.m.Vread


    def CheckCurrents(self):
        """
        Check to see if (Ids(1) == Ics(3)) and (Igs(2) == Isx(4))
        """
        self.m.checkInitialized()
        #Measure a new point
        self.m._Model__setAddress(self.m.bl, self.m.wl)
        res = self.m.smu.measureTrace(read_all=True)
        print 'Voltage: (ds:%.2e, gs:%.2e, cs:%.2e, sx:%.2e)' % tuple(res[:, 0])
        print 'Current: (ds:%.2e, gs:%.2e, cs:%.2e, sx:%.2e)' % tuple(res[:, 1])
        check = (res[0,1] == res[2,1]) and (res[1,1] == res[3,1])
        print check



    def Set(self, V=None):
        if V:
            self.m.set_pulse['HIGH']= V
            pub.sendMessage('RefreshControls')

        self.m.current_pulse = 'Set'
        pub.sendMessage('RefreshHardware')
        self.m.Pulse()


    def Reset(self, V=None):
        if V:
            self.m.reset_pulse['HIGH']= V
            pub.sendMessage('RefreshControls')

        self.m.current_pulse = 'Reset'
        pub.sendMessage('RefreshHardware')
        self.m.Pulse()


    def ResetSet(self, Vset=None):
        self.Reset()
        self.Set(Vset)



    ######################## Composite Functions 

    def MeasureArray(self):
        for bl in range(1,11):
            for wl in range(1,11):
                self.__blwl(bl, wl)
                self.m.MeasureR()
                if self.__abort(): return  


    def SetArray(self):
        for bl in range(1,11):
            for wl in range(1,11):
                self.__blwl(bl, wl)
                self.Set()
                if self.__abort(): return   


    def ResetArray(self):
        for bl in range(1,11):
            for wl in range(1,11):
                self.__blwl(bl, wl)
                self.Reset()        
                if self.__abort(): return  


    def FourStates(self):
        typelist = ['Reset', 'Set', 'Set', 'Set']
        vlist = [0, .8, 1.4, 2.0]
        bl_list = [4.,5.,6.,7.,8.,9.,10.]


        for bl in bl_list:
            self.m.bl = bl

            for i in range(1000):
                for t, v in zip(typelist, vlist):
                    self.m.current_pulse = t
                    self.m.set_pulse['HIGH']= v
                    pub.sendMessage('RefreshControls')
                    pub.sendMessage('RefreshHardware')
                    self.m.Pulse()
                    if self.__abort(): return  


 


    def VgSweep(self):
        vlist = np.arange(1.0,3.0,0.05)

        # bl_list = [ 1 ]
        # wl_list = [ 1 ]

        # for bl, wl in zip(bl_list, wl_list):
        #     self.__blwl(bl, wl)
               
        for i in np.arange(1000):
            # np.random.shuffle(vlist)

            for v in vlist:
                self.ResetSet(v)
                if self.__abort(): return  

 


    def ManyPartialReset(self):
        nclear = 7
        vlist = np.arange(1.0,3.0,0.2)

        self.__ChangePulse('Set', 500, 5000, 500, 3.0)

        for v in vlist:

            self.__ChangePulse('Reset', 5, 50, 5, 3.0)
            self.m.note = 'clear'

            for i in range(nclear):
                self.Reset()
                if self.__abort(): return  

            for i in range(nclear):
                self.Set()
                if self.__abort(): return  
    
            self.__ChangePulse('Reset', 5, 300, 5, v)
            self.m.note = 'data'
            self.Reset()



    def BL_partialSet(self):

        #Setup
        self.__ChangePulse('Set', 100, 500, 1000, 3.0)
        self.__ChangePulse('Reset', 5, 50, 5, 3.0)
        blwl_list = list(itertools.product(np.arange(1,11), repeat=2))
        np.random.shuffle(blwl_list)

        #Switch Device
        for bl, wl in blwl_list:
            self.__blwl(bl, wl)


            #Initialization
            self.m.note = 'Initialize'

            for i in range(5):
                for i in range(4):
                    self.__ChangePulse('Gate', 1e-5, 1e-3, 1e-5, 3.0, nano=False)
                    self.Reset()

                for i in range(7):
                    self.__ChangePulse('Gate', 1e-5, 1e-3, 1e-5, 1.5, nano=False)
                    self.Set()

            for i in range(4):
                    self.__ChangePulse('Gate', 1e-5, 1e-3, 1e-5, 3.0, nano=False)
                    self.Reset()




            # Take Data (120 points each)
            for i in np.arange(120):
                vlist = np.arange(0.7,1.71,0.01)

                for v in vlist:
                    self.__ChangePulse('Gate', 1e-5, 1e-3, 1e-5, v, nano=False)
                    self.m.note = str(v)
                    self.Set()

                    self.__ChangePulse('Gate', 1e-5, 1e-3, 1e-5, 3.0, nano=False)
                    self.Reset()
                    if self.__abort(): return


