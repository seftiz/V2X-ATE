import pywinauto
import logging
import time, os


class SIRIT_DSRC_TOOL(object):

    def __init__( self ):
        self.pwa_app = pywinauto.application.Application()
        self.tabs_names = {'STATUS':0, 'PIPES':1, 'CFG_PIPES':2, 'GPS':3}

    def get_app_handle(self):
        try:
            w_handle = pywinauto.findwindows.find_windows(title_re=u'3M DSRC Sniffer Configuration Tool*', class_name='WindowsForms10.Window.8.app.0.2bf8098')[0]
            self.window = self.pwa_app.window_(handle=w_handle)
        except Exception as e:
            raise Exception("Application not found")

    def start_sirit ( self, sirit_app = 'C:\\Program Files\\3M\\3M DSRC Sniffer Configuration Tool\\Sirit.IEEE80211.exe' ):
        os.startfile(sirit_app)
        time.sleep(8)
        while not self.is_sirit_active():
            time.sleep(1)

        time.sleep(2)
        self.get_app_handle()
        self.select_window()
        # Press Connect 
        ctrl = self.window['Button2']
        ctrl.Click()
        
        # Wait for connection
        time.sleep(1)

    def is_sirit_active(self):
        try:
            w_handle = pywinauto.findwindows.find_windows(title_re=u'3M DSRC Sniffer Configuration Tool*', class_name='WindowsForms10.Window.8.app.0.2bf8098')[0]
            return True
        except Exception as e:
            return False
            
    def change_channel_freq(self, interface, channel ):

        freq_list = self.window['ListBox']
        avaliable_freq = freq_list.Texts()
        if not (str(channel) in avaliable_freq):
            raise IndexError("Freq is not avaliable")

        try:
            index = avaliable_freq.index(str(channel))
            freq_list.Select(index-1)
        except Exception as e:
            raise e

        interface_list = self.window['ListView']
        interface_list.Click()

        if not('wlan%d' % interface in interface_list.Texts()):
            raise IndexError("Interface not found")
        
        interface_list.Select(interface)

        # Press change channel
        ctrl = self.window['Button']
        ctrl.Click()

        # Approve the msg box
        try:
            prompt_handle = pywinauto.findwindows.find_windows(title=u' ', class_name='#32770')[0]
            prompt_window = self.pwa_app.window_(handle=prompt_handle)
            ok_button = prompt_window['OK']
            ok_button.Click()
        except Exception:
            pass

    def select_window ( self ):
        self.window.Click()

    def select_tab( self, tab_name ):
        ctrl = self.window['TabControl']
        if not tab_name in self.tabs_names:
            raise Exception("Tab name is unknown, options {}".format( self.tabs_names ) )
        try:
            ctrl.Select(self.tabs_names[tab_name])
        except Exception as e:
            raise e

    def start_gps_track( self ):
        
        self.select_window()
        self.select_tab('GPS')
        try:
            ctrl = self.window['Start']
            ctrl.Click()   
        except Exception:
            ctrl = self.window['Stop']
            ctrl.Click()   
            time.sleep(0.5)
        try:
            ctrl = self.window['Start']
            ctrl.Click()   
        except Exception:
            pass

    def stop_gps_track():

        self.select_window()
        self.select_tab('GPS')
        try:
            ctrl = self.window['Stop']
            ctrl.Click()   
        except Exception:
            pass

    def change_gateway_time(self):
        self.select_window()
        self.select_tab('GPS')
 
        ctrl = self.window['Button2']
        ctrl.Click()
        time.sleep(0.5)
        w_handle = pywinauto.findwindows.find_windows(title=u'Change gateway datetime', class_name='#32770')[0]
        window = self.pwa_app.window_(handle=w_handle)
        window.SetFocus()
        ctrl = window['&Yes']
        ctrl.Click()
        time.sleep(1)
        w_handle = pywinauto.findwindows.find_windows(title=u'', class_name='#32770')[0]
        window = self.pwa_app.window_(handle=w_handle)
        window.SetFocus()
        ctrl = window['OK']
        ctrl.Click()
        # Try again JIC
        try:
            ctrl = window['OK']
            ctrl.Click()
        except Exception:
            pass

    def get_gps_state(self):
        self.select_window()
        self.select_tab('GPS')

        ctrl = self.window['Button']
        ctrl.SetFocus()
        gps_state = ctrl.Texts()

        if 'unlock' in gps_state:
            return [ False, [] ]
        else:
            ctrl = self.window['Edit']
            ctrl.Select()
            gps_data = ctrl.Texts()
            return [ True, gps_data ]

    def configure_tool_default( self, freq_list = [178,184,180] ):

        for idx,freq in enumerate( freq_list ):
            
            self.change_channel_freq( idx , freq )
            time.sleep(1)






if __name__ == "__main__":

    # Test 
    tool = SIRIT_DSRC_TOOL()

    if tool.is_sirit_active():
        tool.get_app_handle()
    else:
        tool.start_sirit()

    tool.select_window()
    tool.change_channel_freq( 0 , 178 )

    
    print " GPS is unlocked"
    gps_state = tool.get_gps_state()
    print gps_state

    tool.start_gps_track()
    tool.change_gateway_time()

    print "GPS shuold be locked"
    gps_state = tool.get_gps_state()
    print gps_state
