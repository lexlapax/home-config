#!/usr/bin/env bash
# Disposable container only. All identities and shared secrets here are fictional fixtures.
set -euo pipefail
[[ ${HOME_CONFIG_RADIUS_CONTAINER:-} == 1 && -f /.dockerenv ]] || { echo 'Run only through the CI container job.' >&2; exit 1; }
cp /payload/network/radius-pilot/files.module /etc/raddb/mods-enabled/homeconfig_pilot
sed 's/@LISTEN_ADDRESS@/127.0.0.1/' /payload/network/radius-pilot/pilot.site.in > /etc/raddb/sites-enabled/homeconfig_pilot
rm -f /etc/raddb/sites-enabled/default /etc/raddb/sites-enabled/inner-tunnel
mkdir -p /etc/raddb/homeconfig
cp /fixtures/pilot-users /etc/raddb/homeconfig/pilot-users
chmod 644 /etc/raddb/homeconfig/pilot-users
cat > /etc/raddb/clients.conf <<'CLIENTS'
client loopback_test {
    ipaddr = 127.0.0.1
    secret = homeconfig-test-only
    require_message_authenticator = yes
}
CLIENTS
radiusd -C
radiusd -f > /tmp/pilot-radius.log 2>&1 &
pilot_pid=$!
trap 'kill "$pilot_pid" 2>/dev/null || true' EXIT
request() {
  printf 'User-Name = "%s"\nUser-Password = "%s"\nMessage-Authenticator = 0x00000000000000000000000000000000\n' "$1" "$2" |
    radclient -x -r 1 -t 2 127.0.0.1 auth homeconfig-test-only 2>&1 || true
}
ready=0
for _attempt in 1 2 3 4 5; do
  response=$(request 020000000001 020000000001)
  if [[ $response == *Access-Accept* ]]; then ready=1; break; fi
  sleep 1
done
[[ $ready == 1 ]] || { cat /tmp/pilot-radius.log; printf '%s\n' "$response"; exit 1; }
[[ $response == *'Tunnel-Private-Group-Id = "30"'* ]] || { printf '%s\n' "$response"; exit 1; }
unknown=$(request 020000000002 020000000002)
[[ $unknown == *Access-Reject* ]] || { printf '%s\n' "$unknown"; exit 1; }
wrong=$(request 020000000001 incorrect-test-password)
[[ $wrong == *Access-Reject* ]] || { printf '%s\n' "$wrong"; exit 1; }
echo 'FreeRADIUS parser and packet checks pass: enrolled VLAN accepted; unknown identity and wrong password rejected.'
