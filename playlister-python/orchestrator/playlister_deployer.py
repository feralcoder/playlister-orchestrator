import time
import logging, sys
from .playlister_state_machine import PlaylisterStateMachine

class PlaylisterDeployer ():
  def __init__(self, name, manifest, script_dir):
    self.playlister_state = PlaylisterStateMachine(name, manifest, script_dir, reinitialize=True)


  ### CLUSTER TRANSITIONS
  def create_cluster(self):
    #self.install_transaction_db()
    #self.install_analytics_db()
    #self.install_frontends()
    self.bootstrap_transaction_db(nuke=True)
    # IMPLEMENT:
    #self.bootstrap_analytics_db(nuke=True)

  def deploy_playlister_code(self, parallel=False):
    self.playlister_state.deploy_playlister_code(parallel)

  def install_transaction_db(self):
    self.playlister_state.install_transaction_db()

  def install_analytics_db(self):
    self.playlister_state.install_analytics_db()

  def install_frontends(self):
    self.playlister_state.install_frontends()

  def bootstrap_transaction_db(self, nuke=False):
    if nuke:
      self.playlister_state.initialize_transaction_db()
    else:
      self.playlister_state.restore_transaction_db()

  def bootstrap_analytics_db(self, nuke=False):
    if nuke:
      self.playlister_state.initialize_analytics_db()
    else:
      self.playlister_state.restore_analytics_db()

  def start_transaction_db(self):
    self.playlister_state.start_transaction_db()

  def stop_transaction_db(self):
    None

  def start_analytics_db(self):
    None

  def stop_analytics_db(self):
    None

  def start_frontends(self):
    None

  def stop_frontends(self):
    None



#
#
#
#
#  def shutdown_cassandra(self):
#    self.playlister_state.setNodeStateAll('stopping')
#    self.playlister_state.transitionNodeStateAll()
#    for node in self.playlister_state.playlister_cluster.backend_nodes:
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      print(node_state)
#      if not (node_state['state'] == 'stopping' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'initial_build_finished': {1}".format(node['name'], node_state))
#
#
#  def deploy_this_thing(self):
#    self.playlister_state.setNodeStateAll('initial_build')
#    for node in self.playlister_state.playlister_cluster.backend_nodes:
#      self.playlister_state.transitionNodeState(node)
#
#    for node in self.playlister_state.playlister_cluster.backend_nodes:
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      print(node_state)
#      if not (node_state['state'] == 'initial_build' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'initial_build_finished': {1}".format(node['name'], node_state))
#
#  def start_cassandra(self):
#    # Nodes are ordered with primary and secondary seeds as #1 and #2 - they were selected from the first 2.
#    for node in self.playlister_state.playlister_cluster.backend_nodes:
#      self.playlister_state.setNodeState(node, 'starting')
#      self.playlister_state.transitionNodeState(node)
#      time.sleep(10)
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      if not (node_state['state'] == 'starting' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'starting_finished': {1}".format(node['name'], node_state))
#      self.playlister_state.node_managers[node['name']].wait_for_cassandra_up()
#      print("Node {0} cassandra is up!".format(node['name']))
#
#      self.playlister_state.setNodeState(node, 'started')
#      self.playlister_state.transitionNodeState(node)
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      if not (node_state['state'] == 'started' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'started_finished': {1}".format(node['name'], node_state))
#      print("Node {0} started!".format(node['name']))
#
#
#
#  def load_schema(self):
#    # Nodes are ordered with primary and secondary seeds as #1 and #2 - they were selected from the first 2.
#    for node in [self.playlister_state.playlister_cluster.backend_nodes[0]]:
#      self.playlister_state.setNodeState(node, 'load_schema')
#      self.playlister_state.transitionNodeState(node)
#      time.sleep(10)
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      if not (node_state['state'] == 'load_schema' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'load_schema_finished': {1}".format(node['name'], node_state))
#      print("Node {0} loaded schema!".format(node['name']))
#      self.playlister_state.setNodeState(node, 'started')
#      self.playlister_state.transitionNodeState(node)
#      time.sleep(10)
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      if not (node_state['state'] == 'started' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'started_finished': {1}".format(node['name'], node_state))
#      print("Node {0} started!".format(node['name']))
#
#
#  def nominalize(self):
#    control_node = self.playlister_state.playlister_cluster.backend_nodes[0]
#    for node in self.playlister_state.playlister_cluster.backend_nodes:
#      node_state = self.playlister_state.node_managers[control_node['name']].get_cass_node_state(node)
#      if not node_state == "UN":
#        raise Exception("Can't nominalize: node {0} is in state {1}!".format(node['name'], node_state))
#    while True:
#      repair_status = self.playlister_state.node_managers[control_node['name']].get_cass_repair_status()
#      if repair_status == True: break
#      print("Cassandra cluster still repairing.  Sleeping.")
#      time.sleep(20)
#    print("Cassandra cluster has finished repairing!")
#
#    self.playlister_state.setNodeStateAll('nominal')
#    self.playlister_state.transitionNodeStateAll()
#    for node in self.playlister_state.playlister_cluster.backend_nodes:
#      node_state = self.playlister_state.node_managers[node['name']].get_puppet_state()
#      if not (node_state['state'] == 'nominal' and node_state['transition'] == 'finished'):
#        raise Exception("Node {0} has not reached 'nominal_finished': {1}".format(node['name'], node_state))
#      print("Node {0} cassandra is nominal!".format(node['name']))
#
