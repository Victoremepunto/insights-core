import doctest
from insights.parsers import etc_udev_rules
from insights.parsers.etc_udev_rules import UdevRules40Redhat
from insights.tests import context_wrap

UDEV_RULES_CONTENT = """
# do not edit this file, it will be overwritten on update

# CPU hotadd request
SUBSYSTEM=="cpu", ACTION=="add", TEST=="online", ATTR{online}=="0", ATTR{online}="1"

# Memory hotadd request
SUBSYSTEM!="memory", GOTO="memory_hotplug_end"
ACTION!="add", GOTO="memory_hotplug_end"
PROGRAM="/bin/uname -p", RESULT=="s390*", GOTO="memory_hotplug_end"

ENV{.state}="online"
PROGRAM="/bin/systemd-detect-virt", RESULT=="none", ENV{.state}="online_movable"
ATTR{state}=="offline", ATTR{state}="$env{.state}"

LABEL="memory_hotplug_end"

# reload sysctl.conf / sysctl.conf.d settings when the bridge module is loaded
ACTION=="add", SUBSYSTEM=="module", KERNEL=="bridge", RUN+="/usr/lib/systemd/systemd-sysctl --prefix=/proc/sys/net/bridge"

# load SCSI generic (sg) driver
SUBSYSTEM=="scsi", ENV{DEVTYPE}=="scsi_device", TEST!="[module/sg]", RUN+="/sbin/modprobe -bv sg"
SUBSYSTEM=="scsi", ENV{DEVTYPE}=="scsi_target", TEST!="[module/sg]", RUN+="/sbin/modprobe -bv sg"

# Rule for prandom character device node permissions
KERNEL=="prandom", MODE="0644"


# Rules for creating the ID_PATH for SCSI devices based on the CCW bus
# using the form: ccw-<BUS_ID>-zfcp-<WWPN>:<LUN>
#
ACTION=="remove", GOTO="zfcp_scsi_device_end"

#
# Set environment variable "ID_ZFCP_BUS" to "1" if the devices
# (both disk and partition) are SCSI devices based on FCP devices
#
KERNEL=="sd*", SUBSYSTEMS=="ccw", DRIVERS=="zfcp", ENV{.ID_ZFCP_BUS}="1"

# For SCSI disks
KERNEL=="sd*[!0-9]", SUBSYSTEMS=="scsi", ENV{.ID_ZFCP_BUS}=="1", ENV{DEVTYPE}=="disk", SYMLINK+="disk/by-path/ccw-$attr{hba_id}-zfcp-$attr{wwpn}:$attr{fcp_lun}"


# For partitions on a SCSI disk
KERNEL=="sd*[0-9]", SUBSYSTEMS=="scsi", ENV{.ID_ZFCP_BUS}=="1", ENV{DEVTYPE}=="partition", SYMLINK+="disk/by-path/ccw-$attr{hba_id}-zfcp-$attr{wwpn}:$attr{fcp_lun}-part%n"

LABEL="zfcp_scsi_device_end"
""".strip()

SAMPLE_INPUT = """
# do not edit this file, it will be overwritten on update
# CPU hotadd request
SUBSYSTEM=="cpu", ACTION=="add", TEST=="online", ATTR{online}=="0", ATTR{online}="1"

# Memory hotadd request
SUBSYSTEM!="memory", ACTION!="add", GOTO="memory_hotplug_end"
PROGRAM="/bin/uname -p", RESULT=="s390*", GOTO="memory_hotplug_end"

LABEL="memory_hotplug_end"
""".strip()


def test_udev_rules():
    result = UdevRules40Redhat(context_wrap(UDEV_RULES_CONTENT))
    for line in ['SUBSYSTEM=="cpu", ACTION=="add", TEST=="online", ATTR{online}=="0", ATTR{online}="1"',
                 'SUBSYSTEM!="memory", GOTO="memory_hotplug_end"',
                 'ACTION!="add", GOTO="memory_hotplug_end"']:
        assert line in result.lines


def test_documentation():
    env = {'udev_rules': UdevRules40Redhat(context_wrap(SAMPLE_INPUT))}
    failed_count, tests = doctest.testmod(etc_udev_rules, globs=env)
    assert failed_count == 0