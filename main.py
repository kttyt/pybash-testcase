import os
from git import Repo

local_repo_path = 'src'
if not os.path.exists(local_repo_path):
    os.mkdir(local_repo_path)

repo = Repo(path=local_repo_path)
print(repo.head.commit.author)
print(repo.head.commit.hexsha)
print(repo.active_branch.name)
