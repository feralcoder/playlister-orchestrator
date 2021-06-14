import os
import re
from string import Template
import logging, sys

from playlister_settings import playlister_settings
script_dir=os.path.dirname(os.path.realpath(__file__))



class PlaylisterCluster ():
  def __init__(self, name, reinitialize=False):
    self.name = name
    self.settings = playlister_settings[self.name]
    self.configs = {}
    self.nodes = {}
    self.cluster_data = {}
    ( self.nodes['FE'], self.nodes['OLAP'], self.nodes['OLTP'] ) = ( [], [], [] )

  def init_markup_maps(self):
    s = self.settings
    data = self.cluster_data
    self.markup_maps = {}
    ( self.markup_maps['OLAP'], self.markup_maps['OLTP'], self.markup_maps['FE'] ) = ( {}, {}, {} )
    self.markup_maps['OLAP']['data'] = { 'cluster_name':data['CLUSTER_NAME'], 'cephfs_list':data['CEPHFS_LIST'], 'manila_key':data['MANILA_KEY'], 'manila_path':data['MANILA_PATH'], 'oltp_ips':data['OLTP_IPS'] }
    self.markup_maps['OLAP']['manifest'] = {  }
    self.markup_maps['OLAP']['facts'] = {  'cluster_name':data['CLUSTER_NAME'], 'cephfs_list':data['CEPHFS_LIST'], 'manila_key':data['MANILA_KEY'], 'manila_path':data['MANILA_PATH'], 'oltp_ips':data['OLTP_IPS'] }
    self.markup_maps['OLTP']['data'] = { 'cluster_name':data['CLUSTER_NAME'], 'cephfs_list':data['CEPHFS_LIST'], 'manila_key':data['MANILA_KEY'], 'manila_path':data['MANILA_PATH'], 'oltp_ips':data['OLTP_IPS'] }
    self.markup_maps['OLTP']['manifest'] = {  }
    self.markup_maps['OLTP']['facts'] = {  'cluster_name':data['CLUSTER_NAME'], 'cephfs_list':data['CEPHFS_LIST'], 'manila_key':data['MANILA_KEY'], 'manila_path':data['MANILA_PATH'], 'oltp_ips':data['OLTP_IPS'] }
    self.markup_maps['FE']['data'] = { 'cluster_name':data['CLUSTER_NAME'], 'cephfs_list':data['CEPHFS_LIST'], 'manila_key':data['MANILA_KEY'], 'manila_path':data['MANILA_PATH'], 'oltp_ips':data['OLTP_IPS'] }
    self.markup_maps['FE']['manifest'] = {  }
    self.markup_maps['FE']['facts'] = {  'cluster_name':data['CLUSTER_NAME'], 'cephfs_list':data['CEPHFS_LIST'], 'manila_key':data['MANILA_KEY'], 'manila_path':data['MANILA_PATH'], 'oltp_ips':data['OLTP_IPS'],
                                         'oltp_vip':data['OLTP_VIP'], 'dbname':'playlister', 'dbuser':'playlister', 'dbpassword':'playlister_password' }

  ### REFACTORING


  ### ORIGINAL

  def parse_manifest_details(self):
    print("NOOP")

  def parse_openstack_details(self, stack_details):
    nodes = {}
    ( nodes['FE'], nodes['OLAP'], nodes['OLTP'] ) = ( [], [], [] )
    regexps = {}
    regexps['OLAP'] = re.compile('^OLAP_BACKEND: (.*)')
    regexps['OLTP'] = re.compile('^OLTP_BACKEND: (.*)')
    regexps['FE'] = re.compile('^FRONTEND: (.*)')
    regexps['FE_VIP'] = re.compile('^FE_VIP: (.*)')
    regexps['OLTP_VIP'] = re.compile('^OLTP_VIP: (.*)')
    regexps['OLAP_VIP'] = re.compile('^OLAP_VIP: (.*)')
    regexps['FE_IPS'] = re.compile('^FE_IPS: (.*)')
    regexps['OLTP_IPS'] = re.compile('^OLTP_IPS: (.*)')
    regexps['OLAP_IPS'] = re.compile('^OLAP_IPS: (.*)')
    regexps['CEPHFS_LIST'] = re.compile('^CEPHFS_LIST: (.*)')
    regexps['MANILA_KEY'] = re.compile('^MANILA_KEY: (.*)')
    regexps['MANILA_PATH'] = re.compile('^MANILA_SHARE_PATH: (.*)')
    regexps['CLUSTER_NAME'] = re.compile('^CLUSTER_NAME: (.*)')
    for line in stack_details.splitlines():
      for node_type in [ 'OLAP', 'OLTP', 'FE' ]:
        match = regexps[node_type].match(line)
        if match:
          logging.info("{0} Line: {1}".format(node_type, match.group(1)))
          nodes[node_type].append(match.group(1))
          break
      if match:
        continue
      else:
        for line_type in [ 'CLUSTER_NAME', 'FE_VIP', 'OLTP_VIP', 'OLAP_VIP', 'FE_IPS', 'OLTP_IPS', 'OLAP_IPS', 'CEPHFS_LIST', 'MANILA_KEY', 'MANILA_PATH' ]:
          match = regexps[line_type].match(line)
          if match:
            logging.info("{0} Line: {1}".format(line_type, match.group(1)))
            self.cluster_data[line_type] = match.group(1).replace(' ', ',')
    for node_type in [ 'OLAP', 'OLTP', 'FE' ]:
      self.nodes[node_type] = []
      for do_node in nodes[node_type]:
        node = {}
        (node['name'], node['id'], node['ip']) = do_node.split(':')
        node['type'] = node_type
        self.nodes[node_type].append(node)
    self.init_markup_maps()

  def remove_node(self, node_name):
    for node_type in [ 'FE', 'OLAP', 'OLTP' ]:
      for node in self.nodes[node_type]:
        if node['name'] == node_name:
          self.nodes[node_type].remove(node)
    if node_name in self.configs.keys(): del self.configs[node_name]


  def configure_node(self, node, state, service_enable=False):
    node_name = node['name']

    with open("{0}/../../files/{1}-node-data.yaml.template".format(script_dir, node['type']), 'r') as f:
      data_template=Template(f.read())
    with open("{0}/../../files/{1}-node-manifest.pp.template".format(script_dir, node['type']), 'r') as f:
      manifest_template=Template(f.read())
    with open("{0}/../../files/{1}-node-facter.txt.template".format(script_dir, node['type']), 'r') as f:
      facts_template=Template(f.read())
    logging.debug("Marking up data_template with {0}".format(str(self.markup_maps[node['type']]['data'])))
    data_text = data_template.substitute(**self.markup_maps[node['type']]['data'], state=state, service_enable=service_enable)
    logging.debug("Marking up manifest_template with {0}".format(str(self.markup_maps[node['type']]['manifest'])))
    manifest_text = manifest_template.substitute(**self.markup_maps[node['type']]['manifest'], node=node['name'], state=state, service_enable=service_enable)
    logging.debug("Marking up facts_template with {0}".format(str(self.markup_maps[node['type']]['facts'])))
    facts_text = facts_template.substitute(**self.markup_maps[node['type']]['facts'], state=state, service_enable=service_enable)
    self.configs[node_name] = {'data':data_text, 'manifest':manifest_text, 'facts':facts_text}
    return self.configs[node_name]

