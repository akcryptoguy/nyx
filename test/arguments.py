"""
Unit tests for nyx.arguments.
"""

import unittest

from nyx.arguments import DEFAULT_ARGS, parse


class TestArgumentParsing(unittest.TestCase):
  def test_that_we_get_default_values(self):
    args = parse([])

    for attr in DEFAULT_ARGS:
      self.assertEqual(DEFAULT_ARGS[attr], getattr(args, attr))

  def test_that_we_load_arguments(self):
    args = parse(['--interface', '10.0.0.25:80'])
    self.assertEqual('10.0.0.25', args.control_address)
    self.assertEqual(80, args.control_port)

    args = parse(['--interface', '80'])
    self.assertEqual(DEFAULT_ARGS['control_address'], args.control_address)
    self.assertEqual(80, args.control_port)

    args = parse(['--socket', '/tmp/my_socket', '--config', '/tmp/my_config'])
    self.assertEqual('/tmp/my_socket', args.control_socket)
    self.assertEqual('/tmp/my_config', args.config)

    args = parse(['--debug', '/tmp/dump'])
    self.assertEqual('/tmp/dump', args.debug_path)

    args = parse(['--log', 'DEBUG,NYX_DEBUG'])
    self.assertEqual('DEBUG,NYX_DEBUG', args.logged_events)

    args = parse(['--version'])
    self.assertEqual(True, args.print_version)

    args = parse(['--help'])
    self.assertEqual(True, args.print_help)

  def test_examples(self):
    args = parse(['-i', '1643'])
    self.assertEqual(1643, args.control_port)

    args = parse(['-l', 'WARN,ERR', '-c', '/tmp/cfg'])
    self.assertEqual('WARN,ERR', args.logged_events)
    self.assertEqual('/tmp/cfg', args.config)

  def test_that_we_reject_unrecognized_arguments(self):
    self.assertRaises(ValueError, parse, ['--blarg', 'stuff'])

  def test_that_we_reject_invalid_interfaces(self):
    invalid_inputs = (
      '',
      '    ',
      'blarg',
      '127.0.0.1',
      '127.0.0.1:',
      ':80',
      '400.0.0.1:80',
      '127.0.0.1:-5',
      '127.0.0.1:500000',
    )

    for invalid_input in invalid_inputs:
      self.assertRaises(ValueError, parse, ['--interface', invalid_input])
