"""

    KeepNote
    Preference data structure

"""

#
#  KeepNote
#  Copyright (c) 2008-2009 Matt Rasmussen
#  Author: Matt Rasmussen <rasmus@alum.mit.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.
#

from keepnote import orderdict
from keepnote.listening import Listeners


class Pref(object):
    """A general preference object"""

    def __init__(self, data=None):
        if data is None:
            self._data = orderdict.OrderDict()
        else:
            self._data = data
        self._is_dirty = False
        self.change_listeners = Listeners()

    def get(self, *args, **kargs):
        """
        Get config value from preferences

        default -- set a default value if it does not exist
        define  -- create a new dict if the key does not exist
        type    -- ensure return value has this type, otherwise return/set default
        """
        if len(args) == 0:
            return self._data
    
        try:
            changed = False
            d = self._data
            if "default" in kargs or "define" in kargs:
                # set default values when needed
                # define keyword causes default value to be a OrderDict()
                # all keys are expected to be present
    
                for arg in args[:-1]:
                    if arg not in d:
                        d[arg] = orderdict.OrderDict()
                        d = d[arg]
                        changed = True
                    else:
                        c = d[arg]
                        # ensure child value c is a dict
                        if not isinstance(c, dict):
                            c = d[arg] = orderdict.OrderDict()
                            changed = True
                        d = c
                if kargs.get("define", False):
                    if args[-1] not in d:
                        d[args[-1]] = orderdict.OrderDict()
                        changed = True
                    d = d[args[-1]]
                else:
                    d = d.setdefault(args[-1], kargs["default"])
            else:
                # no default or define specified
                # all keys are expected to be present
                for arg in args:
                    d = d[arg]
    
            # check type
            if "type" in kargs and "default" in kargs:
                if not isinstance(d, kargs["type"]):
                    args2 = args + (kargs["default"],)
                    return self.set(*args2)
            if changed:
                self.change_listeners.notify()
            return d
    
        except KeyError:
            raise Exception("unknown config value '%s'" % ".".join(args))
    
    def set(self, *args):
        """Set config value in preferences"""
        pref = self._data

        self._is_dirty = True
        
        if len(args) == 0:
            return
        elif len(args) == 1:
            pref.clear()
            pref.update(args[0])
            self.change_listeners.notify()
            return args[0]
        else:
            keys = args[:-1]
            val = args[-1]
            self.get(*keys[:-1])[keys[-1]] = val
            self.change_listeners.notify()
            return val
    
    def clear(self, *args):
        """Clear the config value"""
        kargs = {"define": True}
        self.get(*args, **kargs).clear()
    
    def is_dirty(self):
        """Returns whether a value has been set since the object was created or reset_dirty() was called (whichever is later)."""
        return self._is_dirty
    
    def reset_dirty(self):
        """Clears the dirty state. Afterwards, is_dirty() will return False."""
        self._is_dirty = False

    def __eq__(self, other):
        return \
            isinstance(other, Pref) and \
            self._data == other._data

    def __ne__(self, other):
        return not self.__eq__(other);

    def __repr__(self):
        return '{cls}[{_data}]'.format(cls=self.__class__.__name__, **self.__dict__)
