import json
import jsonlines
import nltk
from nltk.stem.snowball import SnowballStemmer
import ast
from index import makeup_fields

index_name = 'book_index'
fields_list = ['title', 'author', 'summary_sentence', 'summary', 'character_list', 'main_ideas', 'quotes', 'picture']


def highlight(search_object, field_list):
    search_object = search_object.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    for field in field_list:
        search_object = search_object.highlight(field, fragment_size=999999999, number_of_fragments=1)


def parse_result(response_object):
    result_list = []
    for hit in response_object.hits:
        result = {}
        result['score'] = hit.meta.score
        result['id'] = hit.meta.id
        for field in hit:
            if field != 'meta':
                result[field] = getattr(hit, field)
        result['title'] = ' | '.join(result['title'])
        if 'hightlight' in hit.meta:
            for field in hit.meta.highlight:
                result[field] = getattr(hit.meta.highlight, field)[0]
        result_list.append(result)
    return result_list


def merge_good_spark(jl_file, json_file):
    stemmer = SnowballStemmer("english")
    file1_temp = {}
    file2_temp = {}

    with jsonlines.open(jl_file) as reader:
        for obj in reader:
            file1_temp[obj['name']] = obj
    with json.load(json_file) as f:
        file2_temp = f

    with jsonlines.open('merged_sparknote.jl', mode='w') as writer:
        merger_file = {}
        for book in file1_temp:
            book_name1 = set([stemmer.stem(word) for word in book['name'].split('')])
            book_name2 = set([stemmer.stem(word) for word in file2_temp.split('')])
            if book_name1 == book_name2:
                merger_file[book['name']] = book
                merger_file[book['name']]['rate'] = book_name2
        writer.write()


def generate_token_dict(corpus='sparknotes/shelve/sparknotes_book_detail_2.jl'):
    """
    To open token_dict as set:
        with open('token_dict.txt', 'r') as f:
            token_set = ast.literal_eval(f.read())
    """
    res = set()
    with jsonlines.open(corpus) as reader:
        for obj in reader:
            book = makeup_fields(obj)
            for field in [book.get(key) for key in
                          ['title', 'author', 'summary_sentence', 'summary', 'character_list_str', 'quote_str',
                           'main_ideas_str']]:
                print(field)
                if field:
                    res = res | set(nltk.word_tokenize(field.lower()))
    with open('token_dict.txt', 'w') as output:
        output.write(str(res))


def boost_fields(boost_weight):
    return list(map(lambda x, y: x + '^' + str(y), fields_list, boost_weight))


if __name__ == '__main__':
    pass
    # generate_token_dict()