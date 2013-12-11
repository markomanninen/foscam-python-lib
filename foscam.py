"""
A module to exploit Foscam Foscam HD816W camera.
"""

import urllib
import xml.etree.ElementTree as ET
from threading import Thread

from os import path
#CUR_PATH = path.dirname(path.dirname(path.realpath(__file__)))
#import sys
#sys.path.append(CUR_PATH)

ERROR_FOSCAM_UNKNOWN = 0
ERROR_FOSCAM_UNAVAILABLE = 1

VERBOSE = True

# Foscam error code.
FOSCAM_SUCCESS           = 0
ERROR_FOSCAM_FORMAT      = -1
ERROR_FOSCAM_AUTH        = -2
ERROR_FOSCAM_CMD         = -3  # Access deny. May the cmd is not supported.
ERROR_FOSCAM_EXE         = -4  # CGI execute fail.
ERROR_FOSCAM_TIMEOUT     = -5
ERROR_FOSCAM_UNKNOWN     = -7  # -6 and -8 are reserved.
ERROR_FOSCAM_UNAVAILABLE = -8  # Disconnected or not a cam.

class FoscamError(Exception):
    def __init__(self, code ):
        super(FoscamError, self).__init__()
        self.code = int(code)

    def __str__(self):
        return  'ErrorCode: %s' % self.code

