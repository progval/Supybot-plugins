# Author: Valentin Lorentz
# CC-0 license.
#
# Note that you have to follow OEIS' license.

import re
import sys
import logging

class InvalidEntry(Exception):
    pass

class ParseError(Exception):
    pass

class OEISEntry(dict):
    _assignments = {
            'A': 'author',
            'E': 'references',
            'O': 'offset',
            }
    _appendings = {
            'C': 'comments',
            'D': 'detreferences',
            'F': 'formula',
            'H': 'references',
            'e': 'examples',
            }
    _concatenations = {
            'p': 'maple',
            't': 'mathematica',
            'o': 'programming',
            }
    def __init__(self, fd, logger=None):
        self._logger = logger
        for key in ('sequence', 'signed'):
            self[key] = []
        for key in self._appendings.values():
            self[key] = []
        for key in self._concatenations.values():
            self[key] = ''
        for line in fd:
            line = line[0:-1]
            if not line:
                break
            if sys.version_info[0] >= 3 and isinstance(line, bytes):
                line = line.decode()
            if line.startswith('#'):
                continue
            try:
                (mode, id_, data) = line.split(' ', 2)
            except ValueError:
                (mode, id_) = line.split(' ', 1)
                data = None
            self['id'] = id_
            self._add(mode[1:], data)
        if not self['sequence']:
            raise InvalidEntry()
        for key in self._appendings.values():
            if not self[key]:
                del self[key]
        for key in self._concatenations.values():
            if not self[key]:
                del self[key]

    def _add(self, mode, data):
        if mode in self._assignments:
            self[self._assignments[mode]] = data
        elif mode in self._appendings:
            self[self._appendings[mode]].append(data)
        elif mode in self._concatenations:
            self[self._concatenations[mode]] += data
        elif mode == 'I':
            self['ids'] = data.split(' ') if data else None
        elif mode == 'K':
            self['keywords'] = data.split(',')
        elif mode == 'N':
            assert 'name' not in self
            self['name'] = data
        elif mode in 'STU':
            self['sequence'].extend([int(x) for x in data.split(',') if x])
        elif mode in 'VWX':
            self['signed'].extend([int(x) for x in data.split(',') if x])
        elif mode == 'Y':
            self['seealso'] = (data[len('Cf. '):-1]).split(', ')
        elif self._logger:
            self._logger.info('Unknown OEIS data mode: %s: %s' % (mode, data))



    _paging_regexp = re.compile('Showing ([0-9]+)-([0-9]+) of ([0-9]+)')

    @classmethod
    def query(cls, fd, logger=None):
        """Fetches a page from the OEIS.

        Return format: ((from, to, total), [results])"""
        paging = None
        for line in fd:
            line = line[0:-1]
            if sys.version_info[0] >= 3 and isinstance(line, bytes):
                line = line.decode()
            if line.startswith('No results.'):
                return ((0, 0, 0), [])
            if line.startswith('Showing '):
                match = cls._paging_regexp.match(line)
                paging = match.groups()
                break
        if not paging:
            raise ParseError
        fd.readline()
        results = []
        try:
            while True:
                results.append(cls(fd, logger))
        except InvalidEntry:
            pass
        return (paging, results)
