logrotate-ng
============

This script is meant to be a fairly simple drop-in replacement of logrotate.
It parses /etc/logrotate.d/* and /etc/logrotate.conf and rotates files into an `archive/YEAR/MONTH/DATE` folder structure

* It will run the postscript/endscript defined in the logrotate file.
* It will also take use of the "create" directive in the configuration files, and create new files if this directive is defined.

Currently it does not use the directives in logrotate.conf as global directives.
