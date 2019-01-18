import os
import signal
import sys
import docker
from git import Git, Repo, InvalidGitRepositoryError
from time import sleep


def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

local_repo_path = 'src'
if not os.path.exists(local_repo_path):
    os.mkdir(local_repo_path)

with Git().custom_environment(GIT_SSH_COMMAND='ssh -i ./test.rsa'):
    try:
        repo = Repo(path=local_repo_path)
    except InvalidGitRepositoryError:
        repo = Repo.clone_from('git@github.com:kontur-exploitation/testcase-pybash.git', local_repo_path)

o = repo.remote('origin')
o.pull()

branches = [h.name for h in repo.heads]

branch = repo.heads[0]

while(True):
    labels = {
        'author': str(repo.head.commit.author),
        'commit': str(repo.head.commit.hexsha),
        'branch': str(repo.active_branch.name)
    }
    print(labels)
    sleep(5)

# client = docker.client.from_env()
# images = client.images.list('web')
#
# tags = [tag for image in images for tag in image.tags]
#
# tag = 'web:1.7'
#
# client.images.build(path='.', tag=tag, labels=labels)
# client.containers.run(tag, auto_remove=True, detach=True, ports={'80': '80'}, name='test')
