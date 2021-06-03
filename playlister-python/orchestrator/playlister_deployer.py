import time

puppetmaster = 'puppetmaster.feralcoder.org'

class PlaylisterDeployer ():
  def __init__(self, name, manifest):
    self.playlister_backend_state = PlaylisterStateMachine(name, manifest, puppetmaster, reinitialize=True)

  def shutdown_cassandra(self):
    self.playlister_backend_state.setNodeStateAll('stopping')
    self.playlister_backend_state.transitionNodeStateAll()
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      print(node_state)
      if not (node_state['state'] == 'stopping' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'initial_build_finished': {1}".format(node['name'], node_state))


  def deploy_this_thing(self):
    self.playlister_backend_state.setNodeStateAll('initial_build')
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      self.playlister_backend_state.transitionNodeState(node)

    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      print(node_state)
      if not (node_state['state'] == 'initial_build' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'initial_build_finished': {1}".format(node['name'], node_state))

  def start_cassandra(self):
    # Nodes are ordered with primary and secondary seeds as #1 and #2 - they were selected from the first 2.
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      self.playlister_backend_state.setNodeState(node, 'starting')
      self.playlister_backend_state.transitionNodeState(node)
      time.sleep(10)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'starting' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'starting_finished': {1}".format(node['name'], node_state))
      self.playlister_backend_state.node_managers[node['name']].wait_for_cassandra_up()
      print("Node {0} cassandra is up!".format(node['name']))

      self.playlister_backend_state.setNodeState(node, 'started')
      self.playlister_backend_state.transitionNodeState(node)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'started' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'started_finished': {1}".format(node['name'], node_state))
      print("Node {0} started!".format(node['name']))



  def load_schema(self):
    # Nodes are ordered with primary and secondary seeds as #1 and #2 - they were selected from the first 2.
    for node in [self.playlister_backend_state.playlister_cluster.backend_nodes[0]]:
      self.playlister_backend_state.setNodeState(node, 'load_schema')
      self.playlister_backend_state.transitionNodeState(node)
      time.sleep(10)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'load_schema' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'load_schema_finished': {1}".format(node['name'], node_state))
      print("Node {0} loaded schema!".format(node['name']))
      self.playlister_backend_state.setNodeState(node, 'started')
      self.playlister_backend_state.transitionNodeState(node)
      time.sleep(10)
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'started' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'started_finished': {1}".format(node['name'], node_state))
      print("Node {0} started!".format(node['name']))


  def nominalize(self):
    control_node = self.playlister_backend_state.playlister_cluster.backend_nodes[0]
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[control_node['name']].get_cass_node_state(node)
      if not node_state == "UN":
        raise Exception("Can't nominalize: node {0} is in state {1}!".format(node['name'], node_state))
    while True:
      repair_status = self.playlister_backend_state.node_managers[control_node['name']].get_cass_repair_status()
      if repair_status == True: break
      print("Cassandra cluster still repairing.  Sleeping.")
      time.sleep(20)
    print("Cassandra cluster has finished repairing!")

    self.playlister_backend_state.setNodeStateAll('nominal')
    self.playlister_backend_state.transitionNodeStateAll()
    for node in self.playlister_backend_state.playlister_cluster.backend_nodes:
      node_state = self.playlister_backend_state.node_managers[node['name']].get_puppet_state()
      if not (node_state['state'] == 'nominal' and node_state['transition'] == 'finished'):
        raise Exception("Node {0} has not reached 'nominal_finished': {1}".format(node['name'], node_state))
      print("Node {0} cassandra is nominal!".format(node['name']))

