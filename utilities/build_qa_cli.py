import os, sys
import shutil
import argparse



# from subprocess import call

ate_public = "/docs/ATE/"
fw_release_extract_dir = ate_public + 'fw_releases/'
qa_fw_lib = ate_public + 'qa/'
fw_release_dir = "/docs/SW/Release/craton-sdk/"

def get_sdk_version( ver ):
    """ Get file version """
    return ver.split('-')[ ver.split('-').index('sdk') + 1 ].split('.')


# NOTE : This file shuld run only on UB01

def compile_ate_cli( args ):

    fw_tar_file = args.ver  # "sdk-4.2.2-beta1"

    fw_version = args.ver  # "sdk-4.2.2-beta1"
    fw_type = args.type

    qa_cli_sc = args.source_code # 'embedded/sdk/sdk-4.x/'

    board_type = args.board

		# Remove the direcory
		# shutil.rmtree( qa_fw_lib )

    # create qa or update if exists
		
    if not os.path.isdir( qa_fw_lib ):
        os.chdir( ate_public )
        os.system('hg clone http://hg/hg/r/qa/ qa')

    os.chdir( qa_fw_lib )
    os.system('hg pull && hg update %s --clean' % args.branch)

    fw_dir = fw_version.rsplit('.',1)[0] # ['sdk-4.3', '0-beta1']
    fw_sub_dir = fw_version.rsplit('.',1)[1].split('-',1)[0] # ['0', 'beta1']

    # Fw_version is 
    fw_dir = fw_release_dir + '/'.join( [fw_version.rsplit('.',1)[0], fw_version.rsplit('.',1)[1].split('-',1)[0], fw_version.rsplit('.',1)[1].split('-',1)[1] ]) + '/'
    fw_dir = fw_dir + fw_type + '/'

    stream = os.popen("find %s -name '*tar*'" % ( fw_dir ) )
    fw_path = stream.readlines()

    fw_path = [fw.rstrip('\n') for fw in fw_path if ( ('tar.xz' or 'tar.bz') in fw) ]

    # Currently only SC supported
    fw_path = [fw for fw in fw_path if ( ('-%s-' % fw_type) in fw) ]

    # move to ate fw releases
    os.chdir( fw_release_extract_dir )
    for sdk_file in fw_path:
        fw_tar_file = fw_release_extract_dir + sdk_file.rsplit('/')[-1]
        print "Starting coping file %s" % fw_tar_file
        shutil.copy2( sdk_file, '.')
        os.system('tar -xvf %s' % fw_tar_file )
        # Delete the file
        os.remove(fw_tar_file)

        fw_local_dir = fw_tar_file.rsplit('.',2)[0]
        # Copy ATE files to libreary for compilation
        shutil.copy2( "/docs/ATE/fw_releases/nxd_bsd.h", fw_local_dir + "/include/." )

        # run src build in src directory
				#if not os.path.isdir( fw_local_dir + '/host/' ):
				#	shutil.rmtree( fw_local_dir + '/host/' )
					
        os.chdir( fw_local_dir )
        os.system( 'cd src && make clean && make all install')
		
        # Goto to embeeded file
        os.chdir( qa_fw_lib + qa_cli_sc )

        # Modify makefile
        make_file_name = "Makefile"
        with open(make_file_name, "r") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'export SDK_DIR :=' in line:
                    lines[i] = 'export SDK_DIR := %s\n' % ( fw_local_dir )

                if 'export BOARD := ' in line:
                    lines[i] = 'export BOARD := %s\n' % ( board_type )

            f.close()

        with open(make_file_name, "w") as f:
            f.write( ''.join(lines) )
            f.close()

        # os.system( 'cat ./Makefile' )


        os.system( 'make clean' )
        # os.system( 'make')
        stream = os.popen('cd %s && make' % (qa_fw_lib + qa_cli_sc) )
        make_results = stream.readlines()

        print ''.join( make_results )
        # Search sub make files 
        c = [a.rstrip('\n') for a in make_results if 'make[1]: Entering directory' in a]

        # Copy the img file to public ftp
        # print "Copy img to public ftp at docs/ATE/ftp/"
        img_name = 'qa-%s-%s-%s.img' % ( args.ver , board_type, fw_type) # '.'.join(get_sdk_version( args.ver )) )
        
        print "Copy img to public ftp at docs/ATE/ftp/{}".format ( img_name )


        shutil.copy2( c[0][ c[0].find('/'):-1 ] + '/arm/img/qa-%s.img' % (fw_type) , '%sftp/%s' % (ate_public, img_name) )


        if os.path.exists( c[1][ c[1].find('/'):-1 ] + '/host/bin/v2x-cli'):
          print "\n\n Host v2x-cli created Copy to ftp"
          # Linux copy
          host_file = "host-{}-{}".format( fw_version, fw_type)
          shutil.copy2( c[1][ c[1].find('/'):-1 ] + '/host/bin/v2x-cli' , '%sftp/%s' % (ate_public, host_file) )

        else:
          print "\n\n ERROR : Host SECTON not created !!!!!!!\n"

    print "\n\n\n ATE CLI build is completed\n\n\n"


def main():

    parser = argparse.ArgumentParser( description='Automatic QA CLI build process script' )
    parser.add_argument( '-v', '--ver', type=str, required=True, help='Firmware tar file (e.g. sdk-4.3.0-beta1 or sdk-4.2.2-pangaea4-i686-linux-gnu)')
    parser.add_argument( '-t', '--type', type=str, required=True, help='Firmware type, either SC or MC')
    parser.add_argument( '-b', '--board', type=str, required=False, default='atk22016', help='Board Type to compile with')
    parser.add_argument( '-br', '--branch', type=str, default='default', help='Mercurial branch to compile with (e.g. default )')
    parser.add_argument( '--source_code', type=str, default='embedded/sdk/sdk-4.x/', help='QA CLI source code library')

	
    args = parser.parse_args()
    
    # sdk-4.3.1-rel
    # args = parser.parse_args( ['-v', 'sdk-4.3.1-rel', '-t', 'sc'] )

    if 'linux' in sys.platform:
        print "starting building on linux"
        compile_ate_cli ( args )

    elif 'win' in sys.platform:
        # run same command but from ssh transport

        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.30.61',  'shochats', 'Ahjaryk5%')
        stream = client.exec_command( 'python ' + qa_fw_lib + '/utilities/build_qa_cli.py' + ' ' .join(args) )
        if stream[0].channel.exit_status != 0:
            raise Exception(" Command falied" )
        # TBD

    else:
        raise OSError("Unsupported OS")

    # print args.file, args.source_code


if __name__ == "__main__":
    main()

