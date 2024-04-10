from paramiko import SSHClient


def ssh_exec_command(ssh: SSHClient, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout_result = stdout.read().decode()
    stderr_result = stderr.read().decode()
    if stdout_result:
        return stdout_result
    elif stderr_result:
        raise Exception(stderr_result)
    else:
        raise Exception('unknown error')
