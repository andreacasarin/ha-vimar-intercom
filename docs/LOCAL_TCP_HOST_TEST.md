# Experimental local TCP test on an existing Home Assistant host

Branch: `experimental/local-tcp-production-test` in
`andreacasarin/ha-vimar-intercom`. This branch merges upstream main and includes
the experimental TCP transport, VIEW-format instance identity and camera
availability notifications. It contains no development Docker stack or media
address override. No working local call or fully offline support is claimed.
Investigation: [upstream issue #179](https://github.com/ha-vimar/ha-vimar-intercom/issues/179).

The owner must perform the installation and any live tests. The commands below
do not place calls or operate locks. Installation restarts HA, so choose a suitable
maintenance window. Keep the intercom's WAN access allowed for the first trial.

## Check whether this changes the network topology

On the production Docker host, set the actual container name and inspect it:

```bash
HA_CONTAINER=homeassistant
docker inspect --format 'Network mode: {{.HostConfig.NetworkMode}}' "$HA_CONTAINER"
docker inspect --format '{{json .Mounts}}' "$HA_CONTAINER"
```

Linux host networking removes the Docker bridge/NAT variable for this instance.
If the container uses a bridge, this remains a comparison of two Docker network
setups, not a test without Docker NAT. Also record whether HA and the intercom
are on the same subnet or separated by routing/firewall rules. Do not change
production Compose networking as part of the initial installation.

## Install with a private backup

Clone on the production Docker host, not inside the HA container:

```bash
git clone --single-branch --branch experimental/local-tcp-production-test \
  https://github.com/andreacasarin/ha-vimar-intercom.git ha-vimar-local-tcp
cd ha-vimar-local-tcp
```

Use the same shell and the actual `HA_CONTAINER` set above. This copies the
integration files; it does not replace your QR credentials, device name or
saved entry. The stopped-container backup includes the complete HA configuration
and may be large. Keep it private and retain the printed path for rollback.

```bash
set -e
umask 077
backup=$(mktemp -d "$HOME/vimar-local-tcp-backup.XXXXXX")
mkdir "$backup/config"
printf 'Private backup: %s\n' "$backup"
docker stop "$HA_CONTAINER"
docker cp "$HA_CONTAINER:/config/." "$backup/config/"
docker cp ./custom_components/vimar_intercom "$HA_CONTAINER:/config/custom_components/"
docker start "$HA_CONTAINER"
```

If a copy fails, the container may remain stopped. Use the backup to restore it
before continuing. These commands assume `/config/custom_components` is writable
through `docker cp`; a separate read-only integration bind mount must be updated
at its source instead. Prevent a HACS update from replacing the experimental
files during the trial. The branch retains upstream's integration version, so
the version number alone does not identify this installation.

## Establish the cloud baseline, then select local TCP

1. After restart, first confirm the existing entry still registers through cloud
   TLS. Do not replace the entry or generate another QR for this mode switch.
2. Open **Settings → Devices & services → Vimar Intercom → Configure → Network
   and actuators** (wording varies with language).
3. Keep the existing device name, credentials, identity, destinations, video and
   encryption settings. Set the intercom's LAN address, enable **Use local SIP**,
   and choose **Local SIP transport: TCP**. Leave the local UDP-port field at its
   existing value; local TCP connects to the panel's port 5060.
4. Save. The options flow tests registration before saving and reloads the
   integration on success. This is a real registration, not an offline form check.
   Confirm diagnostics show `tcp-local`; a Connected sensor alone is insufficient.
5. Restart HA once more while WAN remains allowed and verify fresh TCP
   registration. This checks reconnection rather than just the options probe.

The setup wizard can fall back to cloud, so use the existing entry's options and
check the actual transport. Keep a private timestamped debug log for each stage.
Do not share raw QR payloads, identity headers, Digest material, tokens or SDP keys.

## Owner-operated call comparison

Only after registration is confirmed, use the already verified indoor/outdoor
call destinations. A reasonable comparison is one ordinary indoor call and one
outdoor view/call, ending each before the next. Do not press door, key, gate,
actuator or unrelated automation controls.

Record registration success, call result, exact SIP error, whether it rang,
whether it was answered, video, receive audio and transmit audio separately.
Ringing alone does not establish two-way audio. If the same immediate 503 occurs
on a Linux host-networked instance, that weakens the Docker Desktop/NAT hypothesis;
it does not identify the PBX policy or rule out subnet/identity differences.

If calls fail with 503 while WAN is allowed, stop there and restore cloud. There
is no benefit to combining that failure with a WAN-blocked test yet. If calls
work locally, coordinate a separate WAN-blocked fresh-start test covering
doorbell events and both media directions. Do not restart the intercom or change
shared equipment as part of this trial.

## Roll back

For a mode-only rollback, disable **Use local SIP** in the integration's network
options and save, then confirm cloud TLS registration. Retain the device name
and pairing identity.

For a code/configuration rollback, use the saved backup path and container name
in the same shell. Stop HA before restoring its config-entry storage:

```bash
docker stop "$HA_CONTAINER"
docker cp "$backup/config/custom_components/vimar_intercom" "$HA_CONTAINER:/config/custom_components/"
docker cp "$backup/config/.storage/core.config_entries" "$HA_CONTAINER:/config/.storage/core.config_entries"
docker start "$HA_CONTAINER"
```

This branch changes existing integration modules and adds no new runtime module,
so copying the backed-up integration restores those files. If your installation
uses a source bind mount, restore that source instead. Restore any WAN block you
changed separately, and verify fresh cloud registration. Keep the full private
backup until the working baseline has been confirmed.
