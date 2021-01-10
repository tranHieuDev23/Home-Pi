import os
import time
import subprocess


def get_ip_address():
    process = subprocess.Popen(
        ['ifconfig', 'wlan0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = process.communicate()
    ip_address = None
    for l in out.decode('utf-8').split('\n'):
        l = l.strip()
        if (l.startswith("inet ")):
            ip_address = l.split(' ')[1]
            break
    return ip_address


def is_wifi_connected():
    return get_ip_address() is not None


def discover_ssid():
    process = subprocess.Popen(
        ['sudo', 'iwlist', 'wlan0', 'scan'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = process.communicate()
    ssids = []
    for l in out.decode('utf-8').split('\n'):
        l = l.strip()
        if (l.startswith("ESSID:")):
            left_quote = l.find('"')
            right_quote = l.rfind('"')
            ssids.append(l[left_quote + 1:right_quote])
    return ssids


def wifi_connect(ssid, psk):
    def __write_new_config_file(filename, ssid, psk):
        with open(filename, 'w') as config_file:
            config_file.write('country=US\n')
            config_file.write(
                'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
            config_file.write('update_config=1\n')
            config_file.write('\n')
            config_file.write('network={\n')
            config_file.write('    ssid="' + ssid + '"\n')
            config_file.write('    psk="' + psk + '"\n')
            config_file.write('}\n')
            config_file.close()

    def __run_command(command):
        cmd_result = os.system(command)
        print(command + " - " + str(cmd_result))

    def __backup_old_file(old_config):
        __run_command('sudo cp %s backup.conf' % old_config)

    def __overwrite_old_file(new_config, old_config):
        __run_command('sudo mv %s %s' % (new_config, old_config))

    def __restart_wifi():
        __run_command('sudo wpa_cli -i wlan0 reconfigure')
        time.sleep(20)

    def __restore_old_config(old_config):
        __run_command('sudo mv backup.conf %s' % old_config)

    new_config = 'wifi.conf'
    wpa_supplicant_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"
    __write_new_config_file(new_config, ssid, psk)
    __backup_old_file(wpa_supplicant_conf)
    __overwrite_old_file(new_config, wpa_supplicant_conf)
    __restart_wifi()
    ip_address = get_ip_address()
    if (ip_address is None):
        __restore_old_config(wpa_supplicant_conf)
        __restart_wifi()
    return ip_address
