killall -q chrome dropbox skype icedove thunderbird firefox firefox-esr chromium xchat hexchat transmission steam firejail 
# Remove cache
bleachbit -c adobe_reader.cache chromium.cache chromium.session chromium.history chromium.form_history elinks.history emesene.cache epiphany.cache firefox.cache firefox.crash_reports firefox.url_history firefox.forms flash.cache flash.cookies google_chrome.cache google_chrome.history google_chrome.form_history google_chrome.search_engines google_chrome.session google_earth.temporary_files links2.history opera.cache opera.form_history opera.history &> /dev/null

        sudo systemctl stop wg-quick@wg0
        sudo iptables -F
        #https://github.com/ParrotSec/anonsurf/blob/c5cc0092dc4ffe7d53b2bb42aebdc00e463cfa84/scripts/anondaemon

export BLUE='\033[1;94m'
export GREEN='\033[1;92m'
export RED='\033[1;91m'
export RESETCOLOR='\033[1;00m'


# If tor didn't start, we start it
        # It is used for startup
if command -v pacman > /dev/null; then
  TOR_UID=$(id -u tor)
elif command -v apt > /dev/null; then
  TOR_UID=$(id -u debian-tor)
elif command -v dnf > /dev/null; then
  TOR_UID=$(id -u toranon)
else
  echo "Unknown distro"
  exit
fi

TOR_PORT=`cat /etc/tor/torrc | grep TransPort | cut -d " " -f 2 | cut -d ":" -f 2`
DNS_PORT=`cat /etc/tor/torrc | grep DNSPort | cut -d " " -f 2 | cut -d ":" -f 2`
# Init DNS
echo -e "[$GREEN*${RESETCOLOR}]$BLUE Modified resolv.conf to use Tor${RESETCOLOR}"

#/usr/bin/dnstool address 127.0.0.1
sudo systemctl stop vpn
sudo systemctl restart iptables
sudo systemctl restart tor

sudo systemctl stop wg-quick@wg0
sudo iptables -F

#DNS

sudo chattr -i /etc/resolv.conf
sudo cp /home/nothing/Nextcloud/blog/dns/resolv.conf.tor /etc/resolv.conf
sudo chattr +i /etc/resolv.conf



 # disable ipv6
 echo -e "[$GREEN*${RESETCOLOR}]$BLUE Disabling IPv6 for security reasons${RESETCOLOR}"
sudo /sbin/sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo /sbin/sysctl -w net.ipv6.conf.default.disable_ipv6=1

 #if ! [ -f /etc/network/iptables.rules ]; then
 #       /usr/sbin/iptables-save > /etc/network/iptables.rules
 #       echo -e "[$GREEN*${RESETCOLOR}]$BLUE Saved iptables rules${RESETCOLOR}"
 #fi

 # Making IPTables rules
sudo /usr/sbin/iptables -F
sudo /usr/sbin/iptables -t nat -F

 # set iptables nat
echo -e "[$GREEN*${RESETCOLOR}]$BLUE Configuring iptables rules to route all traffic through tor${RESETCOLOR}"
sudo /usr/sbin/iptables -t nat -A OUTPUT -m owner --uid-owner $TOR_UID -j RETURN

 #set dns redirect
 echo -e " $GREEN+$BLUE Redirecting DNS traffic through tor${RESETCOLOR}"
sudo /usr/sbin/iptables -t nat -A OUTPUT -d 127.0.0.1/32 -p udp -m udp --dport 53 -j REDIRECT --to-ports $DNS_PORT

 #resolve .onion domains mapping 10.192.0.0/10 address space
sudo /usr/sbin/iptables -t nat -A OUTPUT -p tcp -d 10.192.0.0/10 -j REDIRECT --to-ports $TOR_PORT
sudo /usr/sbin/iptables -t nat -A OUTPUT -p udp -d 10.192.0.0/10 -j REDIRECT --to-ports $TOR_PORT

 #exclude local addresses
 for NET in $TOR_EXCLUDE 127.0.0.0/9 127.128.0.0/10; do
        sudo  /usr/sbin/iptables -t nat -A OUTPUT -d $NET -j RETURN
        sudo  /usr/sbin/iptables -A OUTPUT -d "$NET" -j ACCEPT
done

 #redirect all other output through TOR
sudo /usr/sbin/iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports $TOR_PORT
#/usr/sbin/iptables -t nat -A OUTPUT -p tcp -j REDIRECT --to-ports $TOR_PORT
sudo /usr/sbin/iptables -t nat -A OUTPUT -p udp -j REDIRECT --to-ports $TOR_PORT
sudo /usr/sbin/iptables -t nat -A OUTPUT -p icmp -j REDIRECT --to-ports $TOR_PORT

 #accept already established connections
sudo /usr/sbin/iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

 #allow only tor output
 echo -e " $GREEN+$BLUE Allowing only tor to browse in clearnet$RESETCOLOR"
sudo /usr/sbin/iptables -A OUTPUT -m owner --uid-owner $TOR_UID -j ACCEPT
sudo /usr/sbin/iptables -A OUTPUT -j REJECT

 # TESTING block all incoming traffics
 # https://trac.torproject.org/projects/tor/wiki/doc/TransparentProxy
sudo /usr/sbin/iptables -A INPUT -m state --state ESTABLISHED -j ACCEPT
sudo /usr/sbin/iptables -A INPUT -i lo -j ACCEPT

sudo /usr/sbin/iptables -A INPUT -j DROP

 ### *filter FORWARD
sudo /usr/sbin/iptables -A FORWARD -j DROP

 ### *filter OUTPUT
sudo /usr/sbin/iptables -A OUTPUT -m state --state INVALID -j DROP
sudo /usr/sbin/iptables -A OUTPUT -m state --state ESTABLISHED -j ACCEPT

 # Allow Tor process output
sudo iptables -A OUTPUT -m owner --uid-owner $TOR_UID -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -m state --state NEW -j ACCEPT

 # Allow loopback output
sudo /usr/sbin/iptables -A OUTPUT -d 127.0.0.1/32 -o lo -j ACCEPT
 # iptables 1.8.5 can't use -o with input
 # /usr/sbin/iptables -A INPUT -d 127.0.0.1/32 -o lo -j ACCEPT

 # Tor transproxy magic
sudo /usr/sbin/iptables -A OUTPUT -d 127.0.0.1/32 -p tcp -m tcp --dport $TOR_PORT --tcp-flags FIN,SYN,RST,ACK SYN -j ACCEPT

     #allow local network traffic:
sudo /usr/sbin/iptables -A INPUT -m iprange --src-range 192.168.0.0-192.168.255.255 -j ACCEPT
sudo /usr/sbin/iptables -A INPUT -m iprange --src-range 172.16.0.0-172.31.255.255 -j ACCEPT
sudo /usr/sbin/iptables -A INPUT -m iprange --src-range 10.0.0.0-10.255.255.255 -j ACCEPT
sudo /usr/sbin/iptables -A INPUT -m iprange --src-range 127.0.0.0-127.255.255.255 -j ACCEPT

sudo /usr/sbin/iptables -A OUTPUT -m iprange --dst-range 192.168.0.0-192.168.255.255 -j ACCEPT
sudo /usr/sbin/iptables -A OUTPUT -m iprange --dst-range 172.16.0.0-172.31.255.255 -j ACCEPT
sudo /usr/sbin/iptables -A OUTPUT -m iprange --dst-range 10.0.0.0-10.255.255.255 -j ACCEPT
sudo /usr/sbin/iptables -A OUTPUT -m iprange --dst-range 127.0.0.0-127.255.255.255 -j ACCEPT