from flask import Flask, abort
import json
import model

app = Flask(__name__)

@app.route('/<string:username>/info', methods=['GET'])
def get_user_info(username):
    user_info = model.get_user_info(username)
    if user_info is None:
        abort(404)
    else:
        return json.dumps(user_info)

@app.route('/<string:username>/star', methods=['GET'])
def get_user_starred_repos(username):
    repos = model.get_user_starred_repo(username, filter_repos_in_db=True)
    if repos is None:
        abort(404)
    else:
        return json.dumps(repos)


@app.route('/<string:username>/predict', methods=['GET'])
def predict(username):
    predicts = model.predict(username)
    if predicts is None:
        abort(404)
    else:
        return json.dumps(predicts)


@app.route('/random', methods=['GET'])
def random_get_repos():
    return json.dumps(model.random_get_repos())


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)