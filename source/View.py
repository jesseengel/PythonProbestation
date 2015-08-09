# MainGUI imports
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

import numpy as np
import pylab
import os
import wx


class View(wx.Frame):
    """
    A Gradual Set program for phase change synapses. This program is meant
    to link to a wxFrame GUI object with a graph, and a run button:
    Requires: gui.draw_plot()
    Provides: self.data_x, self.data_y, self.title
    """    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Pulse Sweep GUI')
        # self.Bind(wx.EVT_CLOSE, self.__close)


         #An event timer for timed events if needed
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)        

        self.__create_menu()
        self.__create_status_bar()
        self.__create_main_panel()

    # def __close(self, event):
    #     self.Destroy()


    
    ### Create Menubars ###
    def __create_menu(self):
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        
        menu_file.AppendSeparator()
        
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
                
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)


    ### Create Status Bar ###
    def __create_status_bar(self):
        self.statusbar = self.CreateStatusBar()



    ### Create Main Panel ###
    def __create_main_panel(self):

        ### Create the elements ###


        ### Big Elements: Panel, Canvas
        self.panel = wx.Panel(self)
        self.R_plot = MyPlot(self.panel, ylabel='Resistance (Ohms)', xlabel='Pulse #', graph_title='Gradual Set/Reset: R(pulse)', semilogy=True)
        self.V_plot = MyPlot(self.panel, ylabel='Magnitude (V or A)', xlabel='Pulse #', graph_title='Pulse Magnitudes')
        # self.create_plot()
        # self.canvas = FigCanvas(self.panel, -1, self.fig)
        # self.canvas.mpl_connect('pick_event', self.on_pick)


        ### Controls

        # Filename 
        self.textctrl_filename = wx.TextCtrl(self.panel, value='', style=wx.TE_PROCESS_ENTER)   
        # Run Number
        self.label_run_number = wx.StaticText(self.panel, label='Run #')
        self.textctrl_run_number = wx.TextCtrl(self.panel, style=wx.TE_PROCESS_ENTER)        



        ### Config Box
        self.config_box = PanelBox(self.panel, name='Config')

        self.label_chip_type = wx.StaticText(self.config_box, label ='Chip Type:')
        self.combo_chip_type = wx.ComboBox(self.config_box, style=wx.CB_READONLY)
        self.combo_chip_type.AppendItems(['Macro', 'Kilobit'])
        # self.combo_chip_type.SetValue('Macro')

        self.label_bl = wx.StaticText(self.config_box, label='BitLine')
        self.label_wl = wx.StaticText(self.config_box, label='WordLine')
        self.textctrl_bl = wx.TextCtrl(self.config_box, style=wx.TE_PROCESS_ENTER)
        self.textctrl_wl = wx.TextCtrl(self.config_box, style=wx.TE_PROCESS_ENTER)


        self.label_program_pulse = wx.StaticText(self.config_box, label ='Program Pulse:')
        self.combo_program_pulse = wx.ComboBox(self.config_box, style=wx.CB_READONLY)
        self.combo_program_pulse.AppendItems(['bl', 'wl'])
        # self.combo_program_pulse.SetValue('wl')

        self.label_bl_card = wx.StaticText(self.config_box, label ='Bitline Card:')
        self.combo_bl_card = wx.ComboBox(self.config_box, style=wx.CB_READONLY)
        self.combo_bl_card.AppendItems(['1', '2'])
        # self.combo_bl_card.SetValue('1')

        self.label_integration_time = wx.StaticText(self.config_box, label ='Integration Time:')
        self.combo_integration_time = wx.ComboBox(self.config_box, style=wx.CB_READONLY)
        self.combo_integration_time.AppendItems(['SHORT', 'MEDIUM', 'LONG'])



        self.label_vread = wx.StaticText(self.config_box, label='Vread:')
        self.textctrl_vread = wx.TextCtrl(self.config_box, style=wx.TE_PROCESS_ENTER)

        labels = [self.label_bl,
                  self.label_wl,
                  self.label_chip_type,
                  self.label_bl_card,
                  self.label_program_pulse,
                  self.label_vread,
                  self.label_integration_time]


        controls = [self.textctrl_bl,
                    self.textctrl_wl,
                    self.combo_chip_type,
                    self.combo_bl_card,
                    self.combo_program_pulse,
                    self.textctrl_vread,
                    self.combo_integration_time]


        self.config_box.set_labels_and_controls(labels, controls)
        ###




        ###A Row of Pulseboxes
        self.pulsebox_set = PulseBox(self.panel, 'Set')
        self.pulsebox_reset = PulseBox(self.panel, 'Reset')
        self.pulsebox_gate = PulseBox(self.panel, 'Gate')

        #Label for how to plug in all the wires
        self.label_config = wx.StaticText(self.panel, label='')

        # #An Update Button
        # self.button_update = wx.Button(self.panel, label='Update')



        # Buttons
        self.button_run = wx.Button(self.panel, label="Run")
        self.button_abort = wx.Button(self.panel, label="Abort")
        self.button_reload = wx.Button(self.panel, label="Reload")
        self.button_filename = wx.Button(self.panel, label="Set Filename")
        self.button_new_file = wx.Button(self.panel, label="NewFile")
        self.button_set_pulse = wx.Button(self.panel, label="Set Pulse")
        self.button_reset_pulse = wx.Button(self.panel, label="Reset Pulse")
        self.button_measure = wx.Button(self.panel, label="Measure R")
        self.button_userprograms = wx.Button(self.panel, label="Load")

        # Program Combo Button
        self.label_program = wx.StaticText(self.panel, label ='Script Programs:')
        self.combo_program = wx.ComboBox(self.panel, style=wx.CB_READONLY)


        
        ###### Arrange the elements #######
        
        #Add(parent, porportion, flags=...) 
        std_flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL

        #Column 0 (Everything)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        #Row 0 (Graphs)
        self.hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox0_1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox0.Add(self.R_plot.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.hbox0.Add(self.V_plot.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.hbox0_1.Add(self.R_plot.toolbar, 1, flag=wx.CENTER | wx.EXPAND)
        self.hbox0_1.Add(self.V_plot.toolbar, 1, flag=wx.CENTER | wx.EXPAND)

        
        #Row 1 (Filename)
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.button_filename, border=5, flag=std_flag | wx.EXPAND)
        self.hbox1.Add(self.textctrl_filename,  proportion=2, border=5, flag=std_flag| wx.EXPAND)
        self.hbox1.Add(self.label_run_number, border=5, flag=std_flag)
        self.hbox1.Add(self.textctrl_run_number, border=5, flag=std_flag)
        self.hbox1.Add(self.button_new_file, border=5, flag=std_flag | wx.EXPAND)
        self.hbox1.Add((0,0), proportion=1)




        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(self.pulsebox_set, border=5, flag = wx.EXPAND)
        self.hbox3.Add(self.pulsebox_reset, border=5, flag = wx.EXPAND)
        self.hbox3.Add(self.pulsebox_gate, border=5, flag = wx.EXPAND)
        self.hbox3.Add(self.config_box, border=5, flag = wx.EXPAND)
        self.hbox3.Add(self.label_config, border=5, flag = wx.EXPAND)


        #Row 5 (Program Buttons)
        self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        # self.hbox4.Add(self.button_update, border=5, flag=std_flag)
        self.hbox4.Add(self.button_measure, border=5, flag=std_flag)
        self.hbox4.Add(self.button_set_pulse, border=5, flag=std_flag)
        self.hbox4.Add(self.button_reset_pulse, border=5, flag=std_flag)
        self.hbox4.Add((350,0), proportion=1)
        self.hbox4.Add(self.label_program, border=5, flag=std_flag)
        self.hbox4.Add(self.combo_program, border=5, flag=std_flag)
        self.hbox4.Add(self.button_run, border=5, flag=std_flag)
        self.hbox4.Add(self.button_abort, border=5, flag=std_flag)
        self.hbox4.Add(self.button_reload, border=5, flag=std_flag)
        self.hbox4.Add(self.button_userprograms, border=5, flag=std_flag)



        #Add to Column 0
        self.vbox.Add(self.hbox0, 1, flag=wx.ALIGN_LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.hbox0_1, 0, flag=wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)
        self.vbox.AddSpacer(10)        
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)
        # self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.AddSpacer(3)
        self.vbox.Add(self.hbox3, 0, flag=wx.ALIGN_LEFT | wx.TOP)       
        self.vbox.AddSpacer(3)
        self.vbox.Add(self.hbox4, 0, flag=wx.ALIGN_LEFT | wx.TOP)       
        self.vbox.AddSpacer(3)

        # #Add the FlexGridSizer to the StaticBoxSizer
        # self.vbox.Add(self.fgs, proportion=1, flag=wx.ALL, border=15)

        # Make it Fit
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
    



















    ### MenuBar EVENT HANDLERS ####

    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
    
    def on_exit(self, event):
        self.Destroy()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')


    # def on_pick(self, event):
    #     # The event received here is of the type
    #     # matplotlib.backend_bases.PickEvent
    #     #
    #     # It carries lots of information, of which we're using
    #     # only a small amount here.
    #     # 
    #     box_points = event.artist.get_bbox().get_points()
    #     msg = "You've clicked on a bar with coords:\n %s" % box_points
        
    #     dlg = wx.MessageDialog(
    #         self, 
    #         msg, 
    #         "Click!",
    #         wx.OK | wx.ICON_INFORMATION)

    #     dlg.ShowModal() 
    #     dlg.Destroy()  


    # def FillComboBoxPrograms(self, program_list):
    #     self.combo_program.AppendItems(program_list)


    


















