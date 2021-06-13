import re
import time
import logging, sys

from .host_commander import HostCommander


class NodeManager ():
  def __init__(self, cluster_config_path, node):
    self.cluster_config_path = cluster_config_path
    self.node = node
    self.host_commander = HostCommander('cliff', '/home/cliff/.ssh/id_rsa', self.node['ip'])
    self.host_commander.reset_fingerprint()

  def puppet_update(self):
    puppet_result = self.host_commander.run("cat ~/.password | sudo -S ls > /dev/null; sudo /opt/puppetlabs/bin/puppet agent --test")
    print(puppet_result[1])
    if puppet_result[2]: print("STDERR OUTPUT:\n{0}".format(puppet_result[2]))
    print("Puppet Agent returned code: {0}".format(puppet_result[0]))
    if puppet_result[0] == 1:
      raise Exception("puppet agent failed!")

  def get_puppet_state(self):
    logging.info("\nGetting puppet state on node {0}.".format(self.node['name']))
    state_result = self.host_commander.run("ls /etc/puppetlabs/fc_puppet_state/")
    if state_result[0] == 2 and 'No such file or directory' in state_result[2]:
      state_result = [ 0, '_' ]
    logging.info(repr(state_result))
    if state_result[0]: raise Exception("Why error result?")
    state_segments = state_result[1].rstrip().split('_')
    return({ 'state':'_'.join(state_segments[:-1]), 'transition':state_segments[-1] })
