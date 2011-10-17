# This file is part of the shareterm project
# Copyright (C) 2011 Adrien LELONG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

SSH=/usr/bin/ssh
CAT=/bin/cat
MKDIR=/bin/mkdir
ECHO=/bin/echo
CHMOD=/bin/chmod

SHARETERMDIR=/var/run/shareterm
#SHARETERMDIR=/home/ad/shareterm
KEYDIR=$SHARETERMDIR/$TARGET_USER
KEYFILE=$KEYDIR/k
PORTFILE=$KEYDIR/port

GUESTUSERNAME=guest

