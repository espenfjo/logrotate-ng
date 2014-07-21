#!/usr/bin/python

# pylint: disable=C0103
import errno
import glob
import grp
import re
from shutil import move
import os
import pwd

from datetime import date, timedelta
from subprocess import call, CalledProcessError


def get_logfiles():
    logrotate_configs = ["/etc/logrotate.conf"]
    logrotate_configs.extend(glob.glob("/etc/logrotate.d/*"))
    actions = []

    for logrotate_config in logrotate_configs:
        log_files = []
        have_script = 0
        script = ""
        runonce = 0
        create = {}
        f = open(logrotate_config, 'r')
        for line in f:
            line = line.strip()
            if re.match('#', line):
                continue
            log_files.extend(parse_line(line))

            if re.search('postrotate', line):
                have_script = 1
                continue
            elif re.search('endscript', line):
                have_script = 0
                continue
            elif re.search('sharedscripts', line):
                runonce = 1
                continue
            elif re.search('create', line):
                create_parts = line.split(' ')
                create['create'] = 1
                if len(create_parts) > 1:
                    create["mode"] = create_parts[1]
                if len(create_parts) > 2:
                    create["user"] = create_parts[2]
                if len(create_parts) > 3:
                    create["group"] = create_parts[3]

                continue

            if have_script:
                script += line
        if not len(log_files) > 0:
            continue

        action = {
            "files": log_files,
            "action": script,
            "runonce": runonce,
            "create": create
        }
        actions.append(action)

    return actions


def parse_line(line):
    line = line.replace('{', '')
    line = line.strip()
    files = []
    if re.search(' ', line):
        for line_part in line.split(' '):
            files.extend(parse_line(line_part))
    elif re.search('\*', line):
        files.extend(glob.glob(line))
    elif os.path.isfile(line):
        files.append(line)

    return files


if __name__ == "__main__":
    actions = get_logfiles()
    for action in actions:
        for logfile in action['files']:
            if not os.path.isfile(logfile):
                continue

            log_dir = os.path.dirname(logfile)
            yesterday = date.today() - timedelta(1)
            date_string = yesterday.strftime('%Y/%m/%d')
            archive_path = "{0}/archive/{1}".format(log_dir, date_string)
            logname = os.path.basename(logfile)
            file_stat = None
            try:
                file_stat = os.stat(logfile)
            except OSError as e:
                print "Could not stat {0}: {1}".format(logfile, e)

            try:
                os.makedirs(archive_path)
            except OSError as err:
                if not err.errno == errno.EEXIST and not os.path.isdir(archive_path):
                    print "Could not create log archive dir: {0}".format(err)
                    continue
            try:
                move(logfile, "{0}/{1}".format(archive_path, logname))
            except OSError as err:
                print "Coult not move '{0}' to '{1}/{2}': {3}".format(logfile, archive_path, logname, err)
                continue

            try:
                call(["/usr/bin/gzip", "-f", "{0}/{1}".format(archive_path, logname)])
            except CalledProcessError as err:
                print "Error gzipping logfile {0}: {1}".format(logfile, err)
                continue

            if 'create' in action['create']:
                with open(logfile, 'a'):
                    os.utime(logfile, None)
                if 'user' in action['create']:
                    uid = pwd.getpwnam(action['create']['user']).pw_uid
                else:
                    uid = file_stat.st_uid
                if 'group' in action['create']:
                    gid = grp.getgrnam(action['create']['group']).gr_gid
                else:
                    gid = file_stat.st_gid

                os.chown(logfile, uid, gid)

                if 'mode' in action['create']:
                    os.chmod(logfile, int(action['create']['mode'], 8))
                else:
                    os.chmod(logfile, file_stat.st_mode & 777)

            if not action['runonce']:
                try:
                    call(["/bin/sh", "-c", "{0}".format(action['action'])])
                except CalledProcessError as err:
                    print "Error running postscript for {0}: {1}".format(logfile, err)
                    continue

        if action['runonce']:
            try:
                call(["/bin/sh", "-c", "{0}".format(action['action'])])
            except CalledProcessError as err:
                print "Error running postscript for {0}: {1}".format(logfile, err)
                continue
