from flask import Flask, request, session, render_template, send_from_directory, abort, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import string, random, re, requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///share.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["50 / minute"],
)

def get_tmp_link(url):
    r = requests.head(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; SafeShareBot; +https://closed.social/safeShare)'})
    if r.status_code != 302:
        abort(r.status_code)

    return r.headers.get('location')

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(256))
    path = db.Column(db.String(16))

@app.route('/safeShare/')
def root():
    return app.send_static_file('index.html')

@app.route('/safeShare/upload', methods=['POST'])
def upload():
    url = request.form.get('url')
    rp = request.form.get('randomPath')

    if not re.match('^https://cloud\.tsinghua\.edu\.cn/f/[a-z0-9]+/(\?dl=1)?$', url):
        abort(422)

    if not url.endswith('?dl=1'):
        url += '?dl=1'
    
    tmp = get_tmp_link(url)

    sh = Share.query.filter_by(url=url).first()
    if not sh:
        sh = Share(url=url)
        db.session.add(sh)
        db.session.commit()

        sh.path = str(sh.id)
        if rp == 'on':
            sh.path += ''.join(random.choices(string.ascii_letters, k=10))
        db.session.commit()

    perm = '/safeShare/' + sh.path

    return render_template('succ.html', tmp=tmp, perm=perm)

@app.route('/safeShare/<pn>')
def download(pn):
    sh = Share.query.filter_by(path=pn).first()
    if not sh: abort(404)

    tmp = get_tmp_link(sh.url)

    return redirect(tmp)

if __name__ == '__main__':
    app.run(debug=True)

