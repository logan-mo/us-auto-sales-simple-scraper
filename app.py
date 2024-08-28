import re
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from bs4.element import Comment
from openai import OpenAI
import json
import dotenv

import time
from selenium import webdriver

dotenv.load_dotenv()
app = Flask(__name__)
client = OpenAI()


def tag_visible(element):
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body: str) -> str:
    soup = BeautifulSoup(body, "html.parser")
    texts = soup.findAll(string=True)
    visible_texts = filter(tag_visible, texts)
    return " ".join(t.strip() for t in visible_texts)


def text_to_json(text: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"Extract useful information about the car from the following text and display it in JSON format. Ensure the output is only valid json: \n{text}",
            }
        ],
    )

    resp1 = completion.choices[0].message.content[
        completion.choices[0].message.content.find("```json\n") + 8 :
    ]
    resp2 = resp1[: resp1.find("```")]

    return json.loads(resp2)


def scrap_html_from_page(url: str) -> str:
    driver = webdriver.Chrome()
    driver.maximize_window()

    driver.get(url)

    time.sleep(5)

    page_source = driver.execute_script("return document.documentElement.outerHTML;")

    driver.quit()
    return page_source


def convert_to_regex_pattern(input_string):
    escaped_string = input_string.replace("/", r"\/")
    regex_pattern = rf"{escaped_string}[^\s\"]+"
    return regex_pattern


def find_all_urls_on_front_page(front_page_url: str, car_page_prefix: str) -> str:
    front_page_html = scrap_html_from_page(front_page_url)
    results = re.findall(convert_to_regex_pattern(car_page_prefix), front_page_html)

    return [front_page_url + result for result in results]


def scrap_all_info_from_website(front_page_url: str, car_page_prefix: str) -> dict:
    car_pages = find_all_urls_on_front_page(front_page_url, car_page_prefix)
    car_info = {}
    for car_page in car_pages:
        car_html = scrap_html_from_page(car_page)
        car_text = text_from_html(car_html)
        car_json = text_to_json(car_text)
        car_info[car_page] = car_json
    return car_info


@app.route("/", methods=["GET", "POST"])
def home():
    concatenated_result = ""
    if request.method == "POST":
        front_page_url = request.form.get("input1", "")
        car_page_prefix = request.form.get("input2", "")
        concatenated_result = scrap_all_info_from_website(
            front_page_url, car_page_prefix
        )
    return render_template("index.html", result=concatenated_result)


@app.route("/process_input", methods=["GET", "POST"])
def process_input():
    output_json = ""
    if request.method == "POST":
        input_html = request.form["input_html"]
        output_json = text_to_json(text_from_html(input_html))
        output_json = json.dumps(output_json, indent=4)
        print(output_json)
    return render_template("input_output.html", output_json=output_json)


if __name__ == "__main__":
    app.run(debug=True)
