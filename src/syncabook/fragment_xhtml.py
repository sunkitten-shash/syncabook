import os.path

import jinja2

import re

from bs4 import BeautifulSoup as bs

from . import TEMPLATES_DIR
from .utils import drop_extension, get_number_of_digits_to_name

# class="Chap-Number-cn"
# everything else in a regular p

def fragment_xhtml_files(input_dir, output_dir, include_heading=False):
    """
    Adds fragments from XHTML files in `input_dir` and saves them as XHTML in `output_dir`.
    Each XHTML file consists of fragments – <span> elements with id='f[0-9]+' grouped by <p></p>.
    """
    os.makedirs(output_dir, exist_ok=True)

    input_filenames = sorted(x for x in os.listdir(input_dir) if (x.endswith('.xhtml')))
    texts_contents = []
    print(f'input_filenames: {input_filenames}')
    for filename in input_filenames:
        with open(os.path.join(input_dir, filename), 'r') as f:
            texts_contents.append(f.read())
    
    xhtmls = _text_contents_to_fixed_xhtmls(texts_contents, include_heading)

    # formatting exists here

    for filename, xhtml in zip(input_filenames, xhtmls):
        # TODO: probably don't need this for the xhtml ver of this
        file_path = os.path.join(output_dir, f'{drop_extension(filename)}.xhtml')
        with open(file_path, 'wb') as f:
            f.write(xhtml)
    
    print(f'\n✔ {len(texts_contents)} XTML files have had fragments added.\n')


# TODO: figure out if we need heading here?
def _text_contents_to_fixed_xhtmls(texts_contents, include_heading):
    xhtmls = []

    # if len(texts_contents) > 1:
    #     xhtmls.append(_process_first_fic_page(texts_contents[0], True))
    #     texts_contents = texts_contents[1:]
    # else:
    #     xhtmls.append(_process_first_fic_page(texts_contents[0]))

    for text_content in texts_contents:
        xhtmls.append(_process_page(text_content))
    return xhtmls


def _process_page(text_content):
    """
    TODO: documentation of method
    """

    paragraphs = []
    soup = bs(text_content, 'html.parser')
    # hopefully these are the paragraphs that should be used?
    paragraphs = soup.find_all('p')

    # list of all fragments (grouped by paragraph), to get a correct fragment count
    p_and_f = []
    for p in paragraphs:
        t = p.decode_contents()
        fragments = _get_fragments(t)
        p_and_f.append(fragments)
    fragments_num = sum(len(p) for p in p_and_f) + 1

    # edit stylesheet reference to reference actual stylesheet with ePub
    # this isn't needed for actual use in the reg ebook version
    # but it's useful for test ebooks to make sure everything's working peachy
    link = soup.find('link')
    link['href'] = "../styles/style.css"

    fragment_id = 1
    n = get_number_of_digits_to_name(fragments_num)
    chapter_title = soup.find('h1', {'class': 'Chap-Number-cn'})
    print(chapter_title)
    chapter_title.wrap(soup.new_tag('div', id=f'f{fragment_id:0>{n}}'))
    fragment_id += 1

    # TODO: I am...realizing that this removes anything that is not a paragraph
    # that seems....possibly problematic haha
    # give each paragraph an id and then replace them 1 by 1??
    # or just be like yeah if there's anything other than a paragraph in there
    # it's getting fucking OBLITERATED
    final_paras = []
    # I feel that you...may not need to do all this...it may be redundant...
    # WAIT try doing a thing where you clear it and then add it
    # in the same thing? cause you have the paragraph so just clear the fuckin tag
    # do this in the base branch tho
    for p in paragraphs:
        t = p.decode_contents()
        p.string = ''
        fragments = _get_fragments(t)
        for f in fragments:
            f = bs(f, 'html.parser')
            wrapper = soup.new_tag('span', id=f'f{fragment_id:0>{n}}')
            # can you. wrap. f instead?
            # also condense lines lol
            wrapper.append(f)
            p.append(wrapper)
            fragment_id += 1
        final_paras.append(p)
    

    # story.string = ''
    # for p in final_paras:
    #     story.append(p)
    # if (notes):
    #     notes.wrap(html_parse.new_tag('span', id=f'f{fragment_id:0>{n}}'))

    return soup.prettify('utf-8')


