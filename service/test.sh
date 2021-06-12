if [ $# -lt 1 ]; then
        echo 'give 1 argument'
else
        if [ $1 = 'login' ]; then
		SESSION=$(curl -H "Content-type: application/json" -X POST -d '{"user_id":"skdlfjl","passwd":"biggong"}' http://127.0.0.1:11100/login)
                echo "$SESSION"
                echo "$SESSION" >> ret
                curl -H "Content-type: application/json" -X POST -d '{"user_id":"skdlfjl","passwd":"biggong"}' http://127.0.0.1:11100/login >> ret
        
	elif [ $1 = 'schedule-add' ]; then
		statement='{"request_type":"schedule_add","session_id":"'$2'","main_schedule":["0603 일정", "9999 일정"]}'
                echo "$statement"
                curl -H "Content-type: application/json" -X POST -d "$statement" http://127.0.0.1:11100/main >> ret
        
	elif [ $1 = 'recipe-add' ]; then
                statement='{"request_type":"recipe_add","session_id":"'$2'","main_name":["케이크1", "케이크2"]}'
                echo "$statement" 
                curl -H "Content-type: application/json" -X POST -d "$statement" http://127.0.0.1:11100/main >> ret

	fi
fi

