import subprocess
import logging, sys

class PuppetMasterFiles ():
  def __init__(self, puppetmaster, code_dir='/etc/puppetlabs/code/environments/production'):
    self.puppetmaster = puppetmaster
    self.code_dir = code_dir

  def sync(self, source_file, dest_file):
    logging.debug("Syncing {0} to puppetmaster:{1}".format(source_file, ":{0}/{1}".format(self.code_dir, dest_file)))
    sync_result = subprocess.run(["/usr/bin/rsync", "-e ssh -o StrictHostKeyChecking=no", source_file, "root@{0}".format(self.puppetmaster) + ":{0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logging.debug("Command output: [ {0}, {1}, {2} ]".format(sync_result.returncode, sync_result.stdout, sync_result.stderr))

  def delete_if_present(self, dest_file):
    delete_result = subprocess.run(["/usr/bin/ssh", "-o StrictHostKeyChecking=no", "root@{0}".format(self.puppetmaster),  "rm -f {0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  def delete(self, dest_file):
    delete_result = subprocess.run(["/usr/bin/ssh", "-o StrictHostKeyChecking=no", "root@{0}".format(self.puppetmaster),  "rm {0}/{1}".format(self.code_dir, dest_file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
