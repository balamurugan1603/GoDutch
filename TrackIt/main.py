from flask import Flask, render_template, redirect, request, jsonify, send_file
from flask_login import login_required, current_user, login_user, logout_user
from flask_httpauth import HTTPBasicAuth
from models import UserModel, login, db
import ast
import json


app = Flask(__name__)
authentication = HTTPBasicAuth()

app.config["SECRET_KEY"] = "XafGH12Cxhij231GB"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login.init_app(app)

login.login_view = "auth"


@app.before_first_request
def create_table():
    db.create_all()


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    if current_user.experiments is None:
        return "No Experiments found"
    experiments = ast.literal_eval(current_user.experiments)["experiments"]
    return render_template("dashboard.html", experiments = experiments)


@app.route("/experiment", methods=["GET"])
@login_required
def experiment():
    body = request.args
    experiments = ast.literal_eval(current_user.experiments)["experiments"]
    exp = None
    for experiment in experiments:
        if str(experiment["id"]) == body["id"]:
            exp = experiment
    if exp is None:
        return "404"
    return render_template("experiment.html", exp_id = experiment["id"], devices = exp["devices"])


@app.route("/download")
@login_required
def download():
    exp_id = request.args.get('exp_id')
    experiments = ast.literal_eval(current_user.experiments)["experiments"]
    exp = None
    for experiment in experiments:
        if str(experiment["id"]) == exp_id:
            exp = experiment
    if exp is None:
        return "404"
    json.dump(exp, open(f"tmp/{exp_id}.json", 'w'))
    return send_file(f"tmp/{exp_id}.json", as_attachment=True)


@app.route("/auth", methods=["GET", "POST"])
def auth():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "POST":
        if "username" in request.form.keys():
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]

            if UserModel.query.filter_by(email=email).first():
                return "Email already exist !"

            user = UserModel(email=email, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect("/dashboard")
        
        else:
            email = request.form["email"]
            user = UserModel.query.filter_by(email=email).first()
            if user is not None and user.check_password(request.form["password"]):
                login_user(user)
                return redirect("/dashboard")

    return render_template("auth.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/dashboard")


# APIs

@app.route('/experiments/getExperiments', methods=["GET"])
@authentication.login_required
def get_experiments():
    user = UserModel.query.filter_by(email=authentication.username()).first()
    if user:
        if user.experiments:
            experiments = ast.literal_eval(user.experiments)
        else:
            experiments = None
    return jsonify(experiments)


@app.route('/experiments/commit', methods=["POST"])
@authentication.login_required
def commit_experiment():
    # {
    #   experiments: [
    #   id: 56123,
    #   name: "LR-HRD",
    #   description: "Linear regression on house rent dataset",
    #   active: 1,
    #   start: "13-11-2022 10:52:12"
    #   end: "",
    #   devices: [
    #       {
    #           device_name: "0",
    #           "metrics": ""
    #       }
    #     ]
    #   ]
    # }
    body = request.get_json()
    user = UserModel.query.filter_by(email=authentication.username()).first()
    if user:
        if user.experiments:
            experiments = ast.literal_eval(user.experiments)
        else:
            experiments = None
        
        if experiments is None:
            experiments = {
                "experiments": []
            }

        exist = False
        for i in range(len(experiments["experiments"])):
            if experiments["experiments"][i]["id"] == body["id"]:
                # Device Type
                # 0 - Worker
                # 1 - Master
                if body["device_type"] == 0:
                    experiments["experiments"][i]["devices"].append({
                        "device_name": body["device_name"],
                        "metrics": body["metrics"]
                    })
                else:
                    if "end" in body.keys():
                        experiments["experiments"][i]["active"] = body["active"]
                        experiments["experiments"][i]["end"] = body["end"]
                    # else:
                    #     experiments["experiments"][i]["active"] = body["active"]
                    
                    if "weights" in body.keys():
                        experiments["experiments"][i]["weights"] = body["weights"]
                    
                exist = True

        if exist != True:
                experiments["experiments"].append({
                            "id": body["id"],
                            "name": body["name"],
                            "description": body["description"],
                            "active": body["active"],
                            "start": body["start"],
                            "end": "",
                            "devices": []
                    })

        new_user = UserModel(
            id = user.id,
            email = user.email, 
            username = user.username, 
            experiments = str(experiments),
            password_hash = user.password_hash
        )
        db.session.delete(user)
        db.session.commit()

        db.session.add(new_user)
        db.session.commit()

        updated = UserModel.query.filter_by(email=authentication.username()).first()
        # resp = {
        #     "id" : updated.id,
        #     "email" : updated.email, 
        #     "username" : updated.username, 
        #     "experiments" : experiments,
        #     "password" : updated.password_hash
        # }

        return "1" # Successful

    return "0" # Unsuccessful


@authentication.verify_password
def authenticate(email, password):
    if (email and password):
        user = UserModel.query.filter_by(email=email).first()
        if user is not None and user.check_password(password):
            return user.email
        else:
            return False
    return False


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
