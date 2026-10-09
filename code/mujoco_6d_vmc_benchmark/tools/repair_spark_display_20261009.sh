#!/usr/bin/env bash
# Target-specific recovery of the pre-existing forced headless Xorg config.
# No driver/kernel installation, reboot, or training startup. Needs sudo to apply.
set -euo pipefail

display_config=/etc/X11/xorg.conf
display_backup=/etc/X11/xorg.conf.sii-backup-20261009
expected_digest=794ba039ae3fd03aef2097cf7b5015da9b74f292c23c7042d3f93ee694490b33
operation=${1:---check}

verify_original() {
    local digest
    digest=$(sha256sum -- "$1")
    [[ ${digest%% *} == "$expected_digest" ]] || {
        echo 'Configuration differs from the inspected file; refusing to overwrite it.' >&2
        exit 1
    }
}

[[ $(hostname) == spark-4eb4 ]] || {
    echo 'This recovery script is only for the inspected spark-4eb4 host.' >&2
    exit 1
}

case "$operation" in
    --check)
        if [[ -f "$display_config" ]]; then
            verify_original "$display_config"
            echo 'Original forced-headless configuration verified. No changes made.'
        elif [[ -f "$display_backup" ]]; then
            verify_original "$display_backup"
            echo 'Original configuration is backed up and disabled. No changes made.'
        else
            echo 'Expected configuration/backup not found.' >&2
            exit 1
        fi
        ;;
    --apply)
        [[ $EUID -eq 0 ]] || { echo 'Run with sudo; enter the password in your own terminal.' >&2; exit 1; }
        [[ -f "$display_config" && ! -L "$display_config" && ! -e "$display_backup" ]] || {
            echo 'Expected original file and unused backup path required; no changes made.' >&2
            exit 1
        }
        verify_original "$display_config"
        mv -T --no-clobber -- "$display_config" "$display_backup"
        [[ ! -e "$display_config" ]] || { echo 'Backup move failed.' >&2; exit 1; }
        verify_original "$display_backup"
        sync -f /etc/X11
        echo 'Original configuration preserved at /etc/X11/xorg.conf.sii-backup-20261009'
        echo 'Restarting the desktop session with automatic display detection...'
        if ! systemctl restart gdm.service; then
            echo 'Desktop restart failed; restoring original configuration.' >&2
            mv -T --no-clobber -- "$display_backup" "$display_config"
            sync -f /etc/X11
            systemctl restart gdm.service || true
            exit 1
        fi
        echo 'Desktop restarted. Check the physical monitor; service success alone does not prove video output.'
        echo 'Rollback, if needed: rerun this same script with sudo and --rollback.'
        ;;
    --rollback)
        [[ $EUID -eq 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
        [[ ! -e "$display_config" && -f "$display_backup" && ! -L "$display_backup" ]] || {
            echo 'Refusing to overwrite a new configuration or use a missing backup.' >&2
            exit 1
        }
        verify_original "$display_backup"
        mv -T --no-clobber -- "$display_backup" "$display_config"
        verify_original "$display_config"
        sync -f /etc/X11
        systemctl restart gdm.service
        echo 'Original display configuration restored.'
        ;;
    *)
        echo 'Usage: repair_spark_display_20261009.sh [--check|--apply|--rollback]' >&2
        exit 2
        ;;
esac
