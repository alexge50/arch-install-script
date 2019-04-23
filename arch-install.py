from os import system
import subprocess

config = {
    'SWAP': True
}

def capture_system(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()

    return output

def total_ram():
    output = str(capture_system('cat /proc/meminfo'))
    MemTotal = output.split('\n')[0]
    MemTotal = MemTotal.split(' ')[-2]

    return int(MemTotal)

def chroot_system(command): 
    system(f'arch-chroot /mnt {command}')

system("loadkeys us")
system("timedatectl set-ntp true")

# partitioning
size = int(capture_system('fdisk -s /dev/sda'))
used_size = 0

system("parted -s /dev/sda -- mklabel msdos mkpart primary ext4 1Mib 513Mib")
system("mkfs.ext4 /dev/sda1")
used_size += 513 * 1024
# SWAP
if config['SWAP']:
    ram = total_ram()
    system(f"parted -s /dev/sda -- mkpart primary linux-swap {used_size}Kib {used_size + ram}Kib")
    used_size += ram + 1
    system("mkswap /dev/sda2 && swapon /dev/sda2")

root = (size - used_size) // 2
print(root)
system(f"parted -s /dev/sda -- mkpart primary ext4 {used_size}Kib {used_size + root}Kib")
used_size += root + 1
system("mkfs.ext4 /dev/sda3")

print(used_size)
system(f"parted -s /dev/sda -- mkpart primary ext4 {used_size}Kib 100%")
system("mkfs.ext4 /dev/sda4")

system("mount /dev/sda3 /mnt")
system("mkdir /mnt/home && mount /dev/sda4 /mnt/home")
system("mkdir /mnt/boot && mount /dev/sda1 /mnt/boot")

# mirror list
mirrors = """
Server = http://mirrors.atviras.lt/archlinux/$repo/os/$arch
Server = http://archlinux.cu.be/$repo/os/$arch
Server = http://mirrors.arnoldthebat.co.uk/archlinux/$repo/os/$arch
Server = http://archlinux.nullpointer.io/$repo/os/$arch
Server = http://archlinux.mirror.wearetriple.com/$repo/os/$arch
Server = http://www.gtlib.gatech.edu/pub/archlinux/$repo/os/$arch
Server = http://mirror.onet.pl/pub/mirrors/archlinux/$repo/os/$arch
Server = http://mirrors.evowise.com/archlinux/$repo/os/$arch
"""

with open("/etc/pacman.d/mirrorlist", 'w') as f:
    f.write(mirrors)

system("pacman --noconfirm -Sy archlinux-keyring")
system("pacstrap /mnt base base-devel")
system("genfstab -U /mnt >> /mnt/etc/fstab")

chroot_system("ln -sf /usr/share/zoneinfo/Europe/Bucharest /etc/localtime")
chroot_system("hwclock --systohc")
chroot_system("sed -i -e 's/#en_US.UTF-8/en_US.UTF-8/g' /etc/locale.gen")
chroot_system("locale-gen")
chroot_system('echo "LANG=en_US.UTF-8" > /etc/locale.conf')
chroot_system('echo "purple-unicorn" > /etc/hostname')
chroot_system('mkinitcpio -p linux')
chroot_system('echo "root\nroot\n" | passwd')
chroot_system("pacman -S amd-ucode intel-ucode grub")
chroot_system("grub-install --target=i386-pc /dev/sda")
chroot_system("grub-mkconfig -o /boot/grub/grub.cfg")

#system("unmount -R /mnt")
#system("reboot")
