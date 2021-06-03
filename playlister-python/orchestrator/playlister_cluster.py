import os
import re
from string import Template

from playlister_settings import playlister_settings
script_dir=os.path.dirname(os.path.realpath(__file__))

class PlaylisterCluster ():
  def __init__(self, name, reinitialize=False):
    self.name = name
    self.settings = playlister_settings[self.name]
    self.configs = {}
    self.backend_nodes = []

  def parse_manifest_details(self):
    print("NOOP")

  def parse_openstack_details(self, stack_details):
    backend_nodes = []
    backend_re = re.compile('^BACKEND: (.*)')
    seed_re = re.compile('^BACKEND_SEEDS: (.*)')
    for line in stack_details.splitlines():
      match = backend_re.match(line)
      if match:
        print("Backend Line: {0}".format(match.group(1)))
        backend_nodes.append(match.group(1))
      match = seed_re.match(line)
      if match:
        print("Seed Line: {0}".format(match.group(1)))
        self.seeds = match.group(1).split(',')
    self.backend_nodes = []
    for backend in backend_nodes:
      node = {}
      (node['name'], node['id'], node['ip']) = backend.split(':')
      if [x for x in self.seeds if node['ip'] == x]:
        node['is_seed']=True
      else:
        node['is_seed']=False
      self.backend_nodes.append(node)

  def remove_node(self, node_name):
    for node in self.backend_nodes:
      if node['name'] == node_name:
        self.backend_nodes.remove(node)
    if node_name in self.configs.keys(): del self.configs[node_name]

  def configure_node(self, node, state):
    s = self.settings
    node_name = node['name']
    seeds = ','.join(self.seeds)
    with open("{0}/../files/node-data.yaml.template".format(script_dir), 'r') as f:
      data_template=Template(f.read())
    with open("{0}/../files/node-manifest.pp.template".format(script_dir), 'r') as f:
      manifest_template=Template(f.read())
    with open("{0}/../files/node-facter.txt.template".format(script_dir), 'r') as f:
      facts_template=Template(f.read())
    data_text = data_template.substitute(cluster_name=s['cluster_name'], dc=s['DC'], rack=s['rack'], package_ensure=s['package_ensure'], package=s['package'])
    manifest_text = manifest_template.substitute(node=node_name, seeds=seeds, state=state)
    facts_text = facts_template.substitute(state=state, test='test', cluster_name=s['cluster_name'], dc=s['DC'], rack=s['rack'], package_ensure=s['package_ensure'], package=s['package'])
    self.configs[node_name] = {'data':data_text, 'manifest':manifest_text, 'facts':facts_text}
    return self.configs[node_name]

  def get_node_config(self, node):
    return self.configs[node['name']]

