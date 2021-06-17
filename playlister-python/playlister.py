import os
import sys
from orchestrator import HostCommander, NodeManager, PlaylisterDeployer, PuppetManifest
import logging, sys

stack_operation = sys.argv[1]
stack_name = sys.argv[2]

script_dir=os.path.dirname(os.path.realpath(__file__))
manifest_dir="{0}/puppet-manifests".format(script_dir)
puppetmaster = 'puppetmaster.feralcoder.org'

log_level=logging.INFO
logging.basicConfig(stream=sys.stderr, level=log_level)


stack_operation = stack_operation.upper()
assert stack_operation in [ 'INSTALL', 'INITIALIZE', 'DEPLOY', 'RESTORE', 'BACKUP', 'START', 'STOP', 'DESTROY', 'FLUSH', 'TEST', 'ENCHILADA' ]
assert stack_name in [ 'playlister', 'playlister2', 'playlister3', 'playlister4', 'playlister5' ]


class PlaylisterOperator:
  def __init__(self, stack_name, manifest_dir, script_dir, puppetmaster, environment="production"):
    self.stack_name = stack_name
    self.manifest_dir = manifest_dir
    self.puppetmaster = puppetmaster
    self.environment = environment
    self.script_dir = script_dir
    # DELAY initializinsg manifest and deployer until first requiring operation is called...
    self.manifest = None
    self.playlister_deployer = None

  def manage(self):
    self.manifest = PuppetManifest(self.manifest_dir, self.stack_name, self.puppetmaster, self.environment)
    logging.debug(repr(self.manifest))
    self.manifest.git_pull()
    self.playlister_deployer = PlaylisterDeployer(self.stack_name, self.manifest, self.script_dir)
    logging.debug(repr(self.playlister_deployer))


  def stack_install(self):
    if not self.manifest:
      self.manage()
    # SPLIT INSTALL / INITIALIZE in playlister_deployer
    self.playlister_deployer.create_cluster()

  def stack_initialize(self):
    if not self.manifest:
      self.manage()
    # SPLIT INSTALL / INITIALIZE in playlister_deployer
    self.playlister_deployer.initialize_cluster()
    #self.playlister_deployer.load_schema()

  def stack_restore(self):
    if not self.manifest:
      self.manage()
    raise Exception("stack_restore not yet implemented!")

  def stack_backup(self):
    if not self.manifest:
      self.manage()
    raise Exception("stack_backup not yet implemented!")

  def stack_deploy(self):
    if not self.manifest:
      self.manage()
    self.playlister_deployer.deploy_playlister_code(parallel=True)

  def stack_start(self):
    if not self.manifest:
      self.manage()
    self.playlister_deployer.start_transaction_db()
    # IMPLEMENT:
    #self.playlister_deployer.start_analytics_db()

  def stack_stop(self):
    if not self.manifest:
      self.manage()
    self.playlister_deployer.stop_transaction_db()
    # IMPLEMENT:
    #self.playlister_deployer.stop_analytics_db()

  # USE DESTROY FOR A CLUSTER WHICH HAS A VALID CONFIGURATION IN OPENSTACK
  def stack_destroy(self):
    if not self.manifest:
      self.manage()
    self.playlister_deployer.destroy_cluster()

  # USE FLUSH FOR A CLUSTER WHICH NO LONGER EXISTS
  def stack_flush(self):
    PlaylisterDeployer.flush_cluster(self.stack_name, self.manifest_dir, self.script_dir, self.puppetmaster, self.environment)


  def stack_test(self):
    if not self.manifest:
      self.manage()
    raise Exception("stack_test not yet implemented!")

  def stack_enchilada(self):
    if not self.manifest:
      self.manage()
    self.playlister_deployer.create_cluster()
    self.playlister_deployer.initialize_cluster()
    self.playlister_deployer.deploy_playlister_code(parallel=True)

  def run_stack_operation(self, operation):
    operations = {
      'INSTALL': self.stack_install,
      'INITIALIZE': self.stack_initialize,
      'RESTORE': self.stack_restore,
      'BACKUP': self.stack_backup,
      'DEPLOY': self.stack_deploy,
      'START': self.stack_start,
      'STOP': self.stack_stop,
      'DESTROY': self.stack_destroy,
      'FLUSH': self.stack_flush,
      'TEST': self.stack_test,
      'ENCHILADA': self.stack_enchilada,
    }
    function = operations.get(operation, lambda: Exception("Invalid operation {0}".format(operation)))
    function()
  



if __name__ == "__main__":
  playlister_operator = PlaylisterOperator(stack_name, manifest_dir, script_dir, puppetmaster, "production")
  playlister_operator.run_stack_operation(stack_operation)
