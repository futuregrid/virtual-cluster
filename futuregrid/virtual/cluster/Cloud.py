#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import re
import ConfigParser

from ConfigParser import NoOptionError
from ConfigParser import NoSectionError

def msg(message):
    print message


def parse_conf(self,
               cloud_args,
               if_create_key,
               file_name='unspecified',
               cloud_instances,
               if_keypair_exits,
               add_keypair):
        """
        Parse configuration file

        Parameters:
            file_name -- configuration file name
            default: unspecified

        Logic:
            Parse configuration file if given, default location
            '~/.futuregrid/futuregrid.cfg'. If no file is given,
            finds configuration file by following order:
                1) finds current directory 'futuregrid.cfg'
                2) finds in default location

            configuration file format:
            [virtual-cluster]
            # Backup file for saving and loading virtual cluster(s)
            backup = ~/.futuregrid/virtual-cluster
            # Slurm configuration input file
            slurm = ~/.futuregrid/slurm.conf.in
            # userkey pem file
            userkey = ~/PUT-YOUR-USER-NAME.pem
            # environment file
            enrc = ~/novarc

            Checks if all files specified in configuration
            file are present.If create-key is set to true,
            first check if key exists, if key does not exist,
            then creates key under the location where is specified
            by userkey in the configuration file

            Due to different version of this tool, back-end
            structure of backup file may change, so checks
            if backup file has the correct format before the start

            Checks all possible errors about configuration file

        No returns
        """

        config = ConfigParser.ConfigParser()
        try:
            # default location ~/.futuregrid/futuregrid.cfg
            # read[], reads begin from last to first
            # so, first reads file_name, then current directory, then default
            config.read([os.path.expanduser('~/.futuregrid/futuregrid.cfg'),
                         'futuregrid.cfg',
                         os.path.expanduser(file_name)])

            cloud_args['backup'] = config.get('virtual-cluster', 'backup')
            cloud_args['userkey'] = config.get('virtual-cluster', 'userkey')
            cloud_args['user'] = os.path.splitext(self.userkey.split('/')[-1])[0]
            cloud_args['enrc'] = config.get('virtual-cluster', 'enrc')
            cloud_args['slurm'] = config.get('virtual-cluster', 'slurm')

            # checking if all file are present
            if not os.path.exists(os.path.expanduser(cloud_args['userkey'])):
                if if_create_key:
                    # create key for user
#                    self.add_keypair(self.user)
                    if if_keypair_exits(cloud_args['user']):
                        msg('\nYou have userkey %s.pem, please correct'
                                 ' its location in configuration file'
                                 % cloud_args['user'])
                        sys.exit()
                    else:
                        add_keypair(cloud_args['user'], cloud_args['userkey'])
                else:
                    msg('ERROR: You must have userkey file')
                    sys.exit(1)
            if not os.path.exists(os.path.expanduser(cloud_args['enrc'])):
                msg('ERROR: You must have novarc file')
                sys.exit(1)
            else:
                nova_key_dir = os.path.dirname(cloud_args['enrc'])
                if nova_key_dir.strip() == "":
                    nova_key_dir = "."
                os.environ["NOVA_KEY_DIR"] = nova_key_dir

                with open(os.path.expanduser(cloud_args['enrc'])) as enrc_content:
                    for line in enrc_content:
                        if re.search("^export ", line):
                            line = line.split()[1]
                            parts = line.split("=")
                            value = ""
                            for i in range(1, len(parts)):
                                parts[i] = parts[i].strip()
                                tempvalue = os.path.expandvars(parts[i])
                                parts[i] = os.path.expanduser(tempvalue)
                                value += parts[i] + "="
                                value = value.rstrip("=")
                                value = value.strip('"')
                                value = value.strip("'")
                                if parts[0] == 'EC2_CERT' or \
                                    parts[0] == 'EC2_PRIVATE_KEY' or \
                                    parts[0] == 'EUCALYPTUS_CERT':
                                    if not os.path.exists(value):
                                        msg('%s does not exist' % value)
                                        sys.exit()
                                os.environ[parts[0]] = value

            if not os.path.exists(os.path.expanduser(cloud_args['slurm'])):
                msg('ERROR: You must have slurm.conf.in file')
                sys.exit(1)

            if not cloud_instances.set_backup_file(cloud_args['backup']):
                msg('\nBackup file is corrupted, or you are using an old'
                        ' version of this tool. Please delete this backup file'
                        ' and try again.')
                sys.exit(1)

        except IOError:
            msg('\nError in reading configuration file!'
                     ' configuration file not created?')
            sys.exit()
        except NoSectionError:
            msg('\nError in reading configuratin file!'
                     ' No section header?')
            sys.exit()
        except NoOptionError:
            msg('\nError in reading configuration file!'
                     ' Correct configuration format?')
            sys.exit()
        except ValueError:
            msg('\nError in reading configuration file!'
                     ' Correct python version?')
            sys.exit()