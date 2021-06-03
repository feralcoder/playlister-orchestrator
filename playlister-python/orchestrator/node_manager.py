import re
import time


class NodeManager ():
  def __init__(self, cluster_config_path, node):
    self.cluster_config_path = cluster_config_path
    self.node = node
    self.host_commander = HostCommander('cliff', '/home/cliff/.ssh/id_rsa')
    self.host_commander.reset_fingerprint(self.node['ip'])

  def puppet_update(self):
    puppet_result = self.host_commander.run(self.node['ip'], "cat ~/.password | sudo -S ls > /dev/null; sudo /opt/puppetlabs/bin/puppet agent --test")
    print(puppet_result[1])
    if puppet_result[2]: print("STDERR OUTPUT:\n{0}".format(puppet_result[2]))
    print("Puppet Agent returned code: {0}".format(puppet_result[0]))
    if puppet_result[0] == 1:
      raise Exception("puppet agent failed!")

  def get_puppet_state(self):
    print("\nGetting puppet state on node {0}.".format(self.node['name']))
    state_result = self.host_commander.run(self.node['ip'], "ls /etc/puppetlabs/fc_puppet_state/")
    raise Exception("Why result[1]?  Anyway, handle list of states.")
    state_segments = state_result[1].rstrip().split('_')
    return({ 'state':'_'.join(state_segments[:-1]), 'transition':state_segments[-1] })

#  def start_cass_full_repair(self):
#    nodetool_repair_out = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool repair --full")
#    if nodetool_repair_out[0]:
#      print("Nodetool repair returned nonzero exit code.  This may not be a problem - please investigate.")
##      raise Exception("Nodetool error getting node state for {0}".format(node['ip']))
#    return nodetool_repair_out[1].rstrip()
#
#  def get_cass_repair_status(self):
#    # True = finished, False = running
#    calculation_done = repair_done = False
#
#    repair_compaction_status = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool compactionstats")
#    if repair_compaction_status[0]:
#      raise Exception("Nodetool error getting compactionstats!")
#    if not re.match(r'pending tasks: 0$', repair_compaction_status[1]):
#      print("Cassandra is still calculating repair differences!")
#      print(repair_compaction_status[1])
#    else:
#      calculation_done = True
#
#    repair_netstats_status = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool netstats")
#    if repair_netstats_status[0]:
#      raise Exception("Nodetool error getting netstats!")
#    if not re.search(r'Mismatch .Blocking.: 0$', repair_netstats_status[1], re.M) or not re.search(r'Mismatch .Background.: 0$', repair_netstats_status[1], re.M):
#      print("Cassandra is still performing repairs!")
#      print(repair_netstats_status[1])
#    else:
#      repair_done = True
#
#    if calculation_done == True and repair_done == True:
#      print("Nodetool repair is fisihed!")
#      return True
#    else:
#      return False
#
#  def get_cass_node_state(self, node):
#    nodetool_test = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool status | grep ' {0} ' | awk '{{print $1}}'".format(node['ip']))
#    if nodetool_test[0]:
#      raise Exception("Nodetool error getting node state for {0}".format(node['ip']))
#    return nodetool_test[1].rstrip()
#
#  def wait_for_cassandra_up(self):
#    #attempts = 2
#    attempts = 120
#    sleep = 10
#    attempt = 0
#    nodetool_test = [None, None, None]
#    while not nodetool_test[1] == "UN\n":
#      if attempt == attempts: raise Exception("Timed out waiting for node {0} to reach 'UN' state!".format(node['ip']))
#      attempt = attempt + 1
#      nodetool_test = self.host_commander.run(self.node['ip'], "/usr/bin/nodetool status | grep ' {0} ' | awk '{{print $1}}'".format(self.node['ip']))
#      time.sleep(sleep)
