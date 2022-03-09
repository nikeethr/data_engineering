#!/bin/bash


TOKEN=ODQ2NTcwMjY0ODA4NzgzOTAy.YgBkKw.lOVmF8lmNETQEicplDwGwzMNzmc
GUILD_ID=944191531286429746
CHANNEL_ID=944191531286429749
RAND=0
WAIT_TIME_ALL_MSGS=20
declare -a MSG_TYPE=(
  "pm"
  "beg"
  "deposit max"
  "search"
  "crime"
  "hunt"
  "fish"
  "dig"
)

# declare -a MSG_TYPE=(
#    "beg"
#    "beg"
#    "beg"
#    "search"
#    "search"
#    "search"
#    "pm"
#    "pm"
#    "pm"
#    "hunt"
#    "hunt"
#    "hunt"
#    "fish"
#    "fish"
#    "dig"
#    "dig"
#    "bet 1500"
#    "use hoe"
# )


function post_content() {
  local __content=$1
  local __data=$(cat <<EOF
{
  "content": "pls ${__content}"
}
EOF
)

  curl --silent -X POST https://discord.com/api/v9/channels/$CHANNEL_ID/messages \
    --header "authorization: ${TOKEN}" \
    --header "content-type: application/json" \
    --output /dev/null \
    --data "${__data}"
}


while :; do
  if [ $RAND -eq 1 ]; then
    echo "RAND"
    MSG_INDEX_RND=$(($RANDOM % ${#MSG_TYPE[@]}))
    MSG="${MSG_TYPE[$MSG_INDEX_RND]}"
    while [ "${MSG_PREV}" == "${MSG}" ]; do
      echo "shuffling: ${MSG} == ${MSG_PREV}"
      MSG_INDEX_RND=$(($RANDOM % ${#MSG_TYPE[@]}))
      MSG="${MSG_TYPE[$MSG_INDEX_RND]}"
    done

    MIN_WAIT_TIME=12
    WAIT_TIME_RAND=2
    WAIT_TIME=$(($MIN_WAIT_TIME + $RANDOM % $WAIT_TIME_RAND))
    MSG_PREV="${MSG}"

    post_content "${MSG}"
    sleep $WAIT_TIME
  else
    for MSG in "${MSG_TYPE[@]}"; do
      post_content "${MSG}"
      sleep 1
    done
    WAIT_TIME_TO_CHECK=$(( $WAIT_TIME_ALL_MSGS - ${#MSG_TYPE[@]} ))
    WAIT_TIME=$(( WAIT_TIME_TO_CHECK > 0 ? WAIT_TIME_TO_CHECK : 1 ))
    sleep $WAIT_TIME
  fi

done
