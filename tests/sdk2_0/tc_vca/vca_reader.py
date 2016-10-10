import os

def multi_file_reader(flist):
    for i in xrange(len(flist)):
        f = open(flist[i][1], "r")
        yield f
        f.close()

class VcaReader(object):
    HEADER_MAX_SIZE = 32
    def __init__(self, vca_log_dir_path=None, vca_log_single_file_path=None):
        if os.name == 'posix':
            self.path_delim = "/"
        else:
            self.path_delim = "\\"

        files_list = []

        if vca_log_dir_path is not None:
            for dpath, _, flist in os.walk(vca_log_dir_path):
                files_list += [(to_slot(dpath[1+len(vca_log_dir_path):], 
                                        self.path_delim),
                                dpath + self.path_delim + fname) for fname in flist]
                files_list.sort()
        elif vca_log_single_file_path is not None:
            files_list.append((0, vca_log_single_file_path))
        else:
            raise ValueError("VcaReader: missing VCA log directory or VCA log file")

        self.__files = multi_file_reader(files_list)
            

    def read_header(self, logfile):
        s = logfile.read(1)
        if len(s) == 0:
            return -1, 0
  
        if s != "%":
            return 0, 0
        i = 0
        header = ""
        while s != "\n" and len(header) < self.HEADER_MAX_SIZE:
            s = logfile.read(1)
            if len(s) == 0:
                return -1, 0
            header += s;
        
        if i == self.HEADER_MAX_SIZE:
            return 0, 0

        words = header.split(",")
       
        msg_len = int(words[0].strip("\r\n"));

        if len(words) < 2:
            req_id = -1
        else:
            req_id = int(words[1].strip("\r\n"))
        return msg_len, req_id


    def get_frames(self):
        import json
        from StringIO import StringIO
        
        for logfile in self.__files: 
            while True:
                flen, req_id = self.read_header(logfile)
                if flen == -1:
                    break
                if flen == 0:
                    continue
                
                jmsg = logfile.read(flen)
                if len(jmsg) < flen:
                    print "incomplete JSON mseeage in log, ignoring:"
                    print jmsg
                    continue
                msg_cut = jmsg.find("%")
                if msg_cut >= 0:
                    print "Unexpected '%', Discarding message"
                    print jmsg
                    logfile.seek(len(jmsg) - msg_cut, 1)
                    continue
                try:
                    jobj = json.load(StringIO(jmsg))
                except:
                    print jmsg
                    raise
                yield jobj

def to_slot(dpath, path_delim):
    import time
    print dpath
    yy, mm, dd, hh, slot = dpath.split(path_delim)
    return time.mktime([int(yy) + 1, int(mm), int(dd), int(hh), int(slot), 0, 0, 0, 0])
    

"""def main():
    import sys
    import os
    if len(sys.argv) < 2:
        print "Usage: %s <log dir>" % (sys.argv[0])
        exit(-1)

    reader = VcaReader(sys.argv[1])

    prev_seq = 0
    for j in reader.get_frames():
        if j[0] == "RxPkt":
            seq = j[1]["seqNum"]
            #print "seq = %d" % (seq)
            if prev_seq + 1 != seq:
                print "warning: prev=%d cur=%d" % (prev_seq, seq)
            prev_seq = seq

if __name__ == '__main__':
    main()"""
