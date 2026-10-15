# Fully local support investigation: Tab 7S Up (40517)

## Paused handoff — 2026-10-15

**The owner has paused this investigation. Local TCP registration works in the
experimental setup; real local calls fail. Fully offline operation has not been
established.** This is a starting point for further investigation, not a working
local-support release or a conclusion that local support can never work.

Shareable branch:
[`andreacasarin/ha-vimar-intercom:experimental/local-tcp-production-test`](https://github.com/andreacasarin/ha-vimar-intercom/tree/experimental/local-tcp-production-test).
Feature request and field findings:
[upstream issue #179](https://github.com/ha-vimar/ha-vimar-intercom/issues/179).
Working-cloud compatibility report:
[upstream issue #172](https://github.com/ha-vimar/ha-vimar-intercom/issues/172).

Hardware: Elvox Tab 7S Up 40517; SW 2.1.0203 [prod], rev67313-2123
(2025-06-10), FW 1.06, HW 00-02. The branch merges upstream main at
`c30f419` (1.0.23). Its integration version is unchanged; identify this branch
by Git revision rather than the version number alone.

### Reusable implementation

- Opt-in local TCP in setup and network options, using the existing account's
  local proxy/domain. UDP remains the default for existing local entries;
  cloud TLS retains its existing path.
- TCP Route/Contact/Via handling, VIEW-style Mobile-IMEI/Contact instance
  alignment, registration lifetime, reliable stream framing, Digest handling,
  reconnect/renewal and no UDP retransmission or runtime cloud fallback in TCP
  mode. This reuses the established outbound TCP stream, without a separate
  inbound TCP listener.
- Camera availability notifications following registration state changes.
- Synthetic loopback tests for registration, 401/407 challenges, framing,
  outgoing/incoming dialogs, routing, reconnect and identity preservation.

Start in `custom_components/vimar_intercom/{config_flow,options_flow,runtime,sip_client}.py`.
The camera fix is in `camera.py`. See `tests/test_local_tcp.py`,
`tests/test_config_flow_registration.py`, `tests/test_transport_probe.py`,
`tests/test_config_flow_steps.py` and `tests/harness/` for reproducible protocol tests.
No Docker development stack, Docker Desktop media-address override, firmware,
app binaries, captures, keys or installation credentials are included here.
The separate general-purpose Docker development contribution is
[upstream PR #183](https://github.com/ha-vimar/ha-vimar-intercom/pull/183).

Last code validation before this documentation-only handoff:
**2,347 passed, 1 skipped, 103 deselected; 97.11% line/branch coverage; Ruff clean.**
The full run used synthetic peers and excluded live hardware, media and browser
markers:

```bash
python -m pytest tests -m 'not live and not media and not browser' \
  --cov=custom_components/vimar_intercom --cov-branch --cov-report=term-missing
ruff check .
```

### Confirmed findings and limits

| Test | Result | What remains unknown |
|---|---|---|
| Cloud integration baseline | Registration/renewal, phonebook, indoor ringing, outdoor video and listening work | Complete two-way audio and offline acceptance were not established |
| Local UDP REGISTER | SIP 503 denial | Response alone does not distinguish identity and transport policy |
| Local TCP with separate development pairing | Authentication/registration succeeded, including HA restart | Registration does not establish call permissions |
| Local TCP indoor/outdoor INVITE with confirmed destinations | Immediate 503, approximately 5–8 ms, without a new 401/407 challenge | Exact PBX policy producing rejection |
| Local HTTP phonebook on port 80 | Connection refused | Availability of other supported local interfaces |
| Official iPhone VIEW, intercom WAN allowed | Cloud TLS 1.3 signaling on TCP 7042, cloud API TLS on TCP 443; UDP to the public server with patterns consistent with audio/video | Encrypted REGISTER/INVITE/SDP/PUBLISH contents |
| Official VIEW, intercom WAN blocked by owner | Indoor ring only; outdoor call failed without a specific error. Fresh cloud TLS plus 687 outgoing and zero returning UDP datagrams from the media server; no direct intercom traffic observed | Firewall enforcement, IPv6 coverage, retained sessions and how the indoor ring was delivered |
| Production host topology | Owner reported a Docker bridge network | No production-host or Linux host-network local call test was performed in this investigation |
| Firmware/updater static analysis | Update archives extracted; Tab Up filesystem payloads remain encrypted | Matching readable PBX implementation and firmware key |

The successful WAN-enabled outdoor-call capture had 502 returning UDP datagrams
from the public server. Other than UDP 5060 signaling, UDP payloads were not
saved: audio/video/RTCP classifications are metadata-based inferences.
No direct phone/intercom local fallback was observed in these filtered captures.
The phone and HA host were not both isolated from WAN, and existing intercom
cloud state was not conclusively eliminated. **Indoor ringing is not proof of
offline calling.** TLS was not intercepted or weakened.

The development test used Docker Desktop and routed private subnets. Docker/NAT,
subnet policy, identity binding, presence publication, cached authentication,
call identifiers and SDP differences remain hypotheses. An explicit fast 503
is different evidence from an accepted call with missing media; neither a port
forward nor a successful REGISTER identifies a fix for the former.

### Follow-up: development QR and same-VLAN VIEW captures (2026-10-15)

The saved development pairing QR was decoded offline: **`CLOUD=1`** (home first,
then cloud). This rules out `CLOUD=2` for that QR, not for every device pairing;
the active iPhone pairing's policy was not independently checked. Neither the
token nor other QR fields were published.

Two further owner-operated outdoor-call captures used official iPhone VIEW
2.18.0 with the phone reported on the intercom VLAN and internet access allowed
for both. Docker remained stopped. Both showed fresh TLS 1.3 cloud SIP on TCP
7042, cloud API TLS on TCP 443 and call-shaped UDP to the public SIP server:

| Same-VLAN capture | Outgoing UDP | Incoming UDP | Direct intercom traffic / SIP 5060–5061 |
|---|---|---|---|
| First call | 246 | 377 | None captured |
| Repeat | 437 | 678 | None captured |

The observed private TCP source was in the intercom's address range; the second
phone-side address seen during an earlier Wi-Fi-restricted attempt did not
appear. VLAN membership, subnet mask and client isolation were not independently
inspected at the router/AP. UDP counts describe flows to/from the public server,
not decoded RTP. Metadata patterns suggest bidirectional audio and incoming
video; TLS and the absence of saved media payloads limit deeper comparison.

The preceding attempt with phone Wi-Fi internet denied failed to establish
cloud SIP and showed cloud API traffic from a second source of unconfirmed
interface origin. It is not a clean same-VLAN/internet-allowed baseline.

These repeats show that same-VLAN placement did not make VIEW select a direct
local call path in the tested configuration. They do not complete the proposed
integration/plain-client test without Docker NAT or prove local support
impossible. Investigation is paused again after these limited follow-ups;
captures remain private and Docker remains stopped.

### Useful next evidence

1. A demonstrated official VIEW local call on comparable hardware with verified
   WAN denial and media paths, preferably from the same subnet.
2. A supported provisioning/connection setting, app-provided SIP diagnostics,
   or vendor documentation identifying local call permissions and initialization.
3. A controlled Linux host-network comparison that holds identity, destinations
   and other settings constant, to test the Docker Desktop/bridge hypothesis.
4. An authorized matching readable firmware/configuration export or relevant
   vendor sources exposing the PBX routing/rejection predicates.

The inspected Android VIEW artifact supplies implementation leads, not proof
of iPhone behavior or a working official local call. Presence, authorization,
Call-ID and SDP differences should be tested separately after identifying a
viable local baseline; do not send guessed vendor messages or actuator tokens.
Firmware modification is not justified by the available evidence.

### Pause and resumption

Both Mac development projects are stopped, with containers and state retained.
Branches, private backups, firmware-analysis artifacts and USB captures remain
on the owner's workstation outside public contributions. No production HA,
intercom setting or firewall rule was changed by the pause operation. The
owner's earlier WAN block was not changed or independently verified during pause.
No new calls or actuators were triggered.

Do not automatically resume live tests. If useful new evidence arrives, first
agree a controlled trial and retain the working cloud configuration and rollback.
[Local TCP host test](LOCAL_TCP_HOST_TEST.md) contains the previously prepared
backup/install/rollback procedure; it has **not** been executed on production by
this investigation. The offline acceptance procedure later in this document
remains unmet.

The following sections retain the historical static-analysis notes and protocol
comparison. Statements scoped to those earlier reviews should not be read as
new live-test results. Firmware, credentials, private paths and raw evidence
must remain private; use synthetic identities in public reproductions.

## Firmware package findings

An initial extension-based search missed the `.swu` and `.enc` files in the
workspace's `sources` directory. A subsequent directory inventory found them.
Static inspection and safe extraction were completed on 2026-10-10.

- `TABSUP2F_1.6.0003.swu` is a 121,430,016-byte SVR4 CRC CPIO archive.
  Its SHA-256 is
  `84cce1ce05e8d3434241eef1e52e856890e163078983798f700a941081d9d961`,
  matching the supplied checksum file and the second package copy.
- All five archive entries passed CPIO checksum verification. They are
  `sw-description`, `sw-description.sig` and three encrypted images. There
  are no additional cleartext executables, scripts, keys or certificates.
- The manifest identifies version `1.6.0003` for `TABSUP2F [rk-pi-2f]` and
  explicitly includes hardware `CMP-RK_00-02_40517`. The release notes name
  release `1.6.0303`, dated 2023-08-28. These differing version labels do not
  establish that the package contains the installed SW 2.1.0203 (2025 build).
- The manifest describes A/B `rootfs` and `fit_image` partitions, plus a
  rescue image installed only if its version is higher. All three images
  have `encrypted = true`; their names suggest SquashFS and ext4, but the
  inner filesystem formats have not been confirmed by decryption.
- Payload sizes are 98,746,384 bytes (rootfs), 9,437,200 bytes (FIT image)
  and 13,242,384 bytes (rescue). Each SHA-256 matches the manifest. Entropy
  is approximately 8 bits per byte and each size is a multiple of 16.
  The two encrypted FIT images share their first 1,024 bytes; this alone
  does not establish the key, IV or encryption parameters.
- Neither a key nor an `ivt` override appears in the cleartext manifest.
  No `Salted__` marker or either SIP denial phrase was found in the encrypted
  payloads. Absence of plaintext strings in ciphertext says nothing about
  which SIP components the decrypted filesystem contains.
- Standard SWUpdate documentation describes AES-CBC image encryption with
  a separately supplied key and IV: [SWUpdate encryption documentation](https://sbabic.github.io/swupdate/2020.11/encrypted_images.html).
  That is the likely scheme here, not verification of this vendor's updater
  implementation. The 512-byte signature cannot be authenticated without
  the trusted verification key; checksum agreement is not signature validation.

Extracted files and a JSON inventory with hashes, sizes and archive offsets
are kept in a private analysis directory outside the integration Git checkout.
The originals were not modified. No firmware code was executed.

**Next evidence required:** an authorized decrypted filesystem or the updater's
AES key/IV configuration, preferably accompanied by an image matching the
installed software build. A read-only filesystem export could also expose the
updater configuration and SIP services. Obtaining it from the live device is
a separate step; this analysis did not attempt device access. SIP credentials
are not known to be the firmware decryption key. Until a relevant filesystem
is readable, neither the rejecting code path nor a viable local call route
can be established from this package.

### Official 2025 package search

The [official 40517 product page](https://www.vimar.com/en/int/catalog/product/index/code/40517)
links release `02.01.0303`, dated 2025-07-07. It was downloaded for static
inspection only. The ZIP contains release notes, `TABSUP2F_2.1.0003.swu`
and its checksum file. The SWU hash matches the supplied checksum:
`cb5c34717d271af5e6eabbb5ca6046a16916410e09dcae1ae1b48af08f88b8d9`.
All five CPIO entries passed checksum verification; the three payload hashes
match its manifest. Hardware compatibility includes `CMP-RK_00-02_40517`.

Its rootfs and FIT payloads are still encrypted, and its rescue image is
byte-identical to the 2023 package's rescue image. The release notes and
manifest do not identify `rev67313-2123` or explain the difference between
the owner's `2.1.0203` and the public release's `2.1.0303`. No exact public
download was found for the owner's version/build. This is a 2.1-family
analysis candidate, not a confirmed copy of the installed software.
The package was not installed and the device was not contacted.

### PC updater inspection

Static inspection on 2026-10-11 of the [official SaveProg](https://www.vimar.com/en/int/save-prog-5346122.html)
3.15.5.0 installer recovered
`SaveProg.exe` and `FWUpdate.exe` without running Vimar code. Published-method
tables and disassembly establish that SaveProg's `ActionReadAndExportExecute`,
`ActionExportndvdbsExecute` and `ActionSaveAndExportExecute` handlers are empty
in this build. FWUpdate's `BitBtnDecryptClick` handler is also empty. Those
names therefore do not establish a usable readback or decryption operation.

SaveProg's nonempty `BitBtnReadFlashClick` belongs to a form captioned
"Reading / Writing Files 7311". Its selectable areas include parameters,
icons, multimedia and PSOC files; this is not evidence of a 40517 filesystem
export. Configuration and phonebook exports must be distinguished from full
firmware readback. Generic ZIP/decryption and Rijndael library symbols are
present, but no SWUpdate key or verified SWUpdate decryption path was found.
A bounded check of embedded hex candidates did not match presumed filesystem
headers; binary or derived keys and other encryption formats remain possible.

The installer's `FWUpdate.fwv` is an unencrypted Abbrevia compound archive.
All 117 file entries were decompressed with their declared sizes verified;
their names and index do not identify a matching 40517/TABSUP SWUpdate image.
The 40517 settings/phonebook defaults decode from Base64/zlib into SQLite
databases. A template `CLOUD=0` value does not establish a local SIP route:
these defaults are not the running configuration, and no explicit SIP/PBX
transport policy or firmware key was identified in them.

The [official FWUpdate manual](https://www.vimar.com/en/int/article/download/file?hash=2b6a69066a20f868a0aeb43a52b1522a&id=5953&type=attachment)
documents erase/write/verify operations, not a firmware export.
The [40517 manual](https://www.vimar.com/irj/go/km/docs/z_catalogo/DOCUMENT/49401466B0_02_MI_40517_P624.113769.pdf)
documents USB-C configuration and updates
via SaveProg, not a shell or filesystem dump. USB readback remains unverified;
do not enter an update or erase workflow to obtain a backup. These results do
not justify firmware modification or a new integration transport.

### Updater cryptographic call paths

Further static analysis on 2026-10-12 recovered FWUpdate's embedded
passphrase-to-MD5 derivation and traced its 16-byte output into
`BFEncryptStringCBCEx` with the decrypt flag. That routine Base64-decodes
records and invokes the bundled LockBox Blowfish-CBC implementation.
The callers bypass this decryption for `.s19`, `.s28` and `.hex` files.
The separate decrypt-button handler remains empty.

A private Python implementation matched the binary's cipher behavior and
decrypted all 75 bundled `.z19` files. Every one of their 245,874 Intel HEX or
S-record checksums passed. This confirms recovery for that updater format;
it does not establish a key for the Tab 7S Up's Linux update package.
Reconstructing the records yielded 7,507,331 bytes of firmware segments for
other models. Several include `40517` in model-name tables, but no matching
Tab Linux filesystem or SWUpdate handler was identified.

The recovered key failed IV-independent presumed filesystem-header checks
against all six encrypted payloads across the 2023 and 2025 SWU packages
when used as a direct AES-128-CBC key. An expanded scan of the extracted
installer and reconstructed segments tested 61 hex-encoded AES-size
candidates and found no header match. These checks depend on direct
AES-CBC filesystem encryption; they cannot exclude other derivations or
packaging. Both SWU filesystems remain encrypted.

SaveProg's traced application MD5 path streams a file in 1,024-byte chunks
and returns its digest. The AES/Rijndael cross-references found in both
executables remain in library code or class tables; no application call
to them was identified. Static direct-call and relocation inspection does
not exclude every indirect or dynamically selected path. The evidence
supports investigating the Linux updater or an official recovery/source
package next, rather than treating this legacy key as the SWUpdate key.

Keys, passphrases, decrypted firmware and detailed disassemblies remain
private outside the integration checkout. No Vimar code was executed and
the intercom was not contacted or changed.

### Official recovery and source-package search

Public manufacturer downloads and source-disclosure searches on 2026-10-12
did not yield a 40517 recovery image or updater source/build bundle. The
[40515 product download](https://www.vimar.com/en/int/catalog/product/index/code/40515)
contains the same `TABSUP2F_2.1.0003.swu` as the 40517 download, confirmed by
SHA-256. It supplies no new readable payload or key material.

Static extraction of the official
[Video Door IP Manager](https://www.vimar.com/en/int/video-door-ip-manager-manuals-and-configuration-13380122.html)
0.78.10 installer revealed a recovery wizard and firmware downloader. Its
application constructs a public manifest URL on Vimar's update server; a
credential-free read returned firmware entries for older IP products,
including Tab 7S 40607, but no 40517/40515/TABSUP2F entry or source bundle.
The listed 40607 package passed its supplied checksums but contains five
opaque `.exp` images. Their high entropy and 16-byte alignment are consistent
with encryption; their cipher, filesystem formats and relevance to 40517
remain unconfirmed. No updater or device-discovery workflow was executed.

The candidate scan expanded to 87 hex-encoded AES-size values across both
PC updaters and the reconstructed legacy images, with no presumed Tab Up
filesystem-header match. The direct AES-CBC assumptions still apply.
Both available Tab Up SWU filesystems remain encrypted.

An official source-availability notice was found for Vimar access points,
not the Tab intercom; it cannot establish availability of Tab sources or
decryption secrets. The next concrete manufacturer request is for an
official matching recovery image/offline unpacker and corresponding
component sources, vendor patches and updater build/install configuration.
Vimar's [technical-support route](https://www.vimar.com/en/int/contact/form/request?type=technic-support)
requires MyVIMAR login. No account action or support submission was made.

## Static integration review

Reviewed checkout: baseline commit `98cf288`.

- `config_flow._test_sip_registration` opens a UDP socket to the local SIP
  port. It sends the Vimar-compatible `const.USER_AGENT`, device name, optional
  `Mobile-IMEI` and `+sip.instance`, and handles a Digest challenge. It does
  not test TCP, calls or media. A 503 before a challenge does not test the
  password; a 503 after authentication still does not identify the policy.
- `config_flow._probe_transport` selects between local UDP and cloud TLS
  based on registration. Registration success is not proof of call routing
  or offline support.
- `runtime.configure` and `sip_client.connect` use the boolean
  `use_local_udp`. False selects cloud DNS resolution and TLS, including the
  cloud domain, Route and Contact construction. Pointing the cloud proxy at
  the intercom is not equivalent to adding local TCP support.
- `sip_client._transport`, `_contact_hdr`, `_route_line`, `_simple_contact`
  and dialog routing must stay consistent with any future local transport.
  Adding TCP requires more than opening a stream socket. Stream framing
  already exists in `sip_message._split_stream`.
- `sip_client._remote_media` reads the peer's SDP addresses and currently
  rejects addresses outside the LAN in local UDP mode. A future local TCP
  mode should preserve that protection. SIP on the LAN alone does not prove
  that RTP/SRTP stays on the LAN.
- `hub._auto_startup` calls `do_connect_profiles` in cloud mode;
  `sip_client.do_connect_profiles` uses a cloud HTTPS endpoint. A local path
  must not depend on this operation or on cloud push delivery for ringing.
- `rest_client` implements HTTP Digest phonebook/status endpoints on port
  80; `cloud_phonebook` is a separate HTTPS cloud path. Neither supplies a
  demonstrated alternative local call/media interface for this installation.

The only justified integration change at this stage is a neutral diagnostic
for local UDP 503 responses. Regression tests cover rejection both before
and after a Digest challenge. This does not enable offline support.

## Analysis procedure for decrypted or newer images

1. Keep the original outside the Git checkout in a private analysis directory.
   Record SHA-256, byte length, origin and any supplied release metadata.
   Match it to the reported build; do not assume an update package contains
   every installed component or the device's current configuration.
2. Inspect magic bytes and container headers before extraction. Identify
   archive/compression, partition images, filesystem types, signatures and
   encryption. Preserve offsets and hashes for every extracted layer.
   Extract as an unprivileged user in a disposable environment, without
   running firmware executables or update scripts. List archive paths first
   and reject paths escaping the extraction directory.
3. Inventory startup scripts, service definitions, executable formats and
   CPU architectures, PBX/SIP binaries, shared libraries and configuration
   templates. Search for the exact denial strings, the app-upgrade denial,
   transport settings, REGISTER/INVITE handlers, Digest handling, pairing
   storage, push profiles and cloud routing.
4. For each rejection string, trace references in the relevant executable
   or library to its caller and branch predicates. Record component hash,
   file offset/virtual address and surrounding control flow. A string match
   alone does not identify the running rejection path. Determine whether
   transport, User-Agent/version, identity, destination, role or cloud
   registration state controls the decision.
5. Trace successful registration into contact storage and incoming/outgoing
   routing, including media relay selection. Look for an existing supported
   local setting or interface before proposing an integration change.
   Distinguish compiled defaults from runtime values and check whether
   provisioning replaces them.

If the relevant payload is encrypted or missing, document that limit and
request the corresponding authorized image or configuration export. Do not
infer a firmware defect or propose a patch from missing evidence.

## Capture comparison if static analysis leaves routing unresolved

Use an authorized router/AP mirror or capture point that sees both the official
VIEW app and the intercom. A capture on the Home Assistant host alone generally
cannot observe traffic between two other switched LAN devices. Keep raw
captures private: Digest responses, identity headers, SDP crypto keys and
media are sensitive even when no plaintext password appears.

Compare app and integration transport, destination, SIP URI/domain, Via,
Contact, Route/Record-Route, identity and User-Agent headers, challenge handling,
registration lifetime, incoming delivery and SDP/media endpoints. If TLS hides
SIP, network metadata still establishes destinations but not header parity;
do not weaken the production TLS connection to obtain plaintext.

Before live registration probes, back up the working HA configuration privately
and arrange a maintenance window: a probe using the same identity can replace
the running binding, even without placing a call. Re-registering the production
client is necessary to restore that binding. Do not overwrite the cloud config
entry to experiment with a transport.

## Offline acceptance and rollback

Run this only after a concrete local candidate exists and the owner authorizes
the specific live call/view actions required by the repository safety rules.
Never exercise door/gate actions as part of this test.

1. Save the integration version, complete HA config entry and options privately;
   retain the working cloud deployment. Record how to restore both the deployed
   files and config, and how to remove temporary firewall rules.
2. Block WAN for both the intercom and the HA host, covering IPv4/IPv6 and every
   egress path while retaining LAN access. Verify denial with firewall counters
   and a capture at the enforcement point. For the app comparison, disable
   cellular fallback and other VPN/egress routes too.
3. End existing sessions and restart HA with WAN already blocked. Require a
   fresh local registration exchange and success response. A cached registered
   flag, still-open cloud socket or renewal alone is not a pass. Record granted
   expiry and continue beyond the previous registration/session lifetime.
4. Have the owner ring the physical bell. Verify a new incoming SIP event and
   HA doorbell event. A simulated HA ring does not count. Verify outdoor video,
   listening and microphone transmission, with a person at the outdoor panel
   confirming audible speech in both directions.
5. Repeat after closing calls and restarting HA again with WAN blocked. Verify
   media destinations and packet paths stay local and no cloud bootstrap is
   required. Restart the intercom only with separate owner approval if needed
   to rule out retained device-side cloud state.
6. Record pass/fail/not-tested separately for fresh registration, real ring,
   video, receive audio and transmit audio, with timestamps, transport and
   private evidence references. List any cloud dependencies still exercised,
   including pairing/provisioning, phonebook refresh and push delivery.
7. Remove temporary blocks, restore cloud files/config if changed, restart HA
   and confirm fresh cloud registration. Restore any binding displaced by a
   probe. Verify the baseline with owner-approved call/view checks.

Implementation gate: add a local transport/interface only after firmware or
app evidence identifies a viable call path. Test its headers, authentication,
stream framing, routing, reconnect/renewal and LAN media restrictions with
synthetic identities and fake peers. Consider firmware modification only
after documenting the exact policy and why integration-side changes cannot
satisfy it. Flashing remains a separately authorized action.

## VIEW TCP comparison and experimental integration support (2026-10-13)

The official store identifies VIEW as `com.vimar.view`. Static inspection used a
mirror artifact with Android manifest version 2.18.0 (1261002152). All three APK
signatures verified with the same certificate, but the publisher certificate
was not independently compared with an owner-exported Google Play copy. These
are findings in that inspected build, not measurements of the owner's app or
intercom. The private analysis retains hashes and source anchors; no APK,
decompiled source, embedded keys or owner credentials belong in this repository.

| Area | Inspected VIEW implementation | Integration after this change |
|---|---|---|
| Local transport | TCP; UDP disabled | Explicit `local_transport=tcp`; existing entries keep UDP |
| Cloud transport | TLS | Existing TLS implementation and 2FV2 default preserved |
| SIP identity/domain | Home uses ID/PWD and DOMAIN/PROXY; cloud uses CDOMAIN/CPROXY | Existing runtime domain selection reused for local TCP |
| Account route | Selected proxy is the account's server and route | Local TCP REGISTER and initial requests carry a local proxy Route with `transport=tcp;lr` |
| Local registration lifetime | 900 seconds | TCP Contact requests 900 seconds; existing grant-aware renewals remain |
| Device headers and User-Agent | Device name/identity, Vimar project/AppVer/ProtVer | Existing identity and Vimar-compatible User-Agent retained |
| Request retransmission | Reliable TCP stream | UDP timers excluded from TCP REGISTER, INVITE and early-media replies |
| Outgoing call destination | SIP target at registered account's domain | Existing configured targets at the local domain; no guessed destinations |
| Dialog routing | Linphone manages remote Contact and Record-Route | Existing Contact/Record-Route handling retained, using the established TCP stream |
| Connection policy | QR CLOUD: both, home-first/cloud-after-pairing, cloud-only | Explicit user-selected mode; no new automatic policy switch or attempt to bypass cloud-only permissions |
| Media encryption | Updated from PICG status reply | Existing automatic per-plant media setting and per-offer answers retained |

The TCP option is exposed in setup and options. The legacy `use_local_udp` key
continues to select local versus cloud mode; `local_transport` selects UDP or TCP
within local mode. Existing entries without the new field keep UDP. When cloud
is selected, even a stored TCP choice has no effect on cloud routing. Setup
keeps its existing registration fallback and reports when it selected cloud.
Runtime TCP reconnects to the local endpoint, without cloud DNS, TLS setup,
push-profile registration or automatic cloud fallback.

This supports signaling on the established outbound TCP connection. It does not
add a separate inbound TCP listener or open new connections to other dialog
peers. A device that requires either behavior needs further routing evidence.
The inspected app's TCP path and an accepted REGISTER do not establish that
a 40517 permits local INVITEs, delivers doorbell events, or carries local media.
The external installation's rejected calls therefore remain a material limit.

Software-only tests exercise a fake loopback TCP panel: fresh Digest registration,
stream framing with fragmented/coalesced responses and bodies, 401/407 handling,
probe cleanup, outgoing and incoming calls, Contact and Record-Route routing,
reconnect registration, and absence of UDP retransmission/cloud fallback. These
are simulated protocol results, not a hardware compatibility claim.

No working entry was changed or deployed. To roll back an eventual TCP trial,
restore the previous local/cloud selection and local transport in options. For
a cloud installation, disabling Use local SIP restores the existing TLS path;
the change neither replaces credentials nor regenerates device identity. Keep
a private configuration backup before any later live trial. The WAN-blocked
fresh-start acceptance procedure above remains required and has not been run.
