from copy import copy
from multiprocessing import Process, Queue

import requests
import colorama
import sys
import threading

import time

from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from fractions import Fraction

import treelib
from treelib import Tree
from graphviz import Digraph

import _thread

tree = Tree()
main_graph = Digraph()
main_graph.clear()

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

total_urls_visited = 0

node_connections = dict()

threads = [threading.Thread]
active_threads_count = 0


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_website_links(url, parent_url=""):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    try:
        soup = BeautifulSoup(requests.get(url, timeout=1).content, "html.parser", )
    except requests.exceptions.InvalidSchema:
        return urls
    except requests.exceptions.ConnectionError:
        return urls

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if href in internal_urls:
            # already in the set
            add_node(href, parent_url, is_external=True)
            continue
        if domain_name not in href:
            # external link
            add_node(href, parent_url, is_external=True)

            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                urls.add(href)
                external_urls.add(href)
            continue
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        add_node(href, parent_url, is_external=False)
        urls.add(href)
        internal_urls.add(href)
    return urls


def crawl(url, max_depth=1, depth=1, parent_url="Parent url", total_urls_seen=0):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """

    links = get_all_website_links(url, parent_url=url)

    for link in links:
        total_urls_seen += 1
        if depth == max_depth:
            print(f"Thread has reached required depth {total_urls_seen}")
            break
        elif total_urls_seen > max_urls:
            print("Thread has seen enough")
            break
        # thread = threading.Thread(target=crawl, args=(link, max_depth, depth + 1, link, total_urls_seen))
        # thread.start()
        # thread.join(256)
        global active_threads_count
        active_threads_count += 1
        _thread.start_new_thread(crawl, (link, max_depth, depth + 1, link, total_urls_seen))
        # crawl(link, max_depth, depth + 1, link, total_urls_seen)

    active_threads_count -= 1
    return

    # crawl(link, depth=depth + 1, parentUrl=link)


def remove_protocol(url):
    if url[len(url) - 1] == "/":
        url = url[:-1]

    return copy(str(url)).replace(":", "-")


def add_node(childUrl, parentUrl, is_external=True):
    try:
        childUrl = remove_protocol(childUrl)
        parentUrl = remove_protocol(parentUrl)

        if node_connections.__contains__(parentUrl):
            node_connections.get(parentUrl).add(childUrl)
        else:
            node_connections.__setitem__(parentUrl, set(childUrl))

        tree.create_node(childUrl, childUrl, parent=parentUrl)
    except treelib.exceptions.DuplicatedNodeIdError:
        # DO NOTHING, convenience tree can't handle duplicate leaves
        return


def transform(matrix):
    return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]


def page_rank_calcualtor(vector, matrix):
    old_vector = vector
    new_vector = [Fraction() for x in range(len(vector))]
    while True:
        vector_index = 0
        for matrix_row in matrix:
            multiplication_sum = Fraction()
            index = 0
            for number in matrix_row:
                multiplication_sum = multiplication_sum.__add__(
                    old_vector[index].__mul__(number))
                index += 1
            multiplication_sum = multiplication_sum.__mul__(Fraction(8, 10))
            multiplication_sum = multiplication_sum.__add__(Fraction(2, 10).__truediv__(Fraction(len(vector), 1)))

            new_vector[vector_index] = multiplication_sum
            vector_index += 1
        # Comparing old and new vectors
        min_difference = sys.maxsize
        for index in range(len(new_vector)):
            diff = abs(old_vector[index] - new_vector[index])
            if diff < min_difference:
                min_difference = diff
        old_vector = [new_vector[x] for x in range(len(new_vector))]

        if min_difference < 0.00001:
            break

    return new_vector


def edges_filter(edges_dict):
    restart = False

    # if edges_dict is dict:
    allowed_urls = list(edges_dict.keys())

    ingoing_urls = set()
    for key_idx in range(len(allowed_urls)):
        key = allowed_urls[key_idx]
        outgoing_urls = set()
        # Take only allowed urls
        for out_url in edges_dict.get(key):
            if allowed_urls.__contains__(out_url):
                outgoing_urls.add(out_url)
        #
        if len(outgoing_urls) == 0:
            edges_dict.__delitem__(key)
            restart = True
        elif len(outgoing_urls) == 1:
            edges_dict.__delitem__(key)
            restart = True
        else:
            edges_dict.__setitem__(key, outgoing_urls)

        if restart:
            return edges_filter(edges_dict)
    return edges_dict


if __name__ == "__main__":
    import argparse

    active_threads_count = 0

    print(f"{GREEN} Max depth limit: {sys.getrecursionlimit()}{RESET}")
    sys.setrecursionlimit(12_000)

    parser = argparse.ArgumentParser(description="Link Extractor Tool with Python")
    parser.add_argument("url", help="The URL to extract links from.")
    parser.add_argument("-m", "--max-urls", help="Number of max URLs to crawl, default is 30.", default=30, type=int)
    parser.add_argument("-d", "--depth", help="Target depth of", default=1, type=int)

    args = parser.parse_args()
    url = args.url
    max_urls = args.max_urls
    max_depth = args.depth

    tree.create_node(remove_protocol(url), remove_protocol(url))  # root

    internal_urls.add(url)
    crawl(url, parent_url=url, max_depth=max_depth)
    lastLength = -1
    while active_threads_count > 0:
        # if threading.activeCount() <= 2:
        #     break
        # elif threading.activeCount() == lastLength:
        #     break
        # lastLength = threading.activeCount()
        print(f"Threads running: {active_threads_count}")
        time.sleep(30)

    print("[+] Total Internal links:", len(internal_urls))
    print("[+] Total External links:", len(external_urls))
    print("[+] Total URLs:", len(external_urls) + len(internal_urls))

    domain_name = urlparse(url).netloc

    try:
        # save the internal links to a file
        with open(f"{domain_name}_internal_links.txt", "w") as f:
            for internal_link in internal_urls:
                print(internal_link, file=f)

        # save the external links to a file
        with open(f"{domain_name}_external_links.txt", "w") as f:
            for external_link in external_urls:
                print(external_link, file=f)
    except:
        print("Could not save")

    tree.save2file('tree.txt')
    tree.to_graphviz("graph.gv")

    # tree.show()

    node_connections = edges_filter(node_connections)
    white_list = node_connections.keys()

    print(node_connections)
    print(white_list)

    for link in white_list:
        if link == remove_protocol(url):
            main_graph.node(name=remove_protocol(link), label=link, color="violet")
            continue

        if external_urls.__contains__(link):
            main_graph.node(name=remove_protocol(link), label=link, color="red")
        else:
            main_graph.node(name=remove_protocol(link), label=link, color="blue")

    for k, v in node_connections.items():
        for connectedTo in v:
            main_graph.edge(remove_protocol(k), remove_protocol(connectedTo))

    matrix = [[0 for x in range(0, len(white_list))] for y in range(0, len(white_list))]

    all_urls = list(white_list)

    if len(white_list) > 0:

        for k, v in node_connections.items():
            if not all_urls.__contains__(k):
                continue
            parentIndex = all_urls.index(k)
            divider_factor = len(v)
            for connectedTo in v:
                childIndex = all_urls.index(connectedTo)
                matrix[parentIndex][childIndex] = Fraction(1, len(v))

        for row in matrix:
            print(row)

        print("\n")

        matrix = transform(matrix)

        for row in matrix:
            print(row)

        page_rank_vector = page_rank_calcualtor(vector=[Fraction(1, len(white_list)) for j in range(len(white_list))],
                                                matrix=matrix)
        page_rank_dict = dict()

        for idx in range(len(page_rank_vector)):
            page_rank_dict.__setitem__(list(white_list)[idx], page_rank_vector[idx])

        print(f"{page_rank_dict} \n")
        print(sum(page_rank_vector))

        for k, v in page_rank_dict.items():
            print(f"page {k} has value {v.numerator / v.denominator}")

        main_graph.render(filename="PAGERANK_GRAPH.gv")
        main_graph.view()
    else:
        print("EMPTY MATRIX")
