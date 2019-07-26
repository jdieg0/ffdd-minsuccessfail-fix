#!/usr/bin/env python3

# Debugging
from IPython import embed

# Input
import readline
from getpass import getpass

# SSH
from paramiko.util import log_to_file
from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import AuthenticationException

# Constants
VERSION = '0.1'
BANNER = """______________________________________________________________________
     _____                                                             
  __|___  |__  _____   ______  ____  ______  __   _  ____   _  __  __  
 |   ___|    ||     | |   ___||    ||   ___||  | | ||    \ | ||  |/ /  
 |   ___|    ||     \ |   ___||    ||   ___||  |_| ||     \| ||     \  
 |___|     __||__|\__\|______||____||___|   |______||__/\____||__|\__\ 
    |_____|_____                                                       
        __|__   |__  _____   ______  ______  _____   ______  ____   _  
  ___  |     \     ||     | |   ___||   ___||     \ |   ___||    \ | | 
 |___| |      \    ||     \ |   ___| `-.`-. |      \|   ___||     \| | 
       |______/  __||__|\__\|______||______||______/|______||__/\____| 
          |_____|                                                      
______________________________________________________________________"""

SERVER = '100.64.0.1'
FIXES = [
    "cd /usr/lib/ddmesh/",
    "sed -i '/if \[ $minSuccessful -lt 4 ]; then minSuccessful=4; fi/d' ddmesh-gateway-check.sh",
    "sed -i '/minSuccessful=/c\    minSuccessful=1' ddmesh-gateway-check.sh", # change line (in case the user has already done some fix); alternatively: "sed -i s/$(( (numIPs+1)\/2 ))/1/g ddmesh-gateway-check.sh",
]
CHECKS = [
    "cd /usr/lib/ddmesh/",
    "./ddmesh-gateway-check.sh",
]

# Functions
def default_input(prompt, default):
    return input('{} [{}]: '.format(prompt, default)) or default

def prefill_input(prompt, text):
    '''
    Prefill user input with default text.

    https://stackoverflow.com/questions/8505163/is-it-possible-to-prefill-a-input-in-python-3s-command-line-interface
    '''
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def main():
    print(BANNER)
    print('\nFreifunk Dresden Konfigurations-Assistent\nminSuccessFail-Fix v{:s}'.format(VERSION))

    # SSH connection
    username = 'root'
    log_to_file('ssh.log') # set up logging

    # User input
    server = SERVER
    authenticated = False
    print()
    while not authenticated:
        server = prefill_input('IP-Adresse deines Freifunk-Routers: ', server)
        password = getpass('Router-Passwort: ',)

        # Connect
        print('\nVerbindung zum Router wird hergestellt...')
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy()) # Policy to use when connecting to a server that doesn't have a host key in either the system or local HostKeys objects; The default policy is to reject all unknown servers (using 'RejectPolicy').
        try:
            ssh.connect(server, username=username, password=password, timeout=10)
            authenticated = True
        except: #AuthenticationException:
            print('\nVerbindung konnte nicht hergestellt werden. Bitte überprüfe deine Eingaben und ob du mit deinem Freifunk-Router verbunden bist.')

    # Apply fix
    print('Aktualisiere Konfiguration...')
    commands = '; '.join(FIXES)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(commands)
    
    errors = ssh_stderr.readlines()
    error_count = len(errors)
    if errors:
        print()
        for error in errors:
            print('FEHLER: {}'.format(error), end='')
        print()
    else:
        # Run gateway check
        print('Prüfe Verbindung zum Freifunk-Netz (dies kann etwas dauern)...')
        commands = '; '.join(CHECKS)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(commands)
        
        #errors = ssh_stderr.readlines()
        #if errors:
        #    print()
        #    for error in errors:
        #        print('FEHLER: {}'.format(error), end='')

        out_list = ssh_stdout.readlines()
        out = ''.join(out_list)
        if 'no gateway found' in out:
            print('\nFEHLER: Kein Gateway gefunden.')
            error_count += 1
        else:
            print('\nGateway gefunden. Dein Router ist in Kürze wieder online! :)')

    # Disconnect
    print('\nBeende Verbindung zum Router...')
    ssh.close()

    if error_count == 0:
        print('Programm erfolgreich beendet.\n')
    else:
        print('Programm mit {:d} Fehler(n) beeendet.\n'.format(error_count))

if __name__ == '__main__':
    main()