#  def configure_nodes(self):
#    for ( node_type, nodes ) in [ ( 'olap', self.olap_nodes ), ( 'oltp', self.oltp_nodes ), ( 'fe', self.fe_nodes ) ]:
#      with open("{0}/../files/{1}-node-data.yaml.template".format(script_dir, node_type), 'r') as f:
#        data_template=Template(f.read())
#      with open("{0}/../files/{1}-node-manifest.pp.template".format(script_dir, node_type), 'r') as f:
#        manifest_template=Template(f.read())
#      with open("{0}/../files/{1}-node-facter.txt.template".format(script_dir, node_type), 'r') as f:
#        facts_template=Template(f.read())
#      data_text = data_template.substitute(**self.markup_maps['node_type'])
#      manifest_text = manifest_template.substitute(**self.markup_maps['node_type'])
#      facts_text = facts_template.substitute(**self.markup_maps['node_type'])
#      for node in nodes:
#        self.configs[node['name']] = {'data':data_text, 'manifest':manifest_text, 'facts':facts_text}
#    return self.configs[node_name]

  def get_node_config(self, node):
    return self.configs[node['name']]

#
#FE_VIP: 172.30.1.12
#FE_IPS: 10.254.0.7 10.254.0.173 10.254.0.238
#OLAP_VIP: 172.30.1.22
#OLAP_IPS: 10.254.0.207 10.254.0.143 10.254.0.104 10.254.0.249
#OLTP_VIP: 172.30.1.32
#OLTP_IPS: 10.254.0.200 10.254.0.76 10.254.0.193 10.254.0.32
#FE_STACK_ID: 70a262c4-cf65-474b-90a9-e444227a030c
#FE_STACK_ID: 87781d0a-bd14-4399-9edd-241ad322ef46
#FE_STACK_ID: 14a9640a-a415-4372-b2cf-650b8db0db8b
#FE_STACK_NAME: playlister2-frontends-7fej4tdf7gbp-3r4rqjaeq5f3-yxlngtsj7umw
#FE_STACK_NAME: playlister2-frontends-7fej4tdf7gbp-piskbrfxmhma-2zunrw6636km
#FE_STACK_NAME: playlister2-frontends-7fej4tdf7gbp-zu7rz5uafjo2-u23e3daklekv
#FRONTEND: playlister2-fe-10-254-0-7:0535fad1-4c80-4579-bcb7-df1e7d55fed2:10.254.0.7
#FRONTEND: playlister2-fe-10-254-0-173:119380eb-5155-4d9c-8250-bf3fc0dc70d2:10.254.0.173
#FRONTEND: playlister2-fe-10-254-0-238:43dbf280-724b-47bf-b74b-19e511c7fa40:10.254.0.238
#OLAP_STACK_ID: 8bbffa3b-f629-467f-9c69-0da40d1bcad5
#OLAP_STACK_ID: 0b92de75-bb3e-44eb-a8fd-daf8a83fa082
#OLAP_STACK_ID: 00edacad-9c6b-42cb-88bc-f0f1d7f029b3
#OLAP_STACK_ID: fe12699e-e53e-4707-be8f-769bfb67fe69
#OLAP_STACK_NAME: playlister2-olap_backends-xnb64i52ittw-x6xpzkber3b4-obagdd4rpz3o
#OLAP_STACK_NAME: playlister2-olap_backends-xnb64i52ittw-ip56wocpwbyx-dnimcc5hamh7
#OLAP_STACK_NAME: playlister2-olap_backends-xnb64i52ittw-qzo2egtebqwa-ocf3aikizyik
#OLAP_STACK_NAME: playlister2-olap_backends-xnb64i52ittw-rzh3xijgxopk-2noldkbnz5pf
#OLAP_BACKEND: playlister2-olap-10-254-0-207:d33caa68-2275-4a57-83c5-c8fef9b025dd:10.254.0.207
#OLAP_BACKEND: playlister2-olap-10-254-0-143:0cc83d2c-54a6-4e4f-871e-6b961340f913:10.254.0.143
#OLAP_BACKEND: playlister2-olap-10-254-0-104:a09ba111-bccd-4efe-8ccb-df16101a7330:10.254.0.104
#OLAP_BACKEND: playlister2-olap-10-254-0-249:163b9e64-8087-435a-a0f5-15d31be52aba:10.254.0.249
#OLTP_STACK_ID: 2f0460a7-e599-4ec5-b0e1-1ceb5b617d4e
#OLTP_STACK_ID: b28d0e06-efaa-481a-98ac-52ad9321164d
#OLTP_STACK_ID: da073d04-a4ec-4d1e-8505-61a321485e37
#OLTP_STACK_ID: 5aea8f6f-2e8a-48e8-a425-e8dcf92e0c5f
#OLTP_STACK_NAME: playlister2-oltp_backends-2ae3ukq327yb-jrgjzz74mc6g-dcaecswmydft
#OLTP_STACK_NAME: playlister2-oltp_backends-2ae3ukq327yb-3a5fjdoqdzzt-d7h6ui3ycdhl
#OLTP_STACK_NAME: playlister2-oltp_backends-2ae3ukq327yb-rwtpovnlqegd-s347wwnt2gr2
#OLTP_STACK_NAME: playlister2-oltp_backends-2ae3ukq327yb-uuwwkjfhrx6l-6mhkgk52pqkc
#OLTP_BACKEND: playlister2-oltp-10-254-0-200:bb099e86-503f-41fc-86d6-37a08f099655:10.254.0.200
#OLTP_BACKEND: playlister2-oltp-10-254-0-76:9a01ede0-cee1-4978-8d2f-6a8afee46d1f:10.254.0.76
#OLTP_BACKEND: playlister2-oltp-10-254-0-193:8c3e4a3e-6647-4053-8796-535f8fe79fc3:10.254.0.193
#OLTP_BACKEND: playlister2-oltp-10-254-0-32:a3745fa7-9833-47f7-b3a0-95c185910df3:10.254.0.32
#MANILA_SHARE_PATH: /volumes/_nogroup/e9004bf1-a0fb-4d01-b413-ae1bc8f744de/85dea32a-4cf2-467b-8309-1558a12683f3
#MANILA_KEY: AQC+WLFgK4A6MhAAwJpuLua5GZQm4x44da/sWg==
#MON_LIST: [v2:192.168.127.210:3300,v1:192.168.127.210:6789] [v2:192.168.127.212:3300,v1:192.168.127.212:6789] [v2:192.168.127.216:3300,v1:192.168.127.216:6789]
#
