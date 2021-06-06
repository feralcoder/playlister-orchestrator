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
    self.fe_nodes = []
    self.olap_nodes = []
    self.oltp_nodes = []
    self.init_markup_maps()

  def init_markup_maps(self):
    s = self.settings
    self.markup_maps = {}
    ( self.markup_maps['OLAP'], self.markup_maps['OLTP'], self.markup_maps['FE'] ) = ( {}, {}, {} )
    self.markup_maps['OLAP']['data'] = { 'cluster_name':s['cluster_name'], 'dc':s['DC'], 'rack':s['rack'], 'package_ensure':s['package_ensure'], 'package':s['package'] }
    self.markup_maps['OLAP']['manifest'] = {  }
    self.markup_maps['OLAP']['facts'] = {  'test':'test', 'cluster_name':s['cluster_name'], 'dc':s['DC'], 'rack':s['rack'], 'package_ensure':s['package_ensure'], 'package':s['package'] }
    self.markup_maps['OLTP']['data'] = { 'cluster_name':s['cluster_name'], 'dc':s['DC'], 'rack':s['rack'], 'package_ensure':s['package_ensure'], 'package':s['package'] }
    self.markup_maps['OLTP']['manifest'] = {  }
    self.markup_maps['OLTP']['facts'] = {  'test':'test', 'cluster_name':s['cluster_name'], 'dc':s['DC'], 'rack':s['rack'], 'package_ensure':s['package_ensure'], 'package':s['package'] }
    self.markup_maps['FE']['data'] = { 'cluster_name':s['cluster_name'], 'dc':s['DC'], 'rack':s['rack'], 'package_ensure':s['package_ensure'], 'package':s['package'] }
    self.markup_maps['FE']['manifest'] = {  }
    self.markup_maps['FE']['facts'] = {  'test':'test', 'cluster_name':s['cluster_name'], 'dc':s['DC'], 'rack':s['rack'], 'package_ensure':s['package_ensure'], 'package':s['package'] }

  def parse_manifest_details(self):
    print("NOOP")

#FE_VIP: 172.30.1.15
#FE_IPS: 10.254.0.158 10.254.0.216 10.254.0.245
#OLAP_VIP: 172.30.1.25
#OLAP_IPS: 10.254.0.80 10.254.0.163 10.254.0.192 10.254.0.178
#OLTP_VIP: 172.30.1.35
#OLTP_IPS: 10.254.0.37 10.254.0.56 10.254.0.199 10.254.0.200
#FE_STACK_ID: 87542638-1c35-41c8-9b9f-ae283e313cce
#FE_STACK_ID: f9b0d14a-5177-4475-ab77-e4e7c932fa33
#FE_STACK_ID: 282fc1a2-d18d-48ea-bdf1-4d28dd21fd98
#FE_STACK_NAME: playlister5-frontends-hvyfpgghytjv-c6jqtsjhzix3-4jomnesyijw7
#FE_STACK_NAME: playlister5-frontends-hvyfpgghytjv-wsuwn723qde4-2od25qxbsadw
#FE_STACK_NAME: playlister5-frontends-hvyfpgghytjv-aonqoa4y2ge4-dxbq3m2g33ok
#FRONTEND: playlister5-fe-10-254-0-158:aa84e340-5d18-4a5f-a230-20035babe808:10.254.0.158
#FRONTEND: playlister5-fe-10-254-0-216:579216c8-d8ca-4d0d-bfe9-43545bc6b6d8:10.254.0.216
#FRONTEND: playlister5-fe-10-254-0-245:a37694eb-8956-41d0-95ff-e49901f9b6cc:10.254.0.245
#OLAP_STACK_ID: 2fe8a675-3cb8-4205-b09a-a1244d6a9636
#OLAP_STACK_ID: 33038159-95af-407c-a403-f89c3dbd77d9
#OLAP_STACK_ID: 83e796cc-b67e-4b5e-b7c1-45c4281f0ab9
#OLAP_STACK_ID: 645175a3-bc0d-444b-9946-9372868331d6
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-5h7mgmgtvgsq-ssdhc6hrage4
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-htwxqkrsxtas-ncbwqayp4pll
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-smjp7gk3girk-l5oruv5fhmkc
#OLAP_STACK_NAME: playlister5-olap_backends-mxiwfqcaux7p-5ldsfo4aqpwb-yal3lhczi7qk
#OLAP_BACKEND: playlister5-olap-10-254-0-80:e0f9a215-e5f5-40ea-8fba-190ca348d4b6:10.254.0.80
#OLAP_BACKEND: playlister5-olap-10-254-0-163:4067625b-e305-43bd-9d4f-6eb63233b16a:10.254.0.163
#OLAP_BACKEND: playlister5-olap-10-254-0-192:5ffafadd-c8a9-4e92-9e9f-c62cbe4a53b6:10.254.0.192
#OLAP_BACKEND: playlister5-olap-10-254-0-178:c1bbff13-b940-446d-a795-567b8e6f3636:10.254.0.178
#OLTP_STACK_ID: cd8e17ad-a8e4-4e02-88f1-6b7030533c45
#OLTP_STACK_ID: 559a9127-73e4-4fc3-b091-9a2ad2114f41
#OLTP_STACK_ID: 6ee7ec26-53a5-47c8-bbc7-9710e23e11e9
#OLTP_STACK_ID: 49404beb-121b-4531-bcef-609480498aca
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-dbfcgntvp2ze-asdzkdyiadxc
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-2e4wiuoe6wsc-pb5xwunh2esw
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-ndv33v6axdu6-6ovnzi6my535
#OLTP_STACK_NAME: playlister5-oltp_backends-wtrlwx4heote-tuuv5wgk5le5-a72ouq4qzyfl
#OLTP_BACKEND: playlister5-oltp-10-254-0-37:8be336f2-c0fd-486e-9d49-4394f3418f63:10.254.0.37
#OLTP_BACKEND: playlister5-oltp-10-254-0-56:3030a28a-4da3-43ac-ba6a-ad476580c63c:10.254.0.56
#OLTP_BACKEND: playlister5-oltp-10-254-0-199:ff5e61be-265c-4891-8b06-e4b369882767:10.254.0.199
#OLTP_BACKEND: playlister5-oltp-10-254-0-200:7081985d-0a31-4dfc-89e0-e0eca9ea717f:10.254.0.200
#MANILA_SHARE_PATH: /volumes/_nogroup/e9004bf1-a0fb-4d01-b413-ae1bc8f744de/85dea32a-4cf2-467b-8309-1558a12683f3
#MANILA_KEY: AQC+WLFgK4A6MhAAwJpuLua5GZQm4x44da/sWg==
#MON_LIST: [v2:192.168.127.210:3300,v1:192.168.127.210:6789] [v2:192.168.127.212:3300,v1:192.168.127.212:6789] [v2:192.168.127.216:3300,v1:192.168.127.216:6789]
  def parse_openstack_details(self, stack_details):
    ( olap_nodes, oltp_nodes, fe_nodes ) = ( [], [], [] )
    olap_re = re.compile('^OLAP_BACKEND: (.*)')
    oltp_re = re.compile('^OLTP_BACKEND: (.*)')
    fe_re = re.compile('^FRONTEND: (.*)')
