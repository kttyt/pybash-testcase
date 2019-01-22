import os
import signal
import sys
from time import sleep

import docker
import docker.errors
from git import Repo, InvalidGitRepositoryError

DELAY = 5
IMAGE_NAME = 'web'
LOCAL_REPO_PATH = 'src'
REMOTE_REPOSITORY = 'git@github.com:kontur-exploitation/testcase-pybash.git'
SSH_KEY_PATH = '~/.ssh/test_rsa'
LOG_FILE = 'app.log'
INNER_LOG_FILE = 'app.log'


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def touch(path):
    if not os.path.isfile(LOG_FILE):
        with open(path, 'a'):
            os.utime(path, None)


def get_updated_commits(fetch_info, state):
    updates = []
    isEmptyState = True if not state else False
    for info in fetch_info:
        hash = info.commit.hexsha
        commited_date = info.commit.committed_date
        branch = str(info.ref).replace('origin/', '')
        if branch not in state or state[branch]['last_hash'] != hash:
            entry = {
                'last_hash': hash,
                'committed_date': commited_date,
                'branch': str(branch)
            }
            state[branch] = entry
            if isEmptyState:
                continue

            updates.append(entry)
    return updates


def create_docker_image(client, author, hexsha, branch):
    labels = {
        'author': str(author),
        'commit': str(hexsha),
        'branch': str(branch)
    }
    tag = f"{IMAGE_NAME}:{hexsha[:7]}"
    client.images.build(path='.', tag=tag, labels=labels)
    return tag


def run_container(client, tag):
    touch(LOG_FILE)
    if os.path.isabs(LOG_FILE):
        log_file_path = LOG_FILE
    else:
        log_file_path = os.path.join(os.getcwd(), LOG_FILE)

    if os.path.isabs(INNER_LOG_FILE):
        inner_log_file_path = INNER_LOG_FILE
    else:
        inner_log_file_path = os.path.join('/tmp', INNER_LOG_FILE)

    container = client.containers.run(
        tag,
        command=inner_log_file_path,
        auto_remove=True,
        detach=True,
        ports={'80': '80'},
        volumes={
            log_file_path: {
                'bind': inner_log_file_path, 'mode': 'rw'
            }
        },
        name='test'
    )

    for _ in range(0, 10):
        sleep(5)
        try:
            container.reload()
        except docker.errors.NotFound:
            return False
        if container.status in 'running':
            return True
    return False


def stop_running_containers(client):
    containers = client.containers.list(filters={'name': 'test', 'status': 'running'})
    if not containers:
        return None
    tag = None
    for container in containers:
        tag = container.image.tags[0]
        container.stop()
    return tag


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)  # Handling pressing 'Ctrl + C'

    if not os.path.exists(LOCAL_REPO_PATH):
        os.mkdir(LOCAL_REPO_PATH)

    try:
        repo = Repo(path=LOCAL_REPO_PATH)
        repo.git.update_environment(GIT_SSH_COMMAND=f'ssh -i {SSH_KEY_PATH}')
    except InvalidGitRepositoryError:
        repo = Repo.clone_from(REMOTE_REPOSITORY, LOCAL_REPO_PATH, env={'GIT_SSH_COMMAND': f'ssh -i {SSH_KEY_PATH}'})

    state = {}

    while True:
        print('New interact')
        fetch_info = repo.remote('origin').fetch()
        updated_commits = get_updated_commits(fetch_info, state)

        if updated_commits:
            print('New commits are detected')
            last_commit = max(updated_commits, key=lambda x: x['committed_date'])
            branch = last_commit['branch']

            repo.git.checkout(branch)
            print(f"Checkout to {branch}")

            repo.git.merge(f'origin/{branch}')
            print(f'Merge {branch} with origin')

            client = docker.client.from_env()
            tag = create_docker_image(
                client,
                branch=branch,
                author=repo.head.commit.author,
                hexsha=repo.head.commit.hexsha
            )
            print(f'Create docker image with tag: {tag}')

            previous_tag = stop_running_containers(client)
            if previous_tag:
                print(f"Old container with tag '{previous_tag} has stopped'")

            print(f'Running new container')
            isRunning = run_container(client, tag)

            if not isRunning and previous_tag:
                run_container(client, previous_tag)
        sleep(DELAY)
