import sys
import tftpy
import logging
import multiprocessing

log = logging.getLogger(__name__)

class TftpSrv():
    """
    Implements a TFTP server.
    """

    def __init__(self, path_dir, listenport = 70, timeout = 5):
        self.path_dir = path_dir
        self.listenport = listenport
        self.timeout = timeout
        self.service = None

    def __del__(self):
        self.stop()

    def set(self, path_dir, listenport = 70, timeout = 5):
        self.stop()
        self.path_dir = path_dir
        self.listenport = listenport
        self.timeout = timeout
        self.start()

    def run(self):
        self.server = tftpy.TftpServer(self.path_dir)
        self.server.listen('0.0.0.0', self.listenport, self.timeout)

    def start(self):
        tftpy.TftpShared.setLogLevel(logging.ERROR)
        self.service = multiprocessing.Process(name="ate_tftp_server", target = self.run)
        self.service.start()
        log.info('Start TFTP server.')
 
    def stop(self):
        if not self.service is None:
            self.service.terminate()
            self.service = None
            log.info('Stop TFTP server')


if __name__ == "__main__":
    #  Defaults
    listenport = 70
    timeout = 5

    if len(sys.argv) < 2:
        raise Exception("Error: tftp_server(path_dir, listenport, timeout) should receives at least 1 arguments.")

    path_dir = sys.argv[1]

    if len(sys.argv) > 2:
        listenport = int(sys.argv[2])
        if len(sys.argv) > 3:
            timeout = int(sys.argv[3])

    print 'Start TFTP server...\nRoot =  {}\nlistenport = {}\ntimeout = {}'.format(path_dir, listenport, timeout)
    tftp_srv = TftpSrv(path_dir, listenport, timeout)
    tftp_srv.run()