class MyPlot(object):
    def __init__(self, parent, graph_title='Gradual Set: R(pulse)', xlabel='Pulse Number',
                    ylabel='Resistance (Ohms)', dimensions=(6.0,5.0), semilogy=False):
        self.graph_title = graph_title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.semilogy = semilogy

        self.dpi = 100
        self.fig = Figure(dimensions, dpi=self.dpi)
        self.canvas = FigCanvas(parent, -1, self.fig)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor([.05,.05,.05])
        self.axes.set_title(self.graph_title, size=12)
        self.axes.set_xlabel(self.xlabel, size=10)
        self.axes.set_ylabel(self.ylabel, size=10)

        # self.canvas.mpl_connect('pick_event', self.on_pick)

        # Create the navigation toolbar, tied to the canvas
        self.toolbar = NavigationToolbar(self.canvas)
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        #
        if semilogy:
            self.plot_data = self.axes.semilogy(np.array([]), 'yo-')[0]
                # , linewidth=1, color=(1, 1, 0),marker='o',markersize=0.5)[0]
        else:
            self.plot_data = self.axes.plot(np.array([]), 'yo-')[0]
            # linewidth=1, color=(1, 1, 0),marker='o',markersize=1)[0]

    def Refresh(self, x, y):
        """ Redraws the plot
        """
        if self.semilogy:
            try:
                ymin = round(min(y[y>0]), 0) - 1
            except ValueError:
                ymin = 1
        else:
            ymin = round(min(y), 0) - 1

        ymax = round(max(y), 0) + 1
        xmin = round(min(x), 0) - 1
        xmax = round(max(x), 0) + 1


        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)
        
        # anecdote: axes.grid assumes b=True if any other flag is
        # given even if b is set to False.
        # so just passing the flag into the first statement won't
        # work.
        #
        if self.semilogy:
            self.axes.yaxis.grid(b=True, which='minor', color=(.2,.2,.2), linestyle=':')
            self.axes.grid(b=True, which='major', color='gray', linestyle=':')
            self.axes.minorticks_on()
        else:
            self.axes.grid(b=True, which='major', color='gray')

        # self.axes.grid(True, color='gray')
        # Using setp here is convenient, because get_xticklabels
        # returns a list over which one needs to explicitly 
        # iterate, and setp already handles this.
        #  
        pylab.setp(self.axes.get_xticklabels(), 
            visible=True)
        
        self.plot_data.set_xdata(x)
        self.plot_data.set_ydata(y)
        
        try:
            self.canvas.draw()
        except ValueError:
            print 'Woops!\nSome Drawing SNAFU happened.\n'



class PulseBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, name='Set'):        
        wx.Panel.__init__(self, parent)

        #Create Controls
        #All Contained in a Static Box       
        self.box = wx.StaticBox(self, label=name + ' Pulse (seconds)')
        self.sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)        

        #A row of labels
        self.label_lead = wx.StaticText(self, label='Leading')
        self.label_width = wx.StaticText(self, label='Width')
        self.label_trail = wx.StaticText(self, label='Trailing')
        self.label_delay = wx.StaticText(self, label='Delay')
        self.label_voltage = wx.StaticText(self, label='Height (V or A)')
        self.label_impedance = wx.StaticText(self, label='Impedance')

        #A row of textctrls
        self.textctrl_lead = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.textctrl_width = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.textctrl_trail = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.textctrl_delay = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.textctrl_voltage = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.textctrl_impedance = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

        #ComboBox
        self.label_type = wx.StaticText(self, label ='Type')
        self.combo_type = wx.ComboBox(self, style=wx.CB_READONLY)
        self.combo_type.AppendItems(['Voltage', 'Current'])
        self.combo_type.SetValue('Voltage')

        #Generate Layout
        #Use a FlexGrid Sizer
        self.fgs = wx.FlexGridSizer(rows=7, cols=2, vgap=9, hgap=25)

        self.fgs.AddMany([(self.label_lead), (self.textctrl_lead, 1, wx.EXPAND),
            (self.label_width), (self.textctrl_width, 1, wx.EXPAND),
            (self.label_trail), (self.textctrl_trail, 1, wx.EXPAND),
            (self.label_delay), (self.textctrl_delay, 1, wx.EXPAND),
            (self.label_impedance), (self.textctrl_impedance, 1, wx.EXPAND),
            (self.label_voltage), (self.textctrl_voltage, 1, wx.EXPAND),
            (self.label_type), (self.combo_type, 1, wx.EXPAND)])

        #Expand the TextCtrl boxes to fill panel
        self.fgs.AddGrowableCol(1, 1)

        #Add the FlexGridSizer to the StaticBoxSizer
        self.sizer.Add(self.fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=15)

        #FitTheSizer
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    # def Refresh(self, pulse_dict):
    #     self.textctrl_lead.SetValue( str(pulse_dict['LEADING']) )
    #     self.textctrl_trail.SetValue( str(pulse_dict['TRAILING']) )
    #     self.textctrl_width.SetValue( str(pulse_dict['WIDTH']) )
    #     self.textctrl_delay.SetValue( str(pulse_dict['DELAY']) )
    #     self.textctrl_impedance.SetValue( '%.2e' % int(pulse_dict['IMPEDANCE']) )
    #     self.textctrl_voltage.SetValue( str(pulse_dict['HIGH']) )
    #     self.combo_type.SetValue( str(pulse_dict['TYPE']) )
    #     # pulse_type = ['Voltage', 'Current'][ str(pulse_dict['TYPE']) == 'CURR' ]
    #     # self.combo_type.SetValue( pulse_type )    




class PanelBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, name='Box', labels=[], controls=[]):        
        wx.Panel.__init__(self, parent)

        #All Contained in a Static Box       
        self.box = wx.StaticBox(self, label=name)
        self.sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)        


    def set_labels_and_controls(self, labels=[], controls=[]):
        rows = len(labels)
        columns = 2

        #Generate Layout
        #Use a FlexGrid Sizer
        self.fgs = wx.FlexGridSizer(rows=rows, cols=columns, vgap=9, hgap=25)

        labels = [ (l,) for l in labels ]
        controls = [ (c, 1, wx.EXPAND) for c in controls ]

        #interleve and flatten ( for object_ in tuple_ ) list
        object_list = [ object_ for tuple_ in zip(labels, controls) for object_ in tuple_]
        self.fgs.AddMany(object_list)

        #Expand the TextCtrl boxes to fill panel
        self.fgs.AddGrowableCol(1, 1)

        #Add the FlexGridSizer to the StaticBoxSizer
        self.sizer.Add(self.fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=15)

        #FitTheSizer
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)