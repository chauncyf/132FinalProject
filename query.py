"""
This module implements a (partial, sample) query interface for elasticsearch movie search. 
You will need to rewrite and expand sections to support the types of queries over the fields in your UI.

Documentation for elasticsearch query DSL:
https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html

For python version of DSL:
https://elasticsearch-dsl.readthedocs.io/en/latest/

Search DSL:
https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html
"""

import re
from flask import *
from index import Book
from pprint import pprint
from elasticsearch_dsl import Q
from elasticsearch_dsl.utils import AttrList
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import helper

app = Flask(__name__, static_folder='public', static_url_path='')
index_name = 'book_index'


# display query page
@app.route("/")
def search():
    return render_template('page_query.html')


@app.route("/query_completion", methods=['GET'])
def search_query():
    search = Search(index='query_index')
    keyword = request.get_json['keyword']
    s = search.query('simple_query_string', fields=['query'], query=keyword, default_operator='and')
    start = 0
    end = 10
    results = []
    response = s[start:end].execute()
    if response.hits.total != 0:
        for hit in response.hits:
            result = {'id': hit.meta.id}
            result['title'] = hit.title[0]
            results.append(result)
    return json.dumps(results)


# display results page for first set of results and "next" sets.
@app.route("/results", methods=['GET', 'POST'])
@app.route("/results/<page>", methods=['GET', 'POST'])
def results(page):
    page_number = request.form['page_number'] or 1

    # convert the <page_number> parameter in url to integer.
    if type(page_number) is not int:
        page_number = int(page_number.encode('utf-8'))

    query = request.form['query']

    search = Search(index=index_name)

    phrase = helper.phrase_filter(query)
    phrase_list, others = phrase

    fields_list = ['title', 'author', 'summary_sentence', 'summary', 'character_list', 'main_ideas', 'quotes',
                   'picture']

    # + AND -
    # HERE WE USE SIMPLE QUERY STRING API FROM ELASTICSEARCH
    # SIMPLE QUERY STRING supports '|', '+', '-', "" phrase search， '*'， etc.
    s = search.query('simple_query_string', fields=fields_list, query=others, default_operator='and')

    # highlight
    helper.highlight(s, fields_list)

    start = 0 + (page_number - 1) * 10
    end = 10 + (page_number - 1) * 10

    message = []
    response = s[start:end].execute()
    if response.hits.total == 0 and len(others) > 0:
        message.append(f'Unknown search term: {others},switch to disjunction.')
        s = s.query('multi_match', query=others, type='cross_fields', fields=fields_list, operator='or')
        response = s[start:end].execute()

    # insert data into response
    result_list = helper.parse_result(response)

    result_num = response.hits.total
    return json.dump({result_list: result_list, result_num: result_num})


# display a particular document given a result number
@app.route("/documents/<res>", methods=['GET'])
def documents(res):
    book = Book.get(id=res, index='sample_film_index').to_dict()
    for term in book:
        if type(book[term]) is AttrList:
            s = "\n"
            for item in book[term]:
                s += item + ",\n "
            book[term] = s
    return json.dumps(book.to_dict())


# this api should return json
@app.route('/hover', methods=['POST'])
def hover_data_collect():
    form = request.form
    query_id = form.get('queryId', '')
    document_id = form.get('id', '')
    time = form.get('time', 3000)


# this api should return json
@app.route('/click', methods=['POST'])
def click_through():
    form = request.form
    query_id = form.get('queryId', '')
    document_id = form.get('id', '')


# this api should return json
@app.route('/page_stay', methods=['POST'])
def page_stay():
    form = request.form
    query_id = form.get('queryId', '')
    document_id = form.get('id', '')
    time = form.get('time', 3000)


# this api should return json
@app.route('/drag', methods=['POST'])
def drag_over_item():
    form = request.form
    query_id = form.get('queryId', '')
    document_id = form.get('id', '')


# this api should return json
@app.route('/hint', methods=['GET'])
def hint():
    form = request.form
    user_input = form.get('userInput', '')
    if len(user_input) == 0:
        return
    else:
        user_input = user_input.lower()
        last_word = user_input[user_input.rindex(' ')+1:]


if __name__ == "__main__":
    app.run()
