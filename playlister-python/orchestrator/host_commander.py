import subprocess

import logging, sys

class HostCommander ():
  def __init__(self, user, key_path, host):
    self.user = user
    self.key_path = key_path
    self.host = host

  def reset_fingerprint(self):
    ssh_result = subprocess.run(["/usr/bin/ssh-keygen", "-R {0}".format(self.host)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  def run(self, command, user=None):
    if not user:
      user = self.user
    ssh_result = subprocess.run(["/usr/bin/ssh", "-J admin1", "-o StrictHostKeyChecking no", "{0}@{1}".format(user, self.host), "{0}".format(command)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #ssh_result = subprocess.run(["/usr/bin/ssh", "-J admin1", "-o StrictHostKeyChecking no", "-i {0}".format(self.key_path), "{0}@{1}".format(user, self.host), "{0}".format(command)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ssh_result:
      return [ssh_result.returncode, ssh_result.stdout.decode('ascii'), ssh_result.stderr.decode('ascii')]
    else:
      raise Exception("error running {0} on {1}".format(command, self.host))


