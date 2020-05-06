#!/bin/bash
# vim: ai ts=2 sw=2 et sts=2 ft=sh

readonly SCRIPT_DIR=$(cd $(dirname $0); pwd)
readonly SCRIPT_NAME=$(basename $0)
readonly LOCKDIR_BASE="/tmp/.lock.$SCRIPT_NAME"
LOCKDIR=""
TMPFILES=""

[ -z "$DOORBELL_NOTIFIER_CONF" ] && DOORBELL_NOTIFIER_CONF="/etc/doorbell_notifier.line.conf"

#[ -z "$LINE_API_KEY" ] &&           LINE_API_KEY="TODO:LINE_API_KEY"
#[ -z "$LINE_API_ENDPOINT" ] &&      LINE_API_ENDPOINT="https://notify-api.line.me/api/notify"
#[ -z "$DOOR_SCOPE_URL" ] &&         DOOR_SCOPE_URL="TODO:YOUR_MJPG_STREAMER_STATIC_URL"

lock() {
  if [ -z "${LOCKDIR}" ]; then
    return 1
  fi

  mkdir "${LOCKDIR}" && touch "${LOCKDIR}/$$"
  return $?
}

unlock() {
  if [ -z "${LOCKDIR}" ]; then
    return 1
  fi

  rm "${LOCKDIR}/$$" && rmdir "${LOCKDIR}"
  return $?
}

cleanup() {
  unlock
  cleanup_tmpfiles
}

cleanup_tmpfiles() {
  [ -n "$TMPFILES" ] && rm -f $TMPFILES
}

add_tmpfiles() {
  TMPFILES="$TMPFILES $*"
}

prepare() {
  LOCKDIR="${LOCKDIR_BASE}"

  if ! lock; then
    ls -l "$LOCKDIR"
    exit 1
  fi

  load_config
  trap cleanup EXIT
}

load_config() {
  if [ -r "$DOORBELL_NOTIFIER_CONF" ]; then
    source "$DOORBELL_NOTIFIER_CONF"
  fi
}

fetch_door_scope_image() {
  local tmpimg="/tmp/door_scope.$$.jpg"
  add_tmpfiles "$tmpimg"
  curl -s "$DOOR_SCOPE_URL" -o "$tmpimg"
  echo "$tmpimg"
}

crop_image() {
  local targetimg="$1"
  local tmpimg="/tmp/door_scope.$$.crop.jpg"
  add_tmpfiles "$tmpimg"
  convert "$targetimg" -crop 600x600+340+60 "$tmpimg"
  echo "$tmpimg"
}

post_to_line() {
  message="$1"
  imagefile="$2"

  curl -s -X POST -H "Authorization: Bearer $LINE_API_KEY" -F "message=$message" -F "imageFile=@$imagefile" "$LINE_API_ENDPOINT"
}

main() {
  prepare "$@"

  imagefile=$(fetch_door_scope_image)
  croppedimg=$(crop_image "$imagefile")
  post_to_line "ドアチャイムが鳴りました" "$croppedimg"
  exit 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
