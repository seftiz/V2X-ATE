import os, sys
import shutil
import argparse
import subprocess
# from subprocess import call

ate_public = "/docs/ATE/"
fw_release_extract_dir = ate_public + 'fw_releases/'
qa_fw_lib = ate_public + 'qa/'
fw_release_dir = "/docs/SW/Release/craton-sdk/"


# NOTE : This file shuld run only on UB01

def compile_ate_cli( args ):

    qa_cli_sc = args.host_source_code # 'embedded/sdk/sdk-4.x/'

    board_type = args.board
    workspace = os.getcwd()
    
    if not os.path.isdir( qa_fw_lib ):
        os.chdir( ate_public )
        #os.system('hg clone http://hg/hg/r/qa/ qa')
        try:
            rc = subprocess.check_call(['hg', 'clone', 'http://hg/hg/r/qa/', 'qa'])
        except OSError:
            pass
    os.chdir( qa_fw_lib )
    os.system('hg pull && hg update %s --clean' % args.branch)
    
    os.chdir(workspace)
    
    print "\n\n\n\n\n\n"
    stream = os.popen("find . -name '*.tar.*'" )
    fw_tar_full_path_list = stream.readlines()
    path, fw_tar_file = os.path.split(fw_tar_full_path_list[0].rstrip('\n'))
    fw_tar_full_path = workspace + '/' + fw_tar_file
    print fw_tar_full_path
    os.chdir(fw_release_extract_dir)
    try:
      shutil.copy2(fw_tar_full_path, '.')
    except IOError, e:
      print "Unable to copy file. %s" % e
    # move to ate fw releases
    os.chdir(fw_release_extract_dir)
    os.system('tar -xvf %s' % fw_tar_file )
    # Delete the file
    os.remove(fw_tar_file)
    
    fw_local_dir = fw_tar_file.rsplit('.',2)[0]
    # Copy ATE files to libreary for compilation
    shutil.copy2( "/docs/ATE/fw_releases/nxd_bsd.h", fw_release_extract_dir + fw_local_dir + "/include/." )
    os.chdir( fw_release_extract_dir + fw_local_dir)
    try:
      rc = subprocess.check_call(['make', 'clean'])
      rc = subprocess.check_call(['make'])
    except OSError:
      pass
    
    stream = os.popen("find . -name 'ref.img'" )
    ref_img_path = stream.readlines()
    ref_img_path = [ref_img.rstrip('\n') for ref_img in ref_img_path]# for sdk_file in fw_path:
    ref_img_path = [ref_img for ref_img in ref_img_path if ( ('%s' % board_type) in ref_img) ]    # fw_tar_file = fw_release_extract_dir + sdk_file.rsplit('/')[-1]
    print ref_img_path[0]
    shutil.copy2(ref_img_path[0], '%sftp/sectonm_automation_ref.img' % (ate_public) )    # print "Starting copying file %s" % fw_tar_file
    # Goto to embeeded file
    os.chdir( qa_fw_lib + qa_cli_sc )
    # Modify makefile
    make_file_name = "Makefile"
    with open(make_file_name, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'export SDK_DIR :=' in line:
                lines[i] = 'export SDK_DIR := %s\n' % ( fw_release_extract_dir + fw_local_dir)

            if 'export BOARD := ' in line:
                lines[i] = 'export BOARD := %s\n' % ( board_type )

        f.close()

    with open(make_file_name, "w") as f:
        f.write( ''.join(lines) )
        f.close()

    # os.system( 'cat ./Makefile' )


    #os.system( 'make clean' )
    try:
        rc = subprocess.check_call(['make', 'clean'])
    except OSError:
        pass
    # os.system( 'make')
    stream = os.popen('cd %s && make' % (qa_fw_lib + qa_cli_sc) )
    make_results = stream.readlines()

    print ''.join( make_results )
    # Search sub make files 
    c = [a.rstrip('\n') for a in make_results if 'bin/v2x-cli' in a]
    print c[0][ (c[0].find('=> ')+3):]

    if os.path.exists( c[0][ (c[0].find('=> ')+3):]):
      print "\n\n Host v2x-cli created"
      shutil.copy2(c[0][( c[0].find('=> ')+3) : ], '%sftp/sectonm-automation-host-cli' % (ate_public) )
    else:
      print "\n\n Host SECTON not created !!!!!!!\n"

def main():

    parser = argparse.ArgumentParser( description='Automatic QA CLI build process script' )
    parser.add_argument( '-b', '--board', type=str, required=False, default='atk22017c', help='Board Type to compile with')
    parser.add_argument( '-br', '--branch', type=str, default='default', help='Mercurial branch to compile with (e.g. default )')
    parser.add_argument( '--host_source_code', type=str, default='embedded/sdk/sdk-4.x/linux', help='QA CLI source code library')


    args = parser.parse_args()
    
    # sdk-4.3.1-rel
    # args = parser.parse_args( ['-v', 'sdk-4.3.1-rel', '-t', 'sc'] )

    if 'linux' in sys.platform:
        print "starting building on linux"
        compile_ate_cli ( args )


    else:
        raise OSError("Unsupported OS")

    # print args.file, args.source_code


if __name__ == "__main__":
    main()

