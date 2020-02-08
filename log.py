#!/usr/bin/env python3

class Logger:

    def __init__(self, verbosity):
        self._verbosity = verbosity
        self._indentation = 0

    def __call__(self, verbosity, *args):
        if self._verbosity >= verbosity:
            print('[{}]'.format(verbosity), self._indentation*'.', end='')
            print(*args)

    @property
    def verbosity(self):
        return self._verbosity

    indent = lambda self: self._indent(1)
    unindent = lambda self: self._indent(-1)

    def _indent(self, by):
        self._indentation += by


if __name__ == '__main__':
    test = lambda logger, verbosity: ' ' if logger.verbosity >= verbosity else ' NOT '
    for logger_verbosity in range(1, 4):
        logger = Logger(logger_verbosity)
        for verbosity in range(1, 4):
            logger(verbosity, 'You should{}see this (logger.verbosity={}, verbosity={}).'.format(test(logger, verbosity), logger.verbosity, verbosity))

    logger = Logger(1)
    logger(1, 'No identation')
    logger.indent()
    logger(1, 'One level')
    logger.indent()
    logger(1, 'Two levels')
    logger.indent()
    logger(1, 'Three levels')
    logger.unindent()
    logger(1, 'Two levels')
    logger.unindent()
    logger(1, 'One level')
    logger.unindent()
    logger(1, 'No indentation')