def _text_contents_to_fixed_xhtmls_old(texts_contents, include_heading):
    # get the paragraphs, which are broken up into fragment lists,
    # for each chunk of text; each chunk of text is 1 file
    texts = [_get_paragraphs(texts_content) for texts_content in texts_contents]

    # calculate total number of fragments to give fragments proper ids
    fragments_num = sum(sum(len(p) for p in t) for t in texts)
    n = get_number_of_digits_to_name(fragments_num)

    # render xhtmls
    xhtmls = []
    fragment_id = 1
    for t in texts:
        paragraphs = []
        for p in t:
            fragments = []
            for f in p:
                fragments.append({'id': f'f{fragment_id:0>{n}}', 'text': f})
                fragment_id += 1
            paragraphs.append(fragments)
    
        heading = None
        if include_heading:
            heading = {
                'id': paragraphs[0][0]['id'],
                'text': ''.join(f['text'] for f in paragraphs[0])
            }
            paragraphs = paragraphs[1:]
        
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )
        template = env.get_template('text.xhtml')
        xhtml = template.render(heading=heading, paragraphs=paragraphs)
        xhtmls.append(xhtml)

    return xhtmls


def _text_contents_to_xhtmls(texts_contents, include_heading):
    # OK. SO. get each paragraph. keep it as a <p> and then change the inner text to have the span
    # around it. Then just have that as the inside of the paragraph.
    # May need to restructure things!! Which is fine!!
    texts = [_get_paragraphs(texts_content) for texts_content in texts_contents]

    # calculate total number of fragments to give fragments proper ids
    fragments_num = sum(sum(len(p) for p in t) for t in texts)
    n = get_number_of_digits_to_name(fragments_num)

    # render xhtmls
    xhtmls = []
    fragment_id = 1
    for t in texts:
        paragraphs = []
        for p in t:
            fragments = []
            for f in p:
                fragments.append({'id': f'f{fragment_id:0>{n}}', 'text': f})
                fragment_id += 1
            paragraphs.append(fragments)

        heading = None
        if include_heading:
            heading = {
                'id': paragraphs[0][0]['id'],
                'text': ''. join(f['text'] for f in paragraphs[0])
            }
            paragraphs = paragraphs[1:]
        
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )
        template = env.get_template('text.xhtml')
        xhtml = template.render(heading=heading, paragraphs=paragraphs)
        xhtmls.append(xhtml)

    return xhtmls


# unchanged from original
def _get_paragraphs(texts_content):
    """
    Returns a list of paragraphs in a text where
    each paragraph is a list of fragments.
    """
    paragraphs = []
    for paragraphs_content in _get_paragraphs_contents(texts_content):
        fragments = _get_fragments(paragraphs_content)
        paragraphs.append(fragments)
        # so structure is:
        # paragraphs[ paragraph1['fragment1', 'fragment2'], [], [] ]
    return paragraphs


def _get_paragraphs_contents(texts_content):
    # so this returns a list of all the paragraphs in a file
    paragraphs = []
    html_parse = bs(texts_content, 'html.parser')
    # NOTE: This makes it so that *only* the story and no notes are parsed
    story = html_parse.find("div", {"class": "userstuff module"})
    return [p.get_text() for p in story.find_all("p")]


def _get_fragments(paragraphs_content):
    # returns a list of all the fragments in a paragraph
    return _get_sentences(paragraphs_content)


def _get_sentences(text):
    """
    Fragment by "{sentence_ending}{space}"
    """
    sentence_endings = {'.', '!', '?'}
    fragments = []
    sentence_start_idx = 0
    sentence_ended = False
    for i, c in enumerate(text):
        if i == len(text) - 1:
            fragments.append(text[sentence_start_idx:i+1])
        if c in sentence_endings:
            sentence_ended = True
            continue
        if sentence_ended and c == ' ':
            fragments.append(text[sentence_start_idx:i+1])
            sentence_start_idx = i+1
        sentence_ended = False
    return fragments