import subprocess


def run_command(command):
    """
    Run a command and return the output.
    """
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out


if __name__ == '__main__':
    command = 'batt'
    output=run_command(command)
    print(output)