class FoscamCamera(object):
    '''A python implementation of the foscam HD816W'''

    def __init__(self, host, port, usr, pwd, daemon=False, verbose=VERBOSE):
        '''
        If ``daemon`` is True, the command will be sent unblockedly.
        '''
        self.host = host
        self.port = port
        self.usr = usr
        self.pwd = pwd
        self.daemon = daemon
        self.verbose = verbose

    @property
    def url(self):
        _url = '%s:%s' % (self.host, self.port)
        return _url

    def send_command(self, cmd, params=None):
        '''
        Send command to foscam.
        '''
        paramstr = ''
        if params:
            paramstr = urllib.urlencode(params)
            paramstr = '&' + paramstr if paramstr else ''
        cmdurl = 'http://%s/cgi-bin/CGIProxy.fcgi?usr=%s&pwd=%s&cmd=%s%s' % (
                                                                  self.url,
                                                                  self.usr,
                                                                  self.pwd,
                                                                  cmd,
                                                                  paramstr,
                                                                  )

        # Parase parameters from response string.
        if self.verbose:
            print 'Send Foscam command: %s' % cmdurl
        try:
            root = ET.fromstring(urllib.urlopen(cmdurl).read())
        except Exception:
            return ERROR_FOSCAM_UNAVAILABLE, None
        code = ERROR_FOSCAM_UNKNOWN
        params = dict()
        for child in root.iter():
            if child.tag == 'result':
                code = int(child.text)

            elif child.tag != 'CGI_Result':
                params[child.tag] = child.text

        if self.verbose:
            print 'Received Foscam response: %s, %s' % (code, params)
        return code, params

    def execute_command(self, cmd, params=None, callback=None):
        '''
        Execute a command and return a parsed response.
        '''
        def execute_with_callbacks(cmd, params=None, callback=None):
            code, params = self.send_command(cmd, params)
            if callback:
                callback(code, params)
            return code, params

        if self.daemon:
            t = Thread(target=execute_with_callbacks,
                    args=(cmd, ), kwargs={'params':params, 'callback':callback})
            t.start()
        else:
            return execute_with_callbacks(cmd, params, callback)

    # *************** Network ******************

    def get_ip_info(self, callback=None):
        '''
        Get ip infomation
        '''
        return self.execute_command('getIPInfo', callback=callback)

    def set_ip_info(self, is_dhcp, ip='', gate='', mask='',
                                dns1='', dns2='', callback=None):
        '''
        isDHCP: 0(False), 1(True)
        System will reboot automatically to take effect after call this CGI command.
        '''
        params = {'isDHCP': is_dhcp,
                  'ip': ip,
                  'gate': gate,
                  'mask': mask,
                  'dns1': dns1,
                  'dns2': dns2,
                 }

        return self.execute_command('setIpInfo', params, callback=callback)

    def get_port_info(self, callback=None):
        '''
        Get http port and media port of camera.
        '''
        return self.execute_command('getPortInfo', callback=callback)

    def set_port_info(self, webport, mediaport, httpsport,
                                      onvifport, callback=None):
        '''
        Set http port and media port of camera.
        '''
        params = {'webPort'   : webport,
                  'mediaPort' : mediaport,
                  'httpsPort' : httpsport,
                  'onvifPort' : onvifport,
                 }
        return self.execute_command('setPortInfo', params, callback=callback)

    def refresh_wifi_list(self, callback=None):
        '''
        Start scan the aps around.
        This operation may takes a while, about 20s or above,
        the other operation on this device will be blocked during the period.
        '''
        return self.execute_command('refreshWifiList', callback=callback)

    def get_wifi_list(self, startno, callback=None):
        '''
        Get the aps around after refreshWifiList.
        Note: Only 10 aps will be returned one time.
        '''
        params = {'startNo': startno}
        return self.execute_command('getWifiList', params, callback=callback)

    def set_wifi_setting(self, ssid, psk, isenable, isusewifi, nettype,
                            encryptype, authmode, keyformat, defaultkey,
                            key1='', key2='', key3='', key4='',
                            key1len=64, key2len=64, key3len=64, key4len=64,
                            callback=None):
        '''
        Set wifi config.
        Camera will not connect to AP unless you enject your cable.
        '''
        params = {'isEnable'   : isenable,
                  'isUseWifi'  : isusewifi,
                  'ssid'       : ssid,
                  'netType'    : nettype,
                  'encryptType': encryptype,
                  'psk'        : psk,
                  'authMode'   : authmode,
                  'keyFormat'  : keyformat,
                  'defaultKey' : defaultkey,
                  'key1'       : key1,
                  'key2'       : key2,
                  'key3'       : key3,
                  'key4'       : key4,
                  'key1Len'    : key1len,
                  'key2Len'    : key2len,
                  'key3Len'    : key3len,
                  'key4Len'    : key4len,
                  }
        return self.execute_command('setWifiSetting', params, callback=callback)

    def get_wifi_config(self, callback=None):
        '''
        Get wifi config
        '''
        return self.execute_command('getWifiConfig', callback=callback)

    def get_upnp_config(self, callback=None):
        '''
        Get UpnP config.
        '''
        return self.execute_command('getUPnPConfig', callback=callback)

    def set_upnp_config(self, isenable, callback=None):
        '''
        Set UPnP config
        '''
        params = {'isEnable': isenable}
        return self.execute_command('setUPnPConfig', params, callback=callback)

    def get_ddns_config(self, callback=None):
        '''
        Get DDNS config.
        '''
        return self.execute_command('getDDNSConfig', callback=callback)

    def set_ddns_config(self, isenable, hostname, ddnsserver,
                                        user, password, callback=None):
        '''
        Set DDNS config.
        '''
        params = {'isEnable': isenable,
                  'hostName': hostname,
                  'ddnsServer': ddnsserver,
                  'user': user,
                  'password': password,
                 }
        return self.execute_command('setDDNSConfig', params, callback=callback)


    # *************** AV Settings  ******************

    def get_sub_video_stream_type(self, callback=None):
        '''
        Get the stream type of sub stream.
        '''
        return self.execute_command('getSubVideoStreamType', callback=callback)

    def set_sub_video_stream_type(self, format, callback=None):
        '''
        Set the stream fromat of sub stream.
        Supported format: (1) H264 : 0
                          (2) MotionJpeg 1
        '''
        params = {'format': format}
        return self.execute_command('setSubVideoStreamType',
                                        params, callback=callback)

    def set_sub_stream_format(self, format, callback=None):
        '''
        Set the stream fromat of sub stream????
        '''
        params = {'format': format}
        return self.execute_command('setSubStreamFormat',
                                        params, callback=callback)

    def get_main_video_stream_type(self, callback=None):
        '''
        Get the stream type of main stream
        '''
        return self.execute_command('getMainVideoStreamType', callback=callback)

    def set_main_video_stream_type(self, streamtype, callback=None):
        '''
        Set the stream type of main stream
        '''
        params = {'streamType': streamtype}
        return self.execute_command('setMainVideoStreamType',
                                        params, callback=callback)

    def get_video_stream_param(self, callback=None):
        '''
        Get video stream param
        '''
        return self.execute_command('getVideoStreamParam', callback=callback)

    def set_video_stream_param(self, streamtype, resolution, bitrate,
            framerate, gop, isvbr, callback=None):
        '''
        Set the video stream param of stream N
        resolution(0~4): 0 720P,
                         1 VGA(640*480),
                         2 VGA(640*360),
                         3 QVGA(320*240),
                         4 QVGA(320*180)
        bitrate: Bit rate of stream type N(20480~2097152)
        framerate: Frame rate of stream type N
        GOP: P frames between 1 frame of stream type N.
             The suggest value is: X * framerate.
        isvbr: 0(Not in use currently), 1(In use)
        '''
        params = {'streamType': streamtype,
                  'resolution': resolution,
                  'bitRate'   : bitrate,
                  'frameRate' : framerate,
                  'GOP'       : gop,
                  'isVBR'     : isvbr
                 }
        return self.execute_command('setVideoStreamParam',
                                         params, callback=callback)


    # *************** User account ******************

    def change_user_name(self, usrname, newusrname, callback=None):
        '''
        Change user name.
        '''
        params = {'usrName': usrname,
                  'newUsrName': newusrname,
                 }
        return self.execute_command('changeUserName', params, callback=callback)

    def change_password(self, usrname, oldpwd, newpwd, callback=None):
        '''
        Change password.
        '''
        params = {'usrName': usrname,
                  'oldPwd' : oldpwd,
                  'newPwd' : newpwd,
                 }
        return self.execute_command('changePassword', params, callback=callback)

    # *************** Device manage *******************

    def set_system_time(self, ntp_server, callback=None):
        '''
        Only support timeSource = 0(Get time from NTP server)
        '''
        if ntp_server not in ['time.nist.gov',
                              'time.kriss.re.kr',
                              'time.windows.com',
                              'time.nuri.net',
                              ]:
            raise ValueError('Unsupported ntpServer')

        params = {'timeSource': 0, 'ntpServer': ntp_server}
        return self.execute_command('setSystemTime', params, callback=callback)

    def get_system_time(self, callback=None):
        '''
        Get system time.
        '''
        return self.execute_command('getSystemTime', callback=callback)

    def get_dev_name(self, callback=None):
        '''
        Get camera name.
        '''
        return self.execute_command('getDevName', callback=callback)

    def set_dev_name(self, devname, callback=None):
        '''
        Set camera name
        '''
        params = {'devName': devname}
        return self.execute_command('setDevName', params, callback=callback)

    # *************** PTZ Control *******************

    def ptz_move_up(self, callback=None):
        '''
        Move up
        '''
        return self.execute_command('ptzMoveUp', callback=callback)

    def ptz_move_down(self, callback=None):
        '''
        Move down
        '''
        return self.execute_command('ptzMoveDown', callback=callback)

    def ptz_move_left(self, callback=None):
        '''
        Move left
        '''
        return self.execute_command('ptzMoveLeft', callback=callback)

    def ptz_move_right(self, callback=None):
        '''
        Move right.
        '''
        return self.execute_command('ptzMoveRight', callback=callback)

    def ptz_move_top_left(self, callback=None):
        '''
        Move to top left.
        '''
        return self.execute_command('ptzMoveTopLeft', callback=callback)

    def ptz_move_top_right(self, callback=None):
        '''
        Move to top right.
        '''
        return self.execute_command('ptzMoveTopRight', callback=callback)

    def ptz_move_bottom_left(self, callback=None):
        '''
        Move to bottom left.
        '''
        return self.execute_command('ptzMoveBottomLeft', callback=callback)

    def ptz_move_bottom_right(self, callback=None):
        '''
        Move to bottom right.
        '''
        return self.execute_command('ptzMoveBottomRight', callback=callback)

    def ptz_stop_run(self, callback=None):
        '''
        Stop run PT
        '''
        return self.execute_command('ptzStopRun', callback=callback)

    def ptz_reset(self, callback=None):
        '''
        Reset PT to default position.
        '''
        return self.execute_command('ptzReset', callback=callback)

    def get_ptz_speed(self, callback=None):
        '''
        Get the speed of PT
        '''
        return self.execute_command('getPTZSpeed', callback=callback)

    def set_ptz_speed(self, speed, callback=None):
        '''
        Set the speed of PT
        '''
        return self.execute_command('setPTZSpeed', {'speed':speed},
                                         callback=callback)