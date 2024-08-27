from flask import Flask, render_template, request
import dotenv

dotenv.load_dotenv()
app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    concatenated_result = ""
    if request.method == "POST":
        input1 = request.form.get("input1", "")
        input2 = request.form.get("input2", "")
        input3 = request.form.get("input3", "")
        concatenated_result = input1 + input2 + input3
    return render_template("index.html", result=concatenated_result)


if __name__ == "__main__":
    app.run(debug=True)
