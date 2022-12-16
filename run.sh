# get the current directory
# curl http://localhost:5000/evaluate_count
# post
# curl -X POST -H "Content-Type: application/json" -d '{
#   "description": "lottery",
#   "amount": 1000.0
# }' http://localhost:5000/evaluate_count


# make run.sh executable
# chmod +x run.sh

#!/bin/sh
export FLASK_APP=./evaluate.py
pipenv install numpy
pipenv install flask
pipenv install pandas
pipenv run flask --debug run -h 0.0.0.0