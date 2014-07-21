logrotate-ng
============

Python script which parses /etc/logrotate.d/* and /etc/logrotate.conf and logrotates files into an archive/YEAR/MONTH/DATE folder structure

It will run the postscript/endscript defined in the logrotate file.
It will also take use of the "create" directive in the configuration files, and create new files if this directive is defined. Currently it does not use the directives in logrotate.conf as global directives.
