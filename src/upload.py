import pexpect
import os

user = os.environ['JMLR_USER']
path = os.environ['JMLR_PATH']
passwd = os.environ['JMLR_PASSWORD']

path = os.path.join(path, 'tmlr')

# Note, the output/output/ is specific to how circleci mounts
# the workspace. To run locally, it should be replaced with output/
command = 'rsync -arvz output/output/ %s@%s' % (user, path)

ssh_newkey = 'Are you sure you want to continue connecting'
child = pexpect.spawn(command)
i = child.expect([ssh_newkey,'Password:',pexpect.EOF])
if i==0:
    child.sendline('yes')
    i = child.expect([ssh_newkey,'Password:',pexpect.EOF])
if i==1:
    child.sendline(passwd)
child.interact()
