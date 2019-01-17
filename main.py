import os
import docker
from git import Repo

local_repo_path = 'src'
if not os.path.exists(local_repo_path):
    os.mkdir(local_repo_path)

repo = Repo(path=local_repo_path)

labels = {
    'author': str(repo.head.commit.author),
    'commit': str(repo.head.commit.hexsha),
    'branch': str(repo.active_branch.name)
}

client = docker.client.from_env()
images = client.images.list('web')

tags = [tag for image in images for tag in image.tags]

tag = 'web:1.7'

client.images.build(path='.', tag=tag, labels=labels)
client.containers.run(tag, auto_remove=True, detach=True, ports={'80': '80'}, name='test')
