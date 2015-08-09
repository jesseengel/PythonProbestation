from __future__ import division
import numpy as np
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

    def __init__(self, model):
        self.m = model
        self.list = [method for method in dir(self) if (not '__' in method) and callable(getattr(self,method))]
        self.Vset = 0.0



    def ResetSet(self):
        self.m.current_pulse = 'Reset'
        pub.sendMessage('RefreshHardware')
        self.m.Pulse()

        self.m.current_pulse = 'Set'
        self.m.set_pulse['HIGH']= self.Vset
        pub.sendMessage('RefreshHardware')
        self.m.Pulse()


    ### ADD CUSTOM FUNCTIONS HERE ###


    def MeasureArray(self):
        for bl in range(1,11):
            for wl in range(1,11):
                self.m.bl = bl
                self.m.wl = wl
                # pub.sendMessage('RefreshControls')
                self.m.MeasureR()

                if self.m.want_to_abort:
                    pub.sendMessage("Abort")
                    return

        


    def SetArray(self):
        self.m.current_pulse = 'Set'
        pub.sendMessage('RefreshHardware')
        for bl in range(1,11):
            for wl in range(1,11):
                pub.sendMessage('RefreshControls')
                self.m.bl = bl
                self.m.wl = wl
                # pub.sendMessage('RefreshControls')
                self.m.Pulse()

                if self.m.want_to_abort:
                    pub.sendMessage("Abort")
                    return

        


    def ResetArray(self):
        self.m.current_pulse = 'Reset'
        pub.sendMessage('RefreshHardware')
        for bl in range(1,11):
            for wl in range(1,11):
                pub.sendMessage('RefreshControls')
                self.m.bl = bl
                self.m.wl = wl
                # pub.sendMessage('RefreshControls')
                self.m.Pulse()
        
                if self.m.want_to_abort:
                    pub.sendMessage("Abort")
                    return