#    seed_re = re.compile('^BACKEND_SEEDS: (.*)')
    for line in stack_details.splitlines():
      for (regexp, nodes, typestr) in [ (olap_re, olap_nodes, 'OLAP'), (oltp_re, oltp_nodes, 'OLTP'), (fe_re, fe_nodes, 'FRONTEND') ]:
        match = regexp.match(line)
        if match:
          print("{0} Line: {1}".format(typestr, match.group(1)))
          nodes.append(match.group(1))
#      match = seed_re.match(line)
#      if match:
#        print("Seed Line: {0}".format(match.group(1)))
#        self.seeds = match.group(1).split(',')
    (self.olap_nodes, self.oltp_nodes, self.fe_nodes) = ( [], [], [] )
    for ( self_nodes, do_nodes, node_type ) in [ ( self.olap_nodes, olap_nodes, 'OLAP' ), ( self.oltp_nodes, oltp_nodes, 'OLTP' ), (self.fe_nodes, fe_nodes, 'FE') ]:
      for do_node in do_nodes:
        node = {}
        (node['name'], node['id'], node['ip']) = do_node.split(':')
        node['type'] = node_type
        self_nodes.append(node)
#      if [x for x in self.seeds if node['ip'] == x]:
#        node['is_seed']=True
#      else:
#        node['is_seed']=False
#      self.backend_nodes.append(node)

  def remove_node(self, node_name):
    for self_nodes in [ self.olap_nodes, self.oltp_nodes, self.fe_nodes ]:
      for node in self_nodes:
        if node['name'] == node_name:
          self_nodes.remove(node)
    if node_name in self.configs.keys(): del self.configs[node_name]


  def configure_node(self, node, state):
    node_name = node['name']

    with open("{0}/../files/{1}-node-data.yaml.template".format(node['type'], script_dir), 'r') as f:
      data_template=Template(f.read())
    with open("{0}/../files/{1}-node-manifest.pp.template".format(node['type'], script_dir), 'r') as f:
      manifest_template=Template(f.read())
    with open("{0}/../files/{1}-node-facter.txt.template".format(node['type'], script_dir), 'r') as f:
      facts_template=Template(f.read())
    data_text = data_template.substitute(**self.markup_maps[node['type']], state=state)
    manifest_text = manifest_template.substitute(**self.markup_maps[node['type']], state=state)
    facts_text = facts_template.substitute(**self.markup_maps[node['type']], state=state)
    self.configs[node_name] = {'data':data_text, 'manifest':manifest_text, 'facts':facts_text}
    return self.configs[node_name]

#  def configure_nodes(self):
#    for ( node_type, nodes ) in [ ( 'olap', self.olap_nodes ), ( 'oltp', self.oltp_nodes ), ( 'fe', self.fe_nodes ) ]:
#      with open("{0}/../files/{1}-node-data.yaml.template".format(node_type, script_dir), 'r') as f:
#        data_template=Template(f.read())
#      with open("{0}/../files/{1}-node-manifest.pp.template".format(node_type, script_dir), 'r') as f:
#        manifest_template=Template(f.read())
#      with open("{0}/../files/{1}-node-facter.txt.template".format(node_type, script_dir), 'r') as f:
#        facts_template=Template(f.read())
#      data_text = data_template.substitute(**self.markup_maps['node_type'])
#      manifest_text = manifest_template.substitute(**self.markup_maps['node_type'])
#      facts_text = facts_template.substitute(**self.markup_maps['node_type'])
#      for node in nodes:
#        self.configs[node['name']] = {'data':data_text, 'manifest':manifest_text, 'facts':facts_text}




    return self.configs[node_name]

  def get_node_config(self, node):
    return self.configs[node['name']]

