import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from subprocess import Popen, PIPE

UPLOAD_FOLDER = "blendfiles"
ALLOWED_EXTENSIONS = set(["blend"])

children = []

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods = ["GET","POST"])
def mainPage():
  if request.method == 'POST':
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
      flash('No selected file')
      return redirect(request.url)
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      args = ["blender","-b"]
      args.append("blendfiles/" + file.filename)
      args.append("-o")
      args.append(request.form["outfile"])
      if request.form["rtype"] == "frame":
        args.append("-f")
        args.append(request.form["start"])
      else:
        args.append("-s")
        args.append(request.form["start"])
        args.append("-e")
        args.append(request.form["end"])
        args.append("-a")
      blend = Popen(args,stdout=PIPE,stderr=PIPE)
      children.append([file.filename,blend])
      return redirect(url_for("show_running"))
  return render_template("index.html")

@app.route("/renders/<filename>")
def uploaded_file(filename):
  return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/renders/")
def show_renders():
  items = os.listdir("blendfiles/")
  return render_template("renders.html",items=items)

@app.route("/running/")
def show_running():
  for i in range(len(children) - 1,-1,-1):
    print(children[i][1].poll())
    if(children[i][1].poll() != None):
      children.remove(children[i])
  res = []
  for c in children:
    res.append(c[0])
  return render_template("running.html",children=res)

@app.route("/running/<int:procid>")
def show_proc(procid):
  if procid < len(children):
    return render_template("procinfo.html", fname=children[procid][0],stdout=children[procid][1].stdout.read(), stderr=children[procid][1].stderr.read())
  else:
    return "Invalid process id"

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=9001)

