from flask import Flask, render_template
import boats
import loads
import login
import oauth
import owners
import slips

app = Flask(__name__)
app.register_blueprint(boats.bp)
app.register_blueprint(loads.bp)
app.register_blueprint(slips.bp)
app.register_blueprint(login.bp)
app.register_blueprint(oauth.bp)
app.register_blueprint(owners.bp)


@app.route('/')
def index():
    return render_template(
        'index.